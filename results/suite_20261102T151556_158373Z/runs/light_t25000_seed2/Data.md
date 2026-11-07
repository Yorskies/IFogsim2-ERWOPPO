### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 27.62 | 44.79 | 19.12 | 0.0535 | 32.74 |
| Optimized ($w^*$) | 0.1803 | 0.2048 | 0.5471 | 0.0677 | 27.27 | 44.79 | 20.24 | 0.0604 | 31.52 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 24.24 | 43.71 | 35.06 | 0.1171 | 24.29 | 0.0054 |
| DQN-Equal | 27.23 | 44.05 | 18.36 | 0.0418 | 33.64 | 0.0517 |
| DDPG-Equal | 24.24 | 44.80 | 32.48 | 0.1692 | 22.79 | 0.0708 |
| PPO-Equal | 27.62 | 44.79 | 19.12 | 0.0535 | 32.74 | 0.0978 |
| ERWO-PPO | 27.27 | 44.79 | 20.24 | 0.0604 | 31.52 | 0.0969 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 27.62 | 44.79 | 19.12 | 0.0535 | 32.74 |
| ERWO-PPO | 27.27 | 44.79 | 20.24 | 0.0604 | 31.52 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 5.7136e-16 | 0.4195 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0073 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 6.8141e-04 | 0.1775 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.2307e-09 | 0.7644 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.4039e-13 | 0.5211 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0429 | NO |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.4035e-17 | 1.5954 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.4034e-07 | 0.3082 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.4035e-17 | 2.4888 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 5.7136e-16 | 0.9449 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4035e-17 | 3.7794 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0243 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 8.0672e-17 | 1.8771 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4035e-17 | 3.1161 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4035e-17 | 3.9756 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 2.3927 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 2.0596 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.3926e-17 | 1.8981 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 8.0672e-17 | 1.9128 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4035e-17 | 2.3618 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.03 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 162.28 s |
| Final PPO training time | 19.74 s |
| Average ERWO-PPO decision time per task | 0.0969 ms |
| Average PPO-Equal decision time per task | 0.0978 ms |
