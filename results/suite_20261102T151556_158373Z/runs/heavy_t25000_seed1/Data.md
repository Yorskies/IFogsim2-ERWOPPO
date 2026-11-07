### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 82.43 | 134.36 | 19.19 | 0.0498 | 97.03 |
| Optimized ($w^*$) | 0.2997 | 0.1145 | 0.1952 | 0.3905 | 83.40 | 134.37 | 18.94 | 0.0457 | 100.10 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0010 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 73.30 | 133.50 | 35.25 | 0.1203 | 69.57 | 0.0052 |
| DQN-Equal | 83.18 | 133.75 | 18.41 | 0.0428 | 101.13 | 0.0506 |
| DDPG-Equal | 83.85 | 134.38 | 18.43 | 0.0421 | 101.55 | 0.0695 |
| PPO-Equal | 82.43 | 134.36 | 19.19 | 0.0498 | 97.03 | 0.0951 |
| ERWO-PPO | 83.40 | 134.37 | 18.94 | 0.0457 | 100.10 | 0.0956 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 82.43 | 134.36 | 19.19 | 0.0498 | 97.03 |
| ERWO-PPO | 83.40 | 134.37 | 18.94 | 0.0457 | 100.10 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 8.4741e-16 | 0.6217 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.6014 | 0.0193 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.1877 | 0.0685 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 6.2104e-09 | 0.9252 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 4.7265e-14 | 0.7580 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0145 | 0.1372 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.6826e-15 | 0.7931 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0016 | 0.1415 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.9512e-08 | 0.7510 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.6443e-05 | 0.2592 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.4991e-11 | 0.2981 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.6799 | 0.0138 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0023 | 0.1400 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.6934e-11 | 1.0058 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.4317e-09 | 0.3725 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7760e-17 | 3.7327 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.5829e-16 | 1.0623 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7760e-17 | 2.8337 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7760e-17 | 2.9869 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7760e-17 | 4.3260 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.02 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 164.61 s |
| Final PPO training time | 19.69 s |
| Average ERWO-PPO decision time per task | 0.0956 ms |
| Average PPO-Equal decision time per task | 0.0951 ms |
