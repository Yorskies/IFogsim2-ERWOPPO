### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 56.81 | 134.35 | 58.94 | 0.3057 | 33.10 |
| Optimized ($w^*$) | 0.3593 | 0.3446 | 0.0689 | 0.2271 | 67.10 | 134.32 | 41.31 | 0.1793 | 53.42 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0011 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0026 |
| Q-Learning-Equal | 63.78 | 133.08 | 54.14 | 0.2618 | 50.88 | 0.0055 |
| DQN-Equal | 83.43 | 134.33 | 18.95 | 0.0468 | 99.80 | 0.0545 |
| DDPG-Equal | 42.30 | 134.40 | 82.05 | 0.3269 | 5.96 | 0.0742 |
| PPO-Equal | 56.81 | 134.35 | 58.94 | 0.3057 | 33.10 | 0.1069 |
| ERWO-PPO | 67.10 | 134.32 | 41.31 | 0.1793 | 53.42 | 0.1053 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 56.81 | 134.35 | 58.94 | 0.3057 | 33.10 |
| ERWO-PPO | 67.10 | 134.32 | 41.31 | 0.1793 | 53.42 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7799e-17 | 2.4860 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0288 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7799e-17 | 2.2986 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7799e-17 | 2.6536 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.6145e-16 | 1.9254 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7799e-17 | 4.1475 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0152 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7799e-17 | 3.0876 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7799e-17 | 2.7878 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7799e-17 | 4.4599 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7799e-17 | 6.3673 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0945 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7799e-17 | 5.6763 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7799e-17 | 3.1434 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7799e-17 | 4.7712 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.1163e-05 | 0.7321 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.8185e-16 | 1.4285 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 4.6124e-15 | 1.5600 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 6.6225e-15 | 1.6646 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0000 | 0.2325 | NO |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.05 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 165.70 s |
| Final PPO training time | 4.03 s |
| Average ERWO-PPO decision time per task | 0.1053 ms |
| Average PPO-Equal decision time per task | 0.1069 ms |
