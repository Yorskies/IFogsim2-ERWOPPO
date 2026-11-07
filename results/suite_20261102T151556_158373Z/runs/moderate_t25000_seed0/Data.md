### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 55.27 | 89.61 | 18.78 | 0.0496 | 65.62 |
| Optimized ($w^*$) | 0.2279 | 0.0986 | 0.3313 | 0.3422 | 55.29 | 89.63 | 18.84 | 0.0521 | 65.42 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0010 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 48.28 | 88.21 | 36.55 | 0.1117 | 46.05 | 0.0054 |
| DQN-Equal | 55.44 | 89.46 | 18.00 | 0.0486 | 66.87 | 0.0504 |
| DDPG-Equal | 55.78 | 89.59 | 17.95 | 0.0426 | 67.60 | 0.0691 |
| PPO-Equal | 55.27 | 89.61 | 18.78 | 0.0496 | 65.62 | 0.0974 |
| ERWO-PPO | 55.29 | 89.63 | 18.84 | 0.0521 | 65.42 | 0.0969 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 55.27 | 89.61 | 18.78 | 0.0496 | 65.62 |
| ERWO-PPO | 55.29 | 89.63 | 18.84 | 0.0521 | 65.42 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0162 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.8188 | 0.0294 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0130 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 5.9461e-04 | 0.4034 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.8188 | 0.0631 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0753 | 0.1210 | NO |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.3024e-08 | 0.2945 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.0388e-04 | 0.1844 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 2.0166e-04 | 0.4892 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 5.2321e-09 | 0.4497 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.1628e-13 | 0.4205 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.8188 | 0.0618 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 5.1630e-06 | 0.1932 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 9.1871e-17 | 1.7488 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 9.1506e-16 | 0.6932 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6722e-17 | 3.4387 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6722e-17 | 2.0472 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6722e-17 | 2.6427 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6722e-17 | 2.0416 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6722e-17 | 3.5613 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.00 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 162.68 s |
| Final PPO training time | 19.73 s |
| Average ERWO-PPO decision time per task | 0.0969 ms |
| Average PPO-Equal decision time per task | 0.0974 ms |
