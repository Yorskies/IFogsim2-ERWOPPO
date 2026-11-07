### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 83.54 | 134.22 | 18.60 | 0.0430 | 100.87 |
| Optimized ($w^*$) | 0.1803 | 0.2048 | 0.5471 | 0.0677 | 84.05 | 134.39 | 18.08 | 0.0399 | 102.41 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0010 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 73.24 | 128.40 | 33.55 | 0.0729 | 80.62 | 0.0053 |
| DQN-Equal | 81.63 | 134.27 | 20.28 | 0.0663 | 94.03 | 0.0503 |
| DDPG-Equal | 83.75 | 133.95 | 18.61 | 0.0489 | 99.94 | 0.0699 |
| PPO-Equal | 83.54 | 134.22 | 18.60 | 0.0430 | 100.87 | 0.0966 |
| ERWO-PPO | 84.05 | 134.39 | 18.08 | 0.0399 | 102.41 | 0.0960 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 83.54 | 134.22 | 18.60 | 0.0430 | 100.87 |
| ERWO-PPO | 84.05 | 134.39 | 18.08 | 0.0399 | 102.41 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.7637e-15 | 0.3506 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 6.0858e-08 | 0.2343 | YES |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.0548e-04 | 0.1382 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.8437e-15 | 1.1274 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.2081e-13 | 0.3693 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6944e-17 | 1.6592 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0037 | 0.1667 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 5.0001e-15 | 0.6008 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6944e-17 | 2.9923 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6944e-17 | 1.9957 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.0548e-04 | 0.2129 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.2081e-13 | 0.6388 | YES |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.5372e-04 | 0.1465 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6944e-17 | 1.9413 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 4.8917e-14 | 0.6203 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6944e-17 | 5.3236 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6944e-17 | 6.0136 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6944e-17 | 3.7150 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6944e-17 | 1.9587 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6944e-17 | 4.4462 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.01 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 164.03 s |
| Final PPO training time | 77.30 s |
| Average ERWO-PPO decision time per task | 0.0960 ms |
| Average PPO-Equal decision time per task | 0.0966 ms |
