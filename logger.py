"""
logger.py
---------
Sistem Pencatatan Log Permanen & Audit Trail Akademik untuk Proyek ERWO-PPO iFogSim2.

Mencatat seluruh proses eksperimen secara otomatis ke direktori `logs/`:
1. `config.json` : Konfigurasi lengkap hyperparameter, seed, workload, dan arsitektur.
2. `console_output.log` : Salinan verbatim seluruh output terminal secara real-time.
3. `pareto_front.csv` : Riwayat seluruh bobot kandidat dan skor objektif NSGA-II.
4. `benchmark_summary.json` : Ringkasan agregat seluruh 8 metode benchmark (Tabel 10, 11, 12).
5. `benchmark_episodes.csv` : Data mentah per episode per metode untuk pembuktian statistik.
6. `statistical_tests.json` : Hasil uji signifikansi (p-value, test statistic, effect size).
7. `computational_overhead.json` : Rincian waktu pencarian, pelatihan, dan inferensi (Tabel 14).
8. `logs/experiment_history.csv` : Master ledger kumulatif seluruh eksperimen yang pernah dijalankan.
"""

from typing import Any, Dict, List, Optional
import os
import sys
import json
import time
from datetime import datetime
import pandas as pd
import numpy as np


class DualOutputTee:
    """Menduplikasi aliran stdout/stderr ke terminal dan file log secara simultan."""
    def __init__(self, terminal_stream, file_stream):
        self.terminal = terminal_stream
        self.log_file = file_stream

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()


class ExperimentLogger:
    """
    Manager logging permanen untuk merekam seluruh jejak komputasi dan data eksperimen.
    """

    def __init__(self, workload: str = "dynamic", exp_tag: Optional[str] = None):
        self.workload = workload
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.tag = f"_{exp_tag}" if exp_tag else ""
        self.exp_id = f"exp_{self.timestamp}_{self.workload}{self.tag}"
        
        # Direktori utama log
        self.base_log_dir = "logs"
        self.exp_dir = os.path.join(self.base_log_dir, "experiments", self.exp_id)
        os.makedirs(self.exp_dir, exist_ok=True)
        
        # File path
        self.console_log_path = os.path.join(self.exp_dir, "console_output.log")
        self.config_path = os.path.join(self.exp_dir, "config.json")
        self.pareto_csv_path = os.path.join(self.exp_dir, "pareto_front.csv")
        self.benchmark_summary_path = os.path.join(self.exp_dir, "benchmark_summary.json")
        self.benchmark_episodes_path = os.path.join(self.exp_dir, "benchmark_episodes.csv")
        self.statistical_tests_path = os.path.join(self.exp_dir, "statistical_tests.json")
        self.overhead_path = os.path.join(self.exp_dir, "computational_overhead.json")
        self.master_history_path = os.path.join(self.base_log_dir, "experiment_history.csv")

        # Inisiasi capture terminal output
        self.log_file_handle = open(self.console_log_path, "w", encoding="utf-8")
        self._orig_stdout = sys.stdout
        self._orig_stderr = sys.stderr
        sys.stdout = DualOutputTee(self._orig_stdout, self.log_file_handle)
        sys.stderr = DualOutputTee(self._orig_stderr, self.log_file_handle)

        print(f"[LOGGER] Eksperimen terdaftar: {self.exp_id}")
        print(f"[LOGGER] Seluruh bukti pengujian disimpan permanen di: {self.exp_dir}")

    def log_config(self, config: Dict[str, Any]) -> None:
        """Menyimpan konfigurasi eksperimen ke config.json."""
        full_config = {
            "exp_id": self.exp_id,
            "timestamp": datetime.now().isoformat(),
            "workload": self.workload,
            **config,
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(full_config, f, indent=4)

    def log_pareto_front(
        self,
        pareto_weights: np.ndarray,
        pareto_objectives: np.ndarray,
        best_idx: int,
    ) -> None:
        """Menyimpan seluruh titik solusi Pareto front ke pareto_front.csv."""
        rows = []
        for i, (w, f) in enumerate(zip(pareto_weights, pareto_objectives)):
            rows.append({
                "solution_id": i + 1,
                "is_best_selected": (i == best_idx),
                "alpha_latency": float(w[0]),
                "beta_energy": float(w[1]),
                "lambda_deadline": float(w[2]),
                "gamma_qos": float(w[3]),
                "f1_latency_score": float(f[0]),
                "f2_energy_score": float(f[1]),
                "f3_deadline_score": float(f[2]),
                "f4_qos_score": float(f[3]),
            })
        df = pd.DataFrame(rows)
        df.to_csv(self.pareto_csv_path, index=False)

    def log_benchmark_results(
        self,
        benchmark_results: Dict[str, Any],
    ) -> None:
        """
        Menyimpan ringkasan benchmark (JSON) dan data mentah per episode (CSV)
        untuk keperluan audit trail dan verifikasi statistik.
        """
        # 1. Summary JSON
        summary_clean = {}
        episode_rows = []

        for method, data in benchmark_results.items():
            summary_clean[method] = {
                "latency": data["latency"],
                "energy": data["energy"],
                "deadline": data["deadline"],
                "qos": data["qos"],
                "violation_rate": data["violation_rate"],
                "load_imbalance": data["load_imbalance"],
                "decision_time_ms": data["decision_time"],
                "reward": data["reward"],
            }

            # 2. Episode Data CSV
            raw = data.get("raw", {})
            num_episodes = len(raw.get("latency", []))
            for ep in range(num_episodes):
                episode_rows.append({
                    "method": method,
                    "episode": ep + 1,
                    "latency": float(raw["latency"][ep]),
                    "energy": float(raw["energy"][ep]),
                    "deadline": float(raw["deadline"][ep]),
                    "qos": float(raw["qos"][ep]),
                    "violation_rate": float(raw["violation_rate"][ep]),
                    "load_imbalance": float(raw["load_imbalance"][ep]),
                })

        with open(self.benchmark_summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_clean, f, indent=4)

        if episode_rows:
            df_ep = pd.DataFrame(episode_rows)
            df_ep.to_csv(self.benchmark_episodes_path, index=False)

    def log_statistical_tests(self, statistical_results: Dict[Any, Any]) -> None:
        """Menyimpan rincian hasil uji signifikansi statistik ke statistical_tests.json."""
        stats_clean = {}
        for (metric, comp), res in statistical_results.items():
            key = f"{metric} | {comp}"
            stats_clean[key] = {
                "metric": metric,
                "comparison": comp,
                "test_name": res["test_name"],
                "p_value": res["p_value"],
                "effect_size_cohen_d": res["effect_size"],
                "significant": res["significant"],
            }
        with open(self.statistical_tests_path, "w", encoding="utf-8") as f:
            json.dump(stats_clean, f, indent=4)

    def log_overhead(self, overhead_results: Dict[str, Any]) -> None:
        """Menyimpan metrik overhead komputasi ke computational_overhead.json."""
        with open(self.overhead_path, "w", encoding="utf-8") as f:
            json.dump(overhead_results, f, indent=4)

    def log_to_master_history(
        self,
        best_weights: np.ndarray,
        erwo_res: Dict[str, Any],
        baseline_res: Dict[str, Any],
        overhead_res: Dict[str, Any],
    ) -> None:
        """Mencatat entri ringkasan ke file master cumulative ledger logs/experiment_history.csv."""
        entry = {
            "exp_id": self.exp_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "workload": self.workload,
            "best_alpha": float(best_weights[0]),
            "best_beta": float(best_weights[1]),
            "best_lambda": float(best_weights[2]),
            "best_gamma": float(best_weights[3]),
            "erwo_latency": float(erwo_res["latency"]),
            "erwo_energy": float(erwo_res["energy"]),
            "erwo_violation_rate": float(erwo_res["violation_rate"]),
            "erwo_load_imbalance": float(erwo_res["load_imbalance"]),
            "erwo_qos": float(erwo_res["qos"]),
            "erwo_decision_time_ms": float(erwo_res["decision_time"]),
            "baseline_latency": float(baseline_res["latency"]),
            "baseline_energy": float(baseline_res["energy"]),
            "baseline_violation_rate": float(baseline_res["violation_rate"]),
            "baseline_qos": float(baseline_res["qos"]),
            "nsga2_search_time_s": float(overhead_res.get("total_search_time", 0.0)),
            "log_folder": self.exp_dir,
        }

        df_entry = pd.DataFrame([entry])
        if os.path.exists(self.master_history_path):
            df_entry.to_csv(self.master_history_path, mode="a", header=False, index=False)
        else:
            df_entry.to_csv(self.master_history_path, mode="w", header=True, index=False)
        print(f"[LOGGER] Entri eksperimen berhasil dicatat ke master ledger: {self.master_history_path}")

    def close(self) -> None:
        """Menutup file stream dan mengembalikan stdout/stderr standar."""
        print(f"[LOGGER] Selesai merekam eksperimen {self.exp_id}.\n")
        sys.stdout = self._orig_stdout
        sys.stderr = self._orig_stderr
        try:
            self.log_file_handle.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
