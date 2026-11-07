### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 56.02 | 89.60 | 17.71 | 0.0411 | 68.28 |
| Optimized ($w^*$) | 0.2997 | 0.1145 | 0.1952 | 0.3905 | 55.99 | 89.57 | 17.79 | 0.0419 | 68.27 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0010 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 52.86 | 87.63 | 23.56 | 0.0504 | 62.30 | 0.0054 |
| DQN-Equal | 55.72 | 88.95 | 17.51 | 0.0420 | 68.08 | 0.0513 |
| DDPG-Equal | 55.84 | 89.62 | 17.94 | 0.0443 | 67.49 | 0.0697 |
| PPO-Equal | 56.02 | 89.60 | 17.71 | 0.0411 | 68.28 | 0.0970 |
| ERWO-PPO | 55.99 | 89.57 | 17.79 | 0.0419 | 68.27 | 0.0972 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 56.02 | 89.60 | 17.71 | 0.0411 | 68.28 |
| ERWO-PPO | 55.99 | 89.57 | 17.79 | 0.0419 | 68.27 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0241 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.8072 | 0.0479 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0178 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.5267 | 0.2634 | NO |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0046 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0276 | 0.2093 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 5.3351e-16 | 0.9441 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.5038 | 0.0602 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0185 | NO |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0589 | NO |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.2355e-04 | 0.1323 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.1784 | 0.0793 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0324 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 4.8592e-06 | 0.6343 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.4206e-07 | 0.2486 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 2.3779 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 2.7290 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.0712e-17 | 1.2810 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.1497e-14 | 1.4345 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 1.8994 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.97 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 161.27 s |
| Final PPO training time | 39.64 s |
| Average ERWO-PPO decision time per task | 0.0972 ms |
| Average PPO-Equal decision time per task | 0.0970 ms |
