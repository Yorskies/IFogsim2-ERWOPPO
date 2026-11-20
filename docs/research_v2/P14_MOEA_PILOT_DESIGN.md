# P14 — pilot study benchmark MOEA (NSGA-II, NSGA-III, MOEA/D, SPEA2) untuk bobot reward PPO

Status: **rancangan disetujui (20 November 2026); implementasi berjalan.** Keputusan dan tambahan setelah tinjauan literatur: §12.
Basis: protokol v0.4 (lock `63d07e43…`), hasil P11/P12, diskusi QA 20 November 2026. File ter-lock v0.4 tidak diubah.
Semua data pilot berasal dari namespace pilot dan split pengembangan baru (§3). **Tidak ada trace test** (test P11, `benchmark_test` P13,
atau split test benchmark penuh) yang dibangkitkan atau dibaca di pilot ini.

## 1. Latar belakang

Temuan P11 yang memotivasi pilot ini:

| Temuan | Angka |
|---|---|
| Noise antar-seed PPO pada F jauh lebih besar daripada efek bobot | SD D antar-run ≈ 0,085; selisih RQ1 0,020 (dz 0,185) |
| Winner's curse: kandidat terpilih tidak mempertahankan keunggulannya | D validasi terpilih 0,174 → D test 0,245 (≈ median kandidat 0,247) |
| NSGA-II ≈ random search; tidak ada perbaikan antar generasi | D minimum per generasi 0,179 / 0,196 / 0,182 / 0,179 |
| Lima biaya ≈ dua tujuan | Spearman zL–zQ 0,99, zL–zD 0,89; zE–zB 0,59; zE–zL −0,52 |
| Setelah training panjang bobot hampir tidak berpengaruh | equal_B 0,167 vs manual_B 0,169; PPO-equal menyusul NSGA-II setelah ≈ 2 × F |

Benchmark penuh empat MOEA hanya bermakna kalau (a) bobot memang berpengaruh lebih besar daripada noise seed, dan (b) evaluator kandidat
bisa dibuat cukup andal dengan compute yang wajar. Pilot ini mengukur keduanya, dan menguji implementasi keempat MOEA.

## 2. Pertanyaan pilot

| # | Pertanyaan | Keluaran |
|---|---|---|
| Q1 | Berapa bagian variasi D yang berasal dari bobot, dibanding dari seed model? Apakah masih ada setelah training 4 × F? | ICC bobot, keuntungan tervalidasi-silang bobot terbaik vs equal |
| Q2 | Berapa seed dan trace per kandidat yang dibutuhkan agar peringkat kandidat andal? | reliabilitas peringkat, proyeksi Spearman-Brown |
| Q3 | Apakah NSGA-II, NSGA-III, MOEA/D, SPEA2 dan random search berjalan benar pada slot yang disetarakan, berapa biayanya, dan seperti apa kualitas sebenarnya dari bobot pilihannya? | implementasi teruji, waktu per slot, petunjuk awal (bukan klaim) |

## 3. Data dan namespace

- **Training:** `pilot_train` (outer 100–102, repeat 0–1; trace stream sama dengan P07/P10). Variasi seed model dibuat lewat basis seed
  baru `p14_model_base = 600000` (seed = basis + indeks bobot × 100 + indeks seed), sehingga noise seed terisolasi dari variasi trace.
- **Evaluasi:** split pengembangan baru **`dev_validation`**: 25 trace per workload (id 40000–40024, total 100 trace), dibangun dengan
  mekanisme yang sama dengan `benchmark_test` P13 (generator identik byte-per-byte dengan generator ter-lock; seed stream memuat label
  split sehingga independen). Alasannya: split `pilot_validation`/`validation` dikunci di 5 trace per workload, terlalu sedikit untuk Q2.
  `dev_validation` adalah data pengembangan, bukan test; boleh dipakai berulang selama pilot dan saat search di benchmark penuh.
- **Reward:** sesuai bobot kandidat; **penilaian selalu D** (definisi utama v0.4, tidak berubah). Learner v0.3 (gamma 0,97), F = 102.400.

## 4. Desain Q1 dan Q2: lanskap bobot

**Bobot (24, ditetapkan sekarang, sebelum data):**
- 1 equal (0,2 × 5) dan 1 manual (0,30/0,15/0,25/0,10/0,20);
- 5 "condong": 0,6 pada satu biaya, 0,1 pada empat lainnya;
- 5 "ekstrem": 0,92 pada satu biaya, 0,02 pada lainnya (batas simpleks);
- 12 acak Dirichlet(1) di simpleks dengan lantai 0,02 (seed `p14_weights = 600001`).

**Run:**
- Q1-F: 24 bobot × 4 seed model, training F pada `pilot_train` outer 100 repeat 0 (stream trace sama untuk semua). Total 96 run.
- Q1-4F: 8 bobot (equal, manual, 5 condong, 1 acak pertama) × 4 seed, training 4 × F = 409.600. Total 32 run.
- Setiap model dievaluasi deterministik pada 100 trace `dev_validation`.

**Metrik:**
- **ICC bobot** (one-way random effects): σ²_bobot / (σ²_bobot + σ²_seed) dari D per (bobot, seed), dihitung terpisah untuk F dan 4F.
- **Keuntungan tervalidasi-silang:** peringkat bobot berdasarkan seed {1,2}; bobot terbaik dinilai ulang di seed {3,4} dan sebaliknya.
  Keuntungan = D(equal) − D(bobot terpilih) di separuh yang tidak dipakai memilih. CI 95 % bootstrap atas seed dan trace.
  Ini mengukur keuntungan nyata setelah winner's curse dihilangkan.
- **Reliabilitas peringkat (Q2):** Spearman antara peringkat 24 bobot dari seed {1,2} dan {3,4}; proyeksi Spearman-Brown ke m seed.
  Pengaruh jumlah trace: reliabilitas dengan 20 vs 100 trace evaluasi.
- Deskriptif: vektor lima biaya per bobot dan pola aksi (apakah bobot berbeda menghasilkan strategi berbeda).

## 5. Desain Q3: mini-run empat MOEA + random search

**Penyetaraan:** semua algoritma memakai ukuran populasi **15** (= 15 arah referensi Das-Dennis untuk 5 objektif, partisi 2; dibutuhkan
NSGA-III dan MOEA/D) dan **90 slot** (= 15 × 6 generasi) per search. Populasi awal identik untuk semua algoritma per outer run
(15 titik: equal + 14 Dirichlet, seed per outer). Pustaka: pymoo 0.6.2 (sudah terpasang), antarmuka ask/tell yang sama dengan P08/P11.

| Algoritma | Konfigurasi |
|---|---|
| NSGA-II | SBX (p 0,9; η 15), PM (η 20; p per variabel 0,2), repair proyeksi simpleks — sama dengan P11 |
| NSGA-III | operator sama; 15 arah referensi Das-Dennis |
| MOEA/D | 15 vektor bobot Das-Dennis, dekomposisi PBI (default pymoo untuk > 2 objektif), tetangga 5, probabilitas seleksi tetangga 0,9; operator diset sama dengan NSGA-II (default pymoo MOEA/D berbeda: SBX p 1,0, η 20). Varian pembaruan: MOEA/D standar (per offspring) bila antarmuka ask/tell mendukung, jika tidak `ParallelMOEAD` (per generasi); ditetapkan dan dicatat saat implementasi |
| SPEA2 | operator sama; archive 15 |
| Random search | 15 titik awal + 75 titik Dirichlet |

**Evaluator mini-run:** sama dengan P11 (2 model × F per kandidat, `pilot_train` repeat 0/1), dinilai pada 20 trace pertama `dev_validation`
(5 per workload). Objektif: lima biaya makro. Pilihan akhir: D minimum di front (aturan P11). Varian 2 objektif dicatat sebagai opsi untuk
benchmark penuh, tidak dijalankan di pilot.

**Run:** 5 algoritma × 3 outer pilot (100–102) = 15 search × 90 slot.

**Kualitas sebenarnya:** bobot terpilih setiap search dilatih ulang dengan 4 seed baru pada F dan dinilai pada 100 trace `dev_validation`.
Dilaporkan: D sebenarnya per algoritma, selisih dengan equal, hypervolume dan IGD⁺ front akhir (dari nilai search), kurva D minimum per
jumlah slot, waktu per slot. **Dengan 3 outer run, Q3 hanya petunjuk dan uji implementasi, bukan klaim.**

## 6. Aturan keputusan (ditetapkan sebelum pilot)

| Gerbang | Kriteria lulus | Sumber |
|---|---|---|
| G1 sinyal | ICC bobot pada F ≥ 0,30 **dan** keuntungan tervalidasi-silang ≥ 0,02 D dengan batas bawah CI > 0 | Q1-F |
| G2 evaluator | jumlah seed per kandidat untuk reliabilitas peringkat ≥ 0,8 adalah ≤ 4 | Q2 |
| G3 implementasi | 15 search selesai; dua search identik (seed sama) menghasilkan record identik; perkiraan benchmark penuh ≤ 5 hari wall | Q3 |

| Hasil | Langkah |
|---|---|
| G1, G2, G3 lulus | rancang dan kunci benchmark penuh (§8) dengan jumlah seed per kandidat dari G2 |
| G1 gagal di F tetapi lulus di 4F | benchmark penuh pada budget kandidat 4 × F (biaya ≈ 4 ×), atau dirancang ulang |
| G1 gagal di F dan 4F | benchmark MOEA di lingkungan ini **tidak dilanjutkan**; hasil pilot dilaporkan sebagai temuan; opsi: lingkungan dengan trade-off nyata (§9) |
| G2 gagal | evaluator diperkuat atau budget kandidat dinaikkan; dihitung ulang biaya sebelum memutuskan |
| G3 gagal | perbaiki implementasi, ulangi Q3 saja |

Semua angka pilot, termasuk hasil yang buruk, dicatat. Ambang tidak diubah setelah melihat data pilot.

**Prediksi jujur sebelum pilot:** dari P11, sangat mungkin ICC bobot pada F rendah (< 0,3), karena noise seed dominan dan PPO yang baik
konvergen ke strategi yang sama (≈ 30 % lokal / 70 % cloud). Kemungkinan G1 gagal cukup besar. Pilot justru dirancang untuk mengetahui ini
dengan biaya setengah hari sebelum menghabiskan beberapa hari untuk benchmark penuh.

## 7. Estimasi compute (12 worker, 1 CPU per job)

Acuan terukur: PPO ≈ 0,76 ms per keputusan training (P11), evaluasi 100 trace ≈ 1 menit.

| Bagian | Run | CPU-jam | Wall |
|---|---:|---:|---:|
| Q1-F | 96 × (F + evaluasi) | ≈ 4 | ≈ 20 menit |
| Q1-4F | 32 × (4F + evaluasi) | ≈ 3,5 | ≈ 20 menit |
| Q3 search | 15 × 90 slot × 2 model × (F + evaluasi 20 trace) | ≈ 75 | ≈ 6,5 jam |
| Q3 kualitas sebenarnya | 15 × 4 × (F + evaluasi) | ≈ 2,5 | ≈ 15 menit |
| **Total** | | **≈ 85** | **≈ 7,5 jam** |

Disk: log keputusan penuh untuk run ≤ 204.800 keputusan (≈ 33 MB per run F) → ≈ 100 GB untuk 2.900 run. **Usulan:** pilot menyimpan
baris episode lengkap dan hanya 10.240 baris keputusan pertama per run (≈ 3 MB) → ≈ 10 GB. Audit reward/biaya per episode tetap penuh.

## 8. Gambaran benchmark penuh (dikunci terpisah setelah pilot)

- Algoritma: NSGA-II, NSGA-III, MOEA/D, SPEA2, random search; 20 outer run (`train_candidate` outer 0–19); populasi 15, slot 90.
- Evaluator: m seed per kandidat dari G2; evaluasi pada `dev_validation`.
- Model final: bobot terpilih dilatih dari nol pada F (`train_final`, seed P11), dievaluasi di split test tertutup baru **`moea_test`**
  (id 50000–50099 × 4 workload), dibuka sekali setelah semua training selesai. equal_F dan equal_B P11 dievaluasi ulang (checkpoint beku).
- RQ (format sama dengan P11 per algoritma): tiap MOEA vs equal_F (RQ1-gaya) dan vs random (RQ2-gaya); peringkat 5 algoritma (uji
  Friedman + post-hoc Holm); kualitas front (hypervolume/IGD⁺ dari evaluasi ulang); kurva anytime; biaya compute.
- Analisis daya uji dari effect size pilot; n ditetapkan sebelum lock.
- Estimasi biaya: 5 × 20 × 90 slot × m model. Dengan m = 2 ≈ 525 CPU-jam (≈ 2 hari wall); m = 4 ≈ 1.050 CPU-jam (≈ 4 hari wall).
  Ditambah training final dan evaluasi (≈ 0,5 hari).

## 9. Opsi: lingkungan dengan trade-off nyata (tidak dijalankan di pilot ini)

Kalau G1 gagal, bobot mungkin tidak penting karena lingkungan sekarang hampir tidak punya trade-off (kebijakan terbaik unggul di kelima biaya;
zE hampir konstan). Varian yang masuk akal secara fisik: biaya/kuota cloud per offload, baterai IoT, atau fog yang bisa tidur saat idle.
Ini memerlukan perubahan config/simulator Java (JAR baru, config hash baru, validasi ulang P02–P06 untuk varian), sehingga perlu
rancangan dan keputusan tersendiri. Varian harus dimotivasi skenario nyata, didaftarkan sebelum data, dan hasil lingkungan utama tetap
dilaporkan.

## 10. Implementasi yang dibutuhkan

- `research_v2/p14_traces.py`: split `dev_validation` (dan nantinya `moea_test`), pola sama dengan `p13_traces.py`.
- `research_v2/p14.py`: orkestrator pilot (Q1, Q2, Q3, laporan, gerbang), job paralel dengan pola P13; launcher `run_p14_pilot.sh`.
- Adapter search: NSGA-III, MOEA/D, SPEA2 lewat ask/tell pymoo dengan repair simpleks, populasi awal bersama, 90 slot.
- Tes unit: generator `dev_validation`, penyetaraan populasi/slot, determinisme search, ICC dan Spearman-Brown pada data sintetis.
- Smoke run ujung ke ujung dengan budget kecil sebelum pilot.

## 11. Keputusan yang perlu diambil sebelum implementasi

1. Bobot Q1 (§4) dan ambang gerbang G1–G3 (§6) diterima atau diubah.
2. Konfigurasi MOEA (§5): populasi 15 dan 90 slot; MOEA/D dengan PBI.
3. Kebijakan log keputusan pilot (§7): 10.240 baris pertama per run.
4. Urutan dengan P13: pilot P14 dulu (≈ 7,5 jam), P13 setelahnya, atau sebaliknya.

## 12. Keputusan (20 November 2026) dan tambahan setelah tinjauan literatur

Keputusan §11 diterima seluruhnya: bobot Q1 dan gerbang G1–G3, populasi 15 / 90 slot / MOEA/D-PBI, log keputusan 10.240 baris pertama
per run, **pilot P14 dijalankan sebelum P13**.

Posisi dalam paper (laporan `reports/Research gap EC bobot reward PPO.md`): framing utama adalah hasil compute-matched (RQ3 P11: melatih
lebih lama mengalahkan search bobot). Benchmark MOEA berfungsi sebagai **uji ketahanan**: apakah hasil nol tetap berlaku untuk NSGA-III,
MOEA/D dan SPEA2. Hasil G1 gagal tetap informatif (bukti diagnosis); yang batal hanya benchmark MOEA penuh.

Tambahan:
1. **Seleksi dengan re-evaluasi elite** (obat winner's curse; Rakshit dkk. 2017, Branke dkk.): pada setiap search, 3 kandidat front
   dengan D terendah dilatih ulang dengan 2 seed baru dan dinilai pada 20 trace search yang sama; terpilih = rata-rata 4 model terendah.
   Dibandingkan dengan aturan P11 (D minimum langsung) pada search yang sama, sehingga biaya tambahan hanya 6 model per search.
2. **Kualitas sebenarnya pada trace independen:** bobot terpilih (kedua aturan) dan equal dilatih 4 seed baru, dinilai pada 80 trace
   `dev_validation` yang tidak dipakai search (id 40005–40024).
3. **Kurva performa terhadap compute** (deskriptif di pilot, wajib di benchmark penuh): D sebenarnya vs keputusan training total, dengan
   PPO-equal dilatih lebih lama sebagai pembanding (Q1-4F menyediakan titik 4 × F).
4. **Ekuivalensi (TOST) dan redundansi objektif (PCA / korelasi lima biaya)**: dihitung deskriptif di pilot; ambang ekuivalensi untuk
   benchmark penuh ditetapkan sebelum lock benchmark dari distribusi pilot.

Catatan implementasi: MOEA/D standar (pymoo 0.6.2) memberi 15 kandidat awal lalu 1 offspring per ask (pembaruan per offspring, setia pada
algoritma asli); NSGA-II, NSGA-III dan SPEA2 memberi 15 per generasi. Semua deterministik dengan seed sama (diuji). Penjadwal job dinamis
menjalankan semua search bersamaan.

**Pengingat (dikerjakan setelah P14):** file Jupyter di `research_v2/` (`Untitled.ipynb`, `.ipynb_checkpoints/*.py`) masuk ke hash sumber
lock P13 (`research_v2/**/*.py`) dan memicu peringatan lock v0.4; autosave saat P13 berjalan akan menghentikan pipeline. Perbaiki
(kecualikan `.ipynb_checkpoints`/pindahkan notebook) sebelum `./run_p13.sh`. Hal yang sama berlaku untuk P14: hash sumber P14 hanya
mencakup file P14 yang eksplisit.
