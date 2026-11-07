### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 18.46 | 44.81 | 61.78 | 0.2979 | 11.11 |
| Optimized ($w^*$) | 0.2951 | 0.1260 | 0.1922 | 0.3867 | 24.83 | 44.81 | 28.14 | 0.1399 | 23.80 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0012 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0027 |
| Q-Learning-Equal | 25.08 | 43.80 | 30.12 | 0.1062 | 26.76 | 0.0057 |
| DQN-Equal | 27.83 | 44.69 | 17.68 | 0.0443 | 33.83 | 0.0556 |
| DDPG-Equal | 27.27 | 44.64 | 20.32 | 0.0673 | 31.54 | 0.0740 |
| PPO-Equal | 18.46 | 44.81 | 61.78 | 0.2979 | 11.11 | 0.1079 |
| ERWO-PPO | 24.83 | 44.81 | 28.14 | 0.1399 | 23.80 | 0.1009 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 18.46 | 44.81 | 61.78 | 0.2979 | 11.11 |
| ERWO-PPO | 24.83 | 44.81 | 28.14 | 0.1399 | 23.80 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.5199e-17 | 4.1988 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.7491 | 0.0144 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.5199e-17 | 4.0363 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.5199e-17 | 4.6887 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.5199e-17 | 3.4702 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.5199e-17 | 2.5424 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 2.1594e-06 | 0.2994 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.5199e-17 | 1.4985 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.5199e-17 | 2.9234 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.5199e-17 | 3.0060 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5199e-17 | 2.0450 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 6.1310e-09 | 0.3834 | YES |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.4035e-15 | 1.1129 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5199e-17 | 2.1519 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5199e-17 | 2.3196 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 0.2955 | 0.1761 | NO |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5199e-17 | 2.1698 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 0.1060 | 0.2471 | NO |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 2.7489e-06 | 0.7305 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.9396e-06 | 0.7723 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.87 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 156.18 s |
| Final PPO training time | 4.04 s |
| Average ERWO-PPO decision time per task | 0.1009 ms |
| Average PPO-Equal decision time per task | 0.1079 ms |
