### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 14.65 | 44.80 | 78.80 | 0.3159 | 2.82 |
| Optimized ($w^*$) | 0.2110 | 0.1298 | 0.2834 | 0.3758 | 20.73 | 44.80 | 48.90 | 0.2621 | 13.99 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0026 |
| Q-Learning-Equal | 25.03 | 44.12 | 30.08 | 0.1068 | 25.61 | 0.0053 |
| DQN-Equal | 28.00 | 44.75 | 17.44 | 0.0439 | 34.06 | 0.0504 |
| DDPG-Equal | 23.03 | 43.30 | 38.38 | 0.1936 | 19.62 | 0.0696 |
| PPO-Equal | 14.65 | 44.80 | 78.80 | 0.3159 | 2.82 | 0.0980 |
| ERWO-PPO | 20.73 | 44.80 | 48.90 | 0.2621 | 13.99 | 0.0968 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 14.65 | 44.80 | 78.80 | 0.3159 | 2.82 |
| ERWO-PPO | 20.73 | 44.80 | 48.90 | 0.2621 | 13.99 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.4877e-17 | 4.9257 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.9589 | 0.0025 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.4877e-17 | 3.7230 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.4877e-17 | 2.4013 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.4877e-17 | 5.2378 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.4877e-17 | 5.7406 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0023 | 0.1242 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.4877e-17 | 4.0258 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.4877e-17 | 9.7312 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.4877e-17 | 8.0920 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.1948e-16 | 1.6494 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4877e-17 | 2.3880 | YES |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.3517e-15 | 1.2810 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.7681e-16 | 1.8914 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.5349e-16 | 2.1558 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4877e-17 | 2.7282 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4877e-17 | 1.3418 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4877e-17 | 2.1077 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4877e-17 | 4.4746 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4877e-17 | 3.5235 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.91 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 157.66 s |
| Final PPO training time | 3.96 s |
| Average ERWO-PPO decision time per task | 0.0968 ms |
| Average PPO-Equal decision time per task | 0.0980 ms |
