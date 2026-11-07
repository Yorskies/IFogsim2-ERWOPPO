### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 41.02 | 89.55 | 52.29 | 0.2800 | 27.60 |
| Optimized ($w^*$) | 0.2030 | 0.1319 | 0.3001 | 0.3650 | 46.64 | 89.60 | 35.90 | 0.1822 | 37.60 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0011 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 44.82 | 87.97 | 44.79 | 0.2085 | 39.78 | 0.0054 |
| DQN-Equal | 55.70 | 88.83 | 17.85 | 0.0447 | 67.66 | 0.0512 |
| DDPG-Equal | 28.57 | 89.62 | 80.99 | 0.3243 | 4.53 | 0.0692 |
| PPO-Equal | 41.02 | 89.55 | 52.29 | 0.2800 | 27.60 | 0.0955 |
| ERWO-PPO | 46.64 | 89.60 | 35.90 | 0.1822 | 37.60 | 0.0961 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 41.02 | 89.55 | 52.29 | 0.2800 | 27.60 |
| ERWO-PPO | 46.64 | 89.60 | 35.90 | 0.1822 | 37.60 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 4.8946e-15 | 1.9283 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.2537 | 0.0881 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 6.2830e-16 | 2.1669 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 4.8816e-16 | 2.6320 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 3.7663e-11 | 1.4150 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6204e-17 | 3.7185 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.1661e-16 | 1.0898 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6204e-17 | 2.6962 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6204e-17 | 4.3038 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6204e-17 | 4.6651 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6204e-17 | 7.5823 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.6450 | 0.0288 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6204e-17 | 6.7805 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6204e-17 | 4.4760 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.6204e-17 | 5.4075 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.4079e-04 | 0.5998 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6204e-17 | 2.2402 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 2.3897e-11 | 1.0690 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.4079e-04 | 0.6190 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 0.0469 | 0.3093 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.95 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 160.47 s |
| Final PPO training time | 4.04 s |
| Average ERWO-PPO decision time per task | 0.0961 ms |
| Average PPO-Equal decision time per task | 0.0955 ms |
