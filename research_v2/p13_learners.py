"""P13 learners: DQN, tabular Q-Learning and DDPG (score relaxation + argmax) on the unchanged v0.4 environment.

Shared with PPO in P11: the 108-feature public observation, Discrete(7) actions, reward with equal weights, gamma 0.97,
the training trace streams (train_final for outer 0-19, pilot_train for tuning), the model seeds, the per-episode audit
(reward/cost identity), and interaction budgets counted in environment decisions.
"""
from pathlib import Path
import time

import gymnasium as gym
import numpy as np
import torch
from stable_baselines3 import DDPG, DQN

from .baselines import eft_scores
from .config import load_config, read_json, require, sha256
from .gym_env import OffloadingEnv, check_policy_interface
from .learning import EpisodeAudit, PilotStream, file_hash, provenance, rng_state, setup_torch, write_json

ALGORITHMS = ('dqn', 'tabq', 'ddpg')
NAMES = {'dqn': 'DQN', 'tabq': 'Q-Learning (tabular)', 'ddpg': 'DDPG (continuous score relaxation + argmax)'}
GAMMA = 0.97                       # learner v0.3, shared by every method
NET = [128, 128]                   # same hidden layers as the PPO actor and critic
EQUAL = [0.2] * 5
LOG_WINDOW = 102_400               # decision-log rows kept at the start and at the end of a run longer than 2 windows

# Registered grids (P13 design, section 4), in index order; ties in tuning go to the lower index.
GRIDS = {
    'dqn': [{'learning_rate': lr, 'target_update_interval': tu, 'exploration_fraction': ef}
            for lr in (1e-4, 3e-4) for tu in (1_000, 10_000) for ef in (0.1, 0.3)],
    'tabq': [{'alpha': a, 'eps_end': e, 'eps_fraction': f}
             for a in (0.05, 0.2) for e in (0.01, 0.05) for f in (0.1, 0.3)],
    'ddpg': [{'actor_lr': lr, 'sigma': s, 'tau': t}
             for lr in (1e-4, 1e-3) for s in (0.1, 0.3) for t in (0.005, 0.02)],
}
FIXED = {
    'dqn': {'buffer_size': 100_000, 'batch_size': 128, 'train_freq': 4, 'gradient_steps': 1, 'learning_starts': 100,
            'exploration_initial_eps': 1.0, 'exploration_final_eps': 0.05, 'tau': 1.0, 'max_grad_norm': 10.0,
            'gamma': GAMMA, 'net_arch': NET, 'activation': 'Tanh'},
    'tabq': {'q_init': 0.0, 'eps_start': 1.0, 'gamma': GAMMA, 'bins': '3 per destination: eft<=0.5d, eft<=d, eft>d',
             'state': '3^7 destination bins x 3 task classes = 6561', 'unseen_state_action': 0},
    'ddpg': {'critic_lr': 1e-3, 'buffer_size': 100_000, 'batch_size': 128, 'train_freq': 1, 'gradient_steps': 1,
             'learning_starts': 100, 'noise': 'Gaussian on the 7 scores', 'gamma': GAMMA, 'net_arch': NET,
             'activation': 'Tanh', 'action': 'argmax of 7 scores in [-1, 1]; ties to the lower index'},
}


def logged(index, budget, window=LOG_WINDOW):
    """Decision-log policy: everything for runs up to 2 windows, else the first and the last `window` decisions."""
    return budget <= 2 * window or index < window or index >= budget - window


class WindowedAudit(EpisodeAudit):
    """EpisodeAudit (every episode row, reward identity) with the windowed per-decision log."""
    def __init__(self, env, stream, directory, budget):
        super().__init__(env, stream, directory)
        self.budget, self.logged_rows = budget, 0

    def _write_decision(self, row):
        if logged(self.decisions, self.budget):
            self.logged_rows += 1
            super()._write_decision({**row, 'decision_index': self.decisions})

    def close(self):
        super().close()
        meta = Path(self.directory) / 'decisions.jsonl.gz.meta.json'
        if meta.exists():
            value = read_json(meta)
            value.update(logged_rows=self.logged_rows, window=LOG_WINDOW,
                         policy='all rows' if self.budget <= 2 * LOG_WINDOW else 'first and last window')
            write_json(meta, value)


class ScoreActions(gym.ActionWrapper):
    """DDPG relaxation: the actor outputs 7 scores in [-1, 1]; the environment executes the argmax."""
    def __init__(self, env):
        super().__init__(env)
        self.action_space = gym.spaces.Box(-1.0, 1.0, (7,), dtype=np.float32)

    def action(self, action):
        return int(np.argmax(np.asarray(action)))


def tabular_state(snapshot):
    """Public snapshot -> state index: 3 bins of estimated finish time vs deadline per destination, times task class."""
    d = snapshot['task.deadline_relative_s']
    index = 0
    for score in eft_scores(snapshot):
        index = index * 3 + (0 if score <= 0.5 * d else 1 if score <= d else 2)
    classes = [snapshot['task.class.light'], snapshot['task.class.medium'], snapshot['task.class.heavy']]
    require(sorted(classes) == [0.0, 0.0, 1.0], 'task class one-hot is not valid')
    return index * 3 + classes.index(1.0)


N_STATES = 3 ** 7 * 3


class TabularQ:
    def __init__(self, seed, budget, alpha, eps_end, eps_fraction):
        self.q = np.zeros((N_STATES, 7))
        self.visits = np.zeros((N_STATES, 7), dtype=np.int64)
        self.rng = np.random.Generator(np.random.PCG64(seed))
        self.budget, self.alpha, self.eps_end, self.eps_fraction = budget, alpha, eps_end, eps_fraction

    def epsilon(self, t):
        return 1.0 + min(1.0, t / (self.eps_fraction * self.budget)) * (self.eps_end - 1.0)

    def act(self, state, t):
        if self.rng.random() < self.epsilon(t):
            return int(self.rng.integers(7))
        return int(np.argmax(self.q[state]))

    def update(self, s, a, r, s_next, terminal):
        target = r if terminal else r + GAMMA * self.q[s_next].max()
        self.q[s, a] += self.alpha * (target - self.q[s, a])
        self.visits[s, a] += 1

    def save(self, directory):
        np.save(directory / 'q.npy', self.q)
        np.save(directory / 'visits.npy', self.visits)


def load_tabular(directory):
    q, visits = np.load(Path(directory) / 'q.npy'), np.load(Path(directory) / 'visits.npy')
    return q, visits


def make_stream(split, outer):
    config = load_config()
    if split == 'train_final':
        from .study_final import FinalStream
        return FinalStream(config, outer)
    return PilotStream(config, outer, 0, split='pilot_train')


def model_seed(config, split, outer):
    """The P11 seeds: final_model_base + outer (as PPO-Equal), pilot: candidate_model_base + 2*outer (repeat 0)."""
    s = config['seeds']
    return s['final_model_base'] + outer if split == 'train_final' else s['candidate_model_base'] + 2 * outer


def train(directory, algorithm, hp, split, outer, budget, jdk_home=None):
    """One complete training run; writes manifest, episodes, windowed decision log, final checkpoint and outcome."""
    from .study_final import TimedOffloadingEnv
    require(algorithm in ALGORITHMS and hp in GRIDS[algorithm], 'Unregistered algorithm or hyperparameters')
    require(split in ('train_final', 'pilot_train') and type(budget) is int and budget > 0, 'Invalid run plan')
    config = load_config()
    seed = model_seed(config, split, outer)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    plan = {'phase': 'P13', 'algorithm': algorithm, 'hyperparameters': hp, 'fixed': FIXED[algorithm], 'split': split,
            'outer': outer, 'model_seed': seed, 'decisions': budget, 'weights': EQUAL, 'config_sha256': sha256(config),
            'decision_log': {'window': LOG_WINDOW, 'all_rows': budget <= 2 * LOG_WINDOW}}
    write_json(directory / 'manifest.json', {**plan, 'status': 'running', 'provenance': provenance(config)})
    stream = make_stream(split, outer)
    env = None
    started = time.monotonic()
    try:
        setup_torch(config)
        env = WindowedAudit(TimedOffloadingEnv(stream, EQUAL, config=config, jdk_home=jdk_home, any_port=True, validate=False),
                            stream, directory, budget)
        checkpoint = directory / f'checkpoint_{budget:08d}'
        if algorithm == 'tabq':
            agent = TabularQ(seed, budget, **hp)
            obs, info = env.reset(seed=0)
            state = tabular_state(info['raw_snapshot'])
            for t in range(budget):
                action = agent.act(state, t)
                obs, reward, terminated, _, info = env.step(action)
                nxt = None if terminated else tabular_state(info['raw_snapshot'])
                agent.update(state, action, reward, nxt, terminated)
                if terminated and t + 1 < budget:
                    obs, info = env.reset(seed=0)
                    nxt = tabular_state(info['raw_snapshot'])
                state = nxt
            require(env.decisions == budget, 'Tabular budget mismatch')
            checkpoint.mkdir()
            agent.save(checkpoint)
            write_json(checkpoint / 'rng.json', {'bit_generator': agent.rng.bit_generator.state})
            files = {'q.npy': file_hash(checkpoint / 'q.npy'), 'visits.npy': file_hash(checkpoint / 'visits.npy')}
            extra = {'visited_states': int((agent.visits.sum(axis=1) > 0).sum()), 'states': N_STATES}
        else:
            model = sb3_model(algorithm, hp, env, seed, directory)
            initial = {k: v.detach().clone() for k, v in model.policy.state_dict().items()}
            model.learn(total_timesteps=budget)
            require(model.num_timesteps == budget == env.decisions, f'{algorithm} budget mismatch')
            require(any(not torch.equal(initial[k], v) for k, v in model.policy.state_dict().items()), 'Policy did not change')
            checkpoint.mkdir()
            model.save(checkpoint / 'model.zip')       # no replay buffer
            torch.save(rng_state(), checkpoint / 'rng.pt')
            files = {'model.zip': file_hash(checkpoint / 'model.zip')}
            extra = {'gradient_updates': int(model._n_updates)}
        write_json(checkpoint / 'state.json', {'decisions': budget, 'algorithm': algorithm, 'files': files, 'audit': env.state()})
        write_json(directory / 'outcome.json', {'status': 'complete', **plan, **extra, 'wall_s': time.monotonic() - started,
                   'rpc_wall_s': env.unwrapped.rpc_wall_s, 'audit': env.state()})
    except BaseException as error:
        write_json(directory / 'outcome.json', {'status': 'failed', 'error': repr(error)})
        raise
    finally:
        if env is not None:
            env.close()
        manifest = read_json(directory / 'manifest.json')
        manifest['status'] = read_json(directory / 'outcome.json')['status']
        write_json(directory / 'manifest.json', manifest)
    return checkpoint


def sb3_model(algorithm, hp, env, seed, directory):
    from stable_baselines3.common.logger import configure
    policy_kwargs = {'net_arch': NET, 'activation_fn': torch.nn.Tanh}
    if algorithm == 'dqn':
        f = FIXED['dqn']
        model = DQN('MlpPolicy', env, seed=seed, device='cpu', gamma=GAMMA, policy_kwargs=policy_kwargs,
                    buffer_size=f['buffer_size'], batch_size=f['batch_size'], train_freq=f['train_freq'],
                    gradient_steps=f['gradient_steps'], learning_starts=f['learning_starts'], tau=f['tau'],
                    exploration_initial_eps=f['exploration_initial_eps'], exploration_final_eps=f['exploration_final_eps'],
                    max_grad_norm=f['max_grad_norm'], **hp)
    else:
        from stable_baselines3.common.noise import NormalActionNoise
        f = FIXED['ddpg']
        model = SplitRateDDPG('MlpPolicy', ScoreActions(env), seed=seed, device='cpu', gamma=GAMMA, policy_kwargs=policy_kwargs,
                              learning_rate=hp['actor_lr'], buffer_size=f['buffer_size'], batch_size=f['batch_size'],
                              train_freq=f['train_freq'], gradient_steps=f['gradient_steps'],
                              learning_starts=f['learning_starts'], tau=hp['tau'],
                              action_noise=NormalActionNoise(np.zeros(7), hp['sigma'] * np.ones(7)))
        model.actor_lr, model.critic_lr = hp['actor_lr'], f['critic_lr']
    model.set_logger(configure(str(Path(directory) / 'sb3'), ['json']))
    return model


class SplitRateDDPG(DDPG):
    """SB3 DDPG uses one learning rate for actor and critic; the registered design uses actor_lr and critic_lr 1e-3."""
    def _update_learning_rate(self, optimizers):
        self.logger.record('train/learning_rate', self.actor_lr)
        for group in self.actor.optimizer.param_groups:
            group['lr'] = self.actor_lr
        for group in self.critic.optimizer.param_groups:
            group['lr'] = self.critic_lr


def load_policy(algorithm, checkpoint):
    """policy(obs, raw_snapshot) -> (action, unseen_state_flag). Deterministic."""
    checkpoint = Path(checkpoint)
    state = read_json(checkpoint / 'state.json')
    for name, digest in state['files'].items():
        require(file_hash(checkpoint / name) == digest, f'Checkpoint file hash mismatch: {name}')
    setup_torch(load_config())
    if algorithm == 'tabq':
        q, visits = load_tabular(checkpoint)
        seen = visits.sum(axis=1) > 0

        def policy(obs, snapshot):
            s = tabular_state(snapshot)
            return int(np.argmax(q[s])), not bool(seen[s])
        return policy
    if algorithm == 'dqn':
        model = DQN.load(checkpoint / 'model.zip', device='cpu')
        check_policy_interface(model.observation_space.shape[0], model.action_space.n)
        return lambda obs, snapshot: (int(model.predict(obs, deterministic=True)[0]), False)
    model = DDPG.load(checkpoint / 'model.zip', device='cpu', custom_objects={'action_noise': None})
    require(model.observation_space.shape == (108,) and model.action_space.shape == (7,), 'DDPG interface mismatch')
    return lambda obs, snapshot: (int(np.argmax(model.predict(obs, deterministic=True)[0])), False)
