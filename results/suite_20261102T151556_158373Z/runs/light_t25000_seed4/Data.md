### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 27.72 | 44.78 | 18.60 | 0.0511 | 33.13 |
| Optimized ($w^*$) | 0.2110 | 0.1298 | 0.2834 | 0.3758 | 27.74 | 44.79 | 18.68 | 0.0485 | 33.27 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 25.03 | 44.13 | 30.22 | 0.1077 | 25.55 | 0.0054 |
| DQN-Equal | 27.92 | 44.68 | 17.96 | 0.0509 | 33.49 | 0.0512 |
| DDPG-Equal | 27.67 | 44.80 | 19.06 | 0.0536 | 32.87 | 0.0700 |
| PPO-Equal | 27.72 | 44.78 | 18.60 | 0.0511 | 33.13 | 0.0984 |
| ERWO-PPO | 27.74 | 44.79 | 18.68 | 0.0485 | 33.27 | 0.0974 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 27.72 | 44.78 | 18.60 | 0.0511 | 33.13 |
| ERWO-PPO | 27.74 | 44.79 | 18.68 | 0.0485 | 33.27 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0346 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0119 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0134 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0126 | 0.3885 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.9888 | 0.0649 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.5951e-08 | 0.2364 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 2.3028e-07 | 0.2795 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0425 | 0.1232 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0456 | 0.3275 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.1860 | 0.1072 | NO |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0237 | 0.0942 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0313 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.9888 | 0.0636 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.6527e-07 | 0.7366 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0040 | 0.1833 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.3026 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 1.4089 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 8.7224e-17 | 1.6173 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.1471 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.5946 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.92 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 158.04 s |
| Final PPO training time | 19.67 s |
| Average ERWO-PPO decision time per task | 0.0974 ms |
| Average PPO-Equal decision time per task | 0.0984 ms |
