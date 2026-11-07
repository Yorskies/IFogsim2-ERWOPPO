### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 20.89 | 44.80 | 49.18 | 0.2723 | 14.21 |
| Optimized ($w^*$) | 0.3101 | 0.1898 | 0.0245 | 0.4756 | 24.04 | 44.78 | 31.18 | 0.1475 | 21.31 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 24.54 | 43.62 | 33.98 | 0.0999 | 24.81 | 0.0054 |
| DQN-Equal | 27.82 | 44.74 | 18.18 | 0.0472 | 33.37 | 0.0503 |
| DDPG-Equal | 24.18 | 44.78 | 33.48 | 0.1577 | 21.87 | 0.0695 |
| PPO-Equal | 20.89 | 44.80 | 49.18 | 0.2723 | 14.21 | 0.0963 |
| ERWO-PPO | 24.04 | 44.78 | 31.18 | 0.1475 | 21.31 | 0.0965 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 20.89 | 44.80 | 49.18 | 0.2723 | 14.21 |
| ERWO-PPO | 24.04 | 44.78 | 31.18 | 0.1475 | 21.31 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.6082e-15 | 2.2026 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.6247 | 0.0480 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 5.5315e-16 | 2.0154 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7931e-17 | 3.6731 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 4.0488e-15 | 2.1943 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7931e-17 | 4.3260 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0076 | 0.0945 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.8970e-17 | 1.9835 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7931e-17 | 3.2587 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7931e-17 | 4.8684 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.6247 | 0.1497 | NO |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.9534 | 0.0006 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0040 | 0.3327 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0381 | 0.2628 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.4518 | 0.2235 | NO |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 0.0017 | 0.4037 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.3422 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 0.0291 | 0.3541 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 2.1679e-10 | 1.1088 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.5668e-09 | 1.0266 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.99 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 160.74 s |
| Final PPO training time | 4.06 s |
| Average ERWO-PPO decision time per task | 0.0965 ms |
| Average PPO-Equal decision time per task | 0.0963 ms |
