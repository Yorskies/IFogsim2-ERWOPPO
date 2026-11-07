### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 28.57 | 89.62 | 80.99 | 0.3243 | 4.53 |
| Optimized ($w^*$) | 0.3231 | 0.2612 | 0.2124 | 0.2033 | 38.12 | 89.57 | 57.69 | 0.2822 | 19.97 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0011 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0026 |
| Q-Learning-Equal | 50.40 | 86.27 | 28.03 | 0.0986 | 55.82 | 0.0054 |
| DQN-Equal | 55.94 | 89.36 | 17.35 | 0.0407 | 68.50 | 0.0544 |
| DDPG-Equal | 29.54 | 89.61 | 78.72 | 0.3231 | 7.13 | 0.0719 |
| PPO-Equal | 28.57 | 89.62 | 80.99 | 0.3243 | 4.53 | 0.0963 |
| ERWO-PPO | 38.12 | 89.57 | 57.69 | 0.2822 | 19.97 | 0.0964 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 28.57 | 89.62 | 80.99 | 0.3243 | 4.53 |
| ERWO-PPO | 38.12 | 89.57 | 57.69 | 0.2822 | 19.97 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.6084e-17 | 6.5029 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.3255 | 0.0776 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.6084e-17 | 4.7791 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.6084e-17 | 2.9752 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.6084e-17 | 5.8914 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6084e-17 | 11.6253 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.4707e-07 | 0.3399 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6084e-17 | 7.8944 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6084e-17 | 16.8778 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6084e-17 | 14.2651 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6084e-17 | 4.9579 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.3255 | 0.0601 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6084e-17 | 3.9659 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6084e-17 | 2.8786 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6084e-17 | 3.6875 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6084e-17 | 6.7832 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6084e-17 | 3.7058 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6084e-17 | 5.5337 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6084e-17 | 6.7900 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6084e-17 | 8.9201 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.93 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 159.57 s |
| Final PPO training time | 4.03 s |
| Average ERWO-PPO decision time per task | 0.0964 ms |
| Average PPO-Equal decision time per task | 0.0963 ms |
