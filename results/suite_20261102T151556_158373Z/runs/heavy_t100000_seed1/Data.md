### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 83.78 | 133.79 | 18.26 | 0.0398 | 102.21 |
| Optimized ($w^*$) | 0.2997 | 0.1145 | 0.1952 | 0.3905 | 84.15 | 134.39 | 18.03 | 0.0394 | 102.74 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0011 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 78.89 | 133.72 | 25.76 | 0.0802 | 85.92 | 0.0053 |
| DQN-Equal | 84.04 | 134.18 | 17.71 | 0.0390 | 102.81 | 0.0513 |
| DDPG-Equal | 80.14 | 134.38 | 22.65 | 0.0694 | 89.02 | 0.0697 |
| PPO-Equal | 83.78 | 133.79 | 18.26 | 0.0398 | 102.21 | 0.0977 |
| ERWO-PPO | 84.15 | 134.39 | 18.03 | 0.0394 | 102.74 | 0.0973 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 83.78 | 133.79 | 18.26 | 0.0398 | 102.21 |
| ERWO-PPO | 84.15 | 134.39 | 18.03 | 0.0394 | 102.74 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7950e-11 | 0.2493 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 6.9119e-14 | 0.7599 | YES |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.2752 | 0.0647 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.1965 | 0.2019 | NO |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.0565e-04 | 0.1400 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.2801 | 0.0717 | NO |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 5.5968e-08 | 0.3003 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0953 | 0.0902 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.2752 | 0.1725 | NO |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.6209 | 0.0181 | NO |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5758e-17 | 2.7877 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.6209 | 0.0199 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5758e-17 | 1.2183 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5758e-17 | 2.5947 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5758e-17 | 3.4575 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5758e-17 | 3.0736 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.7649e-15 | 0.8802 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5758e-17 | 1.9166 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5758e-17 | 3.7787 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5758e-17 | 3.5533 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.93 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 160.90 s |
| Final PPO training time | 79.30 s |
| Average ERWO-PPO decision time per task | 0.0973 ms |
| Average PPO-Equal decision time per task | 0.0977 ms |
