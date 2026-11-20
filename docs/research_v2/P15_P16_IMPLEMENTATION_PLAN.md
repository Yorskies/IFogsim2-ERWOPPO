# P15–P16 — benchmark penuh MOEA dengan noise dikurangi (P15) dan evaluasi akhir (P16): implementation plan

Status: **rancangan disetujui (20 November 2026); implementasi P15.0–P15.2 berjalan.** Keputusan §8: lihat §9.
Basis: protokol v0.4 (lock `63d07e43…`), P11, P12, pilot P14 (Q1/Q2 selesai 20 November 2026, Q3 belum dijalankan),
[catatan winner's curse](WINNERS_CURSE_P11_P14.md), [laporan literatur](../../reports/Research%20gap%20EC%20bobot%20reward%20PPO.md).

## 0. Keputusan peneliti dan deviasi dari gerbang P14 (dicatat sebelum data P15)

Aturan gerbang pilot P14 (§6 rancangan P14) menyatakan benchmark MOEA penuh tidak dilanjutkan bila G1 gagal di F dan 4 × F. Hasil pilot:
G1 gagal (ICC 0,26 di F, 0,19 di 4 × F; keuntungan tervalidasi-silang −0,054 dan +0,007), G2 gagal (12 seed per kandidat untuk
reliabilitas 0,8 di F; tak tercapai di 4 × F), G3 belum dinilai (Q3 belum dijalankan).

Peneliti memutuskan (20 November 2026) **tetap menjalankan benchmark penuh dengan evaluator yang noise-nya dikurangi**, sebagai uji paling
kuat yang adil bagi keempat MOEA, dan **menganalisis apa pun hasilnya setelah P16 selesai**. Ini dicatat sebagai **deviasi beralasan dari
aturan gerbang P14**, diambil sebelum ada data P15/P16. Alasan: (1) pertanyaan reviewer "apakah kegagalan hanya milik NSGA-II atau milik
evaluator yang terlalu bising" hanya terjawab tuntas jika keempat MOEA diuji dengan evaluator yang reliabel; (2) hasil null dengan evaluator
reliabel adalah bukti lebih kuat daripada null P11. Prediksi yang dicatat sebelum data: selisih antar-MOEA kecil (≤ 0,01 D), dan tidak ada
MOEA yang jauh mengalahkan equal (batas atas manfaat menurut Q1 ≈ 0,01–0,02 D).

## 1. Tujuan dan pertanyaan riset

| Kode | Pertanyaan | Keluarga |
|---|---|---|
| H1a–H1d | NSGA-II / NSGA-III / MOEA/D / SPEA2 (bobot terpilih, PPO final pada F) vs PPO-equal pada F | primer (Holm, 4 uji) |
| H2a–H2d | setiap MOEA vs random search, evaluator dan budget identik | primer (Holm, 4 uji) |
| H3 | peringkat 5 metode search (Friedman) | sekunder |
| H4a–H4e | setiap metode search vs PPO-equal dilatih lebih lama (checkpoint `equal_B` P11, 19,6 jt keputusan, compute lebih kecil dari search P15) | sekunder (Holm) |
| H5 | bobot tetap `lean_zD` (dari pilot, tanpa search) vs equal pada F | sekunder, tunggal |
| E1 | ekuivalensi (TOST) H1 dengan margin δ terdaftar | sekunder |
| D1–D4 | deskriptif: winner's curse (skor search vs D akhir), kurva anytime, kualitas front (hypervolume, IGD⁺), biaya compute | deskriptif |

Orientasi: selisih = D(pembanding) − D(perlakuan); positif = perlakuan lebih baik. Unit analisis: outer run (n = 20), nilai per metode per
outer = rata-rata D dari 4 seed model final (§4). Uji: sign-flip exact berpasangan, CI 95 % bootstrap crossed (outer × trace), dz.
Non-signifikan = bukti tidak cukup, bukan kesetaraan; kesetaraan hanya lewat E1.

## 2. Pengurangan noise: apa yang diubah dan kenapa (berbasis data P11/P14)

| Sumber noise | Bukti | Tindakan di P15/P16 |
|---|---|---|
| Training PPO (seed) pada skor kandidat | P11: korelasi 2 model bobot sama 0,11; P14 Q2: reliabilitas 2 seed 0,40 | **4 seed per kandidat** (reliabilitas ≈ 0,57) + **resampling adaptif elite**: 3 kandidat terbaik setiap generasi mendapat 8 seed tambahan (total 12; reliabilitas ≈ 0,8 sesuai Q2) |
| Trace evaluasi kandidat | P14 Q2: 20 vs 100 trace → 0,39 vs 0,40 | 20 trace `dev_validation` (40000–40004) cukup; tidak ditambah |
| Seleksi akhir dari skor bising (winner's curse) | P11: 0,174 → 0,249, prediksi shrinkage 0,240–0,256 | **seleksi hanya di antara kandidat ber-12 seed** (elite), bukan minimum mentah |
| Training model final (seed) | SD seed F ≈ 0,061 (P14) | **4 seed model final per metode per outer**, D akhir = rata-rata |
| Training lebih panjang | P14: 4 × F mengecilkan noise dan sinyal sekaligus, reliabilitas peringkat ≈ 0 | **budget kandidat tetap F** |
| Pembanding | — | equal_F dan `lean_zD` juga 4 seed final, stream dan seed sama (bilangan acak bersama) |

Batas yang dicatat: evaluator ini menaikkan reliabilitas peringkat kandidat, tetapi tidak menciptakan sinyal; Q1 memberi batas atas manfaat
≈ 0,01–0,02 D.

## 3. P15 — benchmark penuh

**Metode:** NSGA-II, NSGA-III, MOEA/D (standar, per offspring, PBI), SPEA2 (dengan perbaikan bug state bersama pymoo), random search.
Konfigurasi sama dengan P14 (`p14_search.py`): populasi 15 (= 15 arah referensi Das-Dennis), **90 slot**, populasi awal sama per outer
(equal + 14 Dirichlet), operator SBX/PM P11, repair simpleks.

**Outer run:** 0–19 (stream training `train_candidate`, repeat = indeks seed mod 2). Seed model kandidat: basis baru `p15_base = 700000`,
seed = basis + 100 × outer + j (j = 0…11), **sama untuk semua kandidat dan algoritma dalam satu outer** (bilangan acak bersama).

**Evaluator kandidat:** untuk setiap kandidat, 4 model PPO (j = 0–3), budget F = 102.400, learner v0.3, evaluasi deterministik pada 20 trace
`dev_validation` 40000–40004. Objektif MOEA = rata-rata lima biaya makro 4 model.

**Resampling adaptif elite:** setelah setiap generasi (NSGA-II/III, SPEA2, random: tiap 15 kandidat; MOEA/D: tiap 15 offspring), 3 kandidat
dengan D terendah di antara semua kandidat yang sudah dievaluasi dan belum ber-12 seed mendapat 8 model tambahan (j = 4–11). Nilai yang
dipakai MOEA untuk kandidat itu diperbarui ke rata-rata 12 model hanya untuk seleksi akhir; nilai yang sudah diserahkan ke algoritma tidak
diubah (menghindari perilaku pymoo yang tidak terdefinisi).

**Seleksi akhir (terdaftar):** di antara kandidat ber-12 seed, D (rata-rata 12 model) terendah; seri → slot lebih awal. Aturan P11
(minimum mentah) dicatat juga untuk analisis winner's curse (D2), bukan untuk uji primer.

**Biaya:** per search ≈ 90 × 4 + 6 × 3 × 8 = 504 model; populasi awal dipakai bersama 5 algoritma (hemat 15 × 4 × 4 per outer).
Total ≈ 100 search × 504 − 4.800 ≈ **45.600 model × ≈ 95 s ≈ 1.200 CPU-jam ≈ 4,2 hari wall (12 worker)**.

**Penyimpanan:** pola P14 (baris episode lengkap, 10.240 baris keputusan pertama per run, model.zip) ≈ 3–4 MB per model → ≈ 150–180 GB.
Sisa disk 310 GB. **Keputusan yang diperlukan:** setujui, atau pangkas log keputusan menjadi 0 baris untuk model kandidat (≈ 60–80 GB).

## 4. P16 — evaluasi akhir

**Model final:** untuk setiap outer 0–19 dan setiap perlakuan, **4 model PPO dari awal** pada F, stream `train_final` outer r, seed
`p16_base = 800000` + 10 × outer + k (k = 0–3), sama untuk semua perlakuan dalam satu outer.

| Perlakuan | Bobot | Model |
|---|---|---|
| NSGA-II, NSGA-III, MOEA/D, SPEA2, random | bobot terpilih P15 (outer yang sama) | 4 × 20 × 5 = 400 |
| equal_F | 0,2 × 5 | 80 |
| `lean_zD` | 0,6 pada zD, 0,1 lainnya | 80 |
| equal_B (P11) | checkpoint P11 beku, 19,6 jt keputusan | 0 (evaluasi saja, 20) |

**Split test baru tersegel `p16_test`:** 100 trace × 4 workload (id 50000–50099), mekanisme `p13_traces` (generator identik, seed stream
memuat label split). Manifest input (hash payload) dibuat saat lock P15; evaluasi hanya setelah semua model final selesai dan catatan
`P16_TEST_OPENED.json` ditulis.

**Biaya:** 560 model × (≈ 80 s training + ≈ 160 s evaluasi 400 trace) + 20 evaluasi equal_B ≈ 38 CPU-jam ≈ **3,5 jam wall**.

**Daya uji (dicatat sebelum data):** dengan 4 seed final, SD per outer ≈ 0,03; SD selisih berpasangan perkiraan 0,03–0,05. Untuk efek
0,013 (batas atas Q1 di F) dz ≈ 0,26–0,43 → power n = 20, α 0,0125 (Holm, 4 uji) ≈ 0,10–0,35. Untuk efek 0,005: < 0,10.
**Hasil null sangat mungkin**; desain ini memaksimalkan kejelasan jawaban (E1 TOST) dalam anggaran yang wajar.

## 5. Analisis (P16, didaftarkan di lock P15)

- Primer H1, H2: sign-flip exact (20 outer), Holm per keluarga, α 0,05; CI bootstrap crossed (outer × trace, 10.000 draw, seed config).
- H3: Friedman 5 metode (blok = outer), post-hoc Wilcoxon berpasangan + Holm.
- H4, H5: sign-flip exact, Holm dalam keluarga sekunder.
- E1: TOST untuk setiap H1 dengan margin **δ = 0,02 D** (≈ selisih RQ1 P11, ≈ 8 % D equal_F) — **keputusan yang diperlukan**.
- D1 winner's curse: skor search kandidat terpilih (4 dan 12 model) vs D akhir test; prediksi shrinkage.
- D2 aturan seleksi: kandidat yang akan dipilih aturan P11 (minimum skor mentah) dibandingkan dengan kandidat terpilih 12 seed — seberapa sering berbeda dan selisih skor 12 seed keduanya (deskriptif; tanpa model final tambahan).
- D3 kurva anytime: D minimum (skor 4 model) vs slot, per algoritma; hypervolume dan IGD⁺ front akhir (skor search).
- D4 compute: keputusan training dan waktu jam per metode, termasuk rasio terhadap equal_B.
- Metrik fisik (energi J, pelanggaran deadline, reliabilitas) untuk H1/H2, analisis redundansi objektif (PCA lima biaya).
- Kode analisis P10/P11 (`analysis/stats.py`) dipakai tanpa perubahan untuk sign-flip, bootstrap dan Holm.

## 6. Tahap implementasi

| Tahap | Isi | Kriteria selesai | Estimasi kerja |
|---|---|---|---|
| **P15.0** | Rancangan ini disetujui; keputusan §8; perbaikan pengingat notebook Jupyter (hash sumber mengecualikan `.ipynb_checkpoints`, notebook dipindah) | keputusan tercatat | — |
| **P15.1** | `research_v2/p15.py`: orkestrator search berbasis P14 (`p14_search.Search`, pool job ber-hash konten, run_job PPO) + evaluator 4 seed + resampling adaptif elite + seleksi 12 seed; `run_p15.sh` | unit test (jumlah model per search, aturan elite, determinisme replay, seleksi); smoke budget kecil ujung ke ujung | ½–1 hari |
| **P15.2** | `research_v2/p16_traces.py` (split `p16_test`), `research_v2/p16.py` (training final 4 seed, pembukaan test, evaluasi, analisis H1–H5/E1/D1–D4, laporan, tabel klaim); `run_p16.sh` | unit test (segel test, pairing seed, TOST, Friedman); smoke | ½–1 hari |
| **P15.3** | **Lock P15**: hash sumber P15/P16 + config + JAR, konfigurasi algoritma, evaluator, seed, aturan seleksi, hipotesis, margin δ, manifest `p16_test`, deviasi §0 | lock terverifikasi; commit | 1 jam |
| **P15.4** | Jalankan P15 (search 100 × 90 slot) | 100 search selesai; 0 kegagalan; determinisme replay lulus | **≈ 4,2 hari** |
| **P16.1** | Training final 560 model; equal_B dievaluasi | semua model selesai; hash cocok | ≈ 1,5 jam |
| **P16.2** | Buka `p16_test` sekali; evaluasi 580 model | 0 error; reward identity | ≈ 2 jam |
| **P16.3** | Analisis terdaftar + laporan + tabel klaim; update dokumen paper | laporan direkonstruksi dari data mentah | ≈ 1 jam |

Total compute ≈ **4,5 hari**; total dengan implementasi ≈ **6 hari**. P13 (DQN/DDPG/Q-tabular) dijalankan setelah P16 atau di sela
bila worker tersedia (tidak bersamaan: keduanya memakai 12 worker).

## 7. Risiko dan mitigasi

| Risiko | Mitigasi |
|---|---|
| Disk penuh (≈ 150–180 GB) | pemeriksaan disk di preflight; opsi log keputusan 0 baris untuk kandidat |
| Proses terhenti (container restart) | job ber-hash konten + replay deterministik → resume tanpa kehilangan |
| MOEA/D berurutan memperlambat akhir run | penjadwal dinamis; MOEA/D 20 search berjalan paralel |
| Perubahan file sumber selama run | lock P15 memverifikasi hash di setiap job; pengecualian notebook |
| Bug pustaka (state bersama pymoo) | instance operator/survival baru per search; test regresi kebocoran state (sudah ada) |
| Power rendah untuk H1/H2 | dicatat sebelum data (§4); E1 TOST memberi jawaban ekuivalensi |
| Godaan mengubah analisis setelah melihat hasil | semua uji, margin, aturan seleksi dikunci di lock P15 sebelum search |

## 8. Keputusan yang diperlukan sebelum P15.1

1. Evaluator: 4 seed per kandidat + 8 seed tambahan untuk 3 elite per generasi (≈ 4,2 hari) — atau 12 seed untuk semua kandidat
   (≈ 10 hari), atau 6 seed + elite (≈ 5,5 hari).
2. Margin ekuivalensi E1: δ = 0,02 D (usulan) atau nilai lain.
3. Arm tambahan `lean_zD` (H5) di P16: ya (usulan, biaya +80 model) atau tidak.
4. Log keputusan model kandidat: 10.240 baris (≈ 150–180 GB) atau 0 baris (≈ 60–80 GB).
5. Q3 pilot P14: dilewati (P15 menggantikannya) — usulan — atau dijalankan dulu sebagai uji implementasi (≈ 5–6 jam).

## 9. Keputusan (20 November 2026)

1. **Evaluator: 4 seed per kandidat + 8 seed tambahan untuk 3 elite per generasi** (total 12 untuk elite), ≈ 4,2 hari.
2. **Margin ekuivalensi E1: δ = 0,02 D.**
3. **Arm `lean_zD` (H5) disertakan** di P16.
4. **Log keputusan:** model kandidat P15 menyimpan **1.024 baris keputusan pertama** (sampel audit) + seluruh baris episode training
   (audit reward/biaya per episode), model, kurva belajar dan baris evaluasi; ukuran terukur di pilot: ≈ 1,6 MB per model → ≈ 75 GB untuk
   P15. Model final P16 menyimpan **10.240 baris** (≈ 5,7 MB per model → ≈ 3 GB). Sisa disk saat keputusan: 309 GB.
5. **Q3 pilot P14 dilewati**; P15 menggantikannya. G3 P14 tidak dinilai; uji implementasi dan waktu dilakukan lewat smoke run P15.
