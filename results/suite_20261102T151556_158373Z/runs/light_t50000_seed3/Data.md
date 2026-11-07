### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 27.83 | 44.78 | 18.20 | 0.0451 | 33.64 |
| Optimized ($w^*$) | 0.2027 | 0.2777 | 0.2284 | 0.2912 | 27.83 | 44.80 | 18.30 | 0.0463 | 33.56 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0026 |
| Q-Learning-Equal | 24.66 | 41.25 | 33.58 | 0.0714 | 27.30 | 0.0053 |
| DQN-Equal | 28.05 | 44.48 | 17.32 | 0.0408 | 34.32 | 0.0498 |
| DDPG-Equal | 14.65 | 44.80 | 78.80 | 0.3159 | 2.82 | 0.0686 |
| PPO-Equal | 27.83 | 44.78 | 18.20 | 0.0451 | 33.64 | 0.0977 |
| ERWO-PPO | 27.83 | 44.80 | 18.30 | 0.0463 | 33.56 | 0.0956 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 27.83 | 44.78 | 18.20 | 0.0451 | 33.64 |
| ERWO-PPO | 27.83 | 44.80 | 18.30 | 0.0463 | 33.56 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0051 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.3000 | 0.0358 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0171 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0572 | 0.2555 | NO |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.8181 | 0.0397 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.7099e-10 | 0.3004 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.1115e-15 | 0.7423 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.8540e-05 | 0.1699 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.5527e-16 | 1.3166 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 5.5032e-14 | 0.3787 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.0796e-17 | 19.2629 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0110 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.0796e-17 | 9.9974 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.0796e-17 | 60.6341 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.0796e-17 | 19.2085 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.0796e-17 | 3.1171 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.0796e-17 | 4.5878 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.0796e-17 | 2.2537 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 2.8380e-14 | 1.1738 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.0796e-17 | 2.6018 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.97 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 160.04 s |
| Final PPO training time | 39.07 s |
| Average ERWO-PPO decision time per task | 0.0956 ms |
| Average PPO-Equal decision time per task | 0.0977 ms |
