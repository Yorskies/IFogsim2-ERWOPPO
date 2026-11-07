### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 32.09 | 89.61 | 74.35 | 0.3180 | 12.22 |
| Optimized ($w^*$) | 0.2997 | 0.1145 | 0.1952 | 0.3905 | 48.05 | 89.61 | 36.11 | 0.1544 | 43.49 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0010 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 52.85 | 87.61 | 23.60 | 0.0503 | 62.28 | 0.0053 |
| DQN-Equal | 55.93 | 89.49 | 17.85 | 0.0416 | 68.11 | 0.0502 |
| DDPG-Equal | 45.77 | 89.61 | 38.44 | 0.1991 | 33.55 | 0.0693 |
| PPO-Equal | 32.09 | 89.61 | 74.35 | 0.3180 | 12.22 | 0.0956 |
| ERWO-PPO | 48.05 | 89.61 | 36.11 | 0.1544 | 43.49 | 0.0935 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 32.09 | 89.61 | 74.35 | 0.3180 | 12.22 |
| ERWO-PPO | 48.05 | 89.61 | 36.11 | 0.1544 | 43.49 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.6140e-17 | 6.0041 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0021 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.6140e-17 | 5.2430 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.6140e-17 | 6.5080 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.6140e-17 | 5.2652 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6140e-17 | 5.0890 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0188 | 0.1885 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6140e-17 | 3.3518 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6140e-17 | 4.5633 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6140e-17 | 5.9979 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 6.6225e-15 | 1.3612 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0115 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.0572e-04 | 0.4044 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.7799e-12 | 1.2789 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0826e-16 | 2.3858 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6140e-17 | 2.8714 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6140e-17 | 2.7775 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6140e-17 | 2.3604 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6140e-17 | 4.1316 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6140e-17 | 4.6498 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.88 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 157.77 s |
| Final PPO training time | 3.93 s |
| Average ERWO-PPO decision time per task | 0.0935 ms |
| Average PPO-Equal decision time per task | 0.0956 ms |
