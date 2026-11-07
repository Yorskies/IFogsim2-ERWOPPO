### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 80.05 | 134.40 | 22.63 | 0.1121 | 87.06 |
| Optimized ($w^*$) | 0.1832 | 0.3323 | 0.3487 | 0.1359 | 80.77 | 134.37 | 20.98 | 0.0773 | 90.76 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0011 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0026 |
| Q-Learning-Equal | 66.19 | 129.63 | 46.33 | 0.2173 | 56.83 | 0.0055 |
| DQN-Equal | 82.72 | 134.06 | 18.92 | 0.0485 | 98.62 | 0.0541 |
| DDPG-Equal | 79.77 | 134.35 | 22.59 | 0.0797 | 87.29 | 0.0717 |
| PPO-Equal | 80.05 | 134.40 | 22.63 | 0.1121 | 87.06 | 0.0997 |
| ERWO-PPO | 80.77 | 134.37 | 20.98 | 0.0773 | 90.76 | 0.0949 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 80.05 | 134.40 | 22.63 | 0.1121 | 87.06 |
| ERWO-PPO | 80.77 | 134.37 | 20.98 | 0.0773 | 90.76 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.2709e-04 | 0.3922 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.4318 | 0.0407 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.3821e-07 | 0.4123 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 6.0317e-16 | 1.5019 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.0116e-07 | 0.6410 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.7852e-16 | 1.1977 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 2.7653e-08 | 0.4184 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.5925e-13 | 0.5493 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.1233e-16 | 2.0577 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 9.1871e-17 | 1.6941 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 9.0509e-08 | 0.5528 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.6699 | 0.0217 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 8.4655e-08 | 0.3860 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.4318 | 0.1343 | NO |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 8.7585e-09 | 0.6521 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7650e-17 | 5.0580 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7650e-17 | 4.0053 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7650e-17 | 4.4029 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7650e-17 | 4.7542 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7650e-17 | 5.2343 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.98 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 162.80 s |
| Final PPO training time | 19.71 s |
| Average ERWO-PPO decision time per task | 0.0949 ms |
| Average PPO-Equal decision time per task | 0.0997 ms |
