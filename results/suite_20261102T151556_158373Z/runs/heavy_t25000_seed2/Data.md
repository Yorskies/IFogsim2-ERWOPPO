### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 80.38 | 134.38 | 22.43 | 0.0827 | 88.78 |
| Optimized ($w^*$) | 0.1803 | 0.2048 | 0.5471 | 0.0677 | 80.78 | 134.36 | 21.73 | 0.0770 | 90.50 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0011 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 76.84 | 131.85 | 28.26 | 0.0938 | 84.29 | 0.0052 |
| DQN-Equal | 83.00 | 133.00 | 18.49 | 0.0449 | 100.11 | 0.0514 |
| DDPG-Equal | 47.68 | 131.23 | 73.65 | 0.3215 | 20.46 | 0.0689 |
| PPO-Equal | 80.38 | 134.38 | 22.43 | 0.0827 | 88.78 | 0.0960 |
| ERWO-PPO | 80.78 | 134.36 | 21.73 | 0.0770 | 90.50 | 0.0961 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 80.38 | 134.38 | 22.43 | 0.0827 | 88.78 |
| ERWO-PPO | 80.78 | 134.36 | 21.73 | 0.0770 | 90.50 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0216 | 0.1856 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0283 | 0.0201 | YES |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0283 | 0.1675 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0283 | 0.2548 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0216 | 0.2565 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 8.3127e-17 | 1.2421 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7506e-17 | 1.5681 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.7335e-16 | 0.8655 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7506e-17 | 2.3971 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7506e-17 | 1.9785 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7506e-17 | 13.6767 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.7475e-16 | 1.6144 | YES |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7506e-17 | 11.0737 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7506e-17 | 18.9903 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7506e-17 | 11.0246 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7506e-17 | 1.8587 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7506e-17 | 2.9247 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.7603e-16 | 1.5159 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.4398e-07 | 0.8012 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 2.3284e-13 | 1.0694 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.98 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 162.88 s |
| Final PPO training time | 19.82 s |
| Average ERWO-PPO decision time per task | 0.0961 ms |
| Average PPO-Equal decision time per task | 0.0960 ms |
