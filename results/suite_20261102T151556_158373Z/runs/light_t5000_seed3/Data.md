### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 15.35 | 44.81 | 76.28 | 0.3147 | 4.19 |
| Optimized ($w^*$) | 0.2027 | 0.2777 | 0.2284 | 0.2912 | 20.54 | 44.79 | 50.50 | 0.2599 | 12.25 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 25.95 | 43.72 | 24.86 | 0.0828 | 29.41 | 0.0053 |
| DQN-Equal | 27.75 | 44.76 | 18.48 | 0.0492 | 33.28 | 0.0517 |
| DDPG-Equal | 14.65 | 44.80 | 78.76 | 0.3160 | 2.83 | 0.0704 |
| PPO-Equal | 15.35 | 44.81 | 76.28 | 0.3147 | 4.19 | 0.1027 |
| ERWO-PPO | 20.54 | 44.79 | 50.50 | 0.2599 | 12.25 | 0.0976 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 15.35 | 44.81 | 76.28 | 0.3147 | 4.19 |
| ERWO-PPO | 20.54 | 44.79 | 50.50 | 0.2599 | 12.25 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.3759e-17 | 3.7798 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.3666 | 0.0397 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.3759e-17 | 3.2252 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.3759e-17 | 2.4206 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.3759e-17 | 3.2279 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.3759e-17 | 6.2017 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.1285 | 0.0838 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.3759e-17 | 4.3220 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.3759e-17 | 9.1493 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.3759e-17 | 8.6155 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.3759e-17 | 5.3194 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.7027 | 0.0268 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.3759e-17 | 3.7653 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.3759e-17 | 2.4878 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.3759e-17 | 4.7002 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.3759e-17 | 4.2495 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.3759e-17 | 1.9180 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.3759e-17 | 3.2797 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.3759e-17 | 5.8870 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.3759e-17 | 6.3747 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.90 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 157.16 s |
| Final PPO training time | 3.97 s |
| Average ERWO-PPO decision time per task | 0.0976 ms |
| Average PPO-Equal decision time per task | 0.1027 ms |
