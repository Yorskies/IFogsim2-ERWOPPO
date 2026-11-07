### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 55.80 | 89.59 | 17.91 | 0.0449 | 67.59 |
| Optimized ($w^*$) | 0.3231 | 0.2612 | 0.2124 | 0.2033 | 56.07 | 89.52 | 17.43 | 0.0409 | 68.53 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0011 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0024 |
| Q-Learning-Equal | 49.49 | 84.68 | 30.39 | 0.0561 | 55.50 | 0.0053 |
| DQN-Equal | 55.67 | 89.58 | 17.75 | 0.0446 | 67.06 | 0.0508 |
| DDPG-Equal | 56.07 | 89.63 | 17.58 | 0.0410 | 68.37 | 0.0694 |
| PPO-Equal | 55.80 | 89.59 | 17.91 | 0.0449 | 67.59 | 0.0964 |
| ERWO-PPO | 56.07 | 89.52 | 17.43 | 0.0409 | 68.53 | 0.0951 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 55.80 | 89.59 | 17.91 | 0.0449 | 67.59 |
| ERWO-PPO | 56.07 | 89.52 | 17.43 | 0.0409 | 68.53 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 3.4037e-13 | 0.2276 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0069 | 0.1185 | YES |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 9.0320e-04 | 0.1069 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 5.4453e-15 | 1.0359 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 6.8368e-12 | 0.3061 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.4677e-12 | 0.3404 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.1101 | 0.1079 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0412 | 0.0719 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.7447e-14 | 1.0961 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 6.9062e-16 | 0.4734 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0001 | NO |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 6.4079e-06 | 0.1905 | YES |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.8962 | 0.0329 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0538 | NO |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.8962 | 0.0544 | NO |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4898e-17 | 4.4792 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4898e-17 | 4.7093 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4898e-17 | 2.7855 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 3.4283e-16 | 1.7188 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4898e-17 | 3.9181 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.95 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 160.48 s |
| Final PPO training time | 77.84 s |
| Average ERWO-PPO decision time per task | 0.0951 ms |
| Average PPO-Equal decision time per task | 0.0964 ms |
