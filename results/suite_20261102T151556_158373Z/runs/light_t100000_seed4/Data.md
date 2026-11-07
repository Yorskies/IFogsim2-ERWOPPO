### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 27.53 | 44.52 | 18.70 | 0.0446 | 33.54 |
| Optimized ($w^*$) | 0.2110 | 0.1298 | 0.2834 | 0.3758 | 28.00 | 44.67 | 17.78 | 0.0425 | 34.12 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 25.11 | 44.13 | 30.22 | 0.1230 | 26.33 | 0.0053 |
| DQN-Equal | 27.37 | 43.81 | 18.32 | 0.0467 | 33.63 | 0.0514 |
| DDPG-Equal | 27.01 | 44.80 | 21.06 | 0.0821 | 30.55 | 0.0695 |
| PPO-Equal | 27.53 | 44.52 | 18.70 | 0.0446 | 33.54 | 0.0967 |
| ERWO-PPO | 28.00 | 44.67 | 17.78 | 0.0425 | 34.12 | 0.0961 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 27.53 | 44.52 | 18.70 | 0.0446 | 33.54 |
| ERWO-PPO | 28.00 | 44.67 | 17.78 | 0.0425 | 34.12 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 3.0401e-15 | 0.5546 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.2092e-05 | 0.3113 | YES |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0021 | 0.1518 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0151 | 0.4151 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 3.2396e-07 | 0.2712 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0902e-16 | 0.8526 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0902e-16 | 1.7390 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0067 | 0.0928 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.1694e-11 | 0.8218 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.4398e-07 | 0.2348 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7931e-17 | 1.3302 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.3533e-08 | 0.3179 | YES |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.3028e-13 | 0.5563 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7931e-17 | 2.3042 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7931e-17 | 1.7473 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.4228 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 3.6746e-15 | 1.1037 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0902e-16 | 1.7612 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.3354 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7931e-17 | 2.7996 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.01 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 161.64 s |
| Final PPO training time | 78.27 s |
| Average ERWO-PPO decision time per task | 0.0961 ms |
| Average PPO-Equal decision time per task | 0.0967 ms |
