### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 37.76 | 89.54 | 59.13 | 0.3001 | 21.65 |
| Optimized ($w^*$) | 0.0585 | 0.3547 | 0.2504 | 0.3364 | 38.26 | 89.55 | 55.91 | 0.3087 | 20.54 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0011 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 49.28 | 88.40 | 32.27 | 0.1228 | 49.90 | 0.0055 |
| DQN-Equal | 56.25 | 89.49 | 17.53 | 0.0416 | 68.24 | 0.0512 |
| DDPG-Equal | 53.61 | 89.59 | 21.47 | 0.0759 | 59.64 | 0.0701 |
| PPO-Equal | 37.76 | 89.54 | 59.13 | 0.3001 | 21.65 | 0.0950 |
| ERWO-PPO | 38.26 | 89.55 | 55.91 | 0.3087 | 20.54 | 0.0953 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 37.76 | 89.54 | 59.13 | 0.3001 | 21.65 |
| ERWO-PPO | 38.26 | 89.55 | 55.91 | 0.3087 | 20.54 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0228 | 0.2977 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.7362 | 0.0131 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.2727e-08 | 0.5895 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 5.6918e-05 | 0.5047 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0662 | 0.3081 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6666e-17 | 13.0294 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.5432 | 0.0987 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6666e-17 | 7.6907 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6666e-17 | 18.4502 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6666e-17 | 14.7646 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6666e-17 | 10.9639 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.5950 | 0.0582 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6666e-17 | 6.7184 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6666e-17 | 13.9156 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6666e-17 | 11.3903 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6666e-17 | 5.8041 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6666e-17 | 1.6203 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6666e-17 | 4.0092 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6666e-17 | 6.8054 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6666e-17 | 6.6675 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.95 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 160.51 s |
| Final PPO training time | 3.93 s |
| Average ERWO-PPO decision time per task | 0.0953 ms |
| Average PPO-Equal decision time per task | 0.0950 ms |
