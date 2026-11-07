# Data akhir eksperimen ERWO-PPO

Status: complete; selesai 2/2 percobaan.

Konfigurasi: kandidat 16 timestep; populasi 2; generasi 1; evaluasi 3 episode; device cpu.
Seed training: [0, 1]. Workload: ['light'].

Setiap kombinasi dilatih ulang dari awal, termasuk pencarian bobot NSGA-II. Anggaran timestep adalah nilai yang diminta; PPO dapat membulatkan ke ukuran rollout.

Nilai tabel adalah rata-rata ± standar deviasi sampel antar-seed training, setelah setiap run dirata-ratakan atas episode evaluasi. N/A berarti baru ada satu seed. Hasil parsial tidak mewakili seluruh matriks.

Latensi, energi, deadline, dan QoS adalah jumlah sub-reward per episode, bukan ms, Joule, atau persentase. Jangan membandingkan jumlah skor lintas workload dengan panjang episode berbeda. Violation menggunakan persen; decision time menggunakan ms.

Seed validasi kandidat: 42..44; seed benchmark: 1000..1002, sama untuk semua metode. Socket Java wajib; fallback Python dinonaktifkan. P-value per-run tersedia di log; tidak dirata-ratakan atau digabung menjadi klaim signifikansi antar-seed.

## light — 16 timestep

Seed selesai: [0, 1] (2/2).

| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Nearest Fog | 14.57 ± 0.00 | 45.07 ± 0.00 | 78.00 ± 0.00 | 0.3165 ± 0.0000 | 2.72 ± 0.00 | 0.0129 ± 0.0016 |
| Least Fog | 27.63 ± 0.00 | 44.76 ± 0.00 | 22.00 ± 0.00 | 0.0410 ± 0.0000 | 32.26 ± 0.00 | 0.0240 ± 0.0007 |
| Q-Learning-Equal | 13.60 ± 1.47 | 34.49 ± 3.07 | 70.00 ± 1.89 | 0.2658 ± 0.0407 | 11.99 ± 0.95 | 0.0707 ± 0.0215 |
| DQN-Equal | 14.46 ± 0.25 | 41.34 ± 4.82 | 78.67 ± 0.94 | 0.3065 ± 0.0151 | 3.86 ± 1.89 | 0.8616 ± 0.2405 |
| DDPG-Equal | 14.46 ± 0.25 | 41.34 ± 4.82 | 78.67 ± 0.94 | 0.3065 ± 0.0151 | 3.86 ± 1.89 | 0.9147 ± 0.0794 |
| PPO-Equal | 14.94 ± 0.92 | 43.13 ± 2.29 | 75.33 ± 5.66 | 0.3093 ± 0.0112 | 4.22 ± 2.40 | 1.1667 ± 0.1343 |
| ERWO-PPO | 15.44 ± 1.64 | 42.05 ± 3.82 | 72.67 ± 9.43 | 0.3018 ± 0.0218 | 6.73 ± 5.96 | 0.9947 ± 0.0060 |

Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): alpha_latency: 0.4226 ± 0.3132; beta_energy: 0.3243 ± 0.0647; lambda_deadline: 0.0551 ± 0.0061; gamma_qos: 0.1979 ± 0.2425.

| Biaya per run | Detik, rata-rata ± SD |
|---|---:|
| avg_cand_train | 4.53 ± 1.60 |
| avg_cand_eval | 0.43 ± 0.24 |
| total_search_time | 9.93 ± 3.69 |
| final_ppo_train_time | 1.61 ± 0.12 |

## Artefak

- `runs.csv`: hasil tiap metode dan seed.
- `summary.json`: agregasi seluruh metrik, bobot, dan overhead.
- `manifest.json`: konfigurasi, fingerprint source, command, dan status tiap percobaan.
- `runs/<workload>_t<budget>_seed<seed>/`: model, Data.md, log, statistik, dan CSV episode tiap run.
