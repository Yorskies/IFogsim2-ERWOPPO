### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 83.71 | 134.30 | 18.39 | 0.0442 | 101.12 |
| Optimized ($w^*$) | 0.1832 | 0.3323 | 0.3487 | 0.1359 | 82.61 | 134.34 | 19.47 | 0.0483 | 97.38 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0010 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 66.19 | 129.64 | 46.33 | 0.2175 | 56.82 | 0.0052 |
| DQN-Equal | 82.99 | 133.51 | 18.63 | 0.0491 | 99.38 | 0.0515 |
| DDPG-Equal | 83.95 | 134.39 | 18.16 | 0.0420 | 101.97 | 0.0702 |
| PPO-Equal | 83.71 | 134.30 | 18.39 | 0.0442 | 101.12 | 0.0953 |
| ERWO-PPO | 82.61 | 134.34 | 19.47 | 0.0483 | 97.38 | 0.0958 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 83.71 | 134.30 | 18.39 | 0.0442 | 101.12 |
| ERWO-PPO | 82.61 | 134.34 | 19.47 | 0.0483 | 97.38 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.0327e-16 | 0.7192 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.5007 | 0.0556 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0239e-08 | 0.2931 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.3053e-10 | 0.8372 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.4199e-16 | 0.9154 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 8.1740e-05 | 0.2425 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7642e-17 | 1.0795 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.7829e-06 | 0.2247 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.6352 | 0.1275 | NO |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 8.1008e-11 | 0.4727 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7642e-17 | 0.8882 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.5007 | 0.0727 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0215e-08 | 0.3560 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.4707e-15 | 1.4041 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7642e-17 | 1.1350 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7642e-17 | 5.7344 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7642e-17 | 3.9705 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7642e-17 | 4.6928 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7642e-17 | 6.3483 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7642e-17 | 6.5738 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.98 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 162.71 s |
| Final PPO training time | 39.41 s |
| Average ERWO-PPO decision time per task | 0.0958 ms |
| Average PPO-Equal decision time per task | 0.0953 ms |
