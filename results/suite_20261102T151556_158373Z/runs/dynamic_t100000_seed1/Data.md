### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 56.02 | 89.60 | 17.69 | 0.0408 | 68.35 |
| Optimized ($w^*$) | 0.2997 | 0.1145 | 0.1952 | 0.3905 | 56.10 | 89.56 | 17.57 | 0.0398 | 68.71 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0010 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 52.26 | 87.95 | 25.27 | 0.0692 | 59.80 | 0.0053 |
| DQN-Equal | 54.93 | 89.45 | 19.87 | 0.0594 | 64.10 | 0.0508 |
| DDPG-Equal | 56.12 | 89.62 | 17.55 | 0.0408 | 68.57 | 0.0689 |
| PPO-Equal | 56.02 | 89.60 | 17.69 | 0.0408 | 68.35 | 0.0949 |
| ERWO-PPO | 56.10 | 89.56 | 17.57 | 0.0398 | 68.71 | 0.0954 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 56.02 | 89.60 | 17.69 | 0.0408 | 68.35 |
| ERWO-PPO | 56.10 | 89.56 | 17.57 | 0.0398 | 68.71 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0011 | 0.0710 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.7150 | 0.0602 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0267 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.7462e-05 | 0.4000 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0045 | 0.1162 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7931e-17 | 0.9847 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 2.5342e-04 | 0.1926 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 8.0134e-14 | 0.5025 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7931e-17 | 2.9790 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7931e-17 | 1.4253 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0170 | NO |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.1726 | 0.0907 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0043 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.9553e-05 | 0.4106 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.7150 | 0.0454 | NO |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.7150 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.3002 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 1.5526 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.1946 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.4912 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.01 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 162.97 s |
| Final PPO training time | 79.23 s |
| Average ERWO-PPO decision time per task | 0.0954 ms |
| Average PPO-Equal decision time per task | 0.0949 ms |
