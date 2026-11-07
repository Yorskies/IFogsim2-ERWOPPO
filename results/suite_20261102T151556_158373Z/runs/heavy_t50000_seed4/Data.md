### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 83.50 | 134.40 | 18.89 | 0.0436 | 100.24 |
| Optimized ($w^*$) | 0.3593 | 0.3446 | 0.0689 | 0.2271 | 83.79 | 134.41 | 18.43 | 0.0419 | 101.31 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0011 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 63.82 | 133.12 | 54.09 | 0.2621 | 50.89 | 0.0053 |
| DQN-Equal | 83.90 | 134.38 | 18.43 | 0.0456 | 100.92 | 0.0510 |
| DDPG-Equal | 42.30 | 134.40 | 82.05 | 0.3269 | 5.96 | 0.0702 |
| PPO-Equal | 83.50 | 134.40 | 18.89 | 0.0436 | 100.24 | 0.0965 |
| ERWO-PPO | 83.79 | 134.41 | 18.43 | 0.0419 | 101.31 | 0.0968 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 83.50 | 134.40 | 18.89 | 0.0436 | 100.24 |
| ERWO-PPO | 83.79 | 134.41 | 18.43 | 0.0419 | 101.31 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.6520e-07 | 0.2004 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0187 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 9.6684e-04 | 0.1298 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.6301e-07 | 0.5969 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 4.8561e-08 | 0.2838 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.4279 | 0.0753 | NO |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0406 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0018 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.2624e-13 | 1.0489 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.3199 | 0.1014 | NO |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7091e-17 | 30.8475 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0101 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7091e-17 | 18.4458 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7091e-17 | 128.6585 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7091e-17 | 34.2448 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7091e-17 | 7.4336 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 9.9213e-17 | 1.5230 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7091e-17 | 6.7293 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7091e-17 | 13.6244 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7091e-17 | 9.4591 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.99 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 163.40 s |
| Final PPO training time | 39.40 s |
| Average ERWO-PPO decision time per task | 0.0968 ms |
| Average PPO-Equal decision time per task | 0.0965 ms |
