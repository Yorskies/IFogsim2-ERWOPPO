### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 39.90 | 89.60 | 54.54 | 0.2893 | 24.69 |
| Optimized ($w^*$) | 0.2279 | 0.0986 | 0.3313 | 0.3422 | 39.85 | 89.60 | 54.62 | 0.2969 | 25.78 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0011 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 48.27 | 88.18 | 36.63 | 0.1111 | 46.04 | 0.0052 |
| DQN-Equal | 55.69 | 89.58 | 17.78 | 0.0439 | 67.57 | 0.0495 |
| DDPG-Equal | 28.57 | 89.62 | 80.99 | 0.3243 | 4.53 | 0.0684 |
| PPO-Equal | 39.90 | 89.60 | 54.54 | 0.2893 | 24.69 | 0.1039 |
| ERWO-PPO | 39.85 | 89.60 | 54.62 | 0.2969 | 25.78 | 0.0956 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 39.90 | 89.60 | 54.54 | 0.2893 | 24.69 |
| ERWO-PPO | 39.85 | 89.60 | 54.62 | 0.2969 | 25.78 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0233 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0040 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0113 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.1277e-07 | 0.5237 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0342 | 0.2538 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.5985e-17 | 8.3683 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0334 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.5985e-17 | 6.3912 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.5985e-17 | 26.0747 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.5985e-17 | 11.0815 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5985e-17 | 6.1664 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0323 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5985e-17 | 4.6599 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5985e-17 | 2.9548 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5985e-17 | 6.6763 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5985e-17 | 3.3286 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5985e-17 | 1.9700 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.6916e-16 | 2.3656 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5985e-17 | 6.1771 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.5985e-17 | 3.4524 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.86 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 157.08 s |
| Final PPO training time | 3.94 s |
| Average ERWO-PPO decision time per task | 0.0956 ms |
| Average PPO-Equal decision time per task | 0.1039 ms |
