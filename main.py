"""
main.py
-------
Skrip utama untuk menjalankan pipeline lengkap Evolutionary Reward Weight Optimization (ERWO)
pada iFogSim2, mencakup:
1. Logging System Permanen & Audit Trail Akademik (logger.py)
2. Tahap 1: Pencarian Bobot Pareto-Optimal NSGA-II Skala Publikasi (Pop=10, Gen=4)
3. Tahap 2: Pelatihan Model RL Penuh (25.000 Timesteps)
4. Tahap 3: Benchmark Komprehensif 8 Metode (n=30 Episode, Paired Seed Protocol)
5. Tahap 4: Uji Signifikansi Statistik (Wilcoxon Signed-Rank Test & Cohen's d)
6. Ekspor Otomatis Hasil ke Data.md & Master History Ledger
"""

import os
import time
import argparse
import numpy as np

from env_ifogsim2 import iFogSim2Env
from agent_ppo import train_agent_with_weights
from optimizer_nsga2 import run_nsga2_optimization
from agent_baselines import (
    LocalOnlyPolicy,
    CloudOnlyPolicy,
    NearestFogPolicy,
    LeastLoadedFogPolicy,
    train_dqn_agent_with_weights,
    evaluate_benchmark_method,
    compute_statistical_comparison,
)
from logger import ExperimentLogger


def export_results_to_data_md(
    pareto_weights: np.ndarray,
    pareto_objectives: np.ndarray,
    best_weights: np.ndarray,
    manual_weights: np.ndarray,
    benchmark_results: dict,
    statistical_results: dict,
    overhead_results: dict,
    file_path: str = "Data.md",
) -> None:
    """Memperbarui file Data.md secara otomatis dengan seluruh nilai empiris hasil eksperimen."""
    
    # Table 10
    eq_res = benchmark_results["PPO-Equal"]
    man_res = benchmark_results["PPO-Manual"]
    erwo_res = benchmark_results["ERWO-PPO"]

    content = f"""### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\\alpha$ | $\\beta$ | $\\lambda$ | $\\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | {eq_res['latency']:.2f} | {eq_res['energy']:.2f} | {eq_res['violation_rate']:.2f} | {eq_res['load_imbalance']:.4f} | {eq_res['qos']:.2f} |
| Manual weights | {manual_weights[0]:.4f} | {manual_weights[1]:.4f} | {manual_weights[2]:.4f} | {manual_weights[3]:.4f} | {man_res['latency']:.2f} | {man_res['energy']:.2f} | {man_res['violation_rate']:.2f} | {man_res['load_imbalance']:.4f} | {man_res['qos']:.2f} |
| Optimized ($w^*$) | {best_weights[0]:.4f} | {best_weights[1]:.4f} | {best_weights[2]:.4f} | {best_weights[3]:.4f} | {erwo_res['latency']:.2f} | {erwo_res['energy']:.2f} | {erwo_res['violation_rate']:.2f} | {erwo_res['load_imbalance']:.4f} | {erwo_res['qos']:.2f} |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""

    methods_order = [
        "Local-only",
        "Cloud-only",
        "Nearest-fog",
        "Least-loaded fog",
        "DQN-Equal",
        "PPO-Equal",
        "PPO-Manual",
        "ERWO-PPO",
    ]

    for m in methods_order:
        r = benchmark_results[m]
        content += (
            f"| {m} | {r['latency']:.2f} | {r['energy']:.2f} | {r['violation_rate']:.2f} | "
            f"{r['load_imbalance']:.4f} | {r['qos']:.2f} | {r['decision_time']:.4f} |\n"
        )

    content += """
*\\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for m in ["PPO-Equal", "PPO-Manual", "ERWO-PPO"]:
        r = benchmark_results[m]
        content += (
            f"| {m} | {r['latency']:.2f} | {r['energy']:.2f} | {r['violation_rate']:.2f} | "
            f"{r['load_imbalance']:.4f} | {r['qos']:.2f} |\n"
        )

    content += """
---

### Table 13. Statistical comparison of ERWO-PPO with PPO baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :--- | :---: | :---: | :---: | :---: |
"""
    stat_order = [
        ("Latency", "ERWO-PPO vs. PPO-Equal"),
        ("Energy", "ERWO-PPO vs. PPO-Equal"),
        ("Violation rate", "ERWO-PPO vs. PPO-Equal"),
        ("Load imbalance", "ERWO-PPO vs. PPO-Equal"),
        ("QoS", "ERWO-PPO vs. PPO-Equal"),
        ("Latency", "ERWO-PPO vs. PPO-Manual"),
        ("QoS", "ERWO-PPO vs. PPO-Manual"),
    ]

    for metric, comp in stat_order:
        s = statistical_results.get((metric, comp), {})
        p_val_str = f"{s.get('p_value', 1.0):.4e}" if s.get('p_value', 1.0) < 0.001 else f"{s.get('p_value', 1.0):.4f}"
        content += (
            f"| {metric} | {comp} | {s.get('test_name', 'Wilcoxon')} | "
            f"{p_val_str} | {s.get('effect_size', 0.0):.4f} | {s.get('significant', 'NO')} |\n"
        )

    content += f"""
---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | {overhead_results['avg_cand_train']:.2f} s |
| Average candidate-evaluation time | {overhead_results['avg_cand_eval']:.2f} s |
| Total NSGA-II search time | {overhead_results['total_search_time']:.2f} s |
| Final PPO training time | {overhead_results['final_ppo_train_time']:.2f} s |
| Average ERWO-PPO decision time per task | {erwo_res['decision_time']:.4f} ms |
| Average PPO-Equal decision time per task | {eq_res['decision_time']:.4f} ms |
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n[Data.md] File berhasil diperbarui 100% dengan seluruh data eksperimen.")


def main():
    parser = argparse.ArgumentParser(description="ERWO-PPO iFogSim2 Publication Benchmark Pipeline")
    parser.add_argument("--workload", type=str, default="dynamic", choices=["light", "moderate", "heavy", "dynamic"],
                        help="Skenario workload simulasi iFogSim2 (default: dynamic)")
    parser.add_argument("--pop-size", type=int, default=10, help="Ukuran populasi NSGA-II (default: 10)")
    parser.add_argument("--generations", type=int, default=4, help="Jumlah generasi NSGA-II (default: 4)")
    parser.add_argument("--final-timesteps", type=int, default=25000, help="Timesteps pelatihan RL akhir (default: 25000)")
    parser.add_argument("--eval-episodes", type=int, default=30, help="Jumlah episode evaluasi benchmark (default: 30)")
    parser.add_argument("--tag", type=str, default=None, help="Tag identifikasi opsional untuk log eksperimen")
    args = parser.parse_args()

    # Inisialisasi Logger Permanen
    with ExperimentLogger(workload=args.workload, exp_tag=args.tag) as logger:
        logger.log_config({
            "pop_size": args.pop_size,
            "generations": args.generations,
            "final_timesteps": args.final_timesteps,
            "eval_episodes": args.eval_episodes,
            "tag": args.tag,
        })

        print("=" * 85)
        print("   ERWO-PPO: PUBLICATION-GRADE MULTI-OBJECTIVE TASK OFFLOADING BENCHMARK   ")
        print("=" * 85)
        print("Spesifikasi Environment iFogSim2 (v0.1.0):")
        print("  - Observation Space : 46 Dimensi (State iFogSim2: CPU, RAM, BW, Latensi, Antrean, Task)")
        print("  - Action Space      : Discrete(7) [0=Lokal, 1-5=Edge/Fog, 6=Cloud]")
        print("  - Multi-Objectives  : 4 Parameter [alpha=Latensi, beta=Energi, lambda=Deadline, gamma=QoS]")
        print(f"  - Workload Scenario : {args.workload.upper()}")
        print(f"  - Eval Episodes (n) : {args.eval_episodes} (Paired Seed Protocol: 1000..{1000 + args.eval_episodes - 1})")
        print(f"  - Final RL Timestep : {args.final_timesteps:,} steps")
        print(f"  - NSGA-II Config    : Pop={args.pop_size}, Gen={args.generations} (Total Evaluasi: {args.pop_size * args.generations})")
        print("-" * 85)

        # ==============================================================================
        # 1. TAHAP 1: NSGA-II PARETO OPTIMIZATION
        # ==============================================================================
        print("\n>>> TAHAP 1: Pencarian Bobot Reward Pareto-Optimal dengan NSGA-II (Table 10)")
        pareto_weights, pareto_objectives, problem = run_nsga2_optimization(
            workload=args.workload,
            pop_size=args.pop_size,
            n_gen=args.generations,
            timesteps_per_eval=2000,
            eval_episodes=3,
            seed=42,
        )

        print("\n[HASIL PARETO FRONT - 4 PARAMETER REWARD (TABLE 10)]")
        header_10 = (
            f"{'No':<3} | {'alpha(Lat)':<10} | {'beta(Eng)':<10} | {'lambda(Dead)':<12} | {'gamma(QoS)':<10} | "
            f"{'F1(Lat)':<8} | {'F2(Eng)':<8} | {'F3(Dead)':<8} | {'F4(QoS)':<8}"
        )
        print(header_10)
        print("-" * len(header_10))
        for i, (w, f) in enumerate(zip(pareto_weights, pareto_objectives)):
            print(
                f"{i+1:<3} | {w[0]:<10.4f} | {w[1]:<10.4f} | {w[2]:<12.4f} | {w[3]:<10.4f} | "
                f"{f[0]:<8.2f} | {f[1]:<8.2f} | {f[2]:<8.2f} | {f[3]:<8.2f}"
            )

        # Pemilihan Bobot Kompromi Terbaik
        total_scores = np.sum(pareto_objectives, axis=1)
        best_idx = int(np.argmax(total_scores))
        best_weights = pareto_weights[best_idx]

        print(f"\n[SELEKSI] Bobot Optimal Terpilih (Solusi Pareto #{best_idx+1}):")
        print(f"  alpha  (Latensi)              : {best_weights[0]:.4f}")
        print(f"  beta   (Konsumsi Energi)      : {best_weights[1]:.4f}")
        print(f"  lambda (Pelanggaran Deadline) : {best_weights[2]:.4f}")
        print(f"  gamma  (QoS Satisfaction)     : {best_weights[3]:.4f}")

        # Catat Pareto Front ke CSV
        logger.log_pareto_front(pareto_weights, pareto_objectives, best_idx)

        # ==============================================================================
        # 2. TAHAP 2: PELATIHAN MODEL RL UTAMA & BASELINE
        # ==============================================================================
        print("\n>>> TAHAP 2: Pelatihan Model RL (ERWO-PPO, PPO-Equal, PPO-Manual, DQN-Equal)")
        
        # 2.1 ERWO-PPO
        print(f"[1/4] Melatih ERWO-PPO (Bobot Optimal w*) selama {args.final_timesteps:,} timesteps...")
        t_start_erwo = time.perf_counter()
        erwo_agent, env_erwo = train_agent_with_weights(
            weights=best_weights,
            workload=args.workload,
            timesteps=args.final_timesteps,
            seed=42,
            verbose=0,
        )
        t_final_ppo_train = time.perf_counter() - t_start_erwo
        env_erwo.close()

        # 2.2 PPO-Equal
        equal_weights = np.array([0.25, 0.25, 0.25, 0.25], dtype=np.float32)
        print(f"[2/4] Melatih PPO-Equal (Bobot Seragam 0.25) selama {args.final_timesteps:,} timesteps...")
        ppo_equal_agent, env_eq = train_agent_with_weights(
            weights=equal_weights,
            workload=args.workload,
            timesteps=args.final_timesteps,
            seed=42,
            verbose=0,
        )
        env_eq.close()

        # 2.3 PPO-Manual
        manual_weights = np.array([0.40, 0.20, 0.30, 0.10], dtype=np.float32)
        print(f"[3/4] Melatih PPO-Manual (Bobot Manual 0.40, 0.20, 0.30, 0.10) selama {args.final_timesteps:,} timesteps...")
        ppo_manual_agent, env_man = train_agent_with_weights(
            weights=manual_weights,
            workload=args.workload,
            timesteps=args.final_timesteps,
            seed=42,
            verbose=0,
        )
        env_man.close()

        # 2.4 DQN-Equal
        print(f"[4/4] Melatih DQN-Equal (Bobot Seragam 0.25) selama {args.final_timesteps:,} timesteps...")
        dqn_agent, env_dqn = train_dqn_agent_with_weights(
            weights=equal_weights,
            workload=args.workload,
            timesteps=args.final_timesteps,
            seed=42,
            verbose=0,
        )
        env_dqn.close()

        # ==============================================================================
        # 3. TAHAP 3: BENCHMARK EVALUASI 8 METODE (PAIRED SEED: n=30)
        # ==============================================================================
        print(f"\n>>> TAHAP 3: Mengevaluasi Seluruh 8 Metode Benchmark ({args.eval_episodes} Episode Berpasangan)")
        
        benchmark_models = {
            "Local-only": LocalOnlyPolicy(),
            "Cloud-only": CloudOnlyPolicy(),
            "Nearest-fog": NearestFogPolicy(),
            "Least-loaded fog": LeastLoadedFogPolicy(),
            "DQN-Equal": dqn_agent,
            "PPO-Equal": ppo_equal_agent,
            "PPO-Manual": ppo_manual_agent,
            "ERWO-PPO": erwo_agent,
        }

        benchmark_results = {}

        for method_name, model in benchmark_models.items():
            print(f"  • Mengevaluasi {method_name}...")
            with iFogSim2Env(workload=args.workload) as eval_env:
                res = evaluate_benchmark_method(
                    model_or_policy=model,
                    env=eval_env,
                    num_episodes=args.eval_episodes,
                    base_seed=1000,
                )
                benchmark_results[method_name] = res

        # Cetak Tabel 11
        print("\n" + "=" * 100)
        print("                         TABLE 11. OVERALL PERFORMANCE COMPARISON                               ")
        print("=" * 100)
        header_11 = f"{'Method':<18} | {'Latency':<9} | {'Energy':<8} | {'Violation(%)':<13} | {'Load Imbalance':<14} | {'QoS':<8} | {'Decision(ms)':<12}"
        print(header_11)
        print("-" * len(header_11))
        for m in benchmark_models.keys():
            r = benchmark_results[m]
            print(
                f"{m:<18} | {r['latency']:<9.2f} | {r['energy']:<8.2f} | {r['violation_rate']:<13.2f} | "
                f"{r['load_imbalance']:<14.4f} | {r['qos']:<8.2f} | {r['decision_time']:<12.4f}"
            )
        print("=" * 100)

        # Cetak Tabel 12
        print("\n" + "=" * 90)
        print("                  TABLE 12. ABLATION STUDY OF PPO REWARD CONFIGURATIONS                 ")
        print("=" * 90)
        header_12 = f"{'Configuration':<18} | {'Latency Score':<14} | {'Energy Efficiency':<18} | {'Violation Rate(%)':<17} | {'Load Imbalance':<14} | {'QoS':<8}"
        print(header_12)
        print("-" * len(header_12))
        for m in ["PPO-Equal", "PPO-Manual", "ERWO-PPO"]:
            r = benchmark_results[m]
            print(
                f"{m:<18} | {r['latency']:<14.2f} | {r['energy']:<18.2f} | {r['violation_rate']:<17.2f} | "
                f"{r['load_imbalance']:<14.4f} | {r['qos']:<8.2f}"
            )
        print("=" * 90)

        # Catat Data Benchmark ke JSON & CSV
        logger.log_benchmark_results(benchmark_results)

        # ==============================================================================
        # 4. TAHAP 4: UJI STATISTIK SIGNIFIKANSI (TABLE 13)
        # ==============================================================================
        print("\n>>> TAHAP 4: Pengujian Signifikansi Statistik (Table 13)")
        
        erwo_raw = benchmark_results["ERWO-PPO"]["raw"]
        ppo_eq_raw = benchmark_results["PPO-Equal"]["raw"]
        ppo_man_raw = benchmark_results["PPO-Manual"]["raw"]

        stat_comparisons = [
            ("Latency", "ERWO-PPO vs. PPO-Equal", erwo_raw["latency"], ppo_eq_raw["latency"]),
            ("Energy", "ERWO-PPO vs. PPO-Equal", erwo_raw["energy"], ppo_eq_raw["energy"]),
            ("Violation rate", "ERWO-PPO vs. PPO-Equal", erwo_raw["violation_rate"], ppo_eq_raw["violation_rate"]),
            ("Load imbalance", "ERWO-PPO vs. PPO-Equal", erwo_raw["load_imbalance"], ppo_eq_raw["load_imbalance"]),
            ("QoS", "ERWO-PPO vs. PPO-Equal", erwo_raw["qos"], ppo_eq_raw["qos"]),
            ("Latency", "ERWO-PPO vs. PPO-Manual", erwo_raw["latency"], ppo_man_raw["latency"]),
            ("QoS", "ERWO-PPO vs. PPO-Manual", erwo_raw["qos"], ppo_man_raw["qos"]),
        ]

        statistical_results = {}
        for metric, comp, data_a, data_b in stat_comparisons:
            stat_res = compute_statistical_comparison(data_a, data_b, alpha_sig=0.05)
            statistical_results[(metric, comp)] = stat_res

        print("\n" + "=" * 90)
        print("            TABLE 13. STATISTICAL COMPARISON OF ERWO-PPO WITH PPO BASELINES             ")
        print("=" * 90)
        header_13 = f"{'Metric':<16} | {'Comparison':<25} | {'Test':<12} | {'Adj. p-value':<14} | {'Effect Size':<12} | {'Significant':<11}"
        print(header_13)
        print("-" * len(header_13))
        for metric, comp, _, _ in stat_comparisons:
            s = statistical_results[(metric, comp)]
            p_val_str = f"{s['p_value']:.4e}" if s['p_value'] < 0.001 else f"{s['p_value']:.4f}"
            print(
                f"{metric:<16} | {comp:<25} | {s['test_name']:<12} | {p_val_str:<14} | "
                f"{s['effect_size']:<12.4f} | {s['significant']:<11}"
            )
        print("=" * 90)

        # Catat Uji Statistik ke JSON
        logger.log_statistical_tests(statistical_results)

        # ==============================================================================
        # 5. TAHAP 5: COMPUTATIONAL OVERHEAD (TABLE 14) & EKSPOR DATA
        # ==============================================================================
        avg_cand_train = float(np.mean(problem.candidate_train_times)) if problem.candidate_train_times else 0.0
        avg_cand_eval = float(np.mean(problem.candidate_eval_times)) if problem.candidate_eval_times else 0.0

        overhead_results = {
            "avg_cand_train": avg_cand_train,
            "avg_cand_eval": avg_cand_eval,
            "total_search_time": problem.total_search_time,
            "final_ppo_train_time": t_final_ppo_train,
        }

        print("\n" + "=" * 80)
        print("                     TABLE 14. COMPUTATIONAL OVERHEAD                           ")
        print("=" * 80)
        print(f"{'Component':<45} | {'Time':<30}")
        print("-" * 80)
        print(f"{'Average PPO candidate-training time':<45} | {avg_cand_train:<25.2f} s")
        print(f"{'Average candidate-evaluation time':<45} | {avg_cand_eval:<25.2f} s")
        print(f"{'Total NSGA-II search time':<45} | {problem.total_search_time:<25.2f} s")
        print(f"{'Final PPO training time':<45} | {t_final_ppo_train:<25.2f} s")
        print(f"{'Average ERWO-PPO decision time per task':<45} | {benchmark_results['ERWO-PPO']['decision_time']:<25.4f} ms")
        print(f"{'Average PPO-Equal decision time per task':<45} | {benchmark_results['PPO-Equal']['decision_time']:<25.4f} ms")
        print("=" * 80)

        # Catat Overhead ke JSON
        logger.log_overhead(overhead_results)

        # Simpan Model ERWO-PPO
        os.makedirs("models", exist_ok=True)
        model_path = os.path.join("models", "ppo_ifogsim2_erwo.zip")
        erwo_agent.save(model_path)
        print(f"\n[SELESAI] Model PPO tersimpan di: {model_path}")

        # Catat ke Master Cumulative Ledger
        logger.log_to_master_history(
            best_weights=best_weights,
            erwo_res=benchmark_results["ERWO-PPO"],
            baseline_res=benchmark_results["PPO-Equal"],
            overhead_res=overhead_results,
        )

        # Ekspor Otomatis ke Data.md
        export_results_to_data_md(
            pareto_weights=pareto_weights,
            pareto_objectives=pareto_objectives,
            best_weights=best_weights,
            manual_weights=manual_weights,
            benchmark_results=benchmark_results,
            statistical_results=statistical_results,
            overhead_results=overhead_results,
            file_path="Data.md",
        )
        print("=" * 85)


if __name__ == "__main__":
    main()
