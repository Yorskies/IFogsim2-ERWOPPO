### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 37.06 | 89.41 | 62.80 | 0.2790 | 16.07 |
| Manual weights | 0.4000 | 0.2000 | 0.3000 | 0.1000 | 28.05 | 89.28 | 85.40 | 0.3235 | 3.34 |
| Optimized ($w^*$) | 0.2791 | 0.1598 | 0.3092 | 0.2518 | 34.56 | 89.53 | 73.40 | 0.3160 | 17.87 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Local-only | 8.46 | 58.08 | 99.60 | 0.3255 | 0.45 | 0.0032 |
| Cloud-only | 22.27 | 73.47 | 89.20 | 0.3201 | 2.43 | 0.0042 |
| Nearest-fog | 28.54 | 89.93 | 84.40 | 0.3233 | 3.55 | 0.0374 |
| Least-loaded fog | 55.59 | 89.33 | 20.80 | 0.0383 | 66.60 | 0.0573 |
| DQN-Equal | 55.44 | 89.43 | 21.00 | 0.0434 | 65.49 | 1.1118 |
| PPO-Equal | 37.06 | 89.41 | 62.80 | 0.2790 | 16.07 | 2.2583 |
| PPO-Manual | 28.05 | 89.28 | 85.40 | 0.3235 | 3.34 | 1.9568 |
| ERWO-PPO | 34.56 | 89.53 | 73.40 | 0.3160 | 17.87 | 1.8926 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 37.06 | 89.41 | 62.80 | 0.2790 | 16.07 |
| PPO-Manual | 28.05 | 89.28 | 85.40 | 0.3235 | 3.34 |
| ERWO-PPO | 34.56 | 89.53 | 73.40 | 0.3160 | 17.87 |

---

### Table 13. Statistical comparison of ERWO-PPO with PPO baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :--- | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0625 | 1.2515 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.6250 | 0.3178 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0625 | 1.9194 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.1250 | 1.4432 | NO |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.4375 | 0.4641 | NO |
| Latency | ERWO-PPO vs. PPO-Manual | Wilcoxon | 0.0625 | 4.2810 | NO |
| QoS | ERWO-PPO vs. PPO-Manual | Wilcoxon | 0.0625 | 5.2793 | NO |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 14.82 s |
| Average candidate-evaluation time | 0.80 s |
| Total NSGA-II search time | 31.23 s |
| Final PPO training time | 29.89 s |
| Average ERWO-PPO decision time per task | 1.8926 ms |
| Average PPO-Equal decision time per task | 2.2583 ms |
