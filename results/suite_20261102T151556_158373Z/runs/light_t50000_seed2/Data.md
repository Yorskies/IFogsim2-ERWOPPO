### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 27.88 | 44.80 | 18.22 | 0.0450 | 33.69 |
| Optimized ($w^*$) | 0.1803 | 0.2048 | 0.5471 | 0.0677 | 27.72 | 44.79 | 18.68 | 0.0502 | 33.13 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 24.24 | 43.71 | 35.06 | 0.1171 | 24.29 | 0.0053 |
| DQN-Equal | 27.80 | 44.72 | 18.10 | 0.0508 | 33.41 | 0.0512 |
| DDPG-Equal | 27.58 | 44.79 | 18.68 | 0.0519 | 32.74 | 0.0692 |
| PPO-Equal | 27.88 | 44.80 | 18.22 | 0.0450 | 33.69 | 0.0991 |
| ERWO-PPO | 27.72 | 44.79 | 18.68 | 0.0502 | 33.13 | 0.0994 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 27.88 | 44.80 | 18.22 | 0.0450 | 33.69 |
| ERWO-PPO | 27.72 | 44.79 | 18.68 | 0.0502 | 33.13 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 6.8538e-10 | 0.2047 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0142 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.1821 | 0.0762 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 6.7105e-11 | 0.8771 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 5.5693e-06 | 0.2607 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0887 | 0.1064 | NO |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.6217e-07 | 0.1867 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0734 | 0.0970 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0745 | NO |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0887 | 0.1320 | NO |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 5.8357e-05 | 0.1781 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0031 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0000 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0694 | 0.2522 | NO |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0017 | 0.1809 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 2.7962 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 2.0739 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.1981e-17 | 2.1336 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 2.2835 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 2.9488 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.92 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 158.14 s |
| Final PPO training time | 39.17 s |
| Average ERWO-PPO decision time per task | 0.0994 ms |
| Average PPO-Equal decision time per task | 0.0991 ms |
