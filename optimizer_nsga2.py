"""
optimizer_nsga2.py
------------------
Berisi algoritma optimasi multi-objektif NSGA-II untuk pencarian 4 bobot reward optimal
[alpha (Latensi), beta (Energi), lambda (Deadline), gamma (QoS)] pada iFogSim2Env
beserta pencatatan computational overhead (candidate train/eval time dan total search time).
"""

from typing import Dict, List, Tuple
import time
import numpy as np
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.termination import get_termination

from agent_ppo import train_agent_with_weights, evaluate_agent


class RewardWeightProblem(ElementwiseProblem):
    """
    Problem definition untuk pencarian 4 bobot reward multi-objektif dengan NSGA-II.
    
    Variabel Keputusan (X): 
    - [alpha, beta, lambda, gamma] dalam rentang [0.01, 1.0].
    
    Objektif (F): 
    - F1: Memaksimalkan Latency Score (negasi)
    - F2: Memaksimalkan Energy Efficiency Score (negasi)
    - F3: Memaksimalkan Deadline Compliance Score (negasi)
    - F4: Memaksimalkan QoS Satisfaction Score (negasi)
    """

    def __init__(self, workload: str = "dynamic", timesteps_per_eval: int = 2500, eval_episodes: int = 3):
        # 4 variabel bobot (n_var=4), 4 objektif (n_obj=4)
        super().__init__(
            n_var=4,
            n_obj=4,
            n_ieq_constr=0,
            xl=np.array([0.01, 0.01, 0.01, 0.01], dtype=np.float32),
            xu=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
        )
        self.workload = workload
        self.timesteps_per_eval = timesteps_per_eval
        self.eval_episodes = eval_episodes
        self.eval_history: List[Dict] = []
        
        # Pelacakan Waktu Komputasi (Overhead)
        self.candidate_train_times: List[float] = []
        self.candidate_eval_times: List[float] = []
        self.total_search_time: float = 0.0

    def _evaluate(self, x: np.ndarray, out: dict, *args, **kwargs) -> None:
        # Normalisasi bobot sehingga total sum(weights) = 1.0
        weights = x / np.sum(x)

        # 1. Catat waktu pelatihan kandidat PPO
        t_train_start = time.perf_counter()
        agent, env = train_agent_with_weights(
            weights=weights,
            workload=self.workload,
            timesteps=self.timesteps_per_eval,
            seed=42,
            verbose=0,
        )
        t_train_end = time.perf_counter()
        self.candidate_train_times.append(t_train_end - t_train_start)

        try:
            # 2. Catat waktu evaluasi kandidat
            t_eval_start = time.perf_counter()
            metrics = evaluate_agent(agent, env, num_episodes=self.eval_episodes)
            t_eval_end = time.perf_counter()
            self.candidate_eval_times.append(t_eval_end - t_eval_start)
        finally:
            env.close()
        
        sub_rewards = metrics["mean_sub_rewards"]

        # Pymoo melakukan MINIMISASI secara default, sehingga sub-reward dinegasikan
        f1 = -sub_rewards[0]  # Latensi (alpha)
        f2 = -sub_rewards[1]  # Konsumsi Energi (beta)
        f3 = -sub_rewards[2]  # Pelanggaran Deadline (lambda)
        f4 = -sub_rewards[3]  # QoS (gamma)

        out["F"] = np.array([f1, f2, f3, f4], dtype=np.float32)

        # Catat histori evaluasi
        self.eval_history.append({
            "weights": weights.copy(),
            "sub_rewards": sub_rewards.copy(),
            "total_reward": metrics["mean_total_reward"],
            "violation_rate": metrics["mean_violation_rate"],
        })


def run_nsga2_optimization(
    workload: str = "dynamic",
    pop_size: int = 6,
    n_gen: int = 3,
    timesteps_per_eval: int = 2000,
    eval_episodes: int = 3,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, RewardWeightProblem]:
    """
    Menjalankan proses optimasi 4 bobot reward menggunakan NSGA-II pada iFogSim2.
    
    Returns:
        pareto_weights: Matriks bobot ternormalisasi [alpha, beta, lambda, gamma] pada Pareto front.
        pareto_objectives: Nilai 4 objektif sub-reward (positif).
        problem: Instance problem beserta history evaluasinya dan overhead waktu.
    """
    problem = RewardWeightProblem(
        workload=workload,
        timesteps_per_eval=timesteps_per_eval,
        eval_episodes=eval_episodes,
    )

    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=FloatRandomSampling(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
        eliminate_duplicates=True,
    )

    termination = get_termination("n_gen", n_gen)

    print(f"[NSGA-II] Memulai optimasi 4 bobot reward iFogSim2 [alpha, beta, lambda, gamma]...")
    print(f"          Workload: {workload}, Populasi: {pop_size}, Generasi: {n_gen}, Timesteps/eval: {timesteps_per_eval}")

    t_start = time.perf_counter()
    res = minimize(
        problem,
        algorithm,
        termination,
        seed=seed,
        verbose=True,
    )
    problem.total_search_time = time.perf_counter() - t_start

    # Ambil solusi pareto optimal
    if res.X is not None and len(res.X) > 0:
        opt_X = np.atleast_2d(res.X)
        opt_F = np.atleast_2d(res.F)

        pareto_weights = opt_X / np.sum(opt_X, axis=1, keepdims=True)
        pareto_objectives = -opt_F
    else:
        pareto_weights = np.array([[0.25, 0.25, 0.25, 0.25]], dtype=np.float32)
        pareto_objectives = np.array([[0.0, 0.0, 0.0, 0.0]], dtype=np.float32)

    return pareto_weights, pareto_objectives, problem
