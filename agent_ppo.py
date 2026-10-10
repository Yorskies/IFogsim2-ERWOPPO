"""
agent_ppo.py
------------
Berisi konfigurasi, pembuatan, pelatihan, dan evaluasi agen PPO (Proximal Policy Optimization)
menggunakan Stable-Baselines3 untuk lingkungan iFogSim2Env (46-dim obs, Discrete 7 action).
Dilengkapi entropy bonus (ent_coef=0.03) untuk eksplorasi aktif dan pencegahan policy collapse.
"""

from typing import Dict, Optional, Tuple, Union
import gymnasium as gym
import numpy as np
import torch
from stable_baselines3 import PPO

from env_ifogsim2 import iFogSim2Env


def create_ppo_agent(
    env: gym.Env,
    learning_rate: float = 3e-4,
    n_steps: int = 256,
    batch_size: int = 64,
    n_epochs: int = 10,
    gamma: float = 0.99,
    gae_lambda: float = 0.95,
    clip_range: float = 0.2,
    ent_coef: float = 0.03,
    seed: Optional[int] = 42,
    verbose: int = 0,
) -> PPO:
    """
    Membuat instance agen PPO dari Stable-Baselines3 dengan input 46 dimensi dan output Discrete(7).
    """
    policy_kwargs = dict(
        net_arch=dict(pi=[128, 128], vf=[128, 128]),
        activation_fn=torch.nn.Tanh,
    )

    model = PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=n_epochs,
        gamma=gamma,
        gae_lambda=gae_lambda,
        clip_range=clip_range,
        ent_coef=ent_coef,
        policy_kwargs=policy_kwargs,
        seed=seed,
        verbose=verbose,
    )
    return model


def train_agent_with_weights(
    weights: np.ndarray,
    workload: str = "dynamic",
    timesteps: int = 25000,
    seed: int = 42,
    verbose: int = 0,
) -> Tuple[PPO, iFogSim2Env]:
    """
    Melatih agen PPO pada lingkungan iFogSim2Env dengan 4 bobot reward [alpha, beta, lambda, gamma].
    """
    env = iFogSim2Env(weights=weights, workload=workload)
    agent = create_ppo_agent(env=env, seed=seed, verbose=verbose)
    agent.learn(total_timesteps=timesteps)
    return agent, env


def evaluate_agent(
    agent: PPO,
    env: Optional[iFogSim2Env] = None,
    num_episodes: int = 5,
    deterministic: bool = True,
) -> Dict[str, Union[float, np.ndarray]]:
    """
    Mengevaluasi performa agen PPO terhadap 4 parameter objektif:
    - [0]: Latensi (alpha)
    - [1]: Konsumsi Energi (beta)
    - [2]: Pelanggaran Deadline (lambda)
    - [3]: QoS Satisfaction (gamma)
    """
    own_env = False
    if env is None:
        env = iFogSim2Env()
        own_env = True

    all_episode_sub_rewards = []
    all_episode_totals = []
    all_deadline_violations = []

    try:
        for ep in range(num_episodes):
            obs, info = env.reset(seed=42 + ep)
            done = False
            ep_sub_rewards = np.zeros(4, dtype=np.float32)
            ep_total_reward = 0.0
            violations_count = 0
            steps = 0

            while not done:
                action, _states = agent.predict(obs, deterministic=deterministic)
                if isinstance(action, np.ndarray):
                    action = int(action.item())

                obs, reward, terminated, truncated, info = env.step(action)
                
                sub_r = info.get("sub_rewards", np.zeros(4, dtype=np.float32))
                ep_sub_rewards += sub_r
                ep_total_reward += reward

                if info.get("is_violated", False):
                    violations_count += 1
                steps += 1

                done = terminated or truncated

            all_episode_sub_rewards.append(ep_sub_rewards)
            all_episode_totals.append(ep_total_reward)
            all_deadline_violations.append(violations_count / max(1, steps))

        mean_sub_rewards = np.mean(all_episode_sub_rewards, axis=0)
        mean_total_reward = float(np.mean(all_episode_totals))
        std_total_reward = float(np.std(all_episode_totals))
        mean_violation_rate = float(np.mean(all_deadline_violations))

        return {
            "mean_sub_rewards": mean_sub_rewards,
            "mean_total_reward": mean_total_reward,
            "std_total_reward": std_total_reward,
            "mean_violation_rate": mean_violation_rate,
        }
    finally:
        if own_env:
            env.close()
