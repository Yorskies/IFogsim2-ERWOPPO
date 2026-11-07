### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 55.93 | 89.60 | 18.00 | 0.0430 | 67.88 |
| Optimized ($w^*$) | 0.0585 | 0.3547 | 0.2504 | 0.3364 | 55.98 | 89.61 | 17.70 | 0.0421 | 68.16 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0011 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 47.24 | 88.24 | 38.13 | 0.1613 | 44.60 | 0.0053 |
| DQN-Equal | 54.97 | 89.61 | 18.02 | 0.0566 | 65.27 | 0.0505 |
| DDPG-Equal | 55.64 | 89.62 | 18.41 | 0.0462 | 66.72 | 0.0692 |
| PPO-Equal | 55.93 | 89.60 | 18.00 | 0.0430 | 67.88 | 0.0951 |
| ERWO-PPO | 55.98 | 89.61 | 17.70 | 0.0421 | 68.16 | 0.0951 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 55.93 | 89.60 | 18.00 | 0.0430 | 67.88 |
| ERWO-PPO | 55.98 | 89.61 | 17.70 | 0.0421 | 68.16 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.3064 | 0.0435 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.9021 | 0.0244 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.2150 | 0.0658 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0077 | 0.2318 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0940 | 0.0872 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6062e-17 | 0.8808 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0024 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.2594 | 0.0715 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.1075e-16 | 2.0478 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 8.5746e-17 | 0.9206 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.9399e-11 | 0.2980 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0152 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.7723e-04 | 0.1539 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 5.6995e-11 | 0.9715 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.7853e-13 | 0.4569 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6062e-17 | 4.8266 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6062e-17 | 1.9457 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6062e-17 | 3.3808 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6062e-17 | 4.7362 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6062e-17 | 5.2713 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.93 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 159.60 s |
| Final PPO training time | 78.03 s |
| Average ERWO-PPO decision time per task | 0.0951 ms |
| Average PPO-Equal decision time per task | 0.0951 ms |
