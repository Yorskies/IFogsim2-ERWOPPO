### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 14.65 | 44.80 | 78.80 | 0.3159 | 2.82 |
| Optimized ($w^*$) | 0.1803 | 0.2048 | 0.5471 | 0.0677 | 20.81 | 44.80 | 48.10 | 0.2420 | 14.23 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 14.87 | 45.07 | 77.94 | 0.3161 | 2.93 | 0.0011 |
| Least Fog | 28.06 | 44.80 | 17.44 | 0.0394 | 34.45 | 0.0025 |
| Q-Learning-Equal | 24.31 | 43.72 | 34.80 | 0.1158 | 24.44 | 0.0053 |
| DQN-Equal | 27.90 | 44.67 | 17.52 | 0.0449 | 33.88 | 0.0518 |
| DDPG-Equal | 21.73 | 43.60 | 44.00 | 0.1820 | 18.95 | 0.0695 |
| PPO-Equal | 14.65 | 44.80 | 78.80 | 0.3159 | 2.82 | 0.0977 |
| ERWO-PPO | 20.81 | 44.80 | 48.10 | 0.2420 | 14.23 | 0.0968 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 14.65 | 44.80 | 78.80 | 0.3159 | 2.82 |
| ERWO-PPO | 20.81 | 44.80 | 48.10 | 0.2420 | 14.23 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.4767e-17 | 4.9164 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.7727 | 0.0092 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.4767e-17 | 3.6631 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.4767e-17 | 1.8149 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.4767e-17 | 4.0843 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.4767e-17 | 5.4901 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.3301e-04 | 0.2928 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.4767e-17 | 3.7256 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.4767e-17 | 4.8297 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.4767e-17 | 6.3870 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.1426e-06 | 0.6718 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.4767e-17 | 2.3520 | YES |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 8.0181e-05 | 0.4724 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 8.1873e-12 | 1.2104 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.5702e-14 | 1.5661 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.5674e-16 | 2.2315 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4767e-17 | 2.0808 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 2.8724e-14 | 1.4193 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 2.3026e-16 | 2.5585 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4767e-17 | 2.8061 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.92 s |
| Average candidate-evaluation time | 0.03 s |
| Total NSGA-II search time | 158.16 s |
| Final PPO training time | 3.76 s |
| Average ERWO-PPO decision time per task | 0.0968 ms |
| Average PPO-Equal decision time per task | 0.0977 ms |
