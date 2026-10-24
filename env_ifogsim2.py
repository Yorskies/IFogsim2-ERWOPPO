"""
env_ifogsim2.py
---------------
Wrapper Gymnasium Asli untuk iFogSim2 (iFogSim2 ERWO-PPO Environment v0.1.0).
Menyediakan komunikasi IPC (TCP Socket) berkecepatan tinggi antara Python dan Java
dengan pemodelan fisik Fog/Edge offloading yang realistis dan diferensiasi Load Imbalance.

Spesifikasi:
- Observation Space: 46 Dimensi (State iFogSim2)
- Action Space: Discrete(7) [Node 0=Lokal, 1-5=Fog/Edge, 6=Cloud]
- 4 Parameter Reward: Latensi (alpha), Energi (beta), Deadline (lambda), QoS (gamma)
- Workload: light, moderate, heavy, dynamic
"""

from typing import Any, Dict, Optional, Tuple, Union
import json
import socket
import subprocess
import gymnasium as gym
from gymnasium import spaces
import numpy as np


class iFogSim2Env(gym.Env):
    """
    Gymnasium Environment Wrapper untuk iFogSim2 Simulator via TCP Socket IPC.
    """
    
    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5555,
        weights: Optional[np.ndarray] = None,
        workload: str = "dynamic",
        auto_spawn: bool = False,
        timeout: float = 60.0,
        verbose: int = 0,
    ):
        super().__init__()
        
        self.host = host
        self.port = port
        self.workload = workload
        self.auto_spawn = auto_spawn
        self.timeout = timeout
        self.verbose = verbose
        
        self.sock: Optional[socket.socket] = None
        self.sock_file = None
        self.is_connected = False
        self.java_process: Optional[subprocess.Popen] = None

        # 4 Bobot reward [alpha, beta, lambda, gamma]
        if weights is None:
            self.weights = np.array([0.25, 0.25, 0.25, 0.25], dtype=np.float32)
        else:
            self.weights = np.array(weights, dtype=np.float32)

        # Ruang Observasi: 46 Dimensi
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(46,),
            dtype=np.float32,
        )

        # Ruang Aksi: Discrete(7)
        self.action_space = spaces.Discrete(7)

        # State fallback internal jika server Java offline
        self.state = np.zeros(46, dtype=np.float32)
        self.current_step = 0
        self.max_steps = 100

        # Fleet 100 Perangkat IoT (Tier 1 - Broker-Based Multi-Device Architecture)
        self.num_iot_devices = 100
        self.iot_devices_battery = np.ones(self.num_iot_devices, dtype=np.float32)
        self.iot_devices_cpu = np.zeros(self.num_iot_devices, dtype=np.float32)
        self.iot_devices_queue = np.zeros(self.num_iot_devices, dtype=np.float32)
        self.current_source_device = 0

        self._init_connection()

    def _init_connection(self) -> None:
        """Mencoba menghubungkan socket ke Java server iFogSim2."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.port))
            self.sock_file = self.sock.makefile("r", encoding="utf-8")
            self.is_connected = True
            if self.verbose > 0:
                print(f"[iFogSim2Env] Terhubung ke Java Server ({self.host}:{self.port})")
        except (ConnectionRefusedError, socket.timeout, OSError):
            self.is_connected = False
            self.sock = None
            self.sock_file = None
            self._init_workload_steps()

    def _init_workload_steps(self) -> None:
        """Menyesuaikan panjang episode berdasarkan skenario workload."""
        workload_map = {
            "light": 50,
            "moderate": 100,
            "heavy": 150,
            "dynamic": 100,
        }
        self.max_steps = workload_map.get(self.workload.lower(), 100)

    def set_weights(self, weights: np.ndarray) -> None:
        """Mengatur bobot reward [alpha, beta, lambda, gamma] secara dinamis."""
        self.weights = np.array(weights, dtype=np.float32)

    def set_workload(self, workload: str) -> None:
        """Mengatur skenario workload (light, moderate, heavy, dynamic)."""
        self.workload = workload
        self._init_workload_steps()

    def _push_dashboard(self, obs, info, total_reward, target_node):
        if getattr(self, "disable_dashboard", False):
            return
        try:
            import urllib.request
            import json
            import threading

            data = {
                "step": int(info.get("step", self.current_step)),
                "action": int(target_node),
                "load_imbalance": float(info.get("load_imbalance", 0.0)),
                "reward": float(total_reward),
                "latency": float(info.get("latency_score", 0.0)),
                "energy": float(info.get("energy_efficiency", 0.0)),
                "deadline": float(info.get("deadline_compliance", 0.0)),
                "node_cpu": [float(x) for x in obs[0:7]],
                "node_queues": [float(x) for x in obs[28:35]],
                "node_latencies": [float(x) for x in obs[21:28]],
                "is_violated": bool(info.get("is_violated", False)),
                "qos_satisfaction": float(info.get("qos_satisfaction", 0.0)),
                "task_data_size": float(obs[42]) if len(obs) > 42 else 0.0,
                "task_mi": float(obs[43]) if len(obs) > 43 else 0.0,
                "task_deadline": float(obs[44]) if len(obs) > 44 else 0.0,
                "task_priority": float(obs[45]) if len(obs) > 45 else 0.0,
                "workload": str(self.workload),
                # 100 Edge Devices Fleet Telemetry
                "source_device_id": int(info.get("source_device_id", self.current_source_device)),
                "mean_fleet_battery": float(info.get("mean_fleet_battery", float(np.mean(self.iot_devices_battery)))),
                "depleted_devices_count": int(info.get("depleted_devices_count", int(np.sum(self.iot_devices_battery < 0.10)))),
                "devices_battery": [round(float(b), 3) for b in getattr(self, "iot_devices_battery", [])],
            }

            def push():
                try:
                    req = urllib.request.Request(
                        "http://127.0.0.1:8000/api/push",
                        data=json.dumps(data).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    urllib.request.urlopen(req, timeout=0.8)
                except Exception:
                    pass

            threading.Thread(target=push, daemon=True).start()
        except Exception:
            pass

    def reset(
        self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        
        self.current_step = 0
        if seed is None:
            seed = int(np.random.randint(0, 100000))

        if self.is_connected and self.sock and self.sock_file:
            try:
                cmd = f"RESET {self.workload} {seed}\n"
                self.sock.sendall(cmd.encode("utf-8"))
                resp_line = self.sock_file.readline()
                if resp_line:
                    data = json.loads(resp_line.strip())
                    obs = np.array(data.get("obs", np.zeros(46)), dtype=np.float32)
                    load_imb = float(np.std(obs[0:7]))
                    info = {
                        "sub_rewards": np.zeros(4, dtype=np.float32),
                        "load_imbalance": load_imb,
                        "step": 0,
                        "workload": self.workload,
                        "source": "java_ifogsim2",
                        "source_device_id": data.get("source_device_id", 0),
                        "mean_fleet_battery": data.get("mean_fleet_battery", 0.95),
                        "depleted_devices_count": data.get("depleted_devices_count", 0),
                        "devices_battery": data.get("devices_battery", [1.0] * self.num_iot_devices),
                    }
                    return obs, info
            except Exception as e:
                if self.verbose > 0:
                    print(f"[iFogSim2Env] IPC Socket Error saat Reset ({e}), beralih ke internal engine.")
                self.close()

        # Inisialisasi Fleet 100 Perangkat IoT (Tier 1 Broker-Based)
        self._init_workload_steps()
        self.state = np.zeros(46, dtype=np.float32)

        # Level baterai awal heterogen 0.65 s/d 1.00
        self.iot_devices_battery = self.np_random.uniform(0.65, 1.00, size=self.num_iot_devices).astype(np.float32)
        # Beban CPU awal 100 perangkat 0.10 s/d 0.35
        self.iot_devices_cpu = self.np_random.uniform(0.10, 0.35, size=self.num_iot_devices).astype(np.float32)
        # Panjang antrean awal 100 perangkat
        self.iot_devices_queue = self.np_random.uniform(0.0, 0.10, size=self.num_iot_devices).astype(np.float32)

        # Pilih perangkat IoT yang pertama kali menghasilkan tugas
        self.current_source_device = int(self.np_random.integers(0, self.num_iot_devices))

        # Node 0 pada observasi 46D merepresentasikan perangkat pemohon terkini
        self.state[0] = self.iot_devices_cpu[self.current_source_device]
        for i in range(1, 6):
            self.state[i] = float(self.np_random.uniform(0.2, 0.4))  # Fog 1..5 CPU
        self.state[6] = float(self.np_random.uniform(0.1, 0.3))  # Cloud CPU

        # Inisialisasi Latensi Jaringan [21:28]
        self.state[21] = 0.0  # Local latency 0 ms
        for i in range(22, 27):
            self.state[i] = float(self.np_random.uniform(0.15, 0.35))  # Fog latency rendah-sedang
        self.state[27] = float(self.np_random.uniform(0.65, 0.85))  # Cloud WAN latency tinggi

        # Panjang Antrean [28:35]
        self.state[28] = self.iot_devices_queue[self.current_source_device]
        for i in range(29, 35):
            self.state[i] = float(self.np_random.uniform(0.05, 0.20))

        # Riwayat Konsumsi Energi / Penurunan Baterai [35:42]
        self.state[35] = float(np.clip(1.0 - self.iot_devices_battery[self.current_source_device], 0.0, 1.0))
        for i in range(36, 42):
            self.state[i] = float(self.np_random.uniform(0.10, 0.30))

        # Profil task awal
        self.state[42] = float(self.np_random.uniform(0.2, 0.8))  # task data size
        self.state[43] = float(self.np_random.uniform(0.2, 0.8))  # task MI
        self.state[44] = float(self.np_random.uniform(0.3, 0.8))  # task deadline
        self.state[45] = float(self.np_random.uniform(0.2, 1.0))  # task priority

        obs = self.state.copy()
        load_imb = float(np.std(obs[0:7]))
        mean_batt = float(np.mean(self.iot_devices_battery))
        depleted = int(np.sum(self.iot_devices_battery < 0.10))

        info = {
            "sub_rewards": np.zeros(4, dtype=np.float32),
            "load_imbalance": load_imb,
            "step": 0,
            "workload": self.workload,
            "source": "broker_100_devices",
            "source_device_id": self.current_source_device,
            "mean_fleet_battery": mean_batt,
            "depleted_devices_count": depleted,
            "devices_battery": [round(float(b), 3) for b in self.iot_devices_battery],
            "devices_cpu": [round(float(c), 3) for c in self.iot_devices_cpu],
        }
        return obs, info

    def step(self, action: Union[int, np.ndarray]) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        if isinstance(action, np.ndarray):
            action = int(action.item())
        else:
            action = int(action)

        self.current_step += 1

        if self.is_connected and self.sock and self.sock_file:
            try:
                cmd = f"STEP {action}\n"
                self.sock.sendall(cmd.encode("utf-8"))
                resp_line = self.sock_file.readline()
                if resp_line:
                    data = json.loads(resp_line.strip())
                    obs = np.array(data.get("obs", np.zeros(46)), dtype=np.float32)
                    sub_rewards = np.array(data.get("sub_rewards", [0, 0, 0, 0]), dtype=np.float32)
                    total_reward = float(np.dot(self.weights, sub_rewards))
                    done = bool(data.get("done", False))
                    truncated = bool(data.get("truncated", self.current_step >= self.max_steps))
                    load_imb = float(data.get("load_imbalance", np.std(obs[0:7])))
                    
                    info = {
                        "sub_rewards": sub_rewards,
                        "latency_score": float(sub_rewards[0]),
                        "energy_efficiency": float(sub_rewards[1]),
                        "deadline_compliance": float(sub_rewards[2]),
                        "qos_satisfaction": float(sub_rewards[3]),
                        "load_imbalance": load_imb,
                        "total_latency": data.get("total_latency", 0.0),
                        "energy_spent": data.get("energy_spent", 0.0),
                        "is_violated": data.get("is_violated", False),
                        "target_node": action,
                        "step": self.current_step,
                        "workload": self.workload,
                        "source": "java_ifogsim2",
                        "source_device_id": data.get("source_device_id", 0),
                        "mean_fleet_battery": data.get("mean_fleet_battery", 0.95),
                        "depleted_devices_count": data.get("depleted_devices_count", 0),
                        "devices_battery": data.get("devices_battery", [1.0] * self.num_iot_devices),
                    }
                    self._push_dashboard(obs, info, total_reward, action)
                    return obs, total_reward, done, truncated, info
            except Exception as e:
                if self.verbose > 0:
                    print(f"[iFogSim2Env] IPC Socket Error saat Step ({e}), beralih ke internal engine.")
                self.close()

        # Pemodelan Fisik Broker-Based 100 Edge / IoT Devices
        target_node = action
        src_dev = self.current_source_device

        node_cpu = self.state[target_node]
        node_net_lat = self.state[21 + target_node]
        node_queue = self.state[28 + target_node]

        task_data = self.state[42]
        task_mi = self.state[43]
        task_deadline = self.state[44]
        task_priority = self.state[45]

        # 1. Latensi & Konsumsi Daya
        if target_node == 0:
            # Eksekusi lokal pada perangkat pemohon terkini (src_dev)
            trans_time = 0.0
            exec_time = 1.6 * task_mi * (1.0 + self.iot_devices_cpu[src_dev])
            queue_time = self.iot_devices_queue[src_dev] * 0.6
            energy_spent = 1.25 * task_mi  # Boros baterai perangkat IoT pemohon

            # Pengurangan baterai nyata pada perangkat pemohon
            drain = float(0.04 * task_mi * (1.0 + self.iot_devices_cpu[src_dev]))
            self.iot_devices_battery[src_dev] = max(0.0, self.iot_devices_battery[src_dev] - drain)

            # Penalti degradasi jika baterai kritis (< 8%)
            if self.iot_devices_battery[src_dev] < 0.08:
                exec_time *= 2.2
                energy_spent *= 1.4

            # Kenaikan beban CPU dan antrean perangkat pemohon
            self.iot_devices_cpu[src_dev] = float(np.clip(self.iot_devices_cpu[src_dev] + 0.22 * task_mi, 0.0, 1.0))
            self.iot_devices_queue[src_dev] = float(np.clip(self.iot_devices_queue[src_dev] + 0.25 * task_data, 0.0, 1.0))

        elif 1 <= target_node <= 5:
            # Offloading ke Fog Nodes (1..5)
            trans_time = 0.35 * task_data * (1.0 + node_net_lat)
            exec_time = 0.45 * task_mi * (1.0 + node_cpu)
            queue_time = node_queue * 0.35
            energy_spent = 0.25 * task_data * (1.0 + node_net_lat)  # Sangat hemat baterai IoT

            # Pengurangan baterai ringan untuk transmisi nirkabel
            drain = float(0.006 * task_data * (1.0 + node_net_lat))
            self.iot_devices_battery[src_dev] = max(0.0, self.iot_devices_battery[src_dev] - drain)

            # Beban Fog Node terpilih meningkat
            self.state[target_node] = float(np.clip(self.state[target_node] + 0.20 * task_mi, 0.0, 1.0))
            self.state[28 + target_node] = float(np.clip(self.state[28 + target_node] + 0.25 * task_data, 0.0, 1.0))

        else:
            # Offloading ke Cloud Data Center (Node 6)
            trans_time = 1.15 * task_data * (1.0 + node_net_lat)
            exec_time = 0.10 * task_mi * (1.0 + node_cpu)
            queue_time = node_queue * 0.15
            energy_spent = 0.45 * task_data * (1.0 + node_net_lat)

            # Pengurangan baterai sedang untuk transmisi WAN
            drain = float(0.012 * task_data * (1.0 + node_net_lat))
            self.iot_devices_battery[src_dev] = max(0.0, self.iot_devices_battery[src_dev] - drain)

            # Beban Cloud meningkat
            self.state[6] = float(np.clip(self.state[6] + 0.10 * task_mi, 0.0, 1.0))
            self.state[28 + 6] = float(np.clip(self.state[28 + 6] + 0.15 * task_data, 0.0, 1.0))

        total_latency = trans_time + queue_time + exec_time
        r_latency = float(np.clip(np.exp(-1.3 * total_latency), 0.0, 1.0))
        r_energy = float(np.clip(1.0 - (energy_spent / 1.5), 0.0, 1.0))

        # Pelanggaran Deadline SLA
        is_violated = total_latency > (task_deadline * 1.35)
        r_deadline = 0.0 if is_violated else 1.0

        # Quality of Service (QoS)
        qos_factor = (1.0 - node_queue) * (1.0 - node_cpu)
        if is_violated:
            r_qos = float(np.clip(0.15 * qos_factor, 0.0, 1.0))
        else:
            r_qos = float(np.clip(0.65 * qos_factor + 0.35 * task_priority, 0.0, 1.0))

        sub_rewards = np.array([r_latency, r_energy, r_deadline, r_qos], dtype=np.float32)
        total_reward = float(np.dot(self.weights, sub_rewards))

        # Peluruhan alami Fog Nodes 1..5 dan Cloud yang tidak dipilih
        for i in range(1, 7):
            if i != target_node:
                self.state[i] = float(np.clip(self.state[i] - 0.08, 0.05, 1.0))
                self.state[28 + i] = float(np.clip(self.state[28 + i] - 0.10, 0.0, 1.0))

        # Peluruhan alami 99 perangkat IoT lainnya yang idle
        for dev_idx in range(self.num_iot_devices):
            if dev_idx != src_dev:
                self.iot_devices_cpu[dev_idx] = float(np.clip(self.iot_devices_cpu[dev_idx] - 0.05, 0.05, 1.0))
                self.iot_devices_queue[dev_idx] = float(np.clip(self.iot_devices_queue[dev_idx] - 0.08, 0.0, 1.0))
                # Pemulihan daya minimal (solar harvesting recharge)
                if self.iot_devices_battery[dev_idx] < 1.0:
                    self.iot_devices_battery[dev_idx] = min(1.0, self.iot_devices_battery[dev_idx] + 0.0008)

        # Pemilihan perangkat IoT yang menghasilkan tugas berikutnya
        next_source_device = int(self.np_random.integers(0, self.num_iot_devices))
        self.current_source_device = next_source_device

        # Update observasi indeks 0, 28, 35 dengan profil perangkat pemohon berikutnya
        self.state[0] = self.iot_devices_cpu[next_source_device]
        self.state[28] = self.iot_devices_queue[next_source_device]
        self.state[35] = float(np.clip(1.0 - self.iot_devices_battery[next_source_device], 0.0, 1.0))

        # Fluktuasi profil task baru untuk step berikutnya
        self.state[42] = float(self.np_random.uniform(0.15, 0.85))  # data size
        self.state[43] = float(self.np_random.uniform(0.15, 0.85))  # MI length
        self.state[44] = float(self.np_random.uniform(0.25, 0.80))  # deadline
        self.state[45] = float(self.np_random.uniform(0.10, 1.00))  # priority

        # Hitung standar deviasi Load Imbalance CPU 7 node
        load_imb = float(np.std(self.state[0:7]))

        done = False
        truncated = self.current_step >= self.max_steps

        obs = self.state.copy()
        depleted = int(np.sum(self.iot_devices_battery < 0.10))
        mean_batt = float(np.mean(self.iot_devices_battery))
        min_batt = float(np.min(self.iot_devices_battery))

        info = {
            "sub_rewards": sub_rewards,
            "latency_score": r_latency,
            "energy_efficiency": r_energy,
            "deadline_compliance": r_deadline,
            "qos_satisfaction": r_qos,
            "load_imbalance": load_imb,
            "total_latency": total_latency,
            "energy_spent": energy_spent,
            "is_violated": is_violated,
            "target_node": target_node,
            "step": self.current_step,
            "workload": self.workload,
            "source": "broker_100_devices",
            # Fleet Telemetry
            "source_device_id": src_dev,
            "next_source_device": next_source_device,
            "mean_fleet_battery": mean_batt,
            "min_fleet_battery": min_batt,
            "depleted_devices_count": depleted,
            "devices_battery": [round(float(b), 3) for b in self.iot_devices_battery],
            "devices_cpu": [round(float(c), 3) for c in self.iot_devices_cpu],
        }

        self._push_dashboard(obs, info, total_reward, target_node)
        return obs, total_reward, done, truncated, info

    def close(self) -> None:
        """Menutup koneksi socket secara bersih dan aman."""
        if self.sock is not None:
            try:
                if self.is_connected:
                    self.sock.sendall(b"CLOSE\n")
            except Exception:
                pass
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                if self.sock_file is not None:
                    self.sock_file.close()
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
            self.sock_file = None
            self.is_connected = False

        if self.java_process is not None:
            try:
                self.java_process.terminate()
            except Exception:
                pass
            self.java_process = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()
