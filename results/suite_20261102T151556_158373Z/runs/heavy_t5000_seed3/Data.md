### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 42.37 | 134.42 | 81.93 | 0.3270 | 6.06 |
| Optimized ($w^*$) | 0.1608 | 0.2265 | 0.5239 | 0.0889 | 44.23 | 134.42 | 79.24 | 0.3255 | 9.84 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0010 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 70.88 | 130.76 | 36.55 | 0.1901 | 68.77 | 0.0053 |
| DQN-Equal | 84.15 | 134.19 | 18.13 | 0.0403 | 102.29 | 0.0498 |
| DDPG-Equal | 42.30 | 134.39 | 82.03 | 0.3269 | 5.96 | 0.0685 |
| PPO-Equal | 42.37 | 134.42 | 81.93 | 0.3270 | 6.06 | 0.0960 |
| ERWO-PPO | 44.23 | 134.42 | 79.24 | 0.3255 | 9.84 | 0.0957 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 42.37 | 134.42 | 81.93 | 0.3270 | 6.06 |
| ERWO-PPO | 44.23 | 134.42 | 79.24 | 0.3255 | 9.84 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 3.5031e-10 | 0.8203 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0008 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.5294e-09 | 0.6125 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 3.5031e-10 | 0.6875 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 3.5031e-10 | 0.8418 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7362e-17 | 17.0018 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0046 | 0.2757 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7362e-17 | 13.5026 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7362e-17 | 86.1042 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7362e-17 | 17.7591 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.5031e-10 | 0.8584 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0303 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 5.7542e-10 | 0.6378 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0578e-06 | 0.6426 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6531e-13 | 0.8633 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7362e-17 | 7.8413 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7362e-17 | 3.6171 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7362e-17 | 7.1543 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7362e-17 | 4.6706 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7362e-17 | 8.0706 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.87 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 158.71 s |
| Final PPO training time | 4.02 s |
| Average ERWO-PPO decision time per task | 0.0957 ms |
| Average PPO-Equal decision time per task | 0.0960 ms |
