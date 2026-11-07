### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 83.48 | 134.41 | 18.67 | 0.0461 | 100.16 |
| Optimized ($w^*$) | 0.3593 | 0.3446 | 0.0689 | 0.2271 | 83.95 | 134.43 | 18.29 | 0.0417 | 101.77 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0010 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 77.74 | 133.71 | 28.17 | 0.1028 | 82.56 | 0.0054 |
| DQN-Equal | 81.30 | 133.97 | 19.71 | 0.0816 | 92.63 | 0.0554 |
| DDPG-Equal | 42.30 | 134.40 | 82.05 | 0.3269 | 5.96 | 0.0736 |
| PPO-Equal | 83.48 | 134.41 | 18.67 | 0.0461 | 100.16 | 0.1074 |
| ERWO-PPO | 83.95 | 134.43 | 18.29 | 0.0417 | 101.77 | 0.1056 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 83.48 | 134.41 | 18.67 | 0.0461 | 100.16 |
| ERWO-PPO | 83.95 | 134.43 | 18.29 | 0.0417 | 101.77 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 4.4970e-15 | 0.3088 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.1200 | 0.0300 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0165 | 0.1004 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.9546e-13 | 1.0778 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.9332e-11 | 0.3846 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6878e-17 | 1.6631 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 2.9546e-13 | 0.5866 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.8411e-10 | 0.3835 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6878e-17 | 2.5965 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6878e-17 | 2.1442 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6878e-17 | 30.5474 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.6799 | 0.0330 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6878e-17 | 17.7347 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6878e-17 | 103.7059 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6878e-17 | 31.4963 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6878e-17 | 3.0416 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.5674e-16 | 0.9743 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6878e-17 | 2.0883 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6878e-17 | 3.3104 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6878e-17 | 3.5317 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.98 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 162.90 s |
| Final PPO training time | 77.20 s |
| Average ERWO-PPO decision time per task | 0.1056 ms |
| Average PPO-Equal decision time per task | 0.1074 ms |
