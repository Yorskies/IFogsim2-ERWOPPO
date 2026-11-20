# P13 — studi benchmark tambahan: DQN, Q-Learning tabular, DDPG (rancangan)

Status: **rancangan disetujui (18 November 2026), diimplementasikan (P13.1); belum dijalankan.** Dimulai setelah P12 (selesai 15 November 2026).
Implementasi: `research_v2/p13.py` (orkestrator), `research_v2/p13_learners.py`, `research_v2/p13_traces.py`, launcher `run_p13.sh`,
tes `tests/research_v2/test_p13.py`. Keputusan §8 tercatat di §9.
Basis: protokol v0.4, lock `P10-lock-3` (`63d07e43…`), hasil P11/P12. P13 tidak mengubah file ter-lock mana pun dan tidak mengubah
klaim konfirmatori P11; P13 punya lock sendiri (`P13-lock`) yang merujuk lock v0.4.

## 1. Tujuan dan pertanyaan

P11 hanya membandingkan cara memilih bobot reward untuk **satu** learner (PPO). Reviewer wajar bertanya apakah PPO itu sendiri pilihan yang
baik. P13 menjawab: *pada lingkungan, observasi, reward (bobot equal) dan budget interaksi yang sama, bagaimana DQN, Q-Learning tabular dan DDPG
dibandingkan dengan PPO-Equal?*

| Kode | Pertanyaan (selisih = D(pembanding) − D(PPO-Equal), positif = PPO lebih baik) | Budget |
|---|---|---|
| B1 | DQN vs PPO-Equal | B = 19.637.248 |
| B2 | Q-Learning tabular vs PPO-Equal | B |
| B3 | DDPG (adaptasi diskret) vs PPO-Equal | B |
| B4–B6 | sama seperti B1–B3 | F = 102.400 |
| B7–B9 | tiap algoritma baru vs `greedy_eft` | B |

B dipilih sebagai primer karena P11 menunjukkan PPO-Equal pada B adalah metode terbaik (D 0,167); itu pembanding terkuat dan paling relevan.

## 2. Status epistemik (penting untuk manuskrip)

- Split test P11 (trace 20000–20099) **sudah dibuka** dan hasil PPO sudah diketahui. Benchmark baru di split itu tidak buta.
- **Usulan:** daftarkan split baru tersegel `benchmark_test` (trace id 30000–30099 per workload, generator dan config sama, belum pernah
  dibangkitkan), dibuka sekali setelah `P13-lock`. Analisis primer P13 dilakukan di split ini; split test P11 dilaporkan sebagai pelengkap.
  PPO (equal_F, equal_B, nsga2) dan heuristik dievaluasi ulang pada split baru dari checkpoint P11 tanpa retraining.
- B1–B3 dianalisis sebagai keluarga primer P13 (Holm, α = 0,05); B4–B9 sekunder (Holm terpisah). Semua dilabeli
  "benchmark P13 terdaftar, terpisah dari klaim konfirmatori P11".

## 3. Metode

Semua metode: lingkungan `gym_env` yang sama (108 fitur publik, `Discrete(7)`: source_iot, F1–F5, cloud), reward bobot **equal**,
gamma 0,97 (sama dengan learner v0.3), trace training yang sama dengan job `equal` P11 per outer run (urutan workload identik),
seed outer 0–19 dengan namespace baru `p13.<algoritma>`, 1 environment, CPU, `torch_threads = 1`.

| Metode | Implementasi | Catatan |
|---|---|---|
| PPO-Equal F / B | checkpoint P11 (`equal_F`, `equal_B`), tanpa retraining | referensi |
| **DQN** | Stable-Baselines3 2.9.2 `DQN`, MLP [128, 128] | aksi diskret, cocok langsung |
| **Q-Learning tabular** | implementasi baru `research_v2/tabular_q.py` | butuh diskretisasi state (§3.1) |
| **DDPG** | SB3 `DDPG` + wrapper aksi kontinu → diskret (§3.2) | adaptasi; dilabeli eksplisit |
| heuristik | always_local, nearest_fog, least_fog, greedy_eft | sama dengan P11 |

### 3.1 Diskretisasi Q-Learning tabular (ditetapkan sebelum tuning)

State dibangun hanya dari snapshot publik (informasi yang sama dengan PPO/heuristik), deterministik:

- Untuk tiap aksi a ∈ 7 node: estimasi waktu selesai `e_a = route.a.estimated_input_delay_s + node.a.earliest_pe_free_delay_s
  + node.a.queued_mi_over_mips_s + task.cpu_mi / node.a.mips_per_pe + route.a.estimated_result_delay_s` (dide-normalisasi dengan konstanta
  referensi `observation`), lalu bin relatif terhadap deadline tugas: `e_a ≤ 0,5·d`, `≤ d`, `> d` → 3 bin.
- Ditambah kelas tugas (light/medium/heavy) → 3⁷ × 3 = 6.561 state × 7 aksi = 45.927 entri Q (inisialisasi 0).
- State tak pernah dikunjungi saat evaluasi: aksi index 0 (lokal) — aturan tetap, fraksi kejadian dilaporkan per model.
- Batas yang harus dicatat: diskretisasi ini memberi Q-Learning fitur turunan yang mirip greedy_eft; itu desain baseline klasik yang
  wajar, tetapi berarti Q-Learning tidak melihat seluruh 108 fitur.

### 3.2 Adaptasi DDPG ke aksi diskret

DDPG dirancang untuk aksi kontinu. Adaptasi terdaftar: actor mengeluarkan vektor skor 7-dimensi di [−1, 1]; wrapper mengeksekusi
`argmax` (seri → index terkecil); critic Q(s, a) menerima vektor kontinu tersebut; noise eksplorasi Gaussian pada vektor skor.
Dilaporkan sebagai **"DDPG (relaksasi kontinu + argmax)"** dengan keterbatasan: gradien critic tidak merefleksikan diskontinuitas argmax.
Alternatif yang lebih standar untuk aksi diskret (Wolpertinger, SAC-Discrete) dicatat di manuskrip; tidak dijalankan kecuali diputuskan.

## 4. Keadilan perbandingan

- **Budget interaksi:** F dan B dihitung sebagai keputusan lingkungan (bukan gradient step), sama dengan ledger P11.
- **Run F terpisah dari run B** untuk algoritma baru, karena jadwal eksplorasi (ε, noise) bergantung pada total budget; checkpoint F dari
  run B bukan run F yang sah. (PPO tidak punya jadwal; P11 memakai checkpoint F dari run yang sama dan itu tetap.)
- **Tuning hyperparameter:** hanya namespace pilot (pilot_train outer 100–102, 20 trace pilot_validation), pada budget F,
  maksimal 8 konfigurasi × 3 seed per algoritma; terpilih = mean D terendah pada pilot_validation, seri → konfigurasi lebih sederhana.
  Tidak ada seed konfirmatori, trace validation search, atau trace test yang dipakai untuk tuning.
  Asimetri yang dicatat: PPO di-tuning lewat diagnosis gamma (5 nilai) dan ablation entropi/rollout/lr pada namespace pilot yang sama.
- Grid yang diusulkan (8 konfigurasi masing-masing, sisanya default SB3 dicatat di lock):

| Algoritma | Grid |
|---|---|
| DQN | lr {1e-4, 3e-4} × target_update_interval {1.000, 10.000} × exploration_fraction {0,1; 0,3}; buffer 100.000, batch 128, train_freq 4, ε akhir 0,05 |
| Q-Learning | α {0,05; 0,2} × ε akhir {0,01; 0,05} × fraksi decay ε {0,1; 0,3}; ε awal 1,0 |
| DDPG | actor lr {1e-4, 1e-3} × σ noise {0,1; 0,3} × τ {0,005; 0,02}; critic lr 1e-3, buffer 100.000, batch 128 |

## 5. Evaluasi dan analisis

- Policy deterministik (DQN/Q-table argmax, actor DDPG tanpa noise), 100 trace × 4 workload, pasangan trace sama untuk semua metode.
- Metrik sama dengan P11: Dglobal, lima biaya (zL, zE, zD, zB, zQ), metrik fisik (latency, energi, deadline, reliability), per workload.
- Statistik memakai mesin P10/P11 tanpa perubahan: n = 20 outer run berpasangan (seed r di metode baru dipasangkan dengan PPO-Equal r),
  sign-flip exact, bootstrap crossed (run × trace) 95% CI, dz; non-signifikan = bukti kurang, bukan kesetaraan.
- Tambahan deskriptif: kurva belajar (D episode training per 1/16 budget B, rata-rata 20 run; termasuk PPO-Equal dari log P11), jam CPU per
  metode, fraksi keputusan di state tak terlihat (Q-tabular), jumlah episode di luar referensi [0, 1] (ditandai, tidak di-clip).

## 6. Perkiraan compute dan penyimpanan (diverifikasi dengan pilot waktu sebelum lock)

Acuan terukur: job PPO-Equal B di P11 = 4,1 jam wall pada 1 CPU (simulasi/RPC ≈ 1,2 jam).

| Komponen | Jumlah | Perkiraan wall / job | Total CPU-jam |
|---|---:|---:|---:|
| Tuning (F, pilot) | 3 × 8 × 3 = 72 | 2–8 menit | ≈ 5 |
| Run F | 3 × 20 = 60 | 2–8 menit | ≈ 4 |
| Q-Learning B | 20 | ≈ 1,5 jam (dominan simulasi) | ≈ 30 |
| DQN B | 20 | ≈ 6–10 jam (≈ 4,9 juta gradient step) | ≈ 160 |
| DDPG B | 20 | ≈ 8–14 jam (actor + critic) | ≈ 220 |
| Evaluasi (benchmark_test + test P11) | ≈ 190 model/heuristik × 2 split | — | ≈ 10 |

Dengan 12 worker (batas container 16 CPU): **≈ 1,5–2 hari** wall. Smoke 2.048 keputusan: DQN ≈ 1,2 ms, DDPG ≈ 3 ms, Q-tabular ≈ 0,5 ms
per keputusan (termasuk simulasi). Perkiraan per run B dicatat otomatis dari waktu run tuning (F) di log pipeline.

Penyimpanan: log keputusan penuh ≈ 6,4 GB gzip per job B → 60 job ≈ 380 GB, melebihi sisa disk (317 GB). Usulan: log keputusan penuh
untuk run F dan tuning; untuk run B hanya 102.400 keputusan pertama dan terakhir + ledger episode lengkap + checkpoint tiap F keputusan
(perubahan operasional, dicatat di lock). Alternatif: pindahkan log P11 ke arsip terpisah dulu.

## 7. Tahapan

| Tahap | Isi | Kriteria lulus |
|---|---|---|
| P13.0 | rancangan ini disetujui; keputusan §8 | keputusan tercatat |
| P13.1 | implementasi: adapter DQN/DDPG, `tabular_q.py`, diskretisasi, wrapper argmax, budget ledger, resume deterministik, segel `benchmark_test` | unit test; smoke 512 keputusan; resume identik; ledger = budget |
| P13.2 | pilot waktu + tuning di namespace pilot | konfigurasi terpilih per algoritma; laporan tuning |
| P13.3 | `P13-lock` (desain, grid terpilih, hash kode/JAR/config, split tersegel) | verifikasi lock |
| P13.4 | training 60 run F + 60 run B (launcher satu perintah seperti `run_p12.sh`) | 120/120 complete, 0 fallback engine |
| P13.5 | buka `benchmark_test` sekali; evaluasi semua metode di dua split | 0 error, reward identity terpenuhi |
| P13.6 | analisis B1–B9, laporan, update tabel klaim dan manuskrip | laporan dapat direkonstruksi dari data mentah |

## 8. Keputusan yang perlu diambil sebelum P13.1

1. Split test baru tersegel `benchmark_test` (disarankan) atau hanya split test P11 (lebih cepat, tapi tidak buta).
2. Varian DDPG: relaksasi kontinu + argmax (rancangan ini) atau ganti/tambah Wolpertinger / SAC-Discrete.
3. Strategi log keputusan untuk run B (log terpotong vs arsip log P11 dulu).
4. Grid tuning §4 diterima atau diubah.

## 9. Keputusan (18 November 2026) dan catatan implementasi

1. **Split baru tersegel `benchmark_test` dipakai** (trace 30000–30099 × 4 workload = 400 trace). Generator sama byte-per-byte dengan
   generator ter-lock (dibuktikan unit test pada split validation/pilot_validation); seed stream memuat label `benchmark_test` sehingga
   independen dari semua split lama. Sebelum lock hanya manifest input (hash payload, jumlah tugas) yang dibangkitkan; evaluasi butuh
   `P13-lock` yang terverifikasi dan catatan pembukaan `results/research_v2/p13/BENCHMARK_OPENED.json`, ditulis sekali setelah training.
   File ter-lock v0.4 tidak diubah (simulator tidak membaca namespace; hanya hash payload).
2. **DDPG: relaksasi skor kontinu + argmax** (tanpa Wolpertinger/SAC-Discrete). Actor lr dan critic lr terpisah (SB3 aslinya satu lr).
3. **Disk:** log keputusan penuh untuk run ≤ 204.800 keputusan (tuning, run F); run B menyimpan 102.400 baris pertama dan terakhir
   + seluruh baris episode training (cukup untuk audit reward/biaya per episode). Perkiraan total ≈ 15–20 GB.
4. **Grid §4 diterima apa adanya.**

Tahapan otomatis (`./run_p13.sh`): preflight → determinisme (tiap algoritma dilatih dua kali 1.024 keputusan; parameter harus identik)
→ tuning (72 run) → `P13-lock` (`results/research_v2/p13/protocol_lock/p13_lock.json`: hash semua source, grid, pilihan tuning,
manifest benchmark_test, hipotesis) → training (120 run; run B terlama lebih dulu) → buka benchmark_test → evaluasi (184 tugas di
benchmark_test, 120 tugas metode baru di test P11) → analisis → tabel klaim (`results/research_v2/p13/claims_p13.md`).
Perubahan kode setelah lock membuat verifikasi lock gagal (disengaja); perubahan apa pun harus dicatat sebagai deviasi.
