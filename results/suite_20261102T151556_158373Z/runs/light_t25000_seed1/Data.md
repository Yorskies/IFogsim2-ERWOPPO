### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 27.72 | 44.80 | 18.64 | 0.0501 | 33.12 |
| Optimized ($w^*$) | 0.2951 | 0.1260 | 0.1922 | 0.3867 | 27.77 | 44.79 | 18.58 | 0.0490 | 33.33 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 25.09 | 43.82 | 30.10 | 0.1061 | 26.77 | 0.0053 |
| DQN-Equal | 27.42 | 44.66 | 18.74 | 0.0564 | 32.45 | 0.0514 |
| DDPG-Equal | 27.76 | 44.76 | 18.54 | 0.0493 | 33.25 | 0.0708 |
| PPO-Equal | 27.72 | 44.80 | 18.64 | 0.0501 | 33.12 | 0.0968 |
| ERWO-PPO | 27.77 | 44.79 | 18.58 | 0.0490 | 33.33 | 0.0965 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 27.72 | 44.80 | 18.64 | 0.0501 | 33.12 |
| ERWO-PPO | 27.77 | 44.79 | 18.58 | 0.0490 | 33.33 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.4613 | 0.0619 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0228 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0102 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.1419 | NO |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0958 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.7113e-13 | 0.4485 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 5.6830e-11 | 0.3457 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0276 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.0088e-08 | 0.8031 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.5889e-09 | 0.4114 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0220 | NO |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.3219 | 0.0782 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0068 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0384 | NO |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0370 | NO |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.4006 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.1211 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.2516e-16 | 1.6397 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 1.7329 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.3157 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.02 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 161.94 s |
| Final PPO training time | 19.57 s |
| Average ERWO-PPO decision time per task | 0.0965 ms |
| Average PPO-Equal decision time per task | 0.0968 ms |
