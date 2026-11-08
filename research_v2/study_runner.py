"""P09 single-worker study runner: dry-run, isolated attempts, accounting and completed-run resume.

Full execution is gated by the audited P08 extension. Test is never opened here.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

from .config import ROOT, load_config, read_json, require, sha256
from .learning import file_hash
from .search import feasible
from .fidelity_v03 import evidence_sha256, require_fidelity_gate
from .learner import CURRENT as CURRENT_LEARNER, effective_learner
from .study_budget import build_plan, validation_trace_manifest


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
    temporary = path.with_name(path.name + f'.tmp.{os.getpid()}')
    with temporary.open('xb') as sink:
        sink.write(encoded)
        sink.flush()
        os.fsync(sink.fileno())
    os.replace(temporary, path)


def process_start(pid):
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
    except (OSError, IndexError):
        return None
    # A zombie/dead entry is not a live owner; containers whose PID 1 never reaps orphans keep them forever.
    return None if fields[0] in ('Z', 'X') else fields[19]


def boot_id():
    try:
        return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    except OSError:
        return None


class StudyLock:
    def __init__(self, root):
        self.path = Path(root) / '.owner.lock'
        self.owner = {'host': socket.gethostname(), 'boot_id': boot_id(), 'pid': os.getpid(),
                      'process_start': process_start(os.getpid()), 'child_pid': None,
                      'child_start': None, 'created_utc': now()}
        self.acquired = False

    def __enter__(self):
        if self.path.exists():
            previous = read_json(self.path)
            same_host = previous.get('host') == self.owner['host'] and previous.get('boot_id') == self.owner['boot_id']
            require(same_host, 'Study lock belongs to another host/boot; inspect before recovery')
            owner_live = process_start(previous['pid']) == previous.get('process_start')
            child_live = previous.get('child_pid') is not None and process_start(previous['child_pid']) == previous.get('child_start')
            require(not owner_live and not child_live, 'Another study owner or child is still active')
            self.path.rename(self.path.with_name(f'.owner.stale.{time.time_ns()}.json'))
        descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, 'w') as sink:
                json.dump(self.owner, sink)
                sink.flush()
                os.fsync(sink.fileno())
        except BaseException:
            self.path.unlink(missing_ok=True)
            raise
        self.acquired = True
        return self

    def child(self, pid=None):
        self.owner['child_pid'] = pid
        self.owner['child_start'] = process_start(pid) if pid is not None else None
        atomic_json(self.path, self.owner)

    def __exit__(self, exc_type, exc, tb):
        if self.acquired and self.path.exists():
            current = read_json(self.path)
            if current.get('pid') == self.owner['pid'] and current.get('process_start') == self.owner['process_start']:
                self.path.unlink()


def prepare(root, *, outers, mini=False, fidelity=None, learner_version=None):
    root = Path(root)
    config = load_config()
    if mini:
        K = 512
        require(fidelity is None, 'Fixture must not be mixed with full fidelity evidence')
        learner_version = learner_version or CURRENT_LEARNER
    else:
        require(fidelity is not None, 'Full study needs audited fidelity evidence')
        K, gated = require_fidelity_gate(fidelity)
        require(learner_version in (None, gated), 'Learner version differs from the one the fidelity gate was run with')
        learner_version = gated
    plan = build_plan(K=K, outers=outers, mini=mini, config=config)
    plan['learner_version'] = learner_version
    plan['learner'] = effective_learner(config, learner_version)[1]
    plan['prepared_utc'] = now()
    plan['jar_sha256'] = read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256']
    plan['source_hashes'] = {p.relative_to(ROOT).as_posix(): file_hash(p)
                             for p in sorted((ROOT / 'research_v2').glob('*.py'))}
    plan['fidelity_evidence'] = None if mini else str(Path(fidelity).resolve())
    plan['fidelity_result_sha256'] = None if mini else evidence_sha256(fidelity)
    root.mkdir(parents=True, exist_ok=False)
    atomic_json(root / 'protocol.json', plan)
    atomic_json(root / 'budget_report.json', budget_report(plan))
    return plan


def budget_report(plan):
    b = plan['budget']
    return {'phase': 'P09', 'fixture_only': plan['fixture_only'], 'outers': plan['outers'],
        'learner_version': plan.get('learner_version', '0.2'), 'K': b['K'], 'Ntrace': b['Ntrace'], 'S': b['S'], 'V': b['V'], 'F': b['F'],
        'C': b['C'], 'B': b['B'], 'rounding_overhead': b['rounding_overhead'],
        'physical_total_per_outer': b['physical_total_per_outer'],
        'physical_total_all_outers': len(plan['outers']) * b['physical_total_per_outer'],
        'jobs_per_outer': 4 if plan['fixture_only'] else 6,
        'artifacts': ['per-job attempts and logs', 'candidate search archive', 'final checkpoints',
                      'baseline checkpoints F/51200/B' if b['B'] >= 51200 else 'baseline checkpoints F/B',
                      'validation trace manifest', 'checksums and profiles'],
        'test_accessed': False,
        'warning': ('Fixture budgets verify orchestration only; they are not study cost.' if plan['fixture_only']
                    else 'Dry-run only: nothing is executed or prepared; test split is never opened by P09.')}


def verify_plan(root):
    root = Path(root)
    p = read_json(root / 'protocol.json')
    config = load_config()
    require(p['version'] == 'P09-study-1' and p['config_sha256'] == sha256(config), 'Study config drift')
    require(p['jar_sha256'] == read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256'],
            'Study JAR drift')
    for name, digest in p['source_hashes'].items():
        require(file_hash(ROOT / name) == digest, f'Study source drift: {name}')
    traces = validation_trace_manifest(config)
    require(traces == p['validation_traces'] and sha256(traces) == p['validation_manifest_sha256'],
            'Validation trace drift')
    version = p.get('learner_version', '0.2')
    if 'learner' in p:
        require(effective_learner(config, version)[1] == p['learner'], 'Learner protocol drift')
    if not p['fixture_only']:
        require(require_fidelity_gate(Path(p['fidelity_evidence'])) == (p['budget']['K'], version),
                'Fidelity K or learner changed')
        require(evidence_sha256(p['fidelity_evidence']) == p['fidelity_result_sha256'], 'Fidelity evidence changed')
    return p


def artifact_paths(attempt, job, budget, mini):
    data = attempt / 'data'
    paths = [attempt / 'profile.json', data / 'result.json']
    if job['role'] == 'search':
        slots = budget['candidate_slots']
        for slot in range(slots):
            base = data / 'candidates' / f'slot_{slot:03d}'
            paths.append(base / 'candidate.json')
            for repeat in (0, 1):
                train = base / f'model_{repeat}'
                checkpoint = train / f'checkpoint_{budget["K"]:08d}'
                paths.extend([train / 'manifest.json', train / 'outcome.json', train / 'decisions.jsonl.gz',
                              checkpoint / 'state.json', checkpoint / 'model.zip', checkpoint / 'rng.pt',
                              base / f'validation_{repeat}' / 'summary.json',
                              base / f'validation_{repeat}' / 'episodes.jsonl'])
    else:
        train = data / 'training'
        paths.extend([train / 'manifest.json', train / 'outcome.json', train / 'decisions.jsonl.gz'])
        checkpoints = [budget['F']] if job['role'] == 'final' else sorted({budget['F'], budget['B'],
            *([51200] if budget['B'] >= 51200 else [])})
        for n in checkpoints:
            checkpoint = train / f'checkpoint_{n:08d}'
            paths.extend([checkpoint / 'state.json', checkpoint / 'model.zip', checkpoint / 'rng.pt'])
        if mini:
            labels = ['F'] if job['role'] == 'final' else ['F', 'B']
            for label in labels:
                paths.extend([data / f'validation_{label}' / 'summary.json',
                              data / f'validation_{label}' / 'episodes.jsonl'])
    return paths


def validate_job(attempt, job, plan):
    budget = plan['budget']
    result = read_json(attempt / 'data/result.json')
    require(result['status'] == 'complete' and result['test_accessed'] is False, 'Incomplete job/result')
    tracked = artifact_paths(attempt, job, budget, plan['fixture_only'])
    require(all(p.is_file() for p in tracked), 'Missing required P09 artifact')
    hashes = {str(p.relative_to(attempt)): file_hash(p) for p in tracked}
    if job['role'] == 'search':
        require(result['candidate_slots'] == budget['candidate_slots'] and
                result['training_decisions'] == budget['S'] and result['validation_decisions'] == budget['V'],
                'Search accounting mismatch')
        feasible(result['selected']['weights'])
        for slot in range(budget['candidate_slots']):
            record = read_json(attempt / 'data/candidates' / f'slot_{slot:03d}/candidate.json')
            require(record['status'] == 'complete' and record['training_decisions'] == 2 * budget['K'] and
                    record['validation_decisions'] == 2 * budget['Ntrace'], 'Candidate accounting mismatch')
    else:
        outcome = read_json(attempt / 'data/training/outcome.json')
        manifest = read_json(attempt / 'data/training/manifest.json')
        expected = budget['F'] if job['role'] == 'final' else budget['B']
        require(outcome['status'] == manifest['status'] == 'complete' and
                outcome['decisions'] == outcome['audit']['decisions'] == expected and
                manifest['split'] == 'train_final' and manifest['outer'] == job['outer'] and
                manifest['model_seed'] == load_config()['seeds']['final_model_base'] + job['outer'],
                'Final/baseline training identity or budget mismatch')
        require(sum(outcome['audit']['decisions_by_workload'].values()) == expected,
                'Workload decision ledger mismatch')
        for n in ([budget['F']] if job['role'] == 'final' else sorted({budget['F'], budget['B'],
                  *([51200] if budget['B'] >= 51200 else [])})):
            checkpoint = attempt / 'data/training' / f'checkpoint_{n:08d}'
            state = read_json(checkpoint / 'state.json')
            require(state['decisions'] == n and state['model_sha256'] == hashes[str(
                (checkpoint / 'model.zip').relative_to(attempt))] and state['rng_sha256'] == hashes[str(
                (checkpoint / 'rng.pt').relative_to(attempt))], 'Final checkpoint corrupt')
        if plan['fixture_only']:
            for label in (['F'] if job['role'] == 'final' else ['F', 'B']):
                summary = read_json(attempt / 'data' / f'validation_{label}/summary.json')
                require(summary['status'] == 'complete' and summary['episodes'] == 20 and
                        summary['evaluation_decisions'] == budget['Ntrace'], 'Incomplete mini validation')
    return hashes


def complete_pointer(root, job):
    return root / 'jobs' / job['id'] / 'complete.json'


def verify_complete(root, job, plan):
    path = complete_pointer(root, job)
    if not path.exists():
        return False
    pointer = read_json(path)
    require(pointer['job_id'] == job['id'] and pointer['status'] == 'complete', 'Invalid completion pointer')
    attempt = root / pointer['attempt']
    require(file_hash(attempt / 'data/result.json') == pointer['result_sha256'], 'Completed result changed')
    for name, digest in pointer['artifact_sha256'].items():
        require(file_hash(attempt / name) == digest, f'Completed artifact changed: {name}')
    require(pointer['artifact_sha256'] == validate_job(attempt, job, plan), 'Completion manifest differs from artifacts')
    return True


class Interrupted(RuntimeError):
    pass


def reap_group(pgid):
    """Kill anything the exited worker left in its own session (e.g. an orphaned JVM server)."""
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def attempt_history(attempts):
    """Count technical and algorithmic failures. Interrupted attempts never consume a retry."""
    technical = algorithmic = 0
    for attempt in attempts:
        path = Path(attempt) / 'status.json'
        status = read_json(path) if path.exists() else {'status': 'interrupted'}
        if status['status'] == 'failed':
            if status.get('kind') == 'technical':
                technical += 1
            else:
                algorithmic += 1
    return technical, algorithmic


class Runner:
    def __init__(self, root, plan, jdk_home, lock):
        self.root, self.plan, self.jdk_home, self.lock = Path(root), plan, jdk_home, lock
        self.interrupted = False
        self.child = None

    def signal(self, signum, frame):
        self.interrupted = True
        if self.child is not None and self.child.poll() is None:
            os.killpg(self.child.pid, signal.SIGTERM)

    def run_job(self, job):
        if verify_complete(self.root, job, self.plan):
            print('REUSED', job['id'], flush=True)
            return
        base = self.root / 'jobs' / job['id']
        base.mkdir(parents=True, exist_ok=True)
        existing = sorted(base.glob('attempt_*'))
        for old in existing:
            status_path = old / 'status.json'
            if status_path.exists() and read_json(status_path)['status'] == 'running':
                atomic_json(status_path, {'status': 'interrupted', 'reason': 'Owner exited before completion',
                                          'ended_utc': now()})
        technical, algorithmic = attempt_history(existing)
        require(algorithmic == 0, f'Previous algorithmic failure in {job["id"]}: no automatic retry; review manually')
        max_failures = 1 + load_config()['execution']['technical_retries']
        while technical < max_failures:
            if self.interrupted:
                raise Interrupted('Runner interrupted')
            index = len(existing)
            attempt = base / f'attempt_{index:03d}'
            attempt.mkdir(exist_ok=False)
            existing.append(attempt)
            atomic_json(attempt / 'status.json', {'status': 'running', 'job_id': job['id'],
                        'attempt': index, 'started_utc': now()})
            command = [sys.executable, '-m', 'research_v2.study_worker', '--study', str(self.root.resolve()),
                       '--job-id', job['id'], '--attempt', str(attempt.resolve()),
                       '--jdk-home', str(self.jdk_home)]
            env = os.environ.copy()
            for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
                env[key] = '1'
            started = time.monotonic()
            with (attempt / 'worker.log').open('w') as sink:
                self.child = subprocess.Popen(command, cwd=ROOT, env=env, stdout=sink,
                                              stderr=subprocess.STDOUT, start_new_session=True)
                self.lock.child(self.child.pid)
                if self.interrupted:  # signal arrived before the child handle existed
                    os.killpg(self.child.pid, signal.SIGTERM)
                returncode = self.child.wait()
                reap_group(self.child.pid)
            self.child = None
            self.lock.child(None)
            if self.interrupted:
                atomic_json(attempt / 'status.json', {'status': 'interrupted', 'job_id': job['id'],
                            'attempt': index, 'wall_s': time.monotonic() - started, 'ended_utc': now()})
                raise Interrupted(f'Interrupted during {job["id"]}')
            if returncode == 0:
                hashes = validate_job(attempt, job, self.plan)
                pointer = {'status': 'complete', 'job_id': job['id'],
                           'attempt': str(attempt.relative_to(self.root)),
                           'result_sha256': hashes['data/result.json'], 'artifact_sha256': hashes,
                           'completed_utc': now()}
                atomic_json(complete_pointer(self.root, job), pointer)
                atomic_json(attempt / 'status.json', {'status': 'complete', 'job_id': job['id'],
                            'attempt': index, 'wall_s': time.monotonic() - started, 'ended_utc': now()})
                print('COMPLETE', job['id'], f'attempt={index}', flush=True)
                return
            failure = read_json(attempt / 'failure.json') if (attempt / 'failure.json').exists() else {
                'kind': 'technical', 'error': f'Worker exited {returncode} without a failure record'}
            atomic_json(attempt / 'status.json', {'status': 'failed', 'job_id': job['id'],
                        'attempt': index, 'kind': failure['kind'], 'error': failure['error'],
                        'wall_s': time.monotonic() - started, 'ended_utc': now()})
            print('FAILED', job['id'], f'attempt={index}', failure['kind'], failure['error'], flush=True)
            require(failure['kind'] == 'technical', 'Algorithmic failure: no automatic retry')
            technical += 1
        raise RuntimeError(f'Technical retry limit reached for {job["id"]}')

    def run(self, *, stop_after=None):
        old_term = signal.signal(signal.SIGTERM, self.signal)
        old_int = signal.signal(signal.SIGINT, self.signal)
        completed = 0
        try:
            for job in self.plan['jobs']:
                if job.get('depends_on'):
                    dependency = next(x for x in self.plan['jobs'] if x['id'] == job['depends_on'])
                    require(verify_complete(self.root, dependency, self.plan), 'Missing completed dependency')
                self.run_job(job)
                completed += 1
                if stop_after is not None and completed >= stop_after:
                    raise Interrupted('Controlled stop after completed job')
            self.summarize()
        finally:
            signal.signal(signal.SIGTERM, old_term)
            signal.signal(signal.SIGINT, old_int)

    def summarize(self):
        jobs = []
        for job in self.plan['jobs']:
            require(verify_complete(self.root, job, self.plan), 'Study has incomplete job')
            pointer = read_json(complete_pointer(self.root, job))
            attempt = self.root / pointer['attempt']
            result = read_json(attempt / 'data/result.json')
            profile = read_json(attempt / 'profile.json')
            jobs.append({'job': job, 'attempt': pointer['attempt'],
                         'training_decisions': result['training_decisions'],
                         'validation_decisions': result.get('validation_decisions', 0),
                         'profile': profile})
        atomic_json(self.root / 'summary.json', {'status': 'complete', 'jobs': jobs,
            'total_training_decisions': sum(x['training_decisions'] for x in jobs),
            'candidate_validation_decisions': sum(x['validation_decisions'] for x in jobs),
            'test_accessed': False, 'completed_utc': now()})


def execute(root, jdk_home, *, stop_after=None):
    root = Path(root)
    plan = verify_plan(root)
    with StudyLock(root) as lock:
        Runner(root, plan, jdk_home, lock).run(stop_after=stop_after)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('plan', 'prepare', 'run', 'resume'):
        p = sub.add_parser(name)
        p.add_argument('--study-dir', type=Path)
        p.add_argument('--outers', type=int, nargs='+')
        p.add_argument('--mini', action='store_true')
        p.add_argument('--fidelity-evidence', type=Path)
        p.add_argument('--jdk-home', type=Path, default=Path('/usr/lib/jvm/java-21-openjdk-amd64'))
        p.add_argument('--stop-after', type=int)
        p.add_argument('--learner-version', choices=('0.2', '0.3'))
    args = parser.parse_args()
    if args.command == 'plan':
        require(args.outers, 'Plan needs outer IDs')
        K, version = (512, args.learner_version or CURRENT_LEARNER) if args.mini else require_fidelity_gate(args.fidelity_evidence)
        plan = build_plan(K=K, outers=args.outers, mini=args.mini)
        plan['learner_version'] = version
        report = budget_report(plan)
        print(json.dumps(report, indent=2))
    elif args.command == 'prepare':
        require(args.study_dir is not None and args.outers, 'Prepare needs study-dir and outer IDs')
        prepare(args.study_dir, outers=args.outers, mini=args.mini, fidelity=args.fidelity_evidence,
                learner_version=args.learner_version)
        print(json.dumps(read_json(args.study_dir / 'budget_report.json'), indent=2))
    else:
        require(args.study_dir is not None, 'Run/resume needs study-dir')
        try:
            execute(args.study_dir, args.jdk_home, stop_after=args.stop_after)
        except Interrupted as error:
            print(str(error), flush=True)
            raise SystemExit(75)


if __name__ == '__main__':
    main()
