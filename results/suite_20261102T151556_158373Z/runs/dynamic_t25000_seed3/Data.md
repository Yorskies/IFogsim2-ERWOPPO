### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 55.27 | 89.58 | 19.06 | 0.0531 | 65.62 |
| Optimized ($w^*$) | 0.3231 | 0.2612 | 0.2124 | 0.2033 | 53.73 | 89.58 | 21.60 | 0.1060 | 59.76 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0011 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0026 |
| Q-Learning-Equal | 50.41 | 86.29 | 28.01 | 0.0987 | 55.82 | 0.0055 |
| DQN-Equal | 54.97 | 89.27 | 17.97 | 0.0604 | 65.19 | 0.0518 |
| DDPG-Equal | 55.43 | 89.61 | 18.66 | 0.0487 | 66.02 | 0.0704 |
| PPO-Equal | 55.27 | 89.58 | 19.06 | 0.0531 | 65.62 | 0.1005 |
| ERWO-PPO | 53.73 | 89.58 | 21.60 | 0.1060 | 59.76 | 0.0972 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 55.27 | 89.58 | 19.06 | 0.0531 | 65.62 |
| ERWO-PPO | 53.73 | 89.58 | 21.60 | 0.1060 | 59.76 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7931e-17 | 1.1345 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.9589 | 0.0051 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.7034e-13 | 0.5302 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7931e-17 | 2.5130 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7931e-17 | 1.4924 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.0245e-15 | 0.9341 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.5987e-12 | 0.5400 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 6.8383e-16 | 0.7472 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.1575e-16 | 2.0263 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.1575e-16 | 1.3920 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.7711e-16 | 1.1975 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.4341 | 0.0601 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 4.8621e-13 | 0.5931 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7931e-17 | 2.8150 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.1527e-16 | 1.5134 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.0555 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 3.7955 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 3.7711e-16 | 1.2689 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 0.0497 | 0.2410 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 3.1937e-11 | 0.9053 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.98 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 161.79 s |
| Final PPO training time | 20.33 s |
| Average ERWO-PPO decision time per task | 0.0972 ms |
| Average PPO-Equal decision time per task | 0.1005 ms |
