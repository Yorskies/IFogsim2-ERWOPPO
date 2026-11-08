"""One isolated P09 job attempt. Launched only by study_runner, never resumes PPO mid-run."""
import argparse
import gzip
import os
from pathlib import Path
import resource
import shutil
import time
import traceback

from stable_baselines3 import PPO

from .config import ContractError, ROOT, load_config, read_json, require, sha256
from .learning import file_hash, write_json
from .search_runner import CandidateEvaluator
from .search_runner_extension import run as full_search
from .study_final import TimedOffloadingEnv, run_final_training, run_final_validation

ENV_PROFILES = []
INFERENCE_WALL_S = 0.0


class ProfiledEnv(TimedOffloadingEnv):
    def close(self):
        if not getattr(self, '_profile_recorded', False):
            ENV_PROFILES.append({'startup_wall_s': self.startup_wall_s, 'rpc_wall_s': self.rpc_wall_s})
            self._profile_recorded = True
        super().close()


def install_profile():
    """Passive timing only; leaves trace, action and PPO calculations unchanged."""
    from . import learning
    learning.OffloadingEnv = ProfiledEnv
    original = PPO.predict

    def predict(self, *args, **kwargs):
        global INFERENCE_WALL_S
        started = time.monotonic()
        try:
            return original(self, *args, **kwargs)
        finally:
            INFERENCE_WALL_S += time.monotonic() - started

    PPO.predict = predict


def compress_decision_logs(data):
    """Raw per-decision audit rows are ~5 KB each (~2.6 TB for the full study). Store deterministic gzip
    (mtime 0) and drop the raw copy. Runs after training/validation; it cannot affect any computation."""
    raw = packed = 0
    for meta in sorted(Path(data).glob('**/decisions.jsonl.gz.meta.json')):   # streamed by EpisodeAudit
        info = read_json(meta)
        raw += info['raw_bytes']
        packed += info['gzip_bytes']
    for source in sorted(Path(data).glob('**/decisions.jsonl')):
        target = source.with_name('decisions.jsonl.gz')
        temporary = source.with_name('.decisions.jsonl.gz.tmp')
        with source.open('rb') as reader, temporary.open('wb') as sink:
            with gzip.GzipFile(filename='', mode='wb', fileobj=sink, compresslevel=6, mtime=0) as packer:
                shutil.copyfileobj(reader, packer, 1 << 20)
            sink.flush()
            os.fsync(sink.fileno())
        os.replace(temporary, target)
        raw += source.stat().st_size
        packed += target.stat().st_size
        source.unlink()
    return raw, packed


def dependency_result(study, job):
    pointer = read_json(study / 'jobs' / job['depends_on'] / 'complete.json')
    target = study / pointer['attempt'] / 'data' / 'result.json'
    require(file_hash(target) == pointer['result_sha256'], 'Search dependency changed after completion')
    return read_json(target)


def execute(study, job, attempt, jdk_home):
    plan = read_json(study / 'protocol.json')
    config = load_config()
    require(plan['config_sha256'] == sha256(config), 'Study config drift')
    require(plan['jar_sha256'] == read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256'],
            'Study JAR drift')
    for name, digest in plan['source_hashes'].items():
        require(file_hash(ROOT / name) == digest, f'Study source drift: {name}')
    install_profile()
    data = attempt / 'data'
    budget = plan['budget']
    outer = job['outer']
    mini = plan['fixture_only']
    role = job['role']
    learner_version = plan.get('learner_version', '0.2')
    started = time.monotonic()
    if role == 'search':
        if mini:
            # One charged fixture slot. This tests orchestration, not NSGA-II quality.
            data.mkdir()
            evaluator = CandidateEvaluator(data / 'candidates', outer, budget['K'], jdk_home, learner_version=learner_version)
            weights = config['search']['equal_weights']
            evaluator(weights, 0)
            selected = evaluator.slots[0]
            result = {'status': 'complete', 'method': 'fixture', 'outer': outer,
                      'candidate_slots': 1, 'selected': selected,
                      'training_decisions': evaluator.training_decisions,
                      'validation_decisions': evaluator.validation_decisions,
                      'test_accessed': False}
            write_json(data / 'result.json', result)
        else:
            full_search(job['method'], outer, data, Path(plan['fidelity_evidence']), jdk_home)
            result = read_json(data / 'result.json')
        require(result['training_decisions'] == budget['S'] and
                result['validation_decisions'] == budget['V'], 'Search budget differs from dry-run')
    elif role == 'final':
        selected = dependency_result(study, job)['selected']
        weights = selected['weights']
        data.mkdir()
        run_final_training(data / 'training', outer, budget['F'], weights, [budget['F']], jdk_home,
                           learner_version=learner_version)
        if mini:
            run_final_validation(data / 'training' / f'checkpoint_{budget["F"]:08d}',
                                 data / 'validation_F', jdk_home)
        write_json(data / 'result.json', {'status': 'complete', 'role': role, 'outer': outer,
            'weights': weights, 'model_seed': config['seeds']['final_model_base'] + outer,
            'training_decisions': budget['F'], 'checkpoint_F': budget['F'], 'protocols': ['A', 'B'],
            'search_reused': job['depends_on'], 'test_accessed': False})
    else:
        require(role == 'baseline' and job['method'] in ('equal', 'manual'), 'Unknown P09 role')
        weights = config['search']['equal_weights' if job['method'] == 'equal' else 'manual_weights']
        data.mkdir()
        checkpoints = sorted({budget['F'], budget['B'], *([51200] if budget['B'] >= 51200 else [])})
        run_final_training(data / 'training', outer, budget['B'], weights, checkpoints, jdk_home,
                           learner_version=learner_version)
        if mini:
            run_final_validation(data / 'training' / f'checkpoint_{budget["F"]:08d}',
                                 data / 'validation_F', jdk_home)
            run_final_validation(data / 'training' / f'checkpoint_{budget["B"]:08d}',
                                 data / 'validation_B', jdk_home)
        write_json(data / 'result.json', {'status': 'complete', 'role': role, 'outer': outer,
            'method': job['method'], 'weights': weights,
            'model_seed': config['seeds']['final_model_base'] + outer,
            'training_decisions': budget['B'], 'checkpoint_F': budget['F'],
            'checkpoint_B': budget['B'], 'protocols': ['A', 'B'], 'test_accessed': False})
    result = read_json(data / 'result.json')
    raw_log_bytes, packed_log_bytes = compress_decision_logs(data)
    if role == 'search':
        startup_wall_s = sum(row['startup_wall_s'] for row in ENV_PROFILES)
        rpc_wall_s = sum(row['rpc_wall_s'] for row in ENV_PROFILES)
        gradient_updates = sum(read_json(data / 'candidates' / f'slot_{slot:03d}' /
            f'model_{repeat}' / f'checkpoint_{budget["K"]:08d}' / 'state.json')['gradient_epochs']
            for slot in range(budget['candidate_slots']) for repeat in (0, 1))
    else:
        training = read_json(data / 'training/outcome.json')
        startup_wall_s = training['startup_wall_s']
        rpc_wall_s = training['rpc_wall_s']
        gradient_updates = training['gradient_updates']
        if mini:
            labels = ['F'] if role == 'final' else ['F', 'B']
            for label in labels:
                summary = read_json(data / f'validation_{label}/summary.json')
                startup_wall_s += summary['startup_wall_s']
                rpc_wall_s += summary['rpc_wall_s']
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    write_json(attempt / 'profile.json', {'wall_s': time.monotonic() - started,
        'cpu_user_s': own.ru_utime + children.ru_utime,
        'cpu_system_s': own.ru_stime + children.ru_stime,
        'max_rss_kib': max(own.ru_maxrss, children.ru_maxrss),
        'startup_wall_s': startup_wall_s,
        'rpc_roundtrip_wall_s_including_simulation': rpc_wall_s,
        'inference_wall_s': INFERENCE_WALL_S,
        'gradient_updates': gradient_updates,
        'decision_log_raw_bytes': raw_log_bytes, 'decision_log_gzip_bytes': packed_log_bytes,
        'training_interactions': result['training_decisions'],
        'candidate_validation_interactions': result.get('validation_decisions', 0),
        'environment_instances': len(ENV_PROFILES) if role == 'search' else 1 + (1 if role == 'final' else 2) * int(mini),
        'note': 'CPU includes exited JVM children; RSS is max of worker/JVM, not summed concurrent memory.'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--job-id', required=True)
    parser.add_argument('--attempt', type=Path, required=True)
    parser.add_argument('--jdk-home', type=Path, default=Path('/usr/lib/jvm/java-21-openjdk-amd64'))
    args = parser.parse_args()
    study = args.study.resolve()
    attempt = args.attempt.resolve()
    plan = read_json(study / 'protocol.json')
    jobs = [job for job in plan['jobs'] if job['id'] == args.job_id]
    require(len(jobs) == 1, 'Unknown or duplicate study job')
    try:
        execute(study, jobs[0], attempt, args.jdk_home)
    except BaseException as error:
        kind = 'algorithmic' if isinstance(error, ContractError) else 'technical'
        write_json(attempt / 'failure.json', {'kind': kind, 'error': repr(error),
            'traceback': traceback.format_exc()[-6000:]})
        raise


if __name__ == '__main__':
    main()
