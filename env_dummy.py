"""
env_dummy.py
------------
Berisi kelas Gymnasium dummy untuk simulasi Task Offloading iFogSim2
dengan observasi 46 dimensi, aksi diskrit 0-6 (7 target nodes),
dan 4 parameter objektif: Latensi (alpha), Konsumsi Energi (beta),
Pelanggaran Deadline (lambda), dan QoS (gamma).
"""

from typing import Any, Dict, Optional, Tuple
import gymnasium as gym
from gymnasium import spaces
import numpy as np


class DummyMultiObjectiveEnv(gym.Env):
    """
    Simulasi Lingkungan Multi-Objektif iFogSim2 Task Offloading.
    
    Observasi (46 Dimensi):
    - [0:7]   : Utilisasi CPU / beban komputasi 7 node (Edge/Fog/Cloud)
    - [7:14]  : Ketersediaan RAM / memori 7 node
    - [14:21] : Kapasitas bandwidth link komunikasi ke 7 node
    - [21:28] : Estimasi latensi jaringan transmisi ke 7 node
    - [28:35] : Panjang antrean tugas (queue size) pada 7 node
    - [35:42] : Tingkat konsumsi energi saat ini pada 7 node
    - [42:46] : Profil tugas baru (Ukuran data, Panjang instruksi MI, Deadline requirement, QoS priority)
    
    Aksi (Discrete 7):
    - 0: Node Lokal (IoT Device)
    - 1-5: Fog / Edge Nodes (Fog Node 1 s/d 5)
    - 6: Cloud Server Data Center
    
    4 Parameter Reward (ERWO):
    - Sub-reward 1 (Latensi - alpha)             : Nilai normalisasi performa latensi (makin cepat makin tinggi)
    - Sub-reward 2 (Konsumsi Energi - beta)      : Nilai efisiensi konsumsi daya (makin hemat makin tinggi)
    - Sub-reward 3 (Pelanggaran Deadline - lambda): Penalti pelanggaran batas waktu (1.0 = sukses tepat waktu, 0.0 = melanggar)
    - Sub-reward 4 (QoS Satisfaction - gamma)    : Kualitas layanan dan throughput satisfaction
    """
    
    metadata = {"render_modes": ["human"]}

    def __init__(self, weights: Optional[np.ndarray] = None, max_steps: int = 100):
        super().__init__()
        
        self.max_steps = max_steps
        self.current_step = 0
        self.num_nodes = 7  # Node 0 s/d 6
        
        # Bobot default untuk 4 sub-reward: [alpha, beta, lambda, gamma]
        if weights is None:
            self.weights = np.array([0.25, 0.25, 0.25, 0.25], dtype=np.float32)
        else:
            self.weights = np.array(weights, dtype=np.float32)

        # Ruang Observasi: 46 Dimensi (rentang nilai ternormalisasi [0.0, 1.0])
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(46,),
            dtype=np.float32,
        )

        # Ruang Aksi: Diskrit 0 s/d 6 (7 target nodes)
        self.action_space = spaces.Discrete(7)

        # State internal
        self.state = np.zeros(46, dtype=np.float32)

    def set_weights(self, weights: np.ndarray) -> None:
        """Mengatur bobot reward [alpha, beta, lambda, gamma] secara dinamis."""
        self.weights = np.array(weights, dtype=np.float32)

    def reset(
        self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        
        self.current_step = 0
        
        # Inisialisasi vektor state 46 dimensi acak realistis
        # Node 0 (Lokal): CPU rendah, latensi 0, energi tinggi jika proses lokal
        # Node 1-5 (Fog): CPU sedang, latensi rendah-sedang, energi sedang
        # Node 6 (Cloud): CPU sangat tinggi, latensi lebih tinggi, daya besar di cloud
        self.state = self.np_random.uniform(0.1, 0.9, size=(46,)).astype(np.float32)
        
        obs = self.state.copy()
        info = {
            "sub_rewards": np.zeros(4, dtype=np.float32),
            "step": self.current_step,
        }
        return obs, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        self.current_step += 1
        target_node = int(action)

        # Karakteristik node terpilih dari state
        node_cpu_load = self.state[target_node]             # Beban CPU (0.0 - 1.0)
        node_network_latency = self.state[21 + target_node]  # Latensi jaringan (0.0 - 1.0)
        node_queue_load = self.state[28 + target_node]       # Antrean tugas (0.0 - 1.0)
        
        # Karakteristik task saat ini
        task_data_size = self.state[42]   # Ukuran data task
        task_mi = self.state[43]          # Panjang instruksi komputasi
        task_deadline = self.state[44]    # Batas toleransi deadline
        task_priority = self.state[45]    # Prioritas QoS

        # 1. Perhitungan Sub-Reward 1: Latensi (alpha)
        # Latensi total = waktu transmisi + waktu tunggu antrean + waktu eksekusi CPU
        exec_time = task_mi * (1.0 + node_cpu_load)
        trans_time = task_data_size * node_network_latency if target_node > 0 else 0.05
        queue_time = node_queue_load * 0.5
        total_latency = trans_time + queue_time + exec_time
        # Normalisasi skor latensi: semakin kecil total_latency semakin mendekati 1.0
        r_latency = float(np.clip(np.exp(-1.5 * total_latency), 0.0, 1.0))

        # 2. Perhitungan Sub-Reward 2: Konsumsi Energi (beta)
        # Transmisi memakan energi perangkat IoT; komputasi lokal memakan energi CPU lokal
        if target_node == 0:
            energy_spent = 0.8 * task_mi  # Eksekusi lokal boros baterai IoT
        else:
            energy_spent = 0.3 * task_data_size * (1.0 + node_network_latency)  # Transmisi wireless
        r_energy = float(np.clip(1.0 - (energy_spent / 1.5), 0.0, 1.0))

        # 3. Perhitungan Sub-Reward 3: Pelanggaran Deadline (lambda)
        # Jika total_latency melebihi task_deadline, terjadi deadline violation
        is_violated = total_latency > (task_deadline * 1.5)
        r_deadline = 0.0 if is_violated else 1.0

        # 4. Perhitungan Sub-Reward 4: QoS Satisfaction (gamma)
        # QoS dinilai dari pemenuhan SLA, availability node, dan prioritas tugas
        qos_factor = (1.0 - node_queue_load) * (1.0 - node_cpu_load)
        if not is_violated:
            r_qos = float(np.clip(0.6 * qos_factor + 0.4 * task_priority, 0.0, 1.0))
        else:
            r_qos = float(np.clip(0.2 * qos_factor, 0.0, 1.0))

        # 4 Sub-Reward Array: [Latency (alpha), Energy (beta), Deadline (lambda), QoS (gamma)]
        sub_rewards = np.array([r_latency, r_energy, r_deadline, r_qos], dtype=np.float32)

        # Skalarisasi total reward dengan bobot [alpha, beta, lambda, gamma]
        total_reward = float(np.dot(self.weights, sub_rewards))

        # Update dinamika lingkungan untuk step berikutnya
        self.state = np.clip(
            self.state + self.np_random.uniform(-0.05, 0.05, size=(46,)),
            0.0,
            1.0,
        ).astype(np.float32)

        terminated = False
        truncated = self.current_step >= self.max_steps

        obs = self.state.copy()
        info = {
            "sub_rewards": sub_rewards,
            "target_node": target_node,
            "total_latency": total_latency,
            "energy_spent": energy_spent,
            "is_violated": is_violated,
            "step": self.current_step,
        }

        return obs, total_reward, terminated, truncated, info
