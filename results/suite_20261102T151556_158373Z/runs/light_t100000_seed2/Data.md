### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 28.00 | 44.78 | 17.88 | 0.0429 | 34.01 |
| Optimized ($w^*$) | 0.1803 | 0.2048 | 0.5471 | 0.0677 | 27.75 | 44.66 | 17.80 | 0.0462 | 33.72 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 25.25 | 44.09 | 30.74 | 0.1064 | 26.33 | 0.0054 |
| DQN-Equal | 27.67 | 44.19 | 17.50 | 0.0418 | 34.18 | 0.0503 |
| DDPG-Equal | 27.93 | 44.80 | 17.94 | 0.0439 | 33.88 | 0.0695 |
| PPO-Equal | 28.00 | 44.78 | 17.88 | 0.0429 | 34.01 | 0.0967 |
| ERWO-PPO | 27.75 | 44.66 | 17.80 | 0.0462 | 33.72 | 0.0966 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 28.00 | 44.78 | 17.88 | 0.0429 | 34.01 |
| ERWO-PPO | 27.75 | 44.66 | 17.80 | 0.0462 | 33.72 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 5.3163e-13 | 0.3220 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.5610e-04 | 0.2832 | YES |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.7432 | 0.0133 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 3.6431e-10 | 0.7001 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 8.0078e-04 | 0.1378 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.2461 | 0.1026 | NO |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.0930e-16 | 1.0818 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.5066 | 0.0497 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.1972e-09 | 0.8686 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 5.4492e-07 | 0.2139 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 8.2257e-08 | 0.2359 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.1861e-06 | 0.3270 | YES |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.7432 | 0.0229 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.9546e-04 | 0.4859 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.2461 | 0.0739 | NO |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 2.2939 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.2865e-14 | 1.1711 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.2616e-17 | 1.7833 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 2.2395 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 2.6613 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.03 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 162.73 s |
| Final PPO training time | 82.46 s |
| Average ERWO-PPO decision time per task | 0.0966 ms |
| Average PPO-Equal decision time per task | 0.0967 ms |
