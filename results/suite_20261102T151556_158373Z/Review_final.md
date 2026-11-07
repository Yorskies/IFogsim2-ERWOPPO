# Review percobaan final ERWO-PPO

Review atas `suite_20261102T151556_158373Z`. Data sumber tidak diubah.

## Kesimpulan

Eksekusi dan agregasi hasil lengkap. ERWO-PPO membantu performa PPO pada anggaran akhir rendah, namun pada 100.000 timestep keunggulannya atas PPO-Equal kecil dan baseline Least Fog masih sangat kuat. Hasil ini belum mendukung klaim superioritas umum ERWO-PPO pada empat profil beban yang berbeda.

## Audit kelengkapan

- 80/80 run selesai, 16 kelompok konfigurasi, lima seed per kelompok.
- 56,000 baris episode benchmark: 80 run × 7 metode × 100 episode.
- 400 file model tersedia dan tidak kosong. File model tidak dideserialisasi dalam audit.
- Agregat per-run cocok dengan CSV episode; agregat antar-seed cocok dengan summary.json: True.
- Konfigurasi log mewajibkan Java; log diperiksa untuk exception/fallback. Ini bukan verifikasi mandiri bahwa proses server memakai bytecode terbaru atau event engine CloudSim.
- Fingerprint source suite cocok dengan source lokal: True.

## 100.000 timestep: ERWO-PPO versus PPO-Equal dan Least Fog

| Workload | Violation ERWO (%) | PPO-Equal (%) | Least Fog (%) | QoS ERWO | PPO-Equal | Least Fog |
|---|---:|---:|---:|---:|---:|---:|
| light | 17.85 | 18.00 | 17.44 | 33.93 | 33.86 | 34.45 |
| moderate | 17.66 | 17.78 | 17.34 | 68.42 | 68.14 | 69.13 |
| heavy | 18.16 | 18.46 | 17.75 | 102.03 | 101.15 | 103.50 |
| dynamic | 17.66 | 17.78 | 17.34 | 68.42 | 68.14 | 69.13 |

Perbaikan violation ERWO terhadap PPO-Equal pada 100.000 timestep hanya sekitar 0,12–0,30 poin persentase. Least Fog memiliki skor latensi, violation, load imbalance, dan QoS lebih baik dari ERWO pada seluruh workload di anggaran ini. Efisiensi energi mendekati sama, dengan trade-off kecil pada beberapa workload.

## Dampak anggaran training

| Workload | ERWO violation 5k (%) | PPO violation 5k (%) | ERWO violation 25k (%) | ERWO violation 50k (%) | ERWO violation 100k (%) |
|---|---:|---:|---:|---:|---:|
| light | 41.36 | 68.97 | 19.04 | 18.20 | 17.85 |
| moderate | 48.05 | 64.26 | 19.33 | 17.96 | 17.66 |
| heavy | 52.32 | 73.64 | 19.85 | 18.83 | 18.16 |
| dynamic | 48.05 | 64.26 | 19.33 | 17.96 | 17.66 |

Pada 5k, penurunan violation ERWO dibanding PPO-Equal sekitar 16,21–27,61 poin persentase. Perbedaan mengecil pada 25k dan mendekati plateau pada 50k–100k. Pada 50k, PPO-Equal lebih baik daripada ERWO pada light dan heavy untuk beberapa metrik, jadi manfaat optimasi bobot tidak konsisten pada semua anggaran.

## Temuan metodologi yang harus dinyatakan

1. **Moderate dan dynamic bukan dua kondisi independen.** Semua 20 pasangan budget/seed memiliki benchmark identik (kecuali timing), bobot identik, dan CSV episode identik: 20/20. Source Java hanya membedakan panjang episode: light 50, moderate/dynamic 100, heavy 150. Distribusi task tidak berubah menurut nama workload. Sebut hasil ini sensitivitas panjang episode, atau implementasikan profil laju kedatangan/intensitas task berbeda dan ulangi eksperimen.

2. **Anggaran total ERWO lebih besar.** Setiap pencarian menjalankan 40 training kandidat, masing-masing diminta 5000 timestep, sebelum training akhir. Biaya pencarian nominal 200.000 timestep belum termasuk evaluasi. Pada budget akhir 5k, total training nominal ERWO menjadi 205k (41× PPO-Equal); pada 100k menjadi 300k (3×). Klaim efisiensi sampel harus menghitung biaya tersebut. PPO membulatkan rollout, sehingga jumlah aktual sedikit lebih besar.

3. **Skor belum satuan fisik.** Skor latensi, energi, dan QoS merupakan jumlah sub-reward per episode. Normalisasi per langkah dibutuhkan untuk perbandingan lintas panjang episode; skor >100 pada heavy bukan efisiensi >100%. Latensi dan energi tersebut tidak boleh diberi label ms atau Joule.

4. **Lima seed training membatasi inferensi.** 100 episode per model bukan 100 seed training. Audit melakukan uji paired sign-flip dua sisi pada lima rata-rata seed untuk ERWO versus PPO-Equal (80 pasangan konfigurasi/metrik): p minimum 0.0625; tidak ada p < 0,05 bahkan sebelum koreksi multipel. Ini bukan bukti kesetaraan; daya uji dengan lima seed rendah. Uji per-episode pada satu model menjawab pertanyaan berbeda dan tidak membuktikan keunggulan antar-training.

5. **Baseline harus tetap dibahas.** Least Fog berbiaya inferensi sekitar 0,0025 ms, sedangkan ERWO sekitar 0,095–0,098 ms (sekitar 38–39× lebih lambat pada 100k). DDPG memiliki variasi antar-seed besar; perbandingan terhadap baseline yang belum stabil tidak cukup untuk menyimpulkan kualitas optimasi reward.

6. **Validasi kandidat sangat pendek.** Pemilihan bobot menggunakan tiga episode validasi (seed 42–44), sedangkan pengujian menggunakan 100 episode (1000–1099). Ini menjaga pemisahan validation/test, tetapi estimasi kualitas kandidat berpotensi bervariansi tinggi. Tidak ada eksperimen lintas anggaran training kandidat dalam suite ini.

7. **Metadata minor.** 80/80 result.json masih menyimpan status `running` dari snapshot sebelum finalisasi. Manifest, output model, serta summary sudah complete dan konsisten. Ini cacat pencatatan status, bukan bukti training belum selesai.

## Biaya pencarian

Total pencarian NSGA-II yang tercatat: 3.58 jam. Total training akhir ERWO saja: 0.79 jam. Keduanya tidak mencakup semua biaya training baseline, evaluasi, startup, atau waktu total batch. Bobot yang sama untuk workload/seed yang sama berulang pada empat anggaran karena pencarian menggunakan konfigurasi dan seed identik; itu perilaku yang diharapkan, bukan bukti file tertukar.

## Klaim yang didukung dan keputusan

Klaim yang didukung: optimasi bobot dapat memperbaiki performa akhir PPO pada budget training akhir rendah dalam model offloading ini, dengan biaya pencarian tambahan. Pada 100k, manfaat terhadap PPO-Equal kecil dan tidak terbukti signifikan antar-seed pada uji audit.

Jangan menyatakan: superioritas atas semua baseline, empat pola kedatangan berbeda, efisiensi komputasi total yang lebih baik, atau validasi simulator iFogSim2 berbasis event penuh. Server socket yang dipakai adalah engine Java custom; source belum menjalankan FogDevice/CloudSim event simulation.

Hasil ini layak diarsipkan sebagai batch final konfigurasi saat ini. Untuk klaim publikasi yang lebih luas, prioritasnya memperbaiki definisi workload, menambah pembanding beranggaran total sama, dan memperbanyak seed training; menaikkan timestep saja tidak mengatasi batasan tersebut.

Rincian audit yang dapat diperiksa ulang tersimpan di `review_audit.json`.
