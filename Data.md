### Table 10. Reward-weight configurations and corresponding validation performance

| Configuration     | $\alpha$ | $\beta$ | $\lambda$ | $\gamma$ | Latency (Score) | Energy (Efficiency) | Violation rate (%) | Load imbalance | QoS (Satisfaction) |
|:------------------|:--------:|:-------:|:---------:|:--------:|:---------------:|:-------------------:|:------------------:|:--------------:|:------------------:|
| Equal weights     |  0.2500  | 0.2500  |  0.2500   |  0.2500  |      55.59      |        89.43        |       19.27        |     0.0424     |       67.11        |
| Manual weights    |  0.4000  | 0.2000  |  0.3000   |  0.1000  |      54.95      |        89.44        |       20.17        |     0.0561     |       64.95        |
| Optimized ($w^*$) |  0.2546  | 0.1209  |  0.3251   |  0.2994  |      55.15      |        89.25        |       19.27        |     0.0450     |       66.24        |

---

### Table 11. Overall performance comparison

| Method           | Average latency (ms)* | Energy consumption* | Deadline violation (%) | Load imbalance | QoS satisfaction | Decision time (ms) |
|:-----------------|:---------------------:|:-------------------:|:----------------------:|:--------------:|:----------------:|:------------------:|
| Local-only       |         8.12          |        58.35        |         99.97          |     0.3271     |       0.01       |       0.0006       |
| Cloud-only       |         21.96         |        73.24        |         87.37          |     0.3217     |       2.40       |       0.0007       |
| Nearest-fog      |         28.48         |        90.01        |         81.60          |     0.3242     |       4.09       |       0.0048       |
| Least-loaded fog |         55.87         |        89.44        |         18.33          |     0.0381     |      68.47       |       0.0079       |
| DQN-Equal        |         55.97         |        89.24        |         18.00          |     0.0414     |      68.45       |       0.2454       |
| PPO-Equal        |         55.59         |        89.43        |         19.27          |     0.0424     |      67.11       |       0.4229       |
| PPO-Manual       |         54.95         |        89.44        |         20.17          |     0.0561     |      64.95       |       0.4541       |
| ERWO-PPO         |         55.15         |        89.25        |         19.27          |     0.0450     |      66.24       |       0.5372       |

*\*Catatan: Kolom Latensi dan Energi saat ini diisi menggunakan "Score/Efisiensi" dari output log. Jika jurnal meminta satuan raw asli (ms dan Joule/Watt), nilai ini dapat disesuaikan kembali dari raw CSV logging iFogSim2 nantinya.*

---

### Table 12. Ablation study of PPO reward configurations

| Configuration | Latency Score | Energy Efficiency | Violation rate (%) | Load imbalance | QoS Satisfaction |
|:--------------|:-------------:|:-----------------:|:------------------:|:--------------:|:----------------:|
| PPO-Equal     |     55.59     |       89.43       |       19.27        |     0.0424     |      67.11       |
| PPO-Manual    |     54.95     |       89.44       |       20.17        |     0.0561     |      64.95       |
| ERWO-PPO      |     55.15     |       89.25       |       19.27        |     0.0450     |      66.24       |

---

### Table 13. Statistical comparison of ERWO-PPO with PPO baselines

| Metric         | Comparison              |   Test   | Adjusted p-value | Effect size | Significant |
|:---------------|:------------------------|:--------:|:----------------:|:-----------:|:-----------:|
| Latency        | ERWO-PPO vs. PPO-Equal  | Wilcoxon |    3.7253e-09    |   0.4473    |     YES     |
| Energy         | ERWO-PPO vs. PPO-Equal  | Wilcoxon |      0.0208      |   0.3552    |     YES     |
| Violation rate | ERWO-PPO vs. PPO-Equal  | Wilcoxon |      0.8952      |   0.0000    |     NO      |
| Load imbalance | ERWO-PPO vs. PPO-Equal  | Wilcoxon |    6.9179e-06    |   1.1371    |     YES     |
| QoS            | ERWO-PPO vs. PPO-Equal  | Wilcoxon |      0.0020      |   0.2795    |     YES     |
| Latency        | ERWO-PPO vs. PPO-Manual | Wilcoxon |      0.0024      |   0.2037    |     YES     |
| QoS            | ERWO-PPO vs. PPO-Manual | Wilcoxon |    2.6885e-05    |   0.4216    |     YES     |

---

### Table 14. Computational overhead

| Component                                |   Time    |
|:-----------------------------------------|:---------:|
| Average PPO candidate-training time      |  4.13 s   |
| Average candidate-evaluation time        |  0.25 s   |
| Total NSGA-II search time                | 175.19 s  |
| Final PPO training time                  |  45.61 s  |
| Average ERWO-PPO decision time per task  | 0.5372 ms |
| Average PPO-Equal decision time per task | 0.4229 ms |
