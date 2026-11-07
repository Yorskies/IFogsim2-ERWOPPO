### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 42.30 | 134.39 | 82.03 | 0.3269 | 5.96 |
| Optimized ($w^*$) | 0.1832 | 0.3323 | 0.3487 | 0.1359 | 62.85 | 134.40 | 48.51 | 0.2518 | 43.15 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0011 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 66.18 | 129.61 | 46.38 | 0.2173 | 56.80 | 0.0053 |
| DQN-Equal | 83.83 | 134.26 | 18.14 | 0.0421 | 101.66 | 0.0503 |
| DDPG-Equal | 68.58 | 134.35 | 38.67 | 0.2038 | 50.60 | 0.0683 |
| PPO-Equal | 42.30 | 134.39 | 82.03 | 0.3269 | 5.96 | 0.0959 |
| ERWO-PPO | 62.85 | 134.40 | 48.51 | 0.2518 | 43.15 | 0.0949 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 42.30 | 134.39 | 82.03 | 0.3269 | 5.96 |
| ERWO-PPO | 62.85 | 134.40 | 48.51 | 0.2518 | 43.15 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7602e-17 | 6.0433 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.9964 | 0.0039 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7602e-17 | 5.4256 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7602e-17 | 2.6530 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7602e-17 | 5.2569 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7602e-17 | 6.0596 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 0.0405 | 0.1875 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7602e-17 | 4.8387 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7602e-17 | 7.3597 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 7.7602e-17 | 7.7144 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.8152e-15 | 1.4844 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.9964 | 0.0610 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0562e-14 | 1.4324 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 2.5196e-10 | 1.0578 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.9752e-06 | 0.8666 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 2.6783e-06 | 0.7874 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7602e-17 | 4.0267 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 0.6930 | 0.2784 | NO |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 2.7436e-07 | 0.8904 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 1.0148e-14 | 1.5403 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.02 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 164.29 s |
| Final PPO training time | 3.80 s |
| Average ERWO-PPO decision time per task | 0.0949 ms |
| Average PPO-Equal decision time per task | 0.0959 ms |
