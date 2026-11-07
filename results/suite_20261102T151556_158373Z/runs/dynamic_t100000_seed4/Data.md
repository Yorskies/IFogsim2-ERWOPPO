### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 56.01 | 89.35 | 17.55 | 0.0396 | 68.66 |
| Optimized ($w^*$) | 0.2030 | 0.1319 | 0.3001 | 0.3650 | 56.13 | 89.59 | 17.72 | 0.0397 | 68.62 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0011 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 51.73 | 88.47 | 25.20 | 0.0783 | 57.11 | 0.0053 |
| DQN-Equal | 55.55 | 88.45 | 17.29 | 0.0434 | 67.96 | 0.0505 |
| DDPG-Equal | 28.50 | 89.61 | 81.23 | 0.3242 | 4.43 | 0.0694 |
| PPO-Equal | 56.01 | 89.35 | 17.55 | 0.0396 | 68.66 | 0.0954 |
| ERWO-PPO | 56.13 | 89.59 | 17.72 | 0.0397 | 68.62 | 0.0944 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 56.01 | 89.35 | 17.55 | 0.0396 | 68.66 |
| ERWO-PPO | 56.13 | 89.59 | 17.72 | 0.0397 | 68.62 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.4292e-04 | 0.1019 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 5.6262e-08 | 0.3856 | YES |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.9323 | 0.0374 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0674 | NO |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0131 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.0107e-15 | 0.5114 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.4354e-17 | 1.7138 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0119 | 0.0961 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.4392e-12 | 1.0676 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.2052e-07 | 0.2097 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4354e-17 | 26.0826 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0331 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4354e-17 | 14.2701 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4354e-17 | 142.1005 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4354e-17 | 26.9042 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4354e-17 | 3.0896 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4354e-17 | 1.7124 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4354e-17 | 1.5428 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4354e-17 | 2.9391 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4354e-17 | 3.1777 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.02 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 163.38 s |
| Final PPO training time | 80.23 s |
| Average ERWO-PPO decision time per task | 0.0944 ms |
| Average PPO-Equal decision time per task | 0.0954 ms |
