### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 27.29 | 44.58 | 19.78 | 0.0555 | 32.01 |
| Optimized ($w^*$) | 0.3101 | 0.1898 | 0.0245 | 0.4756 | 27.81 | 44.79 | 18.06 | 0.0459 | 33.60 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 24.54 | 43.63 | 34.02 | 0.0999 | 24.79 | 0.0053 |
| DQN-Equal | 27.51 | 43.89 | 17.82 | 0.0435 | 33.97 | 0.0508 |
| DDPG-Equal | 27.66 | 44.80 | 18.72 | 0.0489 | 32.96 | 0.0697 |
| PPO-Equal | 27.29 | 44.58 | 19.78 | 0.0555 | 32.01 | 0.0982 |
| ERWO-PPO | 27.81 | 44.79 | 18.06 | 0.0459 | 33.60 | 0.0982 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 27.29 | 44.58 | 19.78 | 0.0555 | 32.01 |
| ERWO-PPO | 27.81 | 44.79 | 18.06 | 0.0459 | 33.60 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.4463e-17 | 0.6654 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.5913e-11 | 0.4603 | YES |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 5.6714e-08 | 0.2954 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 9.8277e-16 | 1.3199 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.4211e-15 | 0.7614 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 9.5708e-09 | 0.4168 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.4463e-17 | 1.9793 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.5888 | 0.0416 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 2.9254e-05 | 0.4368 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.6415e-04 | 0.1820 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 5.2781e-06 | 0.1918 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.5888 | 0.0314 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0092 | 0.1114 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7256e-07 | 0.6367 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 5.1965e-09 | 0.3046 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4463e-17 | 2.8156 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4463e-17 | 2.3494 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4463e-17 | 2.2030 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4463e-17 | 1.7734 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4463e-17 | 2.8207 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.05 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 163.16 s |
| Final PPO training time | 20.96 s |
| Average ERWO-PPO decision time per task | 0.0982 ms |
| Average PPO-Equal decision time per task | 0.0982 ms |
