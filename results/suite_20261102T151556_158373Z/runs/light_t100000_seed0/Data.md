### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 27.92 | 44.73 | 17.68 | 0.0448 | 33.95 |
| Optimized ($w^*$) | 0.3101 | 0.1898 | 0.0245 | 0.4756 | 27.98 | 44.65 | 17.88 | 0.0423 | 34.06 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0010 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 24.70 | 43.87 | 35.82 | 0.1297 | 25.09 | 0.0053 |
| DQN-Equal | 27.90 | 44.63 | 17.82 | 0.0473 | 33.53 | 0.0503 |
| DDPG-Equal | 27.99 | 44.80 | 17.72 | 0.0427 | 34.13 | 0.0685 |
| PPO-Equal | 27.92 | 44.73 | 17.68 | 0.0448 | 33.95 | 0.0946 |
| ERWO-PPO | 27.98 | 44.65 | 17.88 | 0.0423 | 34.06 | 0.0944 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 27.92 | 44.73 | 17.68 | 0.0448 | 33.95 |
| ERWO-PPO | 27.98 | 44.65 | 17.88 | 0.0423 | 34.06 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0564 | 0.0789 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0057 | 0.1708 | YES |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0344 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.1693e-07 | 0.5921 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0564 | 0.0499 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0010 | 0.1141 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.8072 | 0.0607 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0104 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.1737e-14 | 1.0525 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.3502e-09 | 0.2584 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0106 | NO |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.1362e-09 | 0.3532 | YES |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.8317 | 0.0281 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.8072 | 0.1235 | NO |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0340 | NO |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5208e-17 | 2.6543 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.1051e-16 | 1.6716 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5208e-17 | 2.4167 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5208e-17 | 2.3136 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5208e-17 | 3.0516 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.97 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 160.26 s |
| Final PPO training time | 78.55 s |
| Average ERWO-PPO decision time per task | 0.0944 ms |
| Average PPO-Equal decision time per task | 0.0946 ms |
