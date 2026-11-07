### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 14.29 | 44.75 | 79.33 | 0.3172 | 2.52 |
| Optimized ($w^*$) | 0.6441 | 0.2786 | 0.0508 | 0.0265 | 14.29 | 44.75 | 79.33 | 0.3172 | 2.52 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.57 | 45.07 | 78.00 | 0.3165 | 2.72 | 0.0117 |
| Least Fog | 27.63 | 44.76 | 22.00 | 0.0410 | 32.26 | 0.0235 |
| Q-Learning-Equal | 14.64 | 36.67 | 68.67 | 0.2370 | 12.66 | 0.0556 |
| DQN-Equal | 14.29 | 44.75 | 79.33 | 0.3172 | 2.52 | 0.6916 |
| DDPG-Equal | 14.29 | 44.75 | 79.33 | 0.3172 | 2.52 | 0.8586 |
| PPO-Equal | 14.29 | 44.75 | 79.33 | 0.3172 | 2.52 | 1.2617 |
| ERWO-PPO | 14.29 | 44.75 | 79.33 | 0.3172 | 2.52 | 0.9904 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 14.29 | 44.75 | 79.33 | 0.3172 | 2.52 |
| ERWO-PPO | 14.29 | 44.75 | 79.33 | 0.3172 | 2.52 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0000 | 0.1453 | NO |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0000 | 4.1108 | NO |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0000 | 1.4087 | NO |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0000 | 2.3493 | NO |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0000 | 3.7210 | NO |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 5.66 s |
| Average candidate-evaluation time | 0.60 s |
| Total NSGA-II search time | 12.54 s |
| Final PPO training time | 1.53 s |
| Average ERWO-PPO decision time per task | 0.9904 ms |
| Average PPO-Equal decision time per task | 1.2617 ms |
