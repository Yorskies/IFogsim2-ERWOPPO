### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 53.68 | 89.49 | 20.01 | 0.0709 | 60.68 |
| Optimized ($w^*$) | 0.2030 | 0.1319 | 0.3001 | 0.3650 | 55.29 | 89.61 | 18.65 | 0.0503 | 65.68 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0011 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 44.90 | 88.01 | 44.58 | 0.2076 | 39.97 | 0.0054 |
| DQN-Equal | 54.56 | 89.20 | 18.29 | 0.0537 | 65.45 | 0.0500 |
| DDPG-Equal | 28.50 | 89.60 | 81.21 | 0.3242 | 4.43 | 0.0691 |
| PPO-Equal | 53.68 | 89.49 | 20.01 | 0.0709 | 60.68 | 0.0972 |
| ERWO-PPO | 55.29 | 89.61 | 18.65 | 0.0503 | 65.68 | 0.0968 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 53.68 | 89.49 | 20.01 | 0.0709 | 60.68 |
| ERWO-PPO | 55.29 | 89.61 | 18.65 | 0.0503 | 65.68 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.4446e-17 | 1.2338 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0104 | 0.1974 | YES |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 6.2542e-07 | 0.2734 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.4446e-17 | 1.9871 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 9.7381e-17 | 1.3206 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.9334e-13 | 0.6058 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.9741e-14 | 0.7033 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.5894 | 0.0757 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0080 | 0.4304 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.4461 | 0.0711 | NO |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4446e-17 | 24.6726 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.9015 | 0.0144 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4446e-17 | 13.6627 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4446e-17 | 66.5373 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4446e-17 | 23.8955 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4446e-17 | 4.8429 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4446e-17 | 2.2338 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4446e-17 | 3.8467 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4446e-17 | 5.5982 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4446e-17 | 5.9199 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.99 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 162.19 s |
| Final PPO training time | 17.92 s |
| Average ERWO-PPO decision time per task | 0.0968 ms |
| Average PPO-Equal decision time per task | 0.0972 ms |
