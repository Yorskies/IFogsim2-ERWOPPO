"""P07 pilot CLI. Only `train` and `prefix-check` perform learning; `plan` is read-only.

Checkpoints are post-update audit/evaluation artifacts, NOT resumable simulator snapshots.
"""
import argparse
import copy
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import random
import subprocess
import sys
import time

import gymnasium as gym
import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.logger import configure

from .config import ROOT, load_config, read_json, require, sha256, validate_config
from .gym_env import OffloadingEnv, validate_weights, check_policy_interface
from .trace_access import TraceKey
from .traces import TraceGenerator

COSTS = ('zL', 'zE', 'zD', 'zB', 'zQ')


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def append_json(path, value):
    with Path(path).open('a', encoding='utf-8') as sink:
        sink.write(json.dumps(value, allow_nan=False) + '\n')


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def setup_torch(config):
    p = config['ppo']
    torch.set_num_threads(p['torch_threads'])
    if torch.get_num_interop_threads() != p['torch_interop_threads']:
        torch.set_num_interop_threads(p['torch_interop_threads'])
    torch.use_deterministic_algorithms(True)


def ppo_kwargs(config):
    p = config['ppo']
    keys = ('learning_rate', 'n_steps', 'batch_size', 'n_epochs', 'gamma', 'gae_lambda',
            'clip_range', 'ent_coef', 'vf_coef', 'max_grad_norm', 'target_kl', 'normalize_advantage', 'device')
    return {**{k: p[k] for k in keys}, 'policy_kwargs': {
        'net_arch': {'pi': p['actor_layers'], 'vf': p['critic_layers']}, 'activation_fn': torch.nn.Tanh}}


def pilot_plan(config, outer, repeat, decisions, weights):
    require(outer in config['seeds']['pilot_outer_ids'], 'Only pilot outer IDs are supported in P07')
    require(type(repeat) is int and 0 <= repeat < config['search']['model_repeats'], 'Invalid pilot repeat')
    require(type(decisions) is int and decisions > 0 and decisions % config['ppo']['n_steps'] == 0,
            'Decision budget must be a positive multiple of rollout size')
    validate_weights(weights)
    require(min(weights) >= 0.02, 'P07 weight lower bound is 0.02')
    return {'phase': 'P07', 'outer': outer, 'repeat': repeat,
            'model_seed': config['seeds']['candidate_model_base'] + 2 * outer + repeat,
            'offset': (outer + repeat) % 4, 'decisions': decisions,
            'rollouts': decisions // config['ppo']['n_steps'], 'weights': list(weights),
            'config_sha256': sha256(config), 'split': 'pilot_train',
            'evaluation_split': 'pilot_validation', 'partial_episode_resume': False}


def candidate_plan(config, outer, repeat, decisions, weights):
    require(type(outer) is int and 0 <= outer < config['seeds']['outer_runs'], 'Invalid candidate outer run')
    plan=pilot_plan(config,config['seeds']['pilot_outer_ids'][0],repeat,decisions,weights)
    plan.update(phase='P08',outer=outer,model_seed=config['seeds']['candidate_model_base']+2*outer+repeat,
                offset=(outer+repeat)%4,split='train_candidate',evaluation_split='validation')
    return plan


class PilotStream:
    """Counter indexed round-robin; ignores policy/reset RNG. Per-workload trace IDs start at zero."""
    def __init__(self, config, outer, repeat, *, split='pilot_train'):
        require(split in ('pilot_train','train_candidate'), 'Unsupported training split')
        planner=pilot_plan if split=='pilot_train' else candidate_plan
        planner(config, outer, repeat, config['ppo']['n_steps'], [0.2] * 5)
        self.split=split
        self.config, self.outer, self.repeat = config, outer, repeat
        self.generator = TraceGenerator(config)
        self.counts = Counter()
        self.next_episode = 0
        self.current = None

    def __call__(self, seed, index):
        require(index == self.next_episode, 'Training episode counter drift')
        order = self.config['training']['workload_order']
        workload = order[(index + self.outer + self.repeat) % len(order)]
        trace_id = self.counts[workload]
        key = TraceKey(self.config['seeds']['master'], self.split, self.outer, self.repeat, trace_id, workload)
        trace = self.generator.generate(key, role='pilot_trainer' if self.split=='pilot_train' else 'candidate_trainer').to_dict()
        self.counts[workload] += 1
        self.next_episode += 1
        self.current = {'namespace': key.to_dict(), 'payload_sha256': trace['payload_sha256'], 'tasks': trace['task_count']}
        return trace

    def state(self):
        return {'next_episode': self.next_episode, 'counts': dict(self.counts), 'current': self.current}


class EpisodeAudit(gym.Wrapper):
    """Audit physical complete episodes and distinguish the active partial episode at budget end."""
    def __init__(self, env, stream, directory):
        super().__init__(env)
        self.stream, self.directory = stream, Path(directory)
        self.decisions = 0
        self.by_workload = Counter()
        self.actions = np.zeros(7, dtype=np.int64)
        self.reset_counters()

    def reset_counters(self):
        self.steps, self.total_reward = 0, 0.0
        self.episode_actions = np.zeros(7, dtype=np.int64)
        self.completed = False

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self.reset_counters()
        self.decision_info = info
        append_json(self.directory / 'traces.jsonl', self.stream.current)
        return obs, info

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        require(not truncated, 'Physical engine unexpectedly truncated an episode')
        require(np.isfinite(reward) and np.isfinite(obs).all(), 'Nonfinite environment output')
        append_json(self.directory / 'decisions.jsonl', {
            'episode': self.stream.state(), 'task_id': self.decision_info.get('task_id'),
            'sim_time_s': self.decision_info.get('sim_time_s'),
            'raw_snapshot': self.decision_info.get('raw_snapshot'), 'action': int(action),
            'reward': reward, 'cost_delta': np.asarray(info.get('cost_delta', [])).tolist(),
            'terminated': terminated})
        self.decision_info = info
        self.decisions += 1
        self.steps += 1
        self.total_reward += reward
        self.actions[int(action)] += 1
        self.episode_actions[int(action)] += 1
        workload = self.stream.current['namespace']['workload']
        self.by_workload[workload] += 1
        self.completed = terminated
        if terminated:
            metrics = info['summary']['metrics']
            z = np.array([metrics['costs'][k] for k in COSTS])
            expected = float(-100 * self.env.unwrapped.weights.dot(z))
            require(np.isclose(self.total_reward, expected, rtol=1e-6, atol=1e-8), 'Episode reward/cost identity failed')
            append_json(self.directory / 'episodes.jsonl', {**self.stream.current, 'decisions': self.steps,
                        'reward': self.total_reward, 'expected_reward': expected,
                        'action_counts': self.episode_actions.tolist(), 'metrics': metrics})
        return obs, reward, terminated, truncated, info

    def state(self):
        return {'decisions': self.decisions, 'decisions_by_workload': dict(self.by_workload),
                'action_counts': self.actions.tolist(), 'stream': self.stream.state(),
                'active_episode': {'decisions': self.steps, 'reward_so_far': self.total_reward,
                                   'unarrived_tasks': 0 if self.completed else self.stream.current['tasks'] - self.steps,
                                   'pending_decided_outcomes': 'unknown; not inferred from arrivals',
                                   'pending_outcomes_not_evaluated': not self.completed,
                                   'cost_cumulative': self.env.unwrapped.last_cost_cumulative.tolist(),
                                   'note': 'Unresolved includes future arrivals; decided tasks can also await outcomes. No success inferred.'}}


def rng_state():
    return {'python': random.getstate(), 'numpy': np.random.get_state(), 'torch_cpu': torch.get_rng_state()}


class AuditedPPO(PPO):
    """Hook after PPO.train, since SB3 rollout-end callbacks run BEFORE optimizer updates."""
    def _excluded_save_params(self):
        return super()._excluded_save_params() + ['audit_env', 'audit_directory', 'audit_instrumentation', 'audit_checkpoint_at']

    def train(self):
        instrument = getattr(self, 'audit_instrumentation', None)
        if instrument is None:
            super().train()
        else:
            with instrument.capture_gradients():
                super().train()
            instrument.after_update(self)
        require(all(torch.isfinite(t).all().item() for t in self.policy.parameters()), 'Nonfinite policy parameters')
        values = {}
        for key, value in self.logger.name_to_value.items():
            if key.startswith('train/') and isinstance(value, (float, int, np.number)):
                # explained_variance is undefined when returns have zero variance; explicitly label it.
                if not np.isfinite(value):
                    require(key == 'train/explained_variance', f'Nonfinite training metric: {key}')
                    values[key] = None
                else:
                    values[key] = float(value)
        values.update(decisions=self.num_timesteps, gradient_epochs=self._n_updates)
        append_json(self.audit_directory / 'learning_curve.jsonl', values)
        checkpoints=getattr(self, 'audit_checkpoint_at', None)
        if checkpoints is None or self.num_timesteps in checkpoints:
            save_checkpoint(self, self.audit_env, self.audit_directory)
        self.audit_env.unwrapped.heartbeat()


def save_checkpoint(model, env, directory):
    directory = Path(directory) / f'checkpoint_{model.num_timesteps:08d}'
    directory.mkdir(exist_ok=False)
    model.save(directory / 'model.zip')  # SB3 includes policy AND optimizer state.
    torch.save(rng_state(), directory / 'rng.pt')
    state = {'decisions': model.num_timesteps, 'gradient_epochs': model._n_updates, 'audit': env.state(),
             'model_sha256': file_hash(directory / 'model.zip'), 'rng_sha256': file_hash(directory / 'rng.pt'),
             'resume_supported': False, 'boundary': 'after PPO update; simulator state is not restorable'}
    write_json(directory / 'state.json', state)


def provenance(config):
    names = ('numpy', 'torch', 'stable-baselines3', 'gymnasium', 'jsonschema')
    paths = sorted((ROOT / 'research_v2').glob('*.py')) + sorted((ROOT / 'configs/research_v2').glob('*.json'))
    receipt = read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')
    return {'python': sys.version, 'platform': platform.platform(),
            'packages': {name: importlib.metadata.version(name) for name in names},
            'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'source_hashes': {p.relative_to(ROOT).as_posix(): file_hash(p) for p in paths},
            'config': config, 'build_receipt': receipt}


def effective_learner(config, spec_path=None):
    if spec_path is None:
        return copy.deepcopy(config), None
    spec=read_json(spec_path)
    factors={'P07-lambda-ablation-1':('gae_lambda',(0.95,1.0)),
             'P07-critic-scale-ablation-1':('vf_coef',(0.5,0.05))}
    require(spec['protocol'] in factors,'Unknown learner diagnostic protocol')
    factor,allowed=factors[spec['protocol']]
    require(spec['simulation_config_sha256']==sha256(config),'Simulation config drift')
    effective=copy.deepcopy(config);effective['ppo']=spec['ppo'];validate_config(effective)
    require(spec['ppo'][factor] in allowed,'Unsupported treatment value')
    require(all(spec['ppo'][k]==v for k,v in config['ppo'].items() if k!=factor),
            f'Ablation may vary only {factor}')
    require(spec['effective_config_sha256']==sha256(effective),'Effective learner hash mismatch')
    return effective,spec


def run_training(directory, outer, repeat, decisions, weights, jdk_home=None, *, learner_spec=None, instrument=False,
                 training_split='pilot_train', phase='P07', checkpoint_at=None, fast_rpc=False, worker_port=None):
    config = load_config()
    require(training_split in ('pilot_train','train_candidate'),'Unsupported training split')
    require(phase in ('P07','P08'),'Unsupported phase')
    planner=pilot_plan if training_split=='pilot_train' else candidate_plan
    plan = planner(config, outer, repeat, decisions, weights)
    plan['phase']=phase
    if checkpoint_at is not None:
        require(decisions in checkpoint_at and all(type(n) is int and 0<n<=decisions and n%512==0 for n in checkpoint_at), 'Invalid checkpoint schedule')
    plan.update(checkpoint_at=checkpoint_at, rpc_schema_validation=not fast_rpc, worker_port=worker_port)
    learner, spec = effective_learner(config, learner_spec)
    plan.update(effective_ppo=learner['ppo'], learner_config_sha256=sha256(learner),
                learner_protocol=spec['protocol'] if spec else '0.2', instrumentation=instrument)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    write_json(directory / 'manifest.json', {**plan, 'status': 'running', 'provenance': provenance(config)})
    (directory / 'environment-freeze.txt').write_text(subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True))
    write_json(directory / 'effective_learner_config.json', learner)
    if spec is not None:
        write_json(directory / 'learner_spec.json', spec)
    env = None
    started = time.monotonic()
    try:
        setup_torch(config)
        stream = PilotStream(config, outer, repeat, split=training_split)
        env = EpisodeAudit(OffloadingEnv(stream, weights, config=config, jdk_home=jdk_home, any_port=worker_port is None, port=worker_port, validate=not fast_rpc), stream, directory)
        model = AuditedPPO('MlpPolicy', env, seed=plan['model_seed'], **ppo_kwargs(learner))
        model.audit_directory, model.audit_env = directory, env
        model.audit_checkpoint_at=checkpoint_at
        model.set_logger(configure(str(directory / 'sb3'), ['json']))
        initial = {k: v.detach().clone() for k, v in model.policy.state_dict().items()}
        from .learning_instrumentation import RolloutInstrumentation, tensor_digest
        write_json(directory / 'initial_policy.json', {'tensor_sha256': tensor_digest(initial)})
        callback = RolloutInstrumentation(directory) if instrument else None
        if callback is not None:
            model.audit_instrumentation = callback
        model.learn(total_timesteps=decisions, callback=callback)
        require(model.num_timesteps == decisions == env.decisions, 'Actual training budget differs from plan')
        changed = any(not torch.equal(initial[k], v) for k, v in model.policy.state_dict().items())
        require(changed, 'Policy parameters did not change')
        write_json(directory / 'outcome.json', {'status': 'complete', **plan, 'policy_changed': changed,
                   'wall_s': time.monotonic() - started, 'audit': env.state(),
                   'evaluation_complete': False})
    except BaseException as error:
        write_json(directory / 'outcome.json', {'status': 'failed', 'error': repr(error)})
        raise
    finally:
        if env is not None:
            env.close()
        outcome_path = directory / 'outcome.json'
        if outcome_path.exists():
            manifest = read_json(directory / 'manifest.json')
            manifest['status'] = read_json(outcome_path)['status']
            write_json(directory / 'manifest.json', manifest)


def aggregate_costs(rows, workloads):
    means = {w: np.mean([[r['metrics']['costs'][k] for k in COSTS] for r in rows
                        if r['namespace']['workload'] == w], axis=0).tolist() for w in workloads}
    require(all(np.isfinite(v).all() for v in means.values()), 'Missing or nonfinite workload costs')
    macro = np.mean(list(means.values()), axis=0)
    return {'cost_order': COSTS, 'costs_by_workload': means, 'macro_costs': macro.tolist(),
            'D_by_workload': {w: float(np.sqrt(np.mean(np.square(v)))) for w, v in means.items()},
            'D_macro': float(np.sqrt(np.mean(np.square(macro))))}


def run_evaluation(checkpoint, directory, jdk_home=None, *, deterministic=True, split='pilot_validation', fast_rpc=False, worker_port=None):
    """Fresh JVM, complete pilot-validation episodes, deterministic actions, equal workload macro means."""
    config = load_config()
    checkpoint = Path(checkpoint)
    state = read_json(checkpoint / 'state.json')
    manifest = read_json(checkpoint.parent / 'manifest.json')
    expected={'pilot_train':'pilot_validation','train_candidate':'validation'}
    require(split==expected.get(manifest['split']), 'Training/evaluation split mismatch')
    require(manifest['config_sha256'] == sha256(config), 'Checkpoint config mismatch')
    require(state['model_sha256'] == file_hash(checkpoint / 'model.zip'), 'Checkpoint model hash mismatch')
    require(manifest['provenance']['build_receipt']['artifact_sha256'] ==
            read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256'], 'Checkpoint JAR mismatch')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    setup_torch(config)
    model = PPO.load(checkpoint / 'model.zip', device='cpu')
    if not deterministic:
        model.set_random_seed(manifest['model_seed'])
    check_policy_interface(model.observation_space.shape[0], model.action_space.n)
    generator = TraceGenerator(config)
    rows = []
    holder = {}
    env = OffloadingEnv(lambda seed, index: holder['trace'], manifest['weights'], config=config,
                        jdk_home=jdk_home, any_port=worker_port is None, port=worker_port, validate=not fast_rpc)
    try:
        for workload in config['training']['workload_order']:
            low, high = config['seeds']['validation_trace_ids']
            for trace_id in range(low, high + 1):
                key = TraceKey(config['seeds']['master'], split, None, None, trace_id, workload)
                trace = generator.generate(key, role='pilot_validator' if split=='pilot_validation' else 'search_validator').to_dict()
                holder['trace'] = trace
                obs, _ = env.reset(seed=0)
                reward_sum, steps = 0.0, 0
                actions = np.zeros(7, dtype=np.int64)
                while True:
                    action, _ = model.predict(obs, deterministic=deterministic)
                    obs, reward, done, truncated, info = env.step(int(action))
                    require(not truncated, 'Evaluation episode truncated')
                    reward_sum += reward
                    steps += 1
                    actions[int(action)] += 1
                    if done:
                        break
                metrics = info['summary']['metrics']
                z = [metrics['costs'][k] for k in COSTS]
                require(steps == trace['task_count'], 'Evaluation did not finish the entire trace')
                require(np.isclose(reward_sum, -100 * np.dot(manifest['weights'], z), rtol=1e-6, atol=1e-8),
                        'Evaluation reward identity failed')
                row = {'namespace': key.to_dict(), 'trace_sha256': trace['payload_sha256'], 'decisions': steps,
                       'reward': reward_sum, 'action_counts': actions.tolist(), 'metrics': metrics}
                rows.append(row)
                append_json(directory / 'episodes.jsonl', row)
        aggregation = aggregate_costs(rows, config['training']['workload_order'])
        require(not any(r['metrics']['diagnosis_required'] for r in rows), 'Out-of-reference costs: stop for diagnosis')
        write_json(directory / 'summary.json', {'status': 'complete', 'episodes': len(rows), 'split': split,
                   **aggregation, 'evaluation_mode': 'deterministic' if deterministic else 'diagnostic_stochastic',
                   'sampling_seed': None if deterministic else manifest['model_seed'],
                   'checkpoint': str(checkpoint.resolve()),
                   'model_sha256': state['model_sha256']})
    finally:
        env.close()


def equal_nested(a, b):
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and torch.equal(a, b)
    if isinstance(a, np.ndarray):
        return isinstance(b, np.ndarray) and np.array_equal(a, b)
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal_nested(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(equal_nested(x, y) for x, y in zip(a, b))
    return a == b


def compare_checkpoints(first, second):
    """Only inspect trusted local artifacts: torch RNG files use pickle."""
    first, second = Path(first), Path(second)
    a, b = PPO.load(first / 'model.zip', device='cpu'), PPO.load(second / 'model.zip', device='cpu')
    x, y = read_json(first / 'state.json'), read_json(second / 'state.json')
    results = {'policy_equal': equal_nested(a.policy.state_dict(), b.policy.state_dict()),
               'optimizer_equal': equal_nested(a.policy.optimizer.state_dict(), b.policy.optimizer.state_dict()),
               'counters_and_stream_equal': all(x[k] == y[k] for k in ('decisions', 'gradient_epochs', 'audit')),
               'rng_equal': equal_nested(torch.load(first / 'rng.pt', weights_only=False),
                                        torch.load(second / 'rng.pt', weights_only=False))}
    return {'pass': all(results.values()), **results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('plan', 'train', 'prefix-check'):
        p = sub.add_parser(name)
        p.add_argument('--outer', type=int, default=100)
        p.add_argument('--repeat', type=int, default=0)
        p.add_argument('--stage', choices=('smoke', 'pilot'), default='smoke')
        p.add_argument('--weights', type=float, nargs=5, default=[0.2] * 5)
        if name != 'plan':
            p.add_argument('--output-dir', type=Path, required=True)
            p.add_argument('--jdk-home', type=Path)
        if name != 'plan':
            p.add_argument('--learner-spec', type=Path)
            p.add_argument('--instrument', action='store_true')
        if name == 'prefix-check':
            p.add_argument('--prefix-decisions', type=int, default=512)
            p.add_argument('--long-decisions', type=int, default=1024)
    p = sub.add_parser('evaluate')
    p.add_argument('--checkpoint', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--jdk-home', type=Path)
    p.add_argument('--diagnostic-stochastic', action='store_true', help='Diagnostic only; does not replace deterministic protocol')
    args = parser.parse_args()
    if args.command == 'evaluate':
        run_evaluation(args.checkpoint, args.output_dir, args.jdk_home, deterministic=not args.diagnostic_stochastic)
        return
    config = load_config()
    decisions = config['training'][args.stage + '_decisions']
    plan = pilot_plan(config, args.outer, args.repeat, decisions, args.weights)
    if args.command == 'plan':
        print(json.dumps(plan, indent=2))
    elif args.command == 'train':
        run_training(args.output_dir, args.outer, args.repeat, decisions, args.weights, args.jdk_home,
                     learner_spec=args.learner_spec, instrument=args.instrument)
    else:
        pilot_plan(config, args.outer, args.repeat, args.prefix_decisions, args.weights)
        pilot_plan(config, args.outer, args.repeat, args.long_decisions, args.weights)
        require(args.long_decisions > args.prefix_decisions, 'Long budget must exceed prefix')
        args.output_dir.mkdir(parents=True, exist_ok=False)
        for name, budget in (('short', args.prefix_decisions), ('long', args.long_decisions)):
            run_training(args.output_dir / name, args.outer, args.repeat, budget, args.weights, args.jdk_home,
                         learner_spec=args.learner_spec, instrument=args.instrument)
        checkpoint = f'checkpoint_{args.prefix_decisions:08d}'
        result = compare_checkpoints(args.output_dir / 'short' / checkpoint, args.output_dir / 'long' / checkpoint)
        write_json(args.output_dir / 'comparison.json', result)
        require(result['pass'], 'Prefix equivalence failed; checkpoint reuse is forbidden')


if __name__ == '__main__':
    main()
