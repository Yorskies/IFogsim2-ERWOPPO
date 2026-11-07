### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 84.13 | 134.30 | 18.06 | 0.0414 | 101.94 |
| Optimized ($w^*$) | 0.1608 | 0.2265 | 0.5239 | 0.0889 | 83.62 | 134.33 | 18.44 | 0.0430 | 100.87 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0010 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 77.36 | 131.42 | 26.38 | 0.0928 | 85.15 | 0.0052 |
| DQN-Equal | 84.11 | 134.43 | 17.79 | 0.0417 | 102.36 | 0.0513 |
| DDPG-Equal | 84.08 | 134.38 | 18.10 | 0.0403 | 102.41 | 0.0706 |
| PPO-Equal | 84.13 | 134.30 | 18.06 | 0.0414 | 101.94 | 0.0959 |
| ERWO-PPO | 83.62 | 134.33 | 18.44 | 0.0430 | 100.87 | 0.0957 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 84.13 | 134.30 | 18.06 | 0.0414 | 101.94 |
| ERWO-PPO | 83.62 | 134.33 | 18.44 | 0.0430 | 100.87 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.5475e-15 | 0.3509 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.4270 | 0.0372 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.0322 | 0.1051 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 4.8932e-07 | 0.6757 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 8.5936e-09 | 0.2823 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 8.8638e-14 | 0.3361 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0030 | 0.1430 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0868e-04 | 0.1848 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 2.3163e-04 | 0.4758 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.1620e-12 | 0.3942 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 6.2772e-11 | 0.3117 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.2469 | 0.0758 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0322 | 0.0943 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.1351e-14 | 1.2010 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.5895e-13 | 0.4065 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7248e-17 | 3.4795 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7248e-17 | 3.3702 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7248e-17 | 1.9368 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7248e-17 | 3.6919 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7248e-17 | 3.2479 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.07 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 166.42 s |
| Final PPO training time | 77.01 s |
| Average ERWO-PPO decision time per task | 0.0957 ms |
| Average PPO-Equal decision time per task | 0.0959 ms |
