### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 55.05 | 89.58 | 19.12 | 0.0545 | 64.84 |
| Optimized ($w^*$) | 0.0585 | 0.3547 | 0.2504 | 0.3364 | 55.16 | 89.59 | 18.76 | 0.0551 | 65.27 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0010 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 49.32 | 88.50 | 32.10 | 0.1238 | 49.92 | 0.0053 |
| DQN-Equal | 55.75 | 89.30 | 17.49 | 0.0413 | 68.30 | 0.0507 |
| DDPG-Equal | 55.27 | 89.61 | 19.09 | 0.0472 | 65.54 | 0.0693 |
| PPO-Equal | 55.05 | 89.58 | 19.12 | 0.0545 | 64.84 | 0.0962 |
| ERWO-PPO | 55.16 | 89.59 | 18.76 | 0.0551 | 65.27 | 0.0963 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 55.05 | 89.58 | 19.12 | 0.0545 | 64.84 |
| ERWO-PPO | 55.16 | 89.59 | 18.76 | 0.0551 | 65.27 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.3625 | 0.0847 | NO |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0013 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.3625 | 0.0752 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0606 | NO |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.3625 | 0.1170 | NO |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.6752e-09 | 0.4620 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 6.7324e-07 | 0.4477 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 5.0863e-09 | 0.2774 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6342e-17 | 1.7547 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6342e-17 | 0.9137 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0888 | NO |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0478 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.4561 | 0.0683 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.7791e-09 | 0.9914 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0775 | NO |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6342e-17 | 3.2765 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6342e-17 | 1.6233 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6342e-17 | 2.4000 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6342e-17 | 2.7544 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.6342e-17 | 3.4232 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.92 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 159.39 s |
| Final PPO training time | 19.74 s |
| Average ERWO-PPO decision time per task | 0.0963 ms |
| Average PPO-Equal decision time per task | 0.0962 ms |
