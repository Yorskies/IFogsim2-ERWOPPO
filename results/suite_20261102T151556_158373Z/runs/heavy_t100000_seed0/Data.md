### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 83.84 | 134.03 | 18.71 | 0.0458 | 100.54 |
| Optimized ($w^*$) | 0.1832 | 0.3323 | 0.3487 | 0.1359 | 84.06 | 134.41 | 17.97 | 0.0407 | 102.35 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0010 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 77.69 | 130.63 | 25.89 | 0.0730 | 86.89 | 0.0053 |
| DQN-Equal | 83.38 | 134.39 | 18.61 | 0.0468 | 100.01 | 0.0507 |
| DDPG-Equal | 83.71 | 134.40 | 18.29 | 0.0433 | 101.06 | 0.0684 |
| PPO-Equal | 83.84 | 134.03 | 18.71 | 0.0458 | 100.54 | 0.0958 |
| ERWO-PPO | 84.06 | 134.41 | 17.97 | 0.0407 | 102.35 | 0.0955 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 83.84 | 134.03 | 18.71 | 0.0458 | 100.54 |
| ERWO-PPO | 84.06 | 134.41 | 17.97 | 0.0407 | 102.35 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.4356e-04 | 0.1515 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 9.2698e-13 | 0.5145 | YES |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.2813e-06 | 0.2072 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 5.5270e-14 | 1.0195 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.5142e-11 | 0.4744 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 5.8389e-11 | 0.4498 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.7575 | 0.0392 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.9061e-04 | 0.1719 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.7809e-15 | 1.6774 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.4832e-13 | 0.5807 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0251e-09 | 0.2360 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.7575 | 0.0234 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0050 | 0.0876 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.5771e-10 | 0.8338 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 6.9532e-10 | 0.3324 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7179e-17 | 3.5884 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7179e-17 | 3.5475 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7179e-17 | 1.9461 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7179e-17 | 3.2607 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7179e-17 | 3.3752 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.94 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 161.20 s |
| Final PPO training time | 76.59 s |
| Average ERWO-PPO decision time per task | 0.0955 ms |
| Average PPO-Equal decision time per task | 0.0958 ms |
