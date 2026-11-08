# P07 ulang — instrumentasi dan ablation lambda

Status: **eksekusi dan audit teknis selesai; hasil ablation negatif**. Protokol diagnostik `P07-lambda-ablation-1` dibekukan sebelum eksekusi. Spesifikasi utama v0.2 tetap utuh; tidak ada adopsi otomatis hyperparameter baru.

## Desain dan implementasi

- Dua kondisi: lambda=0,95 vs 1,0. Gamma=1 dan seluruh parameter lain tetap.
- Seed outer 100/101/102, repeat 0, bobot equal, 10.240 keputusan/model, CPU satu thread.
- Dua smoke 512 keputusan, enam pilot, serta dua lintasan prefix panjang 10.752.
- Tiap pilot dievaluasi deterministik pada checkpoint 512 dan 10.240, lalu sampling pada checkpoint akhir sebagai diagnosis berlabel.
- Tidak ada akses test/validation konfirmatori. Trace training dan 20 payload pilot validation identik antar-kondisi. Model dimulai dari bobot awal identik.

`learning_instrumentation.py` menyimpan observasi, aksi, reward, value, advantage mentah, return, episode_starts, log-prob lama, last-value/done bootstrap, dan gamma/lambda dalam NPZ sebelum update. Setiap minibatch mencatat norm gradient sebelum/sesudah clipping; tiap update mencatat jumlah langkah optimizer, clip fraction rasio PPO, dan perubahan parameter. Rumus GAE/return dihitung ulang dari buffer tersimpan dan diperiksa. Advantage mentah adalah sebelum normalisasi per-minibatch SB3.

Update tetap memakai PPO SB3 yang terpasang. Pembungkus clipping memanggil fungsi asli dengan parameter yang sama; tidak ada salinan algoritma optimizer atau reward baru.

### Config simulator dan learner

Config/JAR simulator asli dipertahankan dan divalidasi dengan handshake yang sama. File spesifikasi learner terpisah memuat **seluruh** konfigurasi PPO efektif, hash config simulator, hash full effective config, serta versi protokol diagnostik. Validasi menolak perubahan selain gae_lambda. Ini memisahkan treatment Python-only dari identitas simulator/trace, tanpa memalsukan hash JAR atau memodifikasi default.json. Setiap run mengarsipkan effective_learner_config.json, learner_spec.json, manifest, source hash dan environment freeze.

## Hasil utama: D deterministik akhir

Lebih kecil lebih baik.

| Seed | lambda 0,95 | lambda 1,0 | Selisih 1,0 − 0,95 |
|---|---:|---:|---:|
| 100 | 0.362634 | 0.694525 | +0.331891 |
| 101 | 0.670584 | 0.705266 | +0.034681 |
| 102 | 0.474897 | 0.512229 | +0.037332 |

**Tidak ada dari tiga seed yang membaik pada lambda=1,0**; mean selisih D +0.134635, median +0.037332. Ini perbandingan deskriptif tiga pasangan, bukan klaim signifikansi atau generalisasi.

Skor D sampling akhir juga memburuk pada ketiga pasangan, jadi hasil negatif tidak terbatas pada satu mode evaluasi:

| Seed | Sampling lambda 0,95 | Sampling lambda 1,0 |
|---|---:|---:|
| 100 | 0.408303 | 0.418063 |
| 101 | 0.450163 | 0.480629 |
| 102 | 0.422692 | 0.461452 |

Tidak semua metrik fisik memburuk: macro reliability r102 naik dari 0,4950 menjadi 0,6020, tetapi biaya imbalance dan kompromi keseluruhan memburuk. Laporan mesin menyimpan lima biaya dan metrik per workload; D bukan pengganti seluruh trade-off.

## Temuan instrumentasi

| Seed | Median std advantage 0,95 / 1,0 | Median norm gradient mentah 0,95 / 1,0 | Minibatch clipped 0,95 / 1,0 |
|---|---|---|---|
| 100 | 0.256 / 5.515 | 1.04 / 67.12 | 87.9% / 100.0% |
| 101 | 0.298 / 6.220 | 1.12 / 76.41 | 92.0% / 100.0% |
| 102 | 0.349 / 6.610 | 1.16 / 76.63 | 90.5% / 100.0% |

Semua 800 minibatch pada setiap pilot lambda=1 terkena global clipping pada batas 0,5. Gradient mentah jauh lebih besar, namun hasil tetap finite. Ini perubahan kondisi optimisasi yang nyata, bukan gradient NaN atau rollout yang hilang.

### Pemeriksaan actor dan critic pada input yang sama

Diagnosis tambahan menghitung gradient pada **policy awal dan keseluruhan buffer pertama 512 sampel** yang identik, tanpa optimizer step atau rollout baru. Ini bukan rekonstruksi urutan minibatch aktual.

| Seed | Norm critic tertimbang / norm actor+entropy pada 0,95 | Rasio pada 1,0 |
|---|---:|---:|
| 100 | 28.1 | 203.7 |
| 101 | 22.6 | 346.5 |
| 102 | 18.1 | 202.2 |

Skala gradient critic jauh lebih dominan ketika lambda=1. Target value/return menjadi lebih lebar sementara arsitektur, vf_coef, learning rate dan global clipping tetap sama. Ini mendukung prioritas diagnosis skala critic dan coupling melalui clipping.

**Batas interpretasi:** norm dominan dan clipping tidak membuktikan actor berhenti belajar. Adam melakukan rescaling per parameter, dan parameter policy memang berubah. EV, return std dan value loss pada dua lambda juga memakai target GAE masing-masing; nilainya bukan ukuran akurasi terhadap common ground truth. Mengubah lambda memperpanjang propagasi sekaligus menaikkan variasi target, sehingga eksperimen ini tidak mengisolasi seluruh mekanisme tersebut satu per satu.

### Pemusatan aksi tetap ada

Lambda=1 r100 memilih F4 sekitar 93–98% tugas; r101 didominasi F1 terutama heavy (~82%); r102 didominasi F2 terutama heavy (~66%). Tujuan dominan berubah, tetapi policy adaptif yang baik belum terbentuk. Entropy sampling training masih tinggi. Hal ini konsisten dengan perbedaan closed-loop sampling versus argmax yang ditemukan sebelumnya.

## Audit validitas dan reproduksibilitas

- **22 tes lulus**, 0 failure/error/skip: GAE hitungan tangan, terminal/partial bootstrap, clipping pasif, guard learner satu faktor, reward dan transformasi.
- Semua tiga baseline lambda=0,95 identik dengan model lama pada checkpoint 512 dan 10.240: policy, optimizer, RNG dan counter/stream. Jadi pencatatan baru tidak mengubah hasil baseline.
- Kedua kondisi memakai initial policy dan stream trace identik. Buffer pertama memiliki observasi/aksi/reward/value/log-prob/bootstrap identik; advantage berbeda sesuai treatment lambda.
- Reward/terminal drain, budget aktual, hash checkpoint dan seluruh GAE buffer tersimpan lulus audit.
- Smoke dan checkpoint 512 pilot identik per kondisi. Prefix 10.240 pada run 10.752 identik dengan pilot berhenti di 10.240 untuk kedua lambda.
- **Tidak ada sertifikasi prefix F=102.400 untuk lambda=1**. Bukti prefix F lambda=0,95 sebelumnya tetap disimpan; ablation ini berskala pilot.

## Review ulang dan keputusan

Hipotesis bahwa lambda=0,95 adalah penyebab tunggal atau bahwa menggantinya menjadi 1 akan memperbaiki P07 **tidak didukung** oleh hasil ini. Ini tidak meniadakan masalah credit assignment: lambda=1 sekaligus mengubah variasi target dan interaksi actor/critic.

**Default tetap lambda=0,95.** Tidak ada perubahan diam-diam pada reward, skor D, simulator, test split atau protokol deployment. P07 ulang selesai sebagai eksperimen diagnostik dengan hasil negatif; policy yang memuaskan belum diperoleh. Pencarian besar P08 belum dijalankan.

Prioritas eksperimen berikutnya adalah meninjau **skala loss/target critic dan coupling global gradient clipping**, dengan faktor tunggal yang ditetapkan terlebih dahulu. Perbedaan sampling–argmax juga tetap perlu diperiksa. Jangan sekaligus mengubah lambda, vf_coef, reward dan metode evaluasi, karena penyebab perbaikan tidak dapat diidentifikasi. Tidak ada eksperimen tambahan tersebut yang dijalankan pada batch ini.

## Accounting

- Training baru: **83.968 keputusan** = 1.024 smoke + 61.440 enam pilot + 21.504 dua lintasan prefix.
- Evaluasi baru: **360 episode lengkap, 349.146 keputusan**.
- Diagnosis gradient full-buffer: 0 optimizer step dan 0 rollout baru.
- Seluruhnya biaya penelitian/pilot. Tidak ada hasil test konfirmatori atau p-value manfaat metode.

## Artefak dan reproduksi

- [protocol.json](protocol.json): rancangan dibekukan sebelum run.
- [ablation_verification.json](ablation_verification.json): audit dan metrik lengkap.
- [review_conclusions.json](review_conclusions.json): keputusan dan batas kesimpulan.
- [first_rollout_loss_decomposition.json](first_rollout_loss_decomposition.json): diagnosis gradient actor/critic.
- [validation_pairing.json](validation_pairing.json): payload evaluasi sama di semua mode/kondisi.
- [tests_verification.json](tests_verification.json): 22 tes terfokus.
- [paired_D.svg](paired_D.svg) dan [advantage_std.svg](advantage_std.svg): grafik standalone.

Reproduksi ke direktori baru; perintah run melakukan training:

```bash
venv/bin/python -m research_v2.lambda_ablation prepare --evidence-dir results/research_v2/P07_lambda_ablation_reproduced
venv/bin/python -m research_v2.lambda_ablation run --evidence-dir results/research_v2/P07_lambda_ablation_reproduced
```

Audit ulang tanpa training/evaluasi online:

```bash
venv/bin/python -m research_v2.lambda_ablation_report --evidence-dir results/research_v2/P07_lambda_ablation_1 --previous-evidence results/research_v2/P07_completion_20261107T205826Z
```

Model.zip, RNG dan seluruh NPZ tersedia lokal. Aturan Git lama mengabaikan model.zip/rng.pt; arsipkan direktori lengkap jika ingin mereproduksi dari artefak di mesin lain.
