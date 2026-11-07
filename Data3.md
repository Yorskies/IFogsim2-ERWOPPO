### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 55.99 | 89.64 | 18.07 | 0.0414 | 67.90 |
| Optimized ($w^*$) | 0.2407 | 0.2727 | 0.3437 | 0.1430 | 56.08 | 89.62 | 18.20 | 0.0412 | 67.76 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.88 | 90.18 | 80.67 | 0.3247 | 4.50 | 0.0040 |
| Least Fog | 56.26 | 89.65 | 17.77 | 0.0380 | 68.75 | 0.0057 |
| Q-Learning-Equal | 51.64 | 89.19 | 28.20 | 0.1015 | 54.50 | 0.0115 |
| DQN-Equal | 55.97 | 89.59 | 18.00 | 0.0429 | 67.56 | 0.1220 |
| DDPG-Equal | 54.95 | 89.64 | 19.97 | 0.0606 | 63.90 | 0.1414 |
| PPO-Equal | 55.99 | 89.64 | 18.07 | 0.0414 | 67.90 | 0.1864 |
| ERWO-PPO | 56.08 | 89.62 | 18.20 | 0.0412 | 67.76 | 0.1856 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 55.99 | 89.64 | 18.07 | 0.0414 | 67.90 |
| ERWO-PPO | 56.08 | 89.62 | 18.20 | 0.0412 | 67.76 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.9849 | 0.0813 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0310 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0341 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0837 | NO |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0530 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.6666 | 0.0964 | NO |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0426 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0522 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0096 | 0.5987 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0781 | NO |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.7253e-08 | 0.9631 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0329 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 8.8787e-04 | 0.4422 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.7253e-08 | 3.1761 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.7253e-08 | 1.4079 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 3.7253e-08 | 2.8787 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.8254e-06 | 0.6559 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 2.2363e-05 | 1.9786 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 3.7253e-08 | 3.1670 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 3.7253e-08 | 3.3379 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 5.86 s |
| Average candidate-evaluation time | 0.16 s |
| Total NSGA-II search time | 240.95 s |
| Final PPO training time | 108.54 s |
| Average ERWO-PPO decision time per task | 0.1856 ms |
| Average PPO-Equal decision time per task | 0.1864 ms |
