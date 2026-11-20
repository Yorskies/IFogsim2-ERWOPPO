"""Content-addressed PPO jobs for P15/P16 (generalises the P14 runner).

A job directory holds spec.json; `python -m research_v2.p15_jobs --dir D` trains (or loads a frozen checkpoint), evaluates
deterministically and writes result.json last. Identical specs hash to the same directory, so nothing is trained twice and a
restart only redoes jobs without result.json.

spec = {kind: 'train' | 'checkpoint', weights, stream: {split: train_candidate | train_final, outer, repeat}, seed, budget,
        eval: {split: dev_validation | p16_test, ids: [lo, hi]} or None (train only), log_rows, learner: '0.3', lock (p16_test only),
        checkpoint (kind 'checkpoint' only)}
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

import numpy as np

from .config import ROOT, load_config, read_json, require, sha256

JDK = '/usr/lib/jvm/java-21-openjdk-amd64'
COSTS = ('zL', 'zE', 'zD', 'zB', 'zQ')
STOP = {'requested': False}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def weights_of(w):
    a = np.asarray(w, dtype=float)
    require(a.shape == (5,) and a.min() >= 0.02 - 1e-12 and abs(a.sum() - 1) < 1e-9, f'invalid weights {w}')
    return [round(float(x), 12) for x in a]


def job_dir(root, spec):
    return Path(root) / 'runs' / sha256(spec)[:16]


def is_done(root, spec):
    return (job_dir(root, spec) / 'result.json').exists()


def result(root, spec):
    return read_json(job_dir(root, spec) / 'result.json')


def eval_rows(root, spec):
    return [json.loads(x) for x in (job_dir(root, spec) / 'eval.jsonl').read_text().splitlines() if x.strip()]


def stream_for(config, stream):
    if stream['split'] == 'train_final':
        from .study_final import FinalStream
        require(stream['repeat'] == 0, 'train_final has repeat 0 only')
        return FinalStream(config, stream['outer'])
    from .learning import PilotStream
    require(stream['split'] in ('train_candidate', 'pilot_train'), f'unknown training split {stream["split"]}')
    return PilotStream(config, stream['outer'], stream['repeat'], split=stream['split'])


def traces_for(config, ev, lock):
    if ev['split'] == 'dev_validation':
        from . import p14_traces as T
        for key in T.keys(config, tuple(ev['ids'])):
            yield key, T.generate(config, key)
        return
    require(ev['split'] == 'p16_test', f'unknown evaluation split {ev["split"]}')
    from . import p16_traces as T
    T.open_test(ROOT / lock)
    for key in T.keys(config, tuple(ev['ids'])):
        yield key, T.generate(config, key, purpose='evaluate')


def run_job(path):
    from .gym_env import OffloadingEnv, check_policy_interface
    from .learning import append_json, aggregate_costs, setup_torch
    from .learning_instrumentation import tensor_digest
    from stable_baselines3 import PPO
    directory = Path(path)
    s = read_json(directory / 'spec.json')
    for name in ('train', 'eval.jsonl', 'eval.jsonl.partial', 'result.json'):
        target = directory / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    config = load_config()
    setup_torch(config)
    started = time.monotonic()
    if s['kind'] == 'train':
        checkpoint = train(directory, s, config)
    else:
        from .learning import file_hash
        checkpoint = ROOT / s['checkpoint']
        require(read_json(checkpoint / 'state.json')['model_sha256'] == file_hash(checkpoint / 'model.zip') == s['model_sha256'],
                'frozen checkpoint hash mismatch')
    train_wall = time.monotonic() - started
    if s['eval'] is None:            # training-only job (P16 trains every final model before the test is opened)
        from .learning import file_hash
        dump(directory / 'result.json', {**s, 'checkpoint_path': checkpoint.relative_to(ROOT).as_posix(),
                                         'model_sha256': file_hash(checkpoint / 'model.zip'), 'train_wall_s': train_wall,
                                         'completed_utc': now()})
        return
    policy = PPO.load(checkpoint / 'model.zip', device='cpu')
    check_policy_interface(policy.observation_space.shape[0], policy.action_space.n)
    holder = {}
    env = OffloadingEnv(lambda seed, index: holder['trace'], s['weights'], config=config, jdk_home=JDK, any_port=True, validate=False)
    rows = []
    try:
        for key, trace in traces_for(config, s['eval'], s.get('lock')):
            holder['trace'] = trace
            obs, _ = env.reset(seed=0)
            steps, reward_sum, actions = 0, 0.0, np.zeros(7, dtype=np.int64)
            while True:
                action = int(policy.predict(obs, deterministic=True)[0])
                obs, reward, terminated, truncated, info = env.step(action)
                require(not truncated, 'evaluation episode truncated')
                steps, reward_sum = steps + 1, reward_sum + reward
                actions[action] += 1
                if terminated:
                    break
            metrics = info['summary']['metrics']
            z = [metrics['costs'][c] for c in COSTS]
            require(steps == trace['task_count'], 'evaluation did not finish the trace')
            require(np.isclose(reward_sum, -100 * np.dot(s['weights'], z), rtol=1e-6, atol=1e-8), 'reward identity failed')
            row = {'namespace': key.to_dict(), 'trace_sha256': trace['payload_sha256'], 'decisions': steps, 'reward': reward_sum,
                   'action_counts': actions.tolist(), 'metrics': metrics}
            rows.append(row)
            append_json(directory / 'eval.jsonl.partial', row)
    finally:
        env.close()
    (directory / 'eval.jsonl.partial').replace(directory / 'eval.jsonl')
    agg = aggregate_costs(rows, config['training']['workload_order'])
    dump(directory / 'result.json', {**s, 'D': agg['D_macro'], 'macro_costs': agg['macro_costs'], 'D_by_workload': agg['D_by_workload'],
                                     'train_wall_s': train_wall, 'total_wall_s': time.monotonic() - started,
                                     'action_share': (np.sum([r['action_counts'] for r in rows], axis=0) /
                                                      sum(r['decisions'] for r in rows)).tolist(),
                                     'flagged_episodes': sum(r['metrics']['diagnosis_required'] for r in rows),
                                     'policy_tensor_sha256': tensor_digest(policy.policy.state_dict()), 'completed_utc': now()})


def train(directory, s, config):
    from .learner import effective_learner
    from .learning import AuditedPPO, EpisodeAudit, ppo_kwargs
    from .study_final import TimedOffloadingEnv
    from stable_baselines3.common.logger import configure

    class FirstRowsAudit(EpisodeAudit):
        def _write_decision(self, row):
            if self.decisions < s['log_rows']:
                super()._write_decision(row)

    learner, _ = effective_learner(config, s['learner'])
    stream = stream_for(config, s['stream'])
    train_dir = directory / 'train'
    train_dir.mkdir()
    env = FirstRowsAudit(TimedOffloadingEnv(stream, s['weights'], config=config, jdk_home=JDK, any_port=True, validate=False),
                         stream, train_dir)
    try:
        model = AuditedPPO('MlpPolicy', env, seed=s['seed'], **ppo_kwargs(learner))
        model.audit_directory, model.audit_env, model.audit_checkpoint_at = train_dir, env, [s['budget']]
        model.set_logger(configure(str(train_dir / 'sb3'), ['json']))
        model.learn(total_timesteps=s['budget'])
        require(model.num_timesteps == s['budget'] == env.decisions, 'training budget mismatch')
    finally:
        env.close()
    return train_dir / f'checkpoint_{s["budget"]:08d}'


class Pool:
    """Runs jobs in separate process groups (JVMs reaped with the group); submit() ignores done/queued/running specs."""
    def __init__(self, root, workers, name, log, stopped):
        self.root, self.workers, self.name, self.log, self.stopped = Path(root), workers, name, log, stopped
        self.queue, self.keys, self.running, self.finished = [], set(), {}, 0
        self.env = {**os.environ, 'PYTHONPATH': str(ROOT)}
        self.last = time.monotonic()

    def submit(self, s):
        key = sha256(s)[:16]
        if key in self.keys or is_done(self.root, s):
            return
        self.keys.add(key)
        self.queue.append(s)

    def step(self):
        for key, (process, s) in list(self.running.items()):
            if process.poll() is None:
                continue
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            del self.running[key]
            require(process.returncode == 0 and is_done(self.root, s),
                    f'{self.name}: job {key} failed (exit {process.returncode}); see {job_dir(self.root, s) / "job.log"}')
            self.finished += 1
        self.stopped()
        while self.queue and len(self.running) < self.workers:
            s = self.queue.pop(0)
            d = job_dir(self.root, s)
            d.mkdir(parents=True, exist_ok=True)
            dump(d / 'spec.json', s)
            sink = open(d / 'job.log', 'w')
            process = subprocess.Popen([sys.executable, '-m', 'research_v2.p15_jobs', '--dir', str(d)], cwd=ROOT, env=self.env,
                                       stdout=sink, stderr=subprocess.STDOUT, start_new_session=True)
            self.running[sha256(s)[:16]] = (process, s)
        if time.monotonic() - self.last > 900:
            self.log(f'{self.name}: {self.finished} jobs finished, {len(self.running)} running, {len(self.queue)} queued')
            self.last = time.monotonic()

    @property
    def idle(self):
        return not self.queue and not self.running

    def drain(self):
        while not self.idle:
            self.step()
            time.sleep(2)

    def close(self):
        for process, _ in self.running.values():
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        for process, _ in self.running.values():
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)


def run_specs(root, specs, workers, name, log, stopped):
    pool = Pool(root, workers, name, log, stopped)
    try:
        for s in specs:
            pool.submit(s)
        log(f'{name}: {len(pool.queue)} of {len(specs)} jobs to run ({workers} workers)')
        pool.drain()
    finally:
        pool.close()
    log(f'{name}: all {len(specs)} jobs complete')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dir', required=True)
    run_job(parser.parse_args().dir)


if __name__ == '__main__':
    main()
