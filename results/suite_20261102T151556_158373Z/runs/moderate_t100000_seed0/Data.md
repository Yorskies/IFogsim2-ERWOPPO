### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 56.01 | 89.61 | 17.74 | 0.0418 | 68.24 |
| Optimized ($w^*$) | 0.2279 | 0.0986 | 0.3313 | 0.3422 | 55.98 | 89.60 | 17.88 | 0.0418 | 68.06 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0011 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 51.23 | 88.26 | 28.63 | 0.0788 | 54.82 | 0.0054 |
| DQN-Equal | 55.50 | 89.54 | 18.28 | 0.0512 | 66.15 | 0.0503 |
| DDPG-Equal | 56.06 | 89.60 | 17.68 | 0.0420 | 68.30 | 0.0693 |
| PPO-Equal | 56.01 | 89.61 | 17.74 | 0.0418 | 68.24 | 0.0943 |
| ERWO-PPO | 55.98 | 89.60 | 17.88 | 0.0418 | 68.06 | 0.0937 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 56.01 | 89.61 | 17.74 | 0.0418 | 68.24 |
| ERWO-PPO | 55.98 | 89.60 | 17.88 | 0.0418 | 68.06 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0273 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0182 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.9321 | 0.0307 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0125 | NO |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.8537 | 0.0581 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.7867e-13 | 0.4194 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.1536 | 0.1078 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.1777 | 0.0865 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.9408e-16 | 1.6763 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.8789e-14 | 0.5950 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.4648 | 0.0759 | NO |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0080 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.8537 | 0.0430 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0596 | NO |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.3751 | 0.0743 | NO |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5284e-17 | 3.1708 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5284e-17 | 1.9607 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5284e-17 | 2.1009 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5284e-17 | 2.3467 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5284e-17 | 3.3117 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.95 s |
| Average candidate-evaluation time | 0.07 s |
| Total NSGA-II search time | 160.54 s |
| Final PPO training time | 77.13 s |
| Average ERWO-PPO decision time per task | 0.0937 ms |
| Average PPO-Equal decision time per task | 0.0943 ms |
