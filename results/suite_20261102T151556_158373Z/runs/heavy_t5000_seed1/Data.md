### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 42.30 | 134.40 | 82.05 | 0.3269 | 5.96 |
| Optimized ($w^*$) | 0.2997 | 0.1145 | 0.1952 | 0.3905 | 56.24 | 134.35 | 59.31 | 0.3027 | 25.14 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0011 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 73.30 | 133.53 | 35.27 | 0.1205 | 69.54 | 0.0053 |
| DQN-Equal | 83.79 | 134.29 | 18.25 | 0.0443 | 100.99 | 0.0512 |
| DDPG-Equal | 57.66 | 134.33 | 57.02 | 0.2973 | 30.17 | 0.0699 |
| PPO-Equal | 42.30 | 134.40 | 82.05 | 0.3269 | 5.96 | 0.0981 |
| ERWO-PPO | 56.24 | 134.35 | 59.31 | 0.3027 | 25.14 | 0.0976 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 42.30 | 134.40 | 82.05 | 0.3269 | 5.96 |
| ERWO-PPO | 56.24 | 134.35 | 59.31 | 0.3027 | 25.14 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7235e-17 | 7.5664 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.4668 | 0.0625 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7235e-17 | 5.2734 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 3.2934e-15 | 1.8932 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7235e-17 | 5.8210 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7235e-17 | 13.9510 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.4668 | 0.0734 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7235e-17 | 9.2562 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7235e-17 | 19.1167 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7235e-17 | 17.5429 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.2719e-06 | 0.5630 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.7701 | 0.0197 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 8.8202e-05 | 0.4407 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.0675 | 0.3029 | NO |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 5.2005e-11 | 1.0323 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7235e-17 | 5.7454 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.3623e-15 | 0.9493 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7235e-17 | 3.8247 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7235e-17 | 6.4908 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7235e-17 | 6.1332 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.02 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 164.61 s |
| Final PPO training time | 4.01 s |
| Average ERWO-PPO decision time per task | 0.0976 ms |
| Average PPO-Equal decision time per task | 0.0981 ms |
