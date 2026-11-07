### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 54.86 | 89.59 | 20.17 | 0.0546 | 63.77 |
| Optimized ($w^*$) | 0.3003 | 0.3825 | 0.2083 | 0.1090 | 54.19 | 89.60 | 20.47 | 0.0694 | 61.37 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.88 | 90.18 | 80.67 | 0.3247 | 4.50 | 0.0046 |
| Least Fog | 56.26 | 89.65 | 17.77 | 0.0380 | 68.75 | 0.0062 |
| Q-Learning-Equal | 46.80 | 89.03 | 38.27 | 0.1657 | 40.35 | 0.0119 |
| DQN-Equal | 55.97 | 89.52 | 17.90 | 0.0440 | 67.78 | 0.1227 |
| DDPG-Equal | 54.22 | 89.62 | 21.67 | 0.0723 | 61.08 | 0.1427 |
| PPO-Equal | 54.86 | 89.59 | 20.17 | 0.0546 | 63.77 | 0.1851 |
| ERWO-PPO | 54.19 | 89.60 | 20.47 | 0.0694 | 61.37 | 0.1845 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 54.86 | 89.59 | 20.17 | 0.0546 | 63.77 |
| ERWO-PPO | 54.19 | 89.60 | 20.47 | 0.0694 | 61.37 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 3.5137e-04 | 0.5673 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0099 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0718 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.8685e-06 | 1.2965 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 5.6591e-05 | 0.7451 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.7253e-08 | 1.5210 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.8335 | 0.1419 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.8536e-04 | 0.6335 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.7253e-08 | 2.5192 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.7253e-08 | 2.1981 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0327 | NO |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0371 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.1629 | 0.3067 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.2012 | NO |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.1073 | NO |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 3.7253e-08 | 3.5487 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.5497e-05 | 0.8997 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 2.0565e-05 | 2.8946 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 5.5879e-08 | 2.9328 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 3.7253e-08 | 4.3614 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 2.54 s |
| Average candidate-evaluation time | 0.16 s |
| Total NSGA-II search time | 107.98 s |
| Final PPO training time | 26.47 s |
| Average ERWO-PPO decision time per task | 0.1845 ms |
| Average PPO-Equal decision time per task | 0.1851 ms |
