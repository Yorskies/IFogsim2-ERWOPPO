### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 27.53 | 44.79 | 19.44 | 0.0560 | 32.44 |
| Optimized ($w^*$) | 0.2027 | 0.2777 | 0.2284 | 0.2912 | 27.32 | 44.79 | 19.66 | 0.0592 | 31.84 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 25.95 | 43.73 | 24.90 | 0.0829 | 29.38 | 0.0054 |
| DQN-Equal | 27.69 | 44.71 | 18.54 | 0.0515 | 33.00 | 0.0516 |
| DDPG-Equal | 14.65 | 44.80 | 78.80 | 0.3159 | 2.82 | 0.0703 |
| PPO-Equal | 27.53 | 44.79 | 19.44 | 0.0560 | 32.44 | 0.0976 |
| ERWO-PPO | 27.32 | 44.79 | 19.66 | 0.0592 | 31.84 | 0.0962 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 27.53 | 44.79 | 19.44 | 0.0560 | 32.44 |
| ERWO-PPO | 27.32 | 44.79 | 19.66 | 0.0592 | 31.84 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.8592e-10 | 0.2783 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.2350 | 0.0107 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.5250 | 0.0367 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0019 | 0.3717 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 8.6495e-07 | 0.2893 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.7925e-14 | 0.5040 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 9.2029e-06 | 0.2101 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 6.7034e-05 | 0.1903 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 2.5196e-10 | 0.8326 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.2209e-13 | 0.5728 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4035e-17 | 18.5801 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.6549 | 0.0234 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.2341e-17 | 9.8453 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4035e-17 | 36.7247 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4035e-17 | 19.1203 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 1.4751 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 1.9192 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 3.5359e-13 | 0.8225 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 3.4037e-13 | 1.1228 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.1037e-14 | 1.0538 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.97 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 159.95 s |
| Final PPO training time | 19.77 s |
| Average ERWO-PPO decision time per task | 0.0962 ms |
| Average PPO-Equal decision time per task | 0.0976 ms |
