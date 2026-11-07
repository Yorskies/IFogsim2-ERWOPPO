### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 83.36 | 134.30 | 19.08 | 0.0464 | 99.75 |
| Optimized ($w^*$) | 0.2997 | 0.1145 | 0.1952 | 0.3905 | 83.97 | 134.38 | 18.11 | 0.0407 | 102.20 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0010 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 74.45 | 133.35 | 32.95 | 0.1346 | 74.45 | 0.0053 |
| DQN-Equal | 83.52 | 134.38 | 18.19 | 0.0448 | 100.56 | 0.0500 |
| DDPG-Equal | 81.11 | 134.35 | 20.98 | 0.0678 | 92.19 | 0.0684 |
| PPO-Equal | 83.36 | 134.30 | 19.08 | 0.0464 | 99.75 | 0.0957 |
| ERWO-PPO | 83.97 | 134.38 | 18.11 | 0.0407 | 102.20 | 0.0956 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 83.36 | 134.30 | 19.08 | 0.0464 | 99.75 |
| ERWO-PPO | 83.97 | 134.38 | 18.11 | 0.0407 | 102.20 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.5349e-14 | 0.4035 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 0.1618 | 0.1132 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.6236e-10 | 0.2608 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.9517e-16 | 1.3502 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 7.7827e-16 | 0.6125 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 6.4333e-14 | 0.3056 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0080 | NO |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.0000 | 0.0239 | NO |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.7829e-14 | 1.3866 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 8.2662e-14 | 0.4326 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7655e-17 | 1.8093 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 0.4759 | 0.0477 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.3536e-16 | 0.7374 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7655e-17 | 2.4125 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 7.7655e-17 | 2.2321 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7655e-17 | 3.8144 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 3.3536e-16 | 1.2137 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7655e-17 | 2.6944 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7655e-17 | 3.5520 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7655e-17 | 4.5086 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 3.96 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 161.92 s |
| Final PPO training time | 39.20 s |
| Average ERWO-PPO decision time per task | 0.0956 ms |
| Average PPO-Equal decision time per task | 0.0957 ms |
