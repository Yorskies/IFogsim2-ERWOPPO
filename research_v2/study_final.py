"""P09 final-policy training on the separate train_final namespace.

The frozen P07/P08 trainer is not changed; checkpoints still contain optimizer and RNG.
"""
from collections import Counter
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.logger import configure

from .config import load_config, read_json, require, sha256, ROOT
from .gym_env import OffloadingEnv, validate_weights, check_policy_interface
from .learning import (AuditedPPO, EpisodeAudit, COSTS, aggregate_costs, append_json, file_hash,
                       ppo_kwargs, provenance, setup_torch, write_json)
from .learning_instrumentation import tensor_digest
from .trace_access import TraceKey
from .traces import TraceGenerator


class FinalStream:
    def __init__(self, config, outer):
        require(type(outer) is int and 0 <= outer < config['seeds']['outer_runs'], 'Invalid final outer')
        self.config, self.outer = config, outer
        self.generator = TraceGenerator(config)
        self.counts = Counter()
        self.next_episode = 0
        self.current = None

    def __call__(self, seed, index):
        require(index == self.next_episode, 'Final stream counter drift')
        order = self.config['training']['workload_order']
        workload = order[(index + self.outer) % len(order)]
        trace_id = self.counts[workload]
        key = TraceKey(self.config['seeds']['master'], 'train_final', self.outer, 0, trace_id, workload)
        trace = self.generator.generate(key, role='final_trainer').to_dict()
        self.counts[workload] += 1
        self.next_episode += 1
        self.current = {'namespace': key.to_dict(), 'payload_sha256': trace['payload_sha256'],
                        'tasks': trace['task_count']}
        return trace

    def state(self):
        return {'next_episode': self.next_episode, 'counts': dict(self.counts), 'current': self.current}


class TimedOffloadingEnv(OffloadingEnv):
    def __init__(self, *args, **kwargs):
        self.rpc_wall_s = 0.0
        started = time.monotonic()
        super().__init__(*args, **kwargs)
        self.startup_wall_s = time.monotonic() - started

    def _call(self, *args, **kwargs):
        started = time.monotonic()
        try:
            return super()._call(*args, **kwargs)
        finally:
            self.rpc_wall_s += time.monotonic() - started


def run_final_training(directory, outer, decisions, weights, checkpoints, jdk_home=None, *, fast_rpc=True, worker_port=None):
    config = load_config()
    rollout = config['ppo']['n_steps']
    require(type(decisions) is int and decisions > 0 and decisions % rollout == 0, 'Invalid final budget')
    require(checkpoints and decisions in checkpoints and all(type(x) is int and 0 < x <= decisions and x % rollout == 0
        for x in checkpoints), 'Invalid final checkpoint schedule')
    weights = validate_weights(weights).tolist()
    require(min(weights) >= config['search']['weight_floor'] - 1e-12, 'Weight below simplex floor')
    stream = FinalStream(config, outer)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    plan = {'phase': 'P09', 'outer': outer, 'repeat': 0, 'model_seed': config['seeds']['final_model_base'] + outer,
            'offset': outer % 4, 'decisions': decisions, 'rollouts': decisions // rollout,
            'weights': weights, 'config_sha256': sha256(config), 'split': 'train_final',
            'evaluation_split': 'validation', 'checkpoint_at': sorted(set(checkpoints)),
            'effective_ppo': config['ppo'], 'learner_config_sha256': sha256(config),
            'partial_episode_resume': False, 'rpc_schema_validation': not fast_rpc,
            'worker_port': worker_port}
    write_json(directory / 'manifest.json', {**plan, 'status': 'running', 'provenance': provenance(config)})
    (directory / 'environment-freeze.txt').write_text(subprocess.check_output(
        [sys.executable, '-m', 'pip', 'freeze'], text=True))
    write_json(directory / 'effective_learner_config.json', config)
    env = None
    started = time.monotonic()
    try:
        setup_torch(config)
        env = EpisodeAudit(TimedOffloadingEnv(stream, weights, config=config, jdk_home=jdk_home,
                            any_port=worker_port is None, port=worker_port, validate=not fast_rpc), stream, directory)
        model = AuditedPPO('MlpPolicy', env, seed=plan['model_seed'], **ppo_kwargs(config))
        model.audit_directory, model.audit_env = directory, env
        model.audit_checkpoint_at = plan['checkpoint_at']
        model.set_logger(configure(str(directory / 'sb3'), ['json']))
        initial = {k: v.detach().clone() for k, v in model.policy.state_dict().items()}
        write_json(directory / 'initial_policy.json', {'tensor_sha256': tensor_digest(initial)})
        model.learn(total_timesteps=decisions)
        require(model.num_timesteps == decisions == env.decisions, 'Final training budget mismatch')
        changed = any(not torch.equal(initial[k], v) for k, v in model.policy.state_dict().items())
        require(changed, 'Final policy parameters did not change')
        write_json(directory / 'outcome.json', {'status': 'complete', **plan, 'policy_changed': changed,
            'wall_s': time.monotonic() - started, 'audit': env.state(),
            'startup_wall_s': env.unwrapped.startup_wall_s,
            'rpc_wall_s': env.unwrapped.rpc_wall_s,
            'gradient_updates': model._n_updates,
            'evaluation_complete': False})
    except BaseException as error:
        write_json(directory / 'outcome.json', {'status': 'failed', 'error': repr(error)})
        raise
    finally:
        if env is not None:
            env.close()
        manifest = read_json(directory / 'manifest.json')
        manifest['status'] = read_json(directory / 'outcome.json')['status']
        write_json(directory / 'manifest.json', manifest)


def run_final_validation(checkpoint, directory, jdk_home=None, *, fast_rpc=True, worker_port=None):
    """Development/validation only. Test remains inaccessible until P10 protocol lock."""
    config = load_config()
    checkpoint = Path(checkpoint)
    state = read_json(checkpoint / 'state.json')
    manifest = read_json(checkpoint.parent / 'manifest.json')
    require(manifest['split'] == 'train_final' and manifest['config_sha256'] == sha256(config),
            'Wrong final checkpoint namespace/config')
    require(state['model_sha256'] == file_hash(checkpoint / 'model.zip'), 'Final model hash mismatch')
    require(manifest['provenance']['build_receipt']['artifact_sha256'] ==
            read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256'], 'Final JAR drift')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    setup_torch(config)
    model = PPO.load(checkpoint / 'model.zip', device='cpu')
    check_policy_interface(model.observation_space.shape[0], model.action_space.n)
    generator = TraceGenerator(config)
    holder = {}
    rows = []
    inference_wall_s = 0.0
    env = TimedOffloadingEnv(lambda seed, index: holder['trace'], manifest['weights'], config=config,
                             jdk_home=jdk_home, any_port=worker_port is None, port=worker_port,
                             validate=not fast_rpc)
    try:
        for workload in config['training']['workload_order']:
            low, high = config['seeds']['validation_trace_ids']
            for trace_id in range(low, high + 1):
                key = TraceKey(config['seeds']['master'], 'validation', None, None, trace_id, workload)
                trace = generator.generate(key, role='search_validator').to_dict()
                holder['trace'] = trace
                obs, _ = env.reset(seed=0)
                reward_sum, steps = 0.0, 0
                actions = np.zeros(7, dtype=np.int64)
                while True:
                    start = time.monotonic()
                    action, _ = model.predict(obs, deterministic=True)
                    inference_wall_s += time.monotonic() - start
                    obs, reward, done, truncated, info = env.step(int(action))
                    require(not truncated, 'Final validation episode truncated')
                    reward_sum += reward
                    steps += 1
                    actions[int(action)] += 1
                    if done:
                        break
                metrics = info['summary']['metrics']
                z = [metrics['costs'][name] for name in COSTS]
                require(steps == trace['task_count'], 'Incomplete final validation trace')
                require(np.isclose(reward_sum, -100 * np.dot(manifest['weights'], z), rtol=1e-6, atol=1e-8),
                        'Final validation reward identity mismatch')
                row = {'namespace': key.to_dict(), 'trace_sha256': trace['payload_sha256'],
                       'decisions': steps, 'reward': reward_sum, 'action_counts': actions.tolist(), 'metrics': metrics}
                rows.append(row)
                append_json(directory / 'episodes.jsonl', row)
        aggregation = aggregate_costs(rows, config['training']['workload_order'])
        require(not any(r['metrics']['diagnosis_required'] for r in rows), 'Physical cost diagnosis required')
        write_json(directory / 'summary.json', {'status': 'complete', 'episodes': len(rows), 'split': 'validation',
            **aggregation, 'evaluation_mode': 'deterministic', 'checkpoint': str(checkpoint.resolve()),
            'model_sha256': state['model_sha256'], 'evaluation_decisions': sum(r['decisions'] for r in rows),
            'startup_wall_s': env.startup_wall_s, 'rpc_wall_s': env.rpc_wall_s,
            'inference_wall_s': inference_wall_s})
    finally:
        env.close()
