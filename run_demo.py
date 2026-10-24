"""
run_demo.py
-----------
Skrip demonstrasi live simulasi task offloading iFogSim2.
Menjalankan episode simulasi bertahap dengan delay yang dapat disesuaikan
dan menyiarkan telemetri secara real-time ke ERWO-PPO Web Dashboard.

Penggunaan:
    python run_demo.py --method ERWO-PPO --workload dynamic --delay 0.15
    python run_demo.py --method "Least-loaded fog" --episodes 5 --delay 0.1
"""

import os
import sys
import time
import argparse
import numpy as np
import urllib.request
import json

from env_ifogsim2 import iFogSim2Env
from agent_baselines import (
    LocalOnlyPolicy,
    CloudOnlyPolicy,
    NearestFogPolicy,
    LeastLoadedFogPolicy,
)


def load_model_or_policy(method_name: str):
    """Memuat model PPO terlatih atau instance kebijakan heuristik."""
    if method_name.upper() == "ERWO-PPO":
        model_path = os.path.join("models", "ppo_ifogsim2_erwo.zip")
        if os.path.exists(model_path):
            try:
                from stable_baselines3 import PPO
                print(f"[Model] Memuat agen PPO terlatih dari: {model_path}")
                return PPO.load(model_path), "PPO"
            except Exception as e:
                print(f"[Model] Gagal memuat PPO ({e}), fallback ke Least-loaded fog.")
        else:
            print(f"[Model] File {model_path} tidak ditemukan, fallback ke Least-loaded fog.")
        return LeastLoadedFogPolicy(), "Policy"
    
    elif method_name.lower() in ["least-loaded", "least-loaded fog", "least_loaded"]:
        return LeastLoadedFogPolicy(), "Policy"
    elif method_name.lower() in ["nearest", "nearest-fog", "nearest_fog"]:
        return NearestFogPolicy(), "Policy"
    elif method_name.lower() in ["cloud", "cloud-only", "cloud_only"]:
        return CloudOnlyPolicy(), "Policy"
    elif method_name.lower() in ["local", "local-only", "local_only"]:
        return LocalOnlyPolicy(), "Policy"
    else:
        print(f"[Model] Metode '{method_name}' tidak dikenal, default ke Least-loaded fog.")
        return LeastLoadedFogPolicy(), "Policy"


def push_to_dashboard(url: str, data: dict):
    """Mengirim payload telemetri ke server dashboard via HTTP POST."""
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=0.8)
    except Exception:
        # Dashboard mungkin belum aktif, abaikan
        pass


def run_demo():
    parser = argparse.ArgumentParser(description="Live Task Offloading Simulation Demo for ERWO-PPO Dashboard")
    parser.add_argument("--method", type=str, default="ERWO-PPO",
                        choices=["ERWO-PPO", "Least-loaded fog", "Nearest-fog", "Cloud-only", "Local-only"],
                        help="Metode penempatan tugas yang diuji (default: ERWO-PPO)")
    parser.add_argument("--workload", type=str, default="dynamic",
                        choices=["light", "moderate", "heavy", "dynamic"],
                        help="Skenario beban tugas (default: dynamic)")
    parser.add_argument("--episodes", type=int, default=3, help="Jumlah episode demonstrasi (default: 3)")
    parser.add_argument("--delay", type=float, default=0.12, help="Jeda waktu antar langkah dalam detik (default: 0.12s)")
    parser.add_argument("--dashboard-url", type=str, default="http://127.0.0.1:8000/api/push",
                        help="URL endpoint push dashboard (default: http://127.0.0.1:8000/api/push)")
    parser.add_argument("--seed", type=int, default=1000, help="Base seed acak (default: 1000)")
    parser.add_argument("--infinite", action="store_true", help="Jalankan terus-menerus tanpa henti")
    args = parser.parse_args()

    agent, agent_type = load_model_or_policy(args.method)

    print("=" * 85)
    print(f"   [+] ERWO-PPO LIVE SIMULATION DEMO [+]   ")
    print("=" * 85)
    print(f"  * Metode Kebijakan  : {args.method} ({agent_type})")
    print(f"  * Beban Kerja       : {args.workload.upper()}")
    print(f"  * Jumlah Episode    : {'Tak Terbatas (Loop)' if args.infinite else args.episodes}")
    print(f"  * Delay per Langkah : {args.delay} detik ({int(args.delay * 1000)} ms)")
    print(f"  * Target Dashboard  : {args.dashboard_url}")
    print("  * Pastikan dashboard server aktif: python run_dashboard.py")
    print("=" * 85)

    node_names = {
        0: "IoT Local",
        1: "Fog 1 (Edge)",
        2: "Fog 2 (Edge)",
        3: "Fog 3 (Edge)",
        4: "Fog 4 (Edge)",
        5: "Fog 5 (Edge)",
        6: "Cloud Center",
    }

    episode = 0
    with iFogSim2Env(workload=args.workload) as env:
        # Nonaktifkan background push internal env agar run_demo yang mengontrol payload lengkap
        env.disable_dashboard = True

        try:
            while args.infinite or episode < args.episodes:
                episode += 1
                eval_seed = args.seed + episode
                obs, info = env.reset(seed=eval_seed)
                done = False
                step = 0
                ep_reward = 0.0
                ep_violations = 0

                print(f"\n>> Memulai Episode #{episode} (Seed: {eval_seed})...")
                header = (
                    f"{'Step':<5} | {'Src Dev':<9} | {'Target Node':<16} | {'Reward':<7} | {'Lat.Sc':<7} | "
                    f"{'Eng.Eff':<7} | {'SLA Viol':<9} | {'Load Imb':<9}"
                )
                print("-" * len(header))
                print(header)
                print("-" * len(header))

                while not done:
                    step += 1
                    src_dev_id = info.get("source_device_id", 0)

                    # Prediksi aksi
                    if agent_type == "PPO":
                        action, _ = agent.predict(obs, deterministic=True)
                        action = int(action.item()) if isinstance(action, np.ndarray) else int(action)
                    else:
                        action, _ = agent.predict(obs, deterministic=True)
                        action = int(action)

                    obs, reward, terminated, truncated, info = env.step(action)
                    done = terminated or truncated

                    ep_reward += reward
                    is_violated = bool(info.get("is_violated", False))
                    if is_violated:
                        ep_violations += 1

                    node_str = node_names.get(action, f"Node {action}")
                    viol_str = "MELANGGAR" if is_violated else "Aman"
                    load_imb = float(info.get("load_imbalance", np.std(obs[0:7])))

                    print(
                        f"{step:<5} | Device#{src_dev_id:<2} | {node_str:<16} | {reward:<7.2f} | {info.get('latency_score', 0):<7.2f} | "
                        f"{info.get('energy_efficiency', 0):<7.2f} | {viol_str:<9} | {load_imb:<9.4f}"
                    )

                    # Siapkan payload lengkap untuk dashboard
                    payload = {
                        "step": step,
                        "action": action,
                        "load_imbalance": load_imb,
                        "reward": float(reward),
                        "latency": float(info.get("latency_score", 0.0)),
                        "energy": float(info.get("energy_efficiency", 0.0)),
                        "deadline": float(info.get("deadline_compliance", 0.0)),
                        "node_cpu": [float(x) for x in obs[0:7]],
                        "node_queues": [float(x) for x in obs[28:35]],
                        "node_latencies": [float(x) for x in obs[21:28]],
                        "is_violated": is_violated,
                        "qos_satisfaction": float(info.get("qos_satisfaction", 0.0)),
                        "task_data_size": float(obs[42]) if len(obs) > 42 else 0.0,
                        "task_mi": float(obs[43]) if len(obs) > 43 else 0.0,
                        "task_deadline": float(obs[44]) if len(obs) > 44 else 0.0,
                        "task_priority": float(obs[45]) if len(obs) > 45 else 0.0,
                        "method_name": args.method,
                        "workload": args.workload,
                        "episode": episode,
                        "source_device_id": src_dev_id,
                        "mean_fleet_battery": float(info.get("mean_fleet_battery", 1.0)),
                        "depleted_devices_count": int(info.get("depleted_devices_count", 0)),
                        "devices_battery": info.get("devices_battery", []),
                    }
                    push_to_dashboard(args.dashboard_url, payload)

                    time.sleep(args.delay)

                viol_rate = (ep_violations / max(1, step)) * 100.0
                print("-" * len(header))
                print(f"[OK] Episode #{episode} Selesai: Total Reward = {ep_reward:.2f}, Pelanggaran SLA = {viol_rate:.1f}%")
                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n[Demo] Dihentikan oleh pengguna (CTRL+C).")

    print("\n[Demo] Selesai.")


if __name__ == "__main__":
    run_demo()
