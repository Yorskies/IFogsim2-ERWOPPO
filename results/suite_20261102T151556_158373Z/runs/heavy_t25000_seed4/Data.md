### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 82.11 | 134.36 | 20.43 | 0.0687 | 95.50 |
| Optimized ($w^*$) | 0.3593 | 0.3446 | 0.0689 | 0.2271 | 83.60 | 134.36 | 18.43 | 0.0444 | 100.98 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0011 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0026 |
| Q-Learning-Equal | 63.82 | 133.12 | 54.09 | 0.2621 | 50.90 | 0.0053 |
| DQN-Equal | 83.42 | 133.82 | 18.10 | 0.0415 | 102.04 | 0.0503 |
| DDPG-Equal | 42.30 | 134.40 | 82.05 | 0.3269 | 5.96 | 0.0696 |
| PPO-Equal | 82.11 | 134.36 | 20.43 | 0.0687 | 95.50 | 0.0966 |
| ERWO-PPO | 83.60 | 134.36 | 18.43 | 0.0444 | 100.98 | 0.0972 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 82.11 | 134.36 | 20.43 | 0.0687 | 95.50 |
| ERWO-PPO | 83.60 | 134.36 | 18.43 | 0.0444 | 100.98 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7205e-17 | 0.9304 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.9279 | 0.0061 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.8123e-15 | 0.5235 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7205e-17 | 2.4114 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7205e-17 | 1.1842 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0609 | 0.1196 | NO |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 4.1652e-14 | 0.7003 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0190 | 0.0924 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.1768e-09 | 0.8881 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.1780e-07 | 0.2734 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7205e-17 | 30.4938 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.9279 | 0.0509 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7205e-17 | 17.9051 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7205e-17 | 115.0450 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7205e-17 | 31.9305 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7205e-17 | 7.3483 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7205e-17 | 1.4561 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7205e-17 | 6.6427 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7205e-17 | 13.4421 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7205e-17 | 9.2191 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.01 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 164.09 s |
| Final PPO training time | 19.54 s |
| Average ERWO-PPO decision time per task | 0.0972 ms |
| Average PPO-Equal decision time per task | 0.0966 ms |
