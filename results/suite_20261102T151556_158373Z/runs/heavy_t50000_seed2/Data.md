### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 83.87 | 134.36 | 18.23 | 0.0414 | 101.81 |
| Optimized ($w^*$) | 0.1803 | 0.2048 | 0.5471 | 0.0677 | 83.05 | 134.37 | 19.16 | 0.0466 | 98.88 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0010 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0024 |
| Q-Learning-Equal | 70.46 | 126.45 | 38.75 | 0.0591 | 78.89 | 0.0053 |
| DQN-Equal | 83.84 | 134.39 | 17.87 | 0.0434 | 101.60 | 0.0506 |
| DDPG-Equal | 81.43 | 134.35 | 21.24 | 0.0697 | 92.90 | 0.0689 |
| PPO-Equal | 83.87 | 134.36 | 18.23 | 0.0414 | 101.81 | 0.0952 |
| ERWO-PPO | 83.05 | 134.37 | 19.16 | 0.0466 | 98.88 | 0.0943 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 83.87 | 134.36 | 18.23 | 0.0414 | 101.81 |
| ERWO-PPO | 83.05 | 134.37 | 19.16 | 0.0466 | 98.88 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.5427e-14 | 0.5611 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0160 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 3.0290e-09 | 0.2594 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 6.9388e-15 | 1.2780 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 8.7480e-16 | 0.7278 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0954e-12 | 0.5290 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0300 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 5.2938e-12 | 0.3488 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0805e-07 | 0.7163 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 6.9388e-15 | 0.6687 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.0403e-16 | 0.9875 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0214 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 6.8842e-14 | 0.5480 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7440e-17 | 2.3648 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7440e-17 | 1.3311 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7440e-17 | 6.6666 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7440e-17 | 7.0827 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7440e-17 | 4.8783 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0954e-12 | 1.1179 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7440e-17 | 4.5420 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.00 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 163.83 s |
| Final PPO training time | 38.80 s |
| Average ERWO-PPO decision time per task | 0.0943 ms |
| Average PPO-Equal decision time per task | 0.0952 ms |
