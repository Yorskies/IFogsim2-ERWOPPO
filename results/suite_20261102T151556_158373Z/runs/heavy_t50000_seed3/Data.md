### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Equal weights | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 83.92 | 134.38 | 18.25 | 0.0409 | 101.97 |
| Optimized ($w^*$) | 0.1608 | 0.2265 | 0.5239 | 0.0889 | 83.10 | 134.38 | 18.97 | 0.0493 | 98.94 |

---

### Table 11. Overall performance comparison

| Method | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Nearest Fog | 42.91 | 135.20 | 81.22 | 0.3270 | 6.21 | 0.0010 |
| Least Fog | 84.34 | 134.40 | 17.75 | 0.0374 | 103.50 | 0.0025 |
| Q-Learning-Equal | 70.88 | 130.78 | 36.52 | 0.1903 | 68.78 | 0.0053 |
| DQN-Equal | 84.02 | 134.17 | 18.00 | 0.0423 | 101.39 | 0.0509 |
| DDPG-Equal | 83.86 | 134.38 | 18.43 | 0.0422 | 101.65 | 0.0702 |
| PPO-Equal | 83.92 | 134.38 | 18.25 | 0.0409 | 101.97 | 0.0964 |
| ERWO-PPO | 83.10 | 134.38 | 18.97 | 0.0493 | 98.94 | 0.0971 |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| PPO-Equal | 83.92 | 134.38 | 18.25 | 0.0409 | 101.97 |
| ERWO-PPO | 83.10 | 134.38 | 18.97 | 0.0493 | 98.94 |

---

### Table 13. Statistical comparison of ERWO-PPO with equal-weight RL baselines

| Metric | Comparison | Test | Adjusted p-value | Effect size | Significant |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Latency | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.0615e-14 | 0.5662 | YES |
| Energy | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.0000 | 0.0024 | NO |
| Violation rate | ERWO-PPO vs. PPO-Equal | Wilcoxon | 2.7004e-07 | 0.1944 | YES |
| Load imbalance | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.9225e-16 | 1.6244 | YES |
| QoS | ERWO-PPO vs. PPO-Equal | Wilcoxon | 1.7228e-16 | 0.7742 | YES |
| Latency | ERWO-PPO vs. DQN-Equal | Wilcoxon | 8.7314e-14 | 0.6313 | YES |
| Energy | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.8555e-05 | 0.2872 | YES |
| Violation rate | ERWO-PPO vs. DQN-Equal | Wilcoxon | 1.3655e-06 | 0.2684 | YES |
| Load imbalance | ERWO-PPO vs. DQN-Equal | Wilcoxon | 3.1193e-13 | 1.3059 | YES |
| QoS | ERWO-PPO vs. DQN-Equal | Wilcoxon | 8.3004e-12 | 0.6326 | YES |
| Latency | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.0826e-14 | 0.5163 | YES |
| Energy | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.0000 | 0.0010 | NO |
| Violation rate | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 1.8007e-04 | 0.1484 | YES |
| Load imbalance | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 3.4917e-15 | 1.3363 | YES |
| QoS | ERWO-PPO vs. DDPG-Equal | Wilcoxon | 6.1970e-15 | 0.7019 | YES |
| Latency | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7563e-17 | 4.2338 | YES |
| Energy | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7563e-17 | 3.9348 | YES |
| Violation rate | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7563e-17 | 3.2809 | YES |
| Load imbalance | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7563e-17 | 4.8418 | YES |
| QoS | ERWO-PPO vs. Q-Learning-Equal | Wilcoxon | 7.7563e-17 | 4.6529 | YES |

---

### Table 14. Computational overhead

| Component | Time |
| :--- | :---: |
| Average PPO candidate-training time | 4.01 s |
| Average candidate-evaluation time | 0.09 s |
| Total NSGA-II search time | 164.33 s |
| Final PPO training time | 38.20 s |
| Average ERWO-PPO decision time per task | 0.0971 ms |
| Average PPO-Equal decision time per task | 0.0964 ms |
