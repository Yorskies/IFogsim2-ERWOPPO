### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 55.55 | 89.59 | 18.56 | 0.0498 | 66.56 |
| Optimized ($w^*$) | 0.2030 | 0.1319 | 0.3001 | 0.3650 | 55.83 | 89.61 | 18.06 | 0.0445 | 67.48 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0010 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 44.90 | 88.01 | 44.58 | 0.2076 | 39.97 | 0.0053 |
| DQN-Equal | 55.46 | 89.28 | 18.42 | 0.0512 | 66.07 | 0.0511 |
| DDPG-Equal | 43.08 | 69.75 | 47.42 | 0.0527 | 44.23 | 0.0703 |
| PPO-Equal | 55.55 | 89.59 | 18.56 | 0.0498 | 66.56 | 0.0966 |
| ERWO-PPO | 55.83 | 89.61 | 18.06 | 0.0445 | 67.48 | 0.0964 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 55.55 | 89.59 | 18.56 | 0.0498 | 66.56 |
| ERWO-PPO | 55.83 | 89.61 | 18.06 | 0.0445 | 67.48 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 4.8685e-08 | 0.2318 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.2936 | 0.0375 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0109 | 0.1044 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.2435e-10 | 0.9168 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.3467e-06 | 0.2791 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 5.9998e-09 | 0.3181 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.1508e-11 | 0.5753 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.1258 | 0.0772 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.1508e-11 | 0.9851 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 8.3424e-10 | 0.4273 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5455e-17 | 7.7002 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5455e-17 | 8.4164 | YES |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5455e-17 | 5.6985 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.6849 | 0.2778 | NO |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5455e-17 | 5.4933 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5455e-17 | 5.1276 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5455e-17 | 2.2519 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5455e-17 | 4.0189 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5455e-17 | 5.8116 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5455e-17 | 6.5216 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.90 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 158.69 s |
| Final PPO training time | 39.16 s |
| Average ERWO-PPO decision time per task | 0.0964 ms |
| Average PPO-Equal decision time per task | 0.0966 ms |
