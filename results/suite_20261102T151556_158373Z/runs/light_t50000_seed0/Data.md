### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 27.71 | 44.65 | 18.36 | 0.0479 | 33.37 |
| Optimized ($w^*$) | 0.3101 | 0.1898 | 0.0245 | 0.4756 | 27.93 | 44.79 | 17.90 | 0.0433 | 33.94 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0010 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 23.20 | 42.06 | 41.40 | 0.0702 | 24.52 | 0.0053 |
| DQN-Equal | 28.04 | 44.83 | 17.46 | 0.0424 | 34.21 | 0.0510 |
| DDPG-Equal | 27.04 | 44.81 | 21.34 | 0.0721 | 30.38 | 0.0701 |
| PPO-Equal | 27.71 | 44.65 | 18.36 | 0.0479 | 33.37 | 0.0963 |
| ERWO-PPO | 27.93 | 44.79 | 17.90 | 0.0433 | 33.94 | 0.0961 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 27.71 | 44.65 | 18.36 | 0.0479 | 33.37 |
| ERWO-PPO | 27.93 | 44.79 | 17.90 | 0.0433 | 33.94 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 3.6589e-13 | 0.2902 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.1861e-08 | 0.3106 | YES |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0607 | 0.0785 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.5198e-10 | 0.8212 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.9549e-08 | 0.2769 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.1340e-06 | 0.1420 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0155 | 0.0924 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0607 | 0.0745 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0034 | 0.2824 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.0485e-04 | 0.1282 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4035e-17 | 1.0899 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.4788 | 0.0410 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.1685e-13 | 0.5761 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4035e-17 | 2.2825 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4035e-17 | 1.6066 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 4.3010 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 4.1033 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.2513e-17 | 3.6862 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 4.3348e-16 | 1.1448 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 4.0256 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.98 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 160.54 s |
| Final PPO training time | 39.47 s |
| Average ERWO-PPO decision time per task | 0.0961 ms |
| Average PPO-Equal decision time per task | 0.0963 ms |
