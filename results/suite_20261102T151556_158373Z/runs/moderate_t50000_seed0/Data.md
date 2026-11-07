### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 55.91 | 89.59 | 18.09 | 0.0423 | 67.77 |
| Optimized ($w^*$) | 0.2279 | 0.0986 | 0.3313 | 0.3422 | 55.67 | 89.58 | 18.32 | 0.0453 | 67.07 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 28.92 | 90.14 | 80.39 | 0.3243 | 4.60 | 0.0011 |
| Least Fog | 56.23 | 89.60 | 17.34 | 0.0378 | 69.13 | 0.0025 |
| Q-Learning-Equal | 48.91 | 85.96 | 34.85 | 0.0692 | 51.46 | 0.0053 |
| DQN-Equal | 55.84 | 89.58 | 17.96 | 0.0457 | 67.22 | 0.0510 |
| DDPG-Equal | 55.81 | 89.62 | 18.15 | 0.0444 | 67.39 | 0.0696 |
| PPO-Equal | 55.91 | 89.59 | 18.09 | 0.0423 | 67.77 | 0.0975 |
| ERWO-PPO | 55.67 | 89.58 | 18.32 | 0.0453 | 67.07 | 0.0974 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 55.91 | 89.59 | 18.09 | 0.0423 | 67.77 |
| ERWO-PPO | 55.67 | 89.58 | 18.32 | 0.0453 | 67.07 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.5729e-05 | 0.2041 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0244 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.7558 | 0.0503 | NO |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.2775e-06 | 0.7901 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 3.0496e-04 | 0.2197 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0093 | 0.1445 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0027 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.4409 | 0.0801 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0996 | NO |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0488 | NO |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.2975 | 0.1174 | NO |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0685 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0368 | NO |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.3110 | 0.2074 | NO |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0989 | NO |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4295e-17 | 4.0656 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4295e-17 | 4.2809 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4295e-17 | 3.2729 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.3586e-15 | 1.4240 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.4295e-17 | 3.9612 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.99 s |
| Average candidate-evaluation time | 0.06 s |
| Total NSGA-II search time | 161.90 s |
| Final PPO training time | 39.14 s |
| Average ERWO-PPO decision time per task | 0.0974 ms |
| Average PPO-Equal decision time per task | 0.0975 ms |
