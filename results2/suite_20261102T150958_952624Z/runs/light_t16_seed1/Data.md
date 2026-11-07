### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 15.59 | 41.50 | 71.33 | 0.3014 | 5.92 |
| Optimized ($w^*$) | 0.2011 | 0.3701 | 0.0594 | 0.3694 | 16.60 | 39.35 | 66.00 | 0.2864 | 10.95 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.57 | 45.07 | 78.00 | 0.3165 | 2.72 | 0.0140 |
| Least Fog | 27.63 | 44.76 | 22.00 | 0.0410 | 32.26 | 0.0245 |
| Q-Learning-Equal | 12.56 | 32.32 | 71.33 | 0.2946 | 11.32 | 0.0859 |
| DQN-Equal | 14.63 | 37.94 | 78.00 | 0.2958 | 5.20 | 1.0316 |
| DDPG-Equal | 14.63 | 37.94 | 78.00 | 0.2958 | 5.20 | 0.9709 |
| PPO-Equal | 15.59 | 41.50 | 71.33 | 0.3014 | 5.92 | 1.0718 |
| ERWO-PPO | 16.60 | 39.35 | 66.00 | 0.2864 | 10.95 | 0.9989 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 15.59 | 41.50 | 71.33 | 0.3014 | 5.92 |
| ERWO-PPO | 16.60 | 39.35 | 66.00 | 0.2864 | 10.95 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.6509 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 2.1411 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.7980 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.6849 | NO |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 2.0655 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 1.1320 | NO |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 1.4205 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 2.2678 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.4707 | NO |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 2.2768 | NO |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 1.1320 | NO |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 1.4205 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 2.2678 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.4707 | NO |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 2.2768 | NO |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0000 | 2.2126 | NO |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0000 | 4.8092 | NO |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0000 | 0.9631 | NO |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0000 | 0.3761 | NO |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0000 | 0.1460 | NO |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.39 s |
| Average candidate-evaluation time | 0.26 s |
| Total NSGA-II search time | 7.33 s |
| Final PPO training time | 1.69 s |
| Average ERWO-PPO decision time per task | 0.9989 ms |
| Average PPO-Equal decision time per task | 1.0718 ms |
