### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 27.92 | 44.79 | 17.94 | 0.0440 | 33.90 |
| Optimized ($w^*$) | 0.2027 | 0.2777 | 0.2284 | 0.2912 | 27.92 | 44.80 | 18.00 | 0.0441 | 33.86 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 24.66 | 41.10 | 32.96 | 0.0468 | 28.05 | 0.0054 |
| DQN-Equal | 27.53 | 44.41 | 18.54 | 0.0493 | 33.16 | 0.0517 |
| DDPG-Equal | 14.65 | 44.80 | 78.80 | 0.3159 | 2.82 | 0.0708 |
| PPO-Equal | 27.92 | 44.79 | 17.94 | 0.0440 | 33.90 | 0.0983 |
| ERWO-PPO | 27.92 | 44.80 | 18.00 | 0.0441 | 33.86 | 0.0986 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 27.92 | 44.79 | 17.94 | 0.0440 | 33.90 |
| ERWO-PPO | 27.92 | 44.80 | 18.00 | 0.0441 | 33.86 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0004 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.3529 | 0.0218 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0100 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0197 | NO |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0167 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 9.3202e-14 | 0.5069 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 2.1527e-16 | 0.9470 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.1169 | 0.0935 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 8.7696e-08 | 0.7853 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.1589e-08 | 0.3397 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.0138e-17 | 19.4807 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0063 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 6.9035e-17 | 10.0491 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.0138e-17 | 65.4808 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.0138e-17 | 19.2010 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.0138e-17 | 3.5047 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.0138e-17 | 5.1275 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 6.9035e-17 | 2.3768 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 0.5562 | 0.3322 | NO |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.0138e-17 | 2.6282 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.02 s |
| Average candidate-evaluation time | 0.04 s |
| Total NSGA-II search time | 162.05 s |
| Final PPO training time | 78.97 s |
| Average ERWO-PPO decision time per task | 0.0986 ms |
| Average PPO-Equal decision time per task | 0.0983 ms |
