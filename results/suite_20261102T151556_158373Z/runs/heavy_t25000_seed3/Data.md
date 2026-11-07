### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 82.32 | 134.36 | 19.91 | 0.0617 | 96.17 |
| Optimized ($w^*$) | 0.1608 | 0.2265 | 0.5239 | 0.0889 | 82.86 | 134.39 | 19.18 | 0.0463 | 98.30 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0010 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 70.88 | 130.78 | 36.52 | 0.1903 | 68.78 | 0.0053 |
| DQN-Equal | 82.73 | 134.09 | 18.63 | 0.0554 | 97.90 | 0.0500 |
| DDPG-Equal | 81.88 | 134.37 | 20.94 | 0.0624 | 94.32 | 0.0688 |
| PPO-Equal | 82.32 | 134.36 | 19.91 | 0.0617 | 96.17 | 0.0976 |
| ERWO-PPO | 82.86 | 134.39 | 19.18 | 0.0463 | 98.30 | 0.0979 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 82.32 | 134.36 | 19.91 | 0.0617 | 96.17 |
| ERWO-PPO | 82.86 | 134.39 | 19.18 | 0.0463 | 98.30 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.9988e-04 | 0.3292 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0440 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0028 | 0.1912 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.2520e-16 | 1.9531 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.2846e-06 | 0.4904 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.7242 | 0.0812 | NO |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 5.1436e-14 | 0.4054 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0028 | 0.1480 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.2474e-14 | 1.4137 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.1003 | NO |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.6611e-10 | 0.5939 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0265 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.5015e-11 | 0.4706 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.7989e-16 | 1.7247 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.5457e-12 | 0.9063 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7690e-17 | 4.1105 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7690e-17 | 3.9292 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7690e-17 | 3.2511 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7690e-17 | 4.9986 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7690e-17 | 4.5654 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.07 s |
| Average candidate-evaluation time | 0.10 s |
| Total NSGA-II search time | 166.70 s |
| Final PPO training time | 20.80 s |
| Average ERWO-PPO decision time per task | 0.0979 ms |
| Average PPO-Equal decision time per task | 0.0976 ms |
