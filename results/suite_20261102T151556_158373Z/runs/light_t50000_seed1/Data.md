### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 27.94 | 44.80 | 17.88 | 0.0441 | 33.93 |
| Optimized ($w^*$) | 0.2951 | 0.1260 | 0.1922 | 0.3867 | 27.88 | 44.81 | 17.82 | 0.0464 | 33.77 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 25.09 | 43.82 | 30.10 | 0.1061 | 26.77 | 0.0053 |
| DQN-Equal | 27.08 | 44.79 | 19.70 | 0.0754 | 30.73 | 0.0522 |
| DDPG-Equal | 27.72 | 44.79 | 18.64 | 0.0533 | 32.82 | 0.0742 |
| PPO-Equal | 27.94 | 44.80 | 17.88 | 0.0441 | 33.93 | 0.0997 |
| ERWO-PPO | 27.88 | 44.81 | 17.82 | 0.0464 | 33.77 | 0.0976 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 27.94 | 44.80 | 17.88 | 0.0441 | 33.93 |
| ERWO-PPO | 27.88 | 44.81 | 17.82 | 0.0464 | 33.77 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0021 | 0.0722 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0070 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0102 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.2376e-05 | 0.4249 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0472 | 0.0764 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7931e-17 | 1.0839 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0295 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 6.3106e-10 | 0.3078 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7931e-17 | 2.0919 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7931e-17 | 1.4230 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 5.9695e-06 | 0.2269 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0423 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0070 | 0.1399 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.3010e-12 | 1.0906 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 9.1937e-12 | 0.4484 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.4954 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.1636 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0323e-16 | 1.7325 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 1.8142 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.4723 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.94 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 159.04 s |
| Final PPO training time | 40.18 s |
| Average ERWO-PPO decision time per task | 0.0976 ms |
| Average PPO-Equal decision time per task | 0.0997 ms |
