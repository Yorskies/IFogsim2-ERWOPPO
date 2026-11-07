### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 55.83 | 89.61 | 18.03 | 0.0444 | 67.52 |
| Optimized ($w^*$) | 0.0585 | 0.3547 | 0.2504 | 0.3364 | 56.01 | 89.61 | 17.74 | 0.0417 | 68.22 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0011 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 47.46 | 80.90 | 36.58 | 0.0653 | 50.33 | 0.0054 |
| DQN-Equal | 55.82 | 89.64 | 18.57 | 0.0453 | 67.29 | 0.0510 |
| DDPG-Equal | 55.61 | 89.62 | 18.27 | 0.0495 | 66.58 | 0.0699 |
| PPO-Equal | 55.83 | 89.61 | 18.03 | 0.0444 | 67.52 | 0.0977 |
| ERWO-PPO | 56.01 | 89.61 | 17.74 | 0.0417 | 68.22 | 0.0952 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 55.83 | 89.61 | 18.03 | 0.0444 | 67.52 |
| ERWO-PPO | 56.01 | 89.61 | 17.74 | 0.0417 | 68.22 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 9.0970e-10 | 0.1511 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.9195 | 0.0123 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.2299 | 0.0621 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.2276e-10 | 0.7665 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.5290e-07 | 0.2167 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 6.0398e-07 | 0.1630 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.3989 | 0.0466 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.1857e-05 | 0.1795 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.7541e-11 | 0.9170 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 2.6368e-09 | 0.2879 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 9.8818e-14 | 0.3467 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.9195 | 0.0111 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0030 | 0.1132 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.4045e-16 | 1.3746 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.5519e-14 | 0.5086 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 5.4669 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 5.6905 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.3801e-17 | 3.7904 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 2.8552e-16 | 1.4713 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 4.6974 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.97 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 161.17 s |
| Final PPO training time | 39.63 s |
| Average ERWO-PPO decision time per task | 0.0952 ms |
| Average PPO-Equal decision time per task | 0.0977 ms |
