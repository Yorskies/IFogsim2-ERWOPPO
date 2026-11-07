# Data akhir eksperimen ERWO-PPO

Status: complete; selesai 80/80 percobaan.

Konfigurasi: kandidat 5000 timestep; populasi 10; generasi 4; evaluasi 100 episode; device cpu.
Seed training: [0, 1, 2, 3, 4]. Workload: ['light', 'moderate', 'heavy', 'dynamic'].

Setiap kombinasi dilatih ulang dari awal, termasuk pencarian bobot NSGA-II. Anggaran timestep adalah nilai yang diminta; PPO dapat membulatkan ke ukuran rollout.

Nilai tabel adalah rata-rata ± standar deviasi sampel antar-seed training, setelah setiap run dirata-ratakan atas episode evaluasi. N/A berarti baru ada satu seed. Hasil parsial tidak mewakili seluruh matriks.

Latensi, energi, deadline, dan QoS adalah jumlah sub-reward per episode, bukan ms, Joule, atau persentase. Jangan membandingkan jumlah skor lintas workload dengan panjang episode berbeda. Violation menggunakan persen; decision time menggunakan ms.

Seed validasi kandidat: 42..44; seed benchmark: 1000..1099, sama untuk semua metode. Socket Java wajib; fallback Python dinonaktifkan. P-value per-run tersedia di log; tidak dirata-ratakan atau digabung menjadi klaim signifikansi antar-seed.

## light — 5,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 14.87 ± 0.00 | 45.07 ± 0.00 | 77.94 ± 0.00 | 0.3161 ± 0.0000 | 2.93 ± 0.00 | 0.0011 ± 0.0000 |
| Least Fog | 28.06 ± 0.00 | 44.80 ± 0.00 | 17.44 ± 0.00 | 0.0394 ± 0.0000 | 34.45 ± 0.00 | 0.0025 ± 0.0001 |
| Q-Learning-Equal | 24.98 ± 0.63 | 43.80 ± 0.19 | 30.77 ± 3.95 | 0.1023 ± 0.0123 | 26.20 ± 2.00 | 0.0054 ± 0.0002 |
| DQN-Equal | 27.86 ± 0.10 | 44.72 ± 0.04 | 17.86 ± 0.45 | 0.0459 ± 0.0023 | 33.69 ± 0.34 | 0.0519 ± 0.0022 |
| DDPG-Equal | 22.17 ± 4.68 | 44.22 ± 0.72 | 42.99 ± 21.83 | 0.1833 ± 0.0892 | 18.96 ± 10.33 | 0.0706 ± 0.0019 |
| PPO-Equal | 16.80 ± 2.78 | 44.80 ± 0.00 | 68.97 ± 13.13 | 0.3033 ± 0.0190 | 7.03 ± 5.29 | 0.1005 ± 0.0048 |
| ERWO-PPO | 22.19 ± 2.07 | 44.79 ± 0.01 | 41.36 ± 10.77 | 0.2103 ± 0.0613 | 17.12 ± 5.10 | 0.0977 ± 0.0018 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2399 ± 0.0586; beta_energy: 0.1856 ± 0.0623; lambda_deadline: 0.2551 ± 0.1897; gamma_qos: 0.3194 ± 0.1551.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 3.92 ± 0.04 |
| avg_cand_eval | 0.03 ± 0.00 |
| total_search_time | 157.98 ± 1.71 |
| final_ppo_train_time | 3.96 ± 0.12 |

## moderate — 5,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 28.92 ± 0.00 | 90.14 ± 0.00 | 80.39 ± 0.00 | 0.3243 ± 0.0000 | 4.60 ± 0.00 | 0.0011 ± 0.0001 |
| Least Fog | 56.23 ± 0.00 | 89.60 ± 0.00 | 17.34 ± 0.00 | 0.0378 ± 0.0000 | 69.13 ± 0.00 | 0.0025 ± 0.0000 |
| Q-Learning-Equal | 49.12 ± 2.95 | 87.68 ± 0.84 | 33.06 ± 8.15 | 0.1183 ± 0.0575 | 50.77 ± 8.69 | 0.0054 ± 0.0001 |
| DQN-Equal | 55.90 ± 0.23 | 89.35 ± 0.30 | 17.67 ± 0.22 | 0.0425 ± 0.0017 | 68.02 ± 0.39 | 0.0508 ± 0.0007 |
| DDPG-Equal | 37.21 ± 11.73 | 89.61 ± 0.01 | 60.12 ± 28.20 | 0.2493 ± 0.1110 | 21.88 ± 24.40 | 0.0695 ± 0.0008 |
| PPO-Equal | 35.87 ± 5.34 | 89.58 ± 0.04 | 64.26 ± 12.71 | 0.3024 ± 0.0187 | 18.14 ± 9.55 | 0.0980 ± 0.0035 |
| ERWO-PPO | 42.18 ± 4.78 | 89.59 ± 0.02 | 48.05 ± 11.05 | 0.2449 ± 0.0712 | 29.48 ± 10.56 | 0.0964 ± 0.0010 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2225 ± 0.1042; beta_energy: 0.1922 ± 0.1114; lambda_deadline: 0.2579 ± 0.0575; gamma_qos: 0.3275 ± 0.0726.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 3.95 ± 0.05 |
| avg_cand_eval | 0.06 ± 0.00 |
| total_search_time | 160.42 ± 2.16 |
| final_ppo_train_time | 4.06 ± 0.17 |

## heavy — 5,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 42.91 ± 0.00 | 135.20 ± 0.00 | 81.22 ± 0.00 | 0.3270 ± 0.0000 | 6.21 ± 0.00 | 0.0011 ± 0.0000 |
| Least Fog | 84.34 ± 0.00 | 134.40 ± 0.00 | 17.75 ± 0.00 | 0.0374 ± 0.0000 | 103.50 ± 0.00 | 0.0025 ± 0.0001 |
| Q-Learning-Equal | 70.19 ± 5.27 | 131.76 ± 1.62 | 40.13 ± 10.14 | 0.1767 ± 0.0691 | 66.05 ± 12.91 | 0.0054 ± 0.0001 |
| DQN-Equal | 83.85 ± 0.28 | 134.23 ± 0.10 | 18.23 ± 0.46 | 0.0431 ± 0.0025 | 101.40 ± 1.04 | 0.0513 ± 0.0019 |
| DDPG-Equal | 50.64 ± 12.03 | 134.38 ± 0.04 | 68.34 ± 19.80 | 0.2964 ± 0.0533 | 19.75 ± 20.17 | 0.0701 ± 0.0024 |
| PPO-Equal | 47.41 ± 7.07 | 134.39 ± 0.03 | 73.64 ± 11.55 | 0.3204 ± 0.0096 | 14.47 ± 12.34 | 0.0983 ± 0.0050 |
| ERWO-PPO | 60.59 ± 10.91 | 134.37 ± 0.04 | 52.32 ± 17.85 | 0.2471 ± 0.0687 | 39.86 ± 22.87 | 0.0977 ± 0.0044 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2367 ± 0.0878; beta_energy: 0.2445 ± 0.0956; lambda_deadline: 0.3368 ± 0.2069; gamma_qos: 0.1820 ± 0.1317.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 3.94 ± 0.13 |
| avg_cand_eval | 0.09 ± 0.00 |
| total_search_time | 161.44 ± 5.02 |
| final_ppo_train_time | 3.97 ± 0.10 |

## dynamic — 5,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 28.92 ± 0.00 | 90.14 ± 0.00 | 80.39 ± 0.00 | 0.3243 ± 0.0000 | 4.60 ± 0.00 | 0.0011 ± 0.0000 |
| Least Fog | 56.23 ± 0.00 | 89.60 ± 0.00 | 17.34 ± 0.00 | 0.0378 ± 0.0000 | 69.13 ± 0.00 | 0.0025 ± 0.0001 |
| Q-Learning-Equal | 49.12 ± 2.95 | 87.68 ± 0.84 | 33.06 ± 8.15 | 0.1183 ± 0.0575 | 50.77 ± 8.69 | 0.0053 ± 0.0001 |
| DQN-Equal | 55.90 ± 0.23 | 89.35 ± 0.30 | 17.67 ± 0.22 | 0.0425 ± 0.0017 | 68.02 ± 0.39 | 0.0512 ± 0.0018 |
| DDPG-Equal | 37.21 ± 11.73 | 89.61 ± 0.01 | 60.12 ± 28.20 | 0.2493 ± 0.1110 | 21.88 ± 24.40 | 0.0700 ± 0.0011 |
| PPO-Equal | 35.87 ± 5.34 | 89.58 ± 0.04 | 64.26 ± 12.71 | 0.3024 ± 0.0187 | 18.14 ± 9.55 | 0.0986 ± 0.0048 |
| ERWO-PPO | 42.18 ± 4.78 | 89.59 ± 0.02 | 48.05 ± 11.05 | 0.2449 ± 0.0712 | 29.48 ± 10.56 | 0.0984 ± 0.0051 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2225 ± 0.1042; beta_energy: 0.1922 ± 0.1114; lambda_deadline: 0.2579 ± 0.0575; gamma_qos: 0.3275 ± 0.0726.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 3.94 ± 0.03 |
| avg_cand_eval | 0.06 ± 0.00 |
| total_search_time | 159.95 ± 1.38 |
| final_ppo_train_time | 3.96 ± 0.07 |

## light — 25,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 14.87 ± 0.00 | 45.07 ± 0.00 | 77.94 ± 0.00 | 0.3161 ± 0.0000 | 2.93 ± 0.00 | 0.0011 ± 0.0000 |
| Least Fog | 28.06 ± 0.00 | 44.80 ± 0.00 | 17.44 ± 0.00 | 0.0394 ± 0.0000 | 34.45 ± 0.00 | 0.0025 ± 0.0000 |
| Q-Learning-Equal | 24.97 ± 0.65 | 43.80 ± 0.19 | 30.86 ± 4.00 | 0.1028 ± 0.0127 | 26.16 ± 2.03 | 0.0053 ± 0.0000 |
| DQN-Equal | 27.55 ± 0.26 | 44.40 ± 0.40 | 18.28 ± 0.39 | 0.0488 ± 0.0061 | 33.31 ± 0.60 | 0.0513 ± 0.0003 |
| DDPG-Equal | 24.39 ± 5.65 | 44.79 ± 0.02 | 33.52 ± 26.00 | 0.1274 ± 0.1173 | 24.94 ± 13.14 | 0.0703 ± 0.0005 |
| PPO-Equal | 27.57 ± 0.18 | 44.75 ± 0.09 | 19.12 ± 0.51 | 0.0532 ± 0.0026 | 32.69 ± 0.48 | 0.0978 ± 0.0006 |
| ERWO-PPO | 27.58 ± 0.27 | 44.79 ± 0.00 | 19.04 ± 0.88 | 0.0526 ± 0.0067 | 32.71 ± 0.96 | 0.0970 ± 0.0008 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2399 ± 0.0586; beta_energy: 0.1856 ± 0.0623; lambda_deadline: 0.2551 ± 0.1897; gamma_qos: 0.3194 ± 0.1551.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 3.99 ± 0.05 |
| avg_cand_eval | 0.03 ± 0.00 |
| total_search_time | 161.07 ± 2.06 |
| final_ppo_train_time | 19.94 ± 0.58 |

## moderate — 25,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 28.92 ± 0.00 | 90.14 ± 0.00 | 80.39 ± 0.00 | 0.3243 ± 0.0000 | 4.60 ± 0.00 | 0.0011 ± 0.0000 |
| Least Fog | 56.23 ± 0.00 | 89.60 ± 0.00 | 17.34 ± 0.00 | 0.0378 ± 0.0000 | 69.13 ± 0.00 | 0.0025 ± 0.0000 |
| Q-Learning-Equal | 49.15 ± 2.92 | 87.73 ± 0.86 | 32.96 ± 8.09 | 0.1184 ± 0.0571 | 50.81 ± 8.63 | 0.0053 ± 0.0001 |
| DQN-Equal | 55.33 ± 0.56 | 89.36 ± 0.15 | 17.86 ± 0.33 | 0.0497 ± 0.0076 | 66.71 ± 1.37 | 0.0503 ± 0.0003 |
| DDPG-Equal | 50.13 ± 12.09 | 89.61 ± 0.01 | 31.08 ± 28.03 | 0.1019 ± 0.1243 | 54.10 ± 27.78 | 0.0696 ± 0.0009 |
| PPO-Equal | 54.80 ± 0.67 | 89.58 ± 0.05 | 19.41 ± 0.60 | 0.0576 ± 0.0083 | 64.02 ± 2.09 | 0.0980 ± 0.0035 |
| ERWO-PPO | 54.99 ± 0.71 | 89.60 ± 0.02 | 19.33 ± 1.27 | 0.0626 ± 0.0244 | 64.47 ± 2.65 | 0.0962 ± 0.0007 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2225 ± 0.1042; beta_energy: 0.1922 ± 0.1114; lambda_deadline: 0.2579 ± 0.0575; gamma_qos: 0.3275 ± 0.0726.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 3.96 ± 0.04 |
| avg_cand_eval | 0.06 ± 0.00 |
| total_search_time | 160.82 ± 1.74 |
| final_ppo_train_time | 19.33 ± 0.82 |

## heavy — 25,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 42.91 ± 0.00 | 135.20 ± 0.00 | 81.22 ± 0.00 | 0.3270 ± 0.0000 | 6.21 ± 0.00 | 0.0011 ± 0.0000 |
| Least Fog | 84.34 ± 0.00 | 134.40 ± 0.00 | 17.75 ± 0.00 | 0.0374 ± 0.0000 | 103.50 ± 0.00 | 0.0025 ± 0.0000 |
| Q-Learning-Equal | 70.21 ± 5.26 | 131.78 ± 1.61 | 40.09 ± 10.14 | 0.1768 ± 0.0693 | 66.07 ± 12.91 | 0.0053 ± 0.0001 |
| DQN-Equal | 83.01 ± 0.30 | 133.75 ± 0.44 | 18.51 ± 0.30 | 0.0466 ± 0.0056 | 99.96 ± 1.72 | 0.0513 ± 0.0016 |
| DDPG-Equal | 67.10 ± 20.32 | 133.75 ± 1.41 | 43.53 ± 31.50 | 0.1665 ± 0.1446 | 61.92 ± 45.04 | 0.0697 ± 0.0012 |
| PPO-Equal | 81.46 ± 1.15 | 134.37 ± 0.02 | 20.92 ± 1.54 | 0.0750 ± 0.0239 | 92.91 ± 4.62 | 0.0970 ± 0.0018 |
| ERWO-PPO | 82.28 ± 1.40 | 134.37 ± 0.01 | 19.85 ± 1.42 | 0.0581 ± 0.0174 | 96.13 ± 5.11 | 0.0963 ± 0.0012 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2367 ± 0.0878; beta_energy: 0.2445 ± 0.0956; lambda_deadline: 0.3368 ± 0.2069; gamma_qos: 0.1820 ± 0.1317.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 4.01 ± 0.04 |
| avg_cand_eval | 0.09 ± 0.00 |
| total_search_time | 164.22 ± 1.59 |
| final_ppo_train_time | 19.91 ± 0.51 |

## dynamic — 25,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 28.92 ± 0.00 | 90.14 ± 0.00 | 80.39 ± 0.00 | 0.3243 ± 0.0000 | 4.60 ± 0.00 | 0.0011 ± 0.0000 |
| Least Fog | 56.23 ± 0.00 | 89.60 ± 0.00 | 17.34 ± 0.00 | 0.0378 ± 0.0000 | 69.13 ± 0.00 | 0.0025 ± 0.0000 |
| Q-Learning-Equal | 49.15 ± 2.92 | 87.73 ± 0.86 | 32.96 ± 8.09 | 0.1184 ± 0.0571 | 50.81 ± 8.63 | 0.0054 ± 0.0001 |
| DQN-Equal | 55.33 ± 0.56 | 89.36 ± 0.15 | 17.86 ± 0.33 | 0.0497 ± 0.0076 | 66.71 ± 1.37 | 0.0510 ± 0.0005 |
| DDPG-Equal | 50.13 ± 12.09 | 89.61 ± 0.01 | 31.08 ± 28.03 | 0.1019 ± 0.1243 | 54.10 ± 27.78 | 0.0702 ± 0.0016 |
| PPO-Equal | 54.80 ± 0.67 | 89.58 ± 0.05 | 19.41 ± 0.60 | 0.0576 ± 0.0083 | 64.02 ± 2.09 | 0.0986 ± 0.0044 |
| ERWO-PPO | 54.99 ± 0.71 | 89.60 ± 0.02 | 19.33 ± 1.27 | 0.0626 ± 0.0244 | 64.47 ± 2.65 | 0.0960 ± 0.0013 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2225 ± 0.1042; beta_energy: 0.1922 ± 0.1114; lambda_deadline: 0.2579 ± 0.0575; gamma_qos: 0.3275 ± 0.0726.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 3.96 ± 0.02 |
| avg_cand_eval | 0.06 ± 0.00 |
| total_search_time | 161.04 ± 0.89 |
| final_ppo_train_time | 19.80 ± 0.31 |

## light — 50,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 14.87 ± 0.00 | 45.07 ± 0.00 | 77.94 ± 0.00 | 0.3161 ± 0.0000 | 2.93 ± 0.00 | 0.0011 ± 0.0000 |
| Least Fog | 28.06 ± 0.00 | 44.80 ± 0.00 | 17.44 ± 0.00 | 0.0394 ± 0.0000 | 34.45 ± 0.00 | 0.0025 ± 0.0000 |
| Q-Learning-Equal | 24.60 ± 0.97 | 43.00 ± 1.27 | 33.48 ± 5.38 | 0.0895 ± 0.0211 | 26.16 ± 1.65 | 0.0054 ± 0.0001 |
| DQN-Equal | 27.69 ± 0.41 | 44.67 ± 0.16 | 18.31 ± 1.01 | 0.0545 ± 0.0147 | 32.98 ± 1.51 | 0.0513 ± 0.0010 |
| DDPG-Equal | 24.97 ± 5.78 | 44.80 ± 0.01 | 31.11 ± 26.69 | 0.1082 ± 0.1165 | 26.50 ± 13.29 | 0.0706 ± 0.0022 |
| PPO-Equal | 27.85 ± 0.09 | 44.77 ± 0.06 | 18.12 ± 0.20 | 0.0453 ± 0.0015 | 33.71 ± 0.23 | 0.0980 ± 0.0014 |
| ERWO-PPO | 27.83 ± 0.08 | 44.79 ± 0.01 | 18.20 ± 0.35 | 0.0466 ± 0.0024 | 33.56 ± 0.31 | 0.0971 ± 0.0015 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2399 ± 0.0586; beta_energy: 0.1856 ± 0.0623; lambda_deadline: 0.2551 ± 0.1897; gamma_qos: 0.3194 ± 0.1551.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 3.95 ± 0.02 |
| avg_cand_eval | 0.03 ± 0.00 |
| total_search_time | 159.49 ± 0.93 |
| final_ppo_train_time | 39.47 ± 0.44 |

## moderate — 50,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 28.92 ± 0.00 | 90.14 ± 0.00 | 80.39 ± 0.00 | 0.3243 ± 0.0000 | 4.60 ± 0.00 | 0.0011 ± 0.0000 |
| Least Fog | 56.23 ± 0.00 | 89.60 ± 0.00 | 17.34 ± 0.00 | 0.0378 ± 0.0000 | 69.13 ± 0.00 | 0.0025 ± 0.0000 |
| Q-Learning-Equal | 47.59 ± 3.57 | 85.03 ± 3.13 | 36.58 ± 8.39 | 0.1002 ± 0.0638 | 49.73 ± 8.41 | 0.0053 ± 0.0000 |
| DQN-Equal | 55.74 ± 0.16 | 89.29 ± 0.31 | 18.02 ± 0.47 | 0.0450 ± 0.0040 | 67.38 ± 0.86 | 0.0514 ± 0.0007 |
| DDPG-Equal | 53.18 ± 5.65 | 85.64 ± 8.88 | 24.11 ± 13.04 | 0.0476 ± 0.0036 | 62.41 ± 10.18 | 0.0693 ± 0.0005 |
| PPO-Equal | 55.84 ± 0.18 | 89.60 ± 0.01 | 18.09 ± 0.30 | 0.0440 ± 0.0035 | 67.59 ± 0.64 | 0.0982 ± 0.0033 |
| ERWO-PPO | 55.86 ± 0.14 | 89.57 ± 0.06 | 17.96 ± 0.23 | 0.0434 ± 0.0016 | 67.74 ± 0.51 | 0.0981 ± 0.0045 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2225 ± 0.1042; beta_energy: 0.1922 ± 0.1114; lambda_deadline: 0.2579 ± 0.0575; gamma_qos: 0.3275 ± 0.0726.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 3.93 ± 0.07 |
| avg_cand_eval | 0.06 ± 0.00 |
| total_search_time | 159.88 ± 2.92 |
| final_ppo_train_time | 39.17 ± 0.44 |

## heavy — 50,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 42.91 ± 0.00 | 135.20 ± 0.00 | 81.22 ± 0.00 | 0.3270 ± 0.0000 | 6.21 ± 0.00 | 0.0011 ± 0.0000 |
| Least Fog | 84.34 ± 0.00 | 134.40 ± 0.00 | 17.75 ± 0.00 | 0.0374 ± 0.0000 | 103.50 ± 0.00 | 0.0025 ± 0.0000 |
| Q-Learning-Equal | 69.16 ± 4.18 | 130.67 ± 2.83 | 41.73 ± 8.47 | 0.1727 ± 0.0785 | 65.97 ± 11.81 | 0.0053 ± 0.0000 |
| DQN-Equal | 83.66 ± 0.41 | 134.17 ± 0.38 | 18.23 ± 0.31 | 0.0450 ± 0.0026 | 100.77 ± 0.88 | 0.0508 ± 0.0006 |
| DDPG-Equal | 74.53 ± 18.06 | 134.38 ± 0.02 | 32.17 ± 27.92 | 0.1097 ± 0.1222 | 78.93 ± 41.05 | 0.0696 ± 0.0009 |
| PPO-Equal | 83.67 ± 0.24 | 134.35 ± 0.04 | 18.57 ± 0.39 | 0.0433 ± 0.0022 | 100.98 ± 0.97 | 0.0958 ± 0.0006 |
| ERWO-PPO | 83.30 ± 0.56 | 134.38 ± 0.03 | 18.83 ± 0.55 | 0.0454 ± 0.0039 | 99.74 ± 1.97 | 0.0959 ± 0.0011 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2367 ± 0.0878; beta_energy: 0.2445 ± 0.0956; lambda_deadline: 0.3368 ± 0.2069; gamma_qos: 0.1820 ± 0.1317.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 3.99 ± 0.02 |
| avg_cand_eval | 0.09 ± 0.00 |
| total_search_time | 163.24 ± 0.94 |
| final_ppo_train_time | 39.00 ± 0.51 |

## dynamic — 50,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 28.92 ± 0.00 | 90.14 ± 0.00 | 80.39 ± 0.00 | 0.3243 ± 0.0000 | 4.60 ± 0.00 | 0.0011 ± 0.0000 |
| Least Fog | 56.23 ± 0.00 | 89.60 ± 0.00 | 17.34 ± 0.00 | 0.0378 ± 0.0000 | 69.13 ± 0.00 | 0.0025 ± 0.0000 |
| Q-Learning-Equal | 47.59 ± 3.57 | 85.03 ± 3.13 | 36.58 ± 8.39 | 0.1002 ± 0.0638 | 49.73 ± 8.41 | 0.0053 ± 0.0000 |
| DQN-Equal | 55.74 ± 0.16 | 89.29 ± 0.31 | 18.02 ± 0.47 | 0.0450 ± 0.0040 | 67.38 ± 0.86 | 0.0509 ± 0.0004 |
| DDPG-Equal | 53.18 ± 5.65 | 85.64 ± 8.88 | 24.11 ± 13.04 | 0.0476 ± 0.0036 | 62.41 ± 10.18 | 0.0697 ± 0.0005 |
| PPO-Equal | 55.84 ± 0.18 | 89.60 ± 0.01 | 18.09 ± 0.30 | 0.0440 ± 0.0035 | 67.59 ± 0.64 | 0.0965 ± 0.0009 |
| ERWO-PPO | 55.86 ± 0.14 | 89.57 ± 0.06 | 17.96 ± 0.23 | 0.0434 ± 0.0016 | 67.74 ± 0.51 | 0.0962 ± 0.0007 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2225 ± 0.1042; beta_energy: 0.1922 ± 0.1114; lambda_deadline: 0.2579 ± 0.0575; gamma_qos: 0.3275 ± 0.0726.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 3.96 ± 0.03 |
| avg_cand_eval | 0.06 ± 0.00 |
| total_search_time | 160.92 ± 1.28 |
| final_ppo_train_time | 39.48 ± 0.22 |

## light — 100,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 14.87 ± 0.00 | 45.07 ± 0.00 | 77.94 ± 0.00 | 0.3161 ± 0.0000 | 2.93 ± 0.00 | 0.0011 ± 0.0000 |
| Least Fog | 28.06 ± 0.00 | 44.80 ± 0.00 | 17.44 ± 0.00 | 0.0394 ± 0.0000 | 34.45 ± 0.00 | 0.0025 ± 0.0000 |
| Q-Learning-Equal | 25.15 ± 0.54 | 43.41 ± 1.30 | 30.89 ± 4.10 | 0.0957 ± 0.0351 | 27.07 ± 1.74 | 0.0053 ± 0.0000 |
| DQN-Equal | 27.65 ± 0.20 | 44.30 ± 0.32 | 18.12 ± 0.44 | 0.0475 ± 0.0039 | 33.53 ± 0.43 | 0.0510 ± 0.0006 |
| DDPG-Equal | 25.07 ± 5.84 | 44.78 ± 0.05 | 30.88 ± 26.82 | 0.1087 ± 0.1169 | 26.84 ± 13.50 | 0.0694 ± 0.0009 |
| PPO-Equal | 27.86 ± 0.19 | 44.72 ± 0.12 | 18.00 ± 0.40 | 0.0443 ± 0.0008 | 33.86 ± 0.19 | 0.0967 ± 0.0014 |
| ERWO-PPO | 27.91 ± 0.10 | 44.72 ± 0.08 | 17.85 ± 0.09 | 0.0441 ± 0.0018 | 33.93 ± 0.16 | 0.0965 ± 0.0015 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2399 ± 0.0586; beta_energy: 0.1856 ± 0.0623; lambda_deadline: 0.2551 ± 0.1897; gamma_qos: 0.3194 ± 0.1551.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 3.98 ± 0.07 |
| avg_cand_eval | 0.03 ± 0.00 |
| total_search_time | 160.49 ± 2.80 |
| final_ppo_train_time | 79.36 ± 1.75 |

## moderate — 100,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 28.92 ± 0.00 | 90.14 ± 0.00 | 80.39 ± 0.00 | 0.3243 ± 0.0000 | 4.60 ± 0.00 | 0.0011 ± 0.0000 |
| Least Fog | 56.23 ± 0.00 | 89.60 ± 0.00 | 17.34 ± 0.00 | 0.0378 ± 0.0000 | 69.13 ± 0.00 | 0.0025 ± 0.0000 |
| Q-Learning-Equal | 50.39 ± 2.05 | 87.52 ± 1.60 | 29.52 ± 5.30 | 0.0887 ± 0.0416 | 54.37 ± 5.79 | 0.0053 ± 0.0000 |
| DQN-Equal | 55.32 ± 0.35 | 89.33 ± 0.49 | 18.24 ± 0.98 | 0.0510 ± 0.0071 | 66.11 ± 1.51 | 0.0511 ± 0.0013 |
| DDPG-Equal | 50.48 ± 12.29 | 89.62 ± 0.01 | 30.49 ± 28.37 | 0.0988 ± 0.1260 | 55.28 ± 28.43 | 0.0696 ± 0.0005 |
| PPO-Equal | 55.95 ± 0.09 | 89.55 ± 0.11 | 17.78 ± 0.18 | 0.0420 ± 0.0020 | 68.14 ± 0.42 | 0.0957 ± 0.0010 |
| ERWO-PPO | 56.05 ± 0.07 | 89.58 ± 0.04 | 17.66 ± 0.17 | 0.0409 ± 0.0011 | 68.42 ± 0.29 | 0.0952 ± 0.0011 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2225 ± 0.1042; beta_energy: 0.1922 ± 0.1114; lambda_deadline: 0.2579 ± 0.0575; gamma_qos: 0.3275 ± 0.0726.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 3.96 ± 0.05 |
| avg_cand_eval | 0.06 ± 0.00 |
| total_search_time | 160.87 ± 1.91 |
| final_ppo_train_time | 78.00 ± 0.82 |

## heavy — 100,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 42.91 ± 0.00 | 135.20 ± 0.00 | 81.22 ± 0.00 | 0.3270 ± 0.0000 | 6.21 ± 0.00 | 0.0010 ± 0.0000 |
| Least Fog | 84.34 ± 0.00 | 134.40 ± 0.00 | 17.75 ± 0.00 | 0.0374 ± 0.0000 | 103.50 ± 0.00 | 0.0025 ± 0.0000 |
| Q-Learning-Equal | 76.99 ± 2.17 | 131.57 ± 2.24 | 27.95 ± 3.28 | 0.0844 ± 0.0131 | 84.23 ± 2.58 | 0.0053 ± 0.0001 |
| DQN-Equal | 82.89 ± 1.34 | 134.25 ± 0.18 | 18.82 ± 1.15 | 0.0551 ± 0.0183 | 98.37 ± 4.75 | 0.0518 ± 0.0020 |
| DDPG-Equal | 74.80 ± 18.24 | 134.30 ± 0.20 | 31.94 ± 28.07 | 0.1058 ± 0.1242 | 79.68 ± 41.55 | 0.0704 ± 0.0019 |
| PPO-Equal | 83.75 ± 0.26 | 134.15 ± 0.24 | 18.46 ± 0.29 | 0.0432 ± 0.0027 | 101.15 ± 0.89 | 0.0987 ± 0.0049 |
| ERWO-PPO | 83.97 ± 0.20 | 134.39 ± 0.04 | 18.16 ± 0.20 | 0.0409 ± 0.0014 | 102.03 ± 0.73 | 0.0980 ± 0.0043 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2367 ± 0.0878; beta_energy: 0.2445 ± 0.0956; lambda_deadline: 0.3368 ± 0.2069; gamma_qos: 0.1820 ± 0.1317.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 3.98 ± 0.06 |
| avg_cand_eval | 0.09 ± 0.00 |
| total_search_time | 163.09 ± 2.26 |
| final_ppo_train_time | 77.48 ± 1.05 |

## dynamic — 100,000 timestep

Seed selesai: [0, 1, 2, 3, 4] (5/5).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 28.92 ± 0.00 | 90.14 ± 0.00 | 80.39 ± 0.00 | 0.3243 ± 0.0000 | 4.60 ± 0.00 | 0.0011 ± 0.0000 |
| Least Fog | 56.23 ± 0.00 | 89.60 ± 0.00 | 17.34 ± 0.00 | 0.0378 ± 0.0000 | 69.13 ± 0.00 | 0.0025 ± 0.0000 |
| Q-Learning-Equal | 50.39 ± 2.05 | 87.52 ± 1.60 | 29.52 ± 5.30 | 0.0887 ± 0.0416 | 54.37 ± 5.79 | 0.0053 ± 0.0000 |
| DQN-Equal | 55.32 ± 0.35 | 89.33 ± 0.49 | 18.24 ± 0.98 | 0.0510 ± 0.0071 | 66.11 ± 1.51 | 0.0514 ± 0.0021 |
| DDPG-Equal | 50.48 ± 12.29 | 89.62 ± 0.01 | 30.49 ± 28.37 | 0.0988 ± 0.1260 | 55.28 ± 28.43 | 0.0696 ± 0.0011 |
| PPO-Equal | 55.95 ± 0.09 | 89.55 ± 0.11 | 17.78 ± 0.18 | 0.0420 ± 0.0020 | 68.14 ± 0.42 | 0.0977 ± 0.0050 |
| ERWO-PPO | 56.05 ± 0.07 | 89.58 ± 0.04 | 17.66 ± 0.17 | 0.0409 ± 0.0011 | 68.42 ± 0.29 | 0.0976 ± 0.0053 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.2225 ± 0.1042; beta_energy: 0.1922 ± 0.1114; lambda_deadline: 0.2579 ± 0.0575; gamma_qos: 0.3275 ± 0.0726.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 3.98 ± 0.06 |
| avg_cand_eval | 0.06 ± 0.00 |
| total_search_time | 161.61 ± 2.38 |
| final_ppo_train_time | 79.37 ± 1.02 |

## Artefak

- `runs.csv`: hasil tiap metode dan seed.
- `summary.json`: agregasi seluruh metrik, bobot, dan overhead.
- `manifest.json`: konfigurasi, fingerprint source, command, dan status tiap percobaan.
- `runs/<workload>_t<budget>_seed<seed>/`: model, Data.md, log, statistik, dan CSV episode tiap run.
