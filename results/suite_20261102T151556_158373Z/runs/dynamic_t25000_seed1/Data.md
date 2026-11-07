### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 54.74 | 89.61 | 20.09 | 0.0599 | 63.33 |
| Optimized ($w^*$) | 0.2997 | 0.1145 | 0.1952 | 0.3905 | 55.48 | 89.61 | 18.78 | 0.0495 | 66.20 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0010 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 52.86 | 87.62 | 23.56 | 0.0503 | 62.30 | 0.0053 |
| DQN-Equal | 55.93 | 89.58 | 17.56 | 0.0445 | 67.74 | 0.0506 |
| DDPG-Equal | 55.68 | 89.61 | 18.47 | 0.0466 | 66.92 | 0.0696 |
| PPO-Equal | 54.74 | 89.61 | 20.09 | 0.0599 | 63.33 | 0.0968 |
| ERWO-PPO | 55.48 | 89.61 | 18.78 | 0.0495 | 66.20 | 0.0964 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 54.74 | 89.61 | 20.09 | 0.0599 | 63.33 |
| ERWO-PPO | 55.48 | 89.61 | 18.78 | 0.0495 | 66.20 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.9148e-17 | 0.6141 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0015 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 6.6521e-10 | 0.2662 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.7749e-16 | 1.5805 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.2099e-16 | 0.8612 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.1794e-14 | 0.3881 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.1753 | 0.0595 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.8574e-09 | 0.2579 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.8952e-12 | 1.1381 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 5.3397e-13 | 0.4776 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.1903e-05 | 0.1640 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0003 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.2996 | 0.0627 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.8574e-05 | 0.5624 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 9.4240e-05 | 0.2116 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 1.9790 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.7840 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.9489e-16 | 1.0124 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0000 | 0.1362 | NO |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.2099e-16 | 1.1989 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.96 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 160.99 s |
| Final PPO training time | 19.74 s |
| Average ERWO-PPO decision time per task | 0.0964 ms |
| Average PPO-Equal decision time per task | 0.0968 ms |
