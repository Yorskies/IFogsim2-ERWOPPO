### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 55.89 | 89.59 | 18.06 | 0.0422 | 67.82 |
| Optimized ($w^*$) | 0.3231 | 0.2612 | 0.2124 | 0.2033 | 55.79 | 89.47 | 17.90 | 0.0438 | 67.69 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0011 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 43.83 | 82.65 | 43.31 | 0.1084 | 44.58 | 0.0053 |
| DQN-Equal | 55.85 | 89.01 | 17.62 | 0.0409 | 68.22 | 0.0506 |
| DDPG-Equal | 55.55 | 89.59 | 18.75 | 0.0474 | 66.38 | 0.0689 |
| PPO-Equal | 55.89 | 89.59 | 18.06 | 0.0422 | 67.82 | 0.0965 |
| ERWO-PPO | 55.79 | 89.47 | 17.90 | 0.0438 | 67.69 | 0.0955 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 55.89 | 89.59 | 18.06 | 0.0422 | 67.82 |
| ERWO-PPO | 55.79 | 89.47 | 17.90 | 0.0438 | 67.69 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0238 | 0.0907 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.1235e-05 | 0.2026 | YES |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.3238 | 0.0346 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 3.3259e-04 | 0.4448 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.3238 | 0.0414 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.1578 | 0.0508 | NO |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 8.4319e-15 | 0.7729 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.1578 | 0.0605 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.4745e-08 | 0.7697 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.8533e-05 | 0.1646 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4690e-05 | 0.2123 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0038 | 0.1908 | YES |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.6551e-06 | 0.1837 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 5.2854e-07 | 0.7394 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.0717e-12 | 0.4079 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 7.3050 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 6.3244 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.3165e-17 | 5.1339 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 2.0772 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 6.1957 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.91 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 159.17 s |
| Final PPO training time | 38.43 s |
| Average ERWO-PPO decision time per task | 0.0955 ms |
| Average PPO-Equal decision time per task | 0.0965 ms |
