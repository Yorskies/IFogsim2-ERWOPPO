### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 27.91 | 44.80 | 17.82 | 0.0450 | 33.90 |
| Optimized ($w^*$) | 0.2951 | 0.1260 | 0.1922 | 0.3867 | 27.91 | 44.80 | 17.80 | 0.0457 | 33.88 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 26.01 | 43.84 | 24.70 | 0.0727 | 29.55 | 0.0053 |
| DQN-Equal | 27.76 | 44.46 | 18.40 | 0.0526 | 33.14 | 0.0511 |
| DDPG-Equal | 27.80 | 44.68 | 18.90 | 0.0590 | 32.80 | 0.0686 |
| PPO-Equal | 27.91 | 44.80 | 17.82 | 0.0450 | 33.90 | 0.0972 |
| ERWO-PPO | 27.91 | 44.80 | 17.80 | 0.0457 | 33.88 | 0.0969 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 27.91 | 44.80 | 17.82 | 0.0450 | 33.90 |
| ERWO-PPO | 27.91 | 44.80 | 17.80 | 0.0457 | 33.88 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0057 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0074 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0033 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.7484 | 0.1376 | NO |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0079 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0021 | 0.1893 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 6.3254e-16 | 0.8134 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0704 | 0.1016 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 2.2560e-10 | 0.9748 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.2747e-08 | 0.3524 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0021 | 0.1463 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.4051e-08 | 0.3106 | YES |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 5.6248e-04 | 0.1891 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 4.3416e-16 | 1.7252 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 6.5997e-13 | 0.5273 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.1731 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.1560 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.5979e-15 | 1.1318 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 9.5136e-17 | 1.8849 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 1.9274 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.86 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 155.75 s |
| Final PPO training time | 78.57 s |
| Average ERWO-PPO decision time per task | 0.0969 ms |
| Average PPO-Equal decision time per task | 0.0972 ms |
