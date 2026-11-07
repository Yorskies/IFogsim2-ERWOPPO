### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 53.25 | 134.39 | 63.25 | 0.3154 | 21.28 |
| Optimized ($w^*$) | 0.1803 | 0.2048 | 0.5471 | 0.0677 | 72.52 | 134.33 | 33.23 | 0.1762 | 67.77 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0011 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 76.80 | 131.81 | 28.31 | 0.0938 | 84.26 | 0.0053 |
| DQN-Equal | 84.04 | 134.09 | 17.67 | 0.0418 | 102.24 | 0.0508 |
| DDPG-Equal | 42.37 | 134.42 | 81.93 | 0.3270 | 6.06 | 0.0695 |
| PPO-Equal | 53.25 | 134.39 | 63.25 | 0.3154 | 21.28 | 0.0947 |
| ERWO-PPO | 72.52 | 134.33 | 33.23 | 0.1762 | 67.77 | 0.0951 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 53.25 | 134.39 | 63.25 | 0.3154 | 21.28 |
| ERWO-PPO | 72.52 | 134.33 | 33.23 | 0.1762 | 67.77 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7449e-17 | 7.1191 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.2444 | 0.0840 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7449e-17 | 5.0082 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7449e-17 | 3.5774 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7449e-17 | 7.3207 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7449e-17 | 4.8659 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.1581e-04 | 0.3316 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7449e-17 | 2.8425 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7449e-17 | 3.7025 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7449e-17 | 5.4889 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7449e-17 | 13.0404 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.2788 | 0.1070 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7449e-17 | 9.0638 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7449e-17 | 4.1628 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7449e-17 | 10.7448 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0028e-13 | 1.5916 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7449e-17 | 2.9376 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.8145e-08 | 0.8318 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 6.4238e-16 | 2.0643 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 2.0148e-16 | 2.3073 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.75 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 153.89 s |
| Final PPO training time | 4.02 s |
| Average ERWO-PPO decision time per task | 0.0951 ms |
| Average PPO-Equal decision time per task | 0.0947 ms |
