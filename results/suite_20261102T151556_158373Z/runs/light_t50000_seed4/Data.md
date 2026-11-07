### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 27.92 | 44.79 | 17.96 | 0.0444 | 33.92 |
| Optimized ($w^*$) | 0.2110 | 0.1298 | 0.2834 | 0.3758 | 27.78 | 44.77 | 18.30 | 0.0469 | 33.43 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0026 |
| Q-Learning-Equal | 25.81 | 44.17 | 27.24 | 0.0828 | 27.91 | 0.0055 |
| DQN-Equal | 27.47 | 44.53 | 18.96 | 0.0632 | 32.23 | 0.0521 |
| DDPG-Equal | 27.89 | 44.81 | 18.08 | 0.0478 | 33.72 | 0.0711 |
| PPO-Equal | 27.92 | 44.79 | 17.96 | 0.0444 | 33.92 | 0.0974 |
| ERWO-PPO | 27.78 | 44.77 | 18.30 | 0.0469 | 33.43 | 0.0967 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 27.92 | 44.79 | 17.96 | 0.0444 | 33.92 |
| ERWO-PPO | 27.78 | 44.77 | 18.30 | 0.0469 | 33.43 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.2925e-07 | 0.1780 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.2799 | 0.0519 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.2457 | 0.0567 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0567e-07 | 0.5867 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 4.1644e-08 | 0.2298 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0801e-10 | 0.3992 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 2.0354e-13 | 0.5692 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0683 | 0.1100 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 2.1435e-15 | 1.3111 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.3881e-12 | 0.5594 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.7713e-07 | 0.1378 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0133 | 0.0890 | YES |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.2799 | 0.0359 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.2799 | 0.1756 | NO |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.4339e-04 | 0.1321 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.0380 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.9397e-17 | 1.2885 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 3.9636e-16 | 1.3440 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.1140 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.1358 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.96 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 159.67 s |
| Final PPO training time | 39.47 s |
| Average ERWO-PPO decision time per task | 0.0967 ms |
| Average PPO-Equal decision time per task | 0.0974 ms |
