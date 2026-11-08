# P07 — eksperimen satu faktor skala critic

Status: **selesai; audit teknis lulus, hasil kinerja campuran**. Protokol `P07-critic-scale-ablation-1` dibekukan sebelum eksekusi. Default tidak diubah dan P08 belum dimulai.

## Desain

Bandingkan vf_coef **0,5 vs 0,05** dengan lambda=0,95, gamma=1, global max_grad_norm=0,5, bobot equal, seed 100/101/102, repeat 0, budget 10.240 per model. Semua parameter lain, JAR, physics, initial policy dan trace identik.

Rasio gradient critic/actor pada diagnosis sebelumnya sekitar 18–28; penurunan koefisien sepuluh kali ditetapkan untuk menguji pengurangan ketimpangan tersebut. Hanya dua nilai ini diuji; bukan grid search. Guard learner menolak perubahan lambda, clipping atau parameter lain secara bersamaan.

Konfigurasi learner efektif diarsipkan terpisah dari config simulator/JAR yang tetap, dengan hash dan manifest per run. Instrumentasi dan PPO SB3 sama seperti ablation lambda sebelumnya.

Outcome utama: D deterministik pada 10.240, dilaporkan per seed dan mean/median pasangan. Sampling hanya diagnosis tambahan. Tidak ada klaim signifikansi dari tiga pasangan atau pemilihan seed terbaik.

## Hasil utama

D lebih kecil lebih baik.

| Seed | vf_coef=0,5 | vf_coef=0,05 | Selisih 0,05 − 0,5 | Hasil |
|---|---:|---:|---:|---|
| 100 | 0.362634 | 0.383460 | +0.020827 | memburuk |
| 101 | 0.670584 | 0.549553 | -0.121031 | membaik |
| 102 | 0.474897 | 0.474897 | +0.000000 | sama |

Mean D turun dari 0.502705 menjadi 0.469303 (sekitar 6.64%), tetapi **median selisih nol**. Satu seed membaik, satu memburuk, satu sama. Perbaikan mean didominasi r101; tidak boleh disimpulkan perbaikan konsisten.

| Seed | Macro reliability 0,5 → 0,05 | Biaya linear equal 0,5 → 0,05 |
|---|---|---|
| 100 | 0.8942 → 0.8647 | 0.2690 → 0.3103 |
| 101 | 0.3194 → 0.5406 | 0.6099 → 0.4964 |
| 102 | 0.4950 → 0.4950 | 0.3702 → 0.3702 |

R101 membaik pada D, reliability dan biaya linear; r100 memburuk pada ketiganya. Pada r102, kedua policy memilih cloud untuk seluruh tugas evaluasi, sehingga metrik sama persis walaupun parameter model berbeda.

Sampling diagnostik:

| Seed | D sampled 0,5 | D sampled 0,05 |
|---|---:|---:|
| 100 | 0.408303 | 0.373298 |
| 101 | 0.450163 | 0.395499 |
| 102 | 0.422692 | 0.427380 |

D sampled membaik pada r100/r101 dan memburuk sedikit pada r102. Perbedaan sampling–argmax tetap penting; hasil sampling tidak mengganti outcome utama.

## Mekanisme: penurunan dominasi critic dan clipping terjadi

Pada policy awal dan buffer pertama yang identik, advantage, return dan norm gradient actor tetap sama. Norm gradient critic tertimbang tepat menjadi 0,1 kali baseline (diperiksa numerik). Rasio critic/actor turun dari 18–28 menjadi 1,8–2,8. Diagnosis ini memakai keseluruhan buffer 512 sampel, bukan urutan minibatch aktual, tanpa optimizer step.

Pada update aktual sepanjang pilot:

| Seed | Minibatch clipped 0,5 / 0,05 | Median norm mentah 0,5 / 0,05 |
|---|---|---|
| 100 | 87.9% / 39.2% | 1.043 / 0.465 |
| 101 | 92.0% / 54.0% | 1.118 / 0.519 |
| 102 | 90.5% / 41.4% | 1.162 / 0.470 |

Aturan clipping tidak berubah: tetap global norm maksimum 0,5. Yang berubah adalah gradient dari loss critic. Jadi ini eksperimen **skala critic**, bukan eksperimen clipping-only. Hasil membuktikan mekanisme tersebut dapat dikurangi, tetapi penurunan clipping sendiri tidak menjamin D membaik.

## Gradient mentah berbeda dari pergerakan parameter aktual

Dari 19 pasangan checkpoint berurutan (512 → 10.240; update pertama tidak termasuk):

| Seed | Median delta L2 actor per rollout 0,5 / 0,05 | Median delta L2 critic 0,5 / 0,05 |
|---|---|---|
| 100 | 0.522 / 0.585 | 0.439 / 0.324 |
| 101 | 0.446 / 0.568 | 0.424 / 0.341 |
| 102 | 0.480 / 0.608 | 0.469 / 0.410 |

Actor bergerak lebih besar dan critic lebih kecil, tetapi perubahan critic **bukan sepuluh kali lebih kecil**. Adam melakukan rescaling per parameter; norm gradient mentah yang dominan tidak dapat langsung diterjemahkan menjadi dominasi update nyata atau klaim actor berhenti belajar. Ukuran L2 di atas juga bukan ukuran kualitas policy.

## Review perilaku dan critic

- R100 menjadi lebih tersebar ke lokal/F3/cloud, tetapi D dan reliability memburuk. Menyebarkan aksi saja bukan kriteria keberhasilan.
- R101 berubah dari F5 100% menjadi F5 sekitar 87–89% dengan sisanya lokal. Pengalihan sebagian trafik memperbaiki hasil seed ini, tetapi policy tetap sangat terkonsentrasi.
- R102 tetap always-cloud. Perbedaan bobot tidak terlihat pada keputusan argmax untuk trace evaluasi ini.
- Mean explained variance diagnostik turun pada semua seed: r100 -0,177 → -0,278; r101 -0,051 → -0,105; r102 0,045 → -0,044. Ini dihitung terhadap target GAE pada state masing-masing policy, bukan common-target true-value accuracy; jangan menjadikannya bukti kausal tunggal.
- Reward linear versus skor RMS D, observasi agregat, dan perubahan closed-loop sampling–argmax yang ditemukan sebelumnya tetap relevan. Tidak ada reward atau metrik yang diubah untuk memperbaiki hasil ini.

## Validitas

- 26 tes lulus, 0 failure/error/skip.
- Baseline vf_coef=0,5 identik dengan baseline lama pada checkpoint 512 dan 10.240 untuk seluruh seed: policy, optimizer, RNG, counter/stream.
- Initial policy dan stream training identik antar-kondisi. Seluruh buffer pertama, termasuk GAE/return, identik sebelum update.
- Payload 20 trace pilot validation identik di kedua kondisi, checkpoint dan mode.
- Buffer GAE, gradient finite/clipping bound, reward/terminal drain, budget aktual dan hash checkpoint lulus audit.
- Smoke/pilot prefix 512 serta pilot 10.240 vs lintasan 10.752 identik per kondisi.
- Tidak ada bukti prefix F=102.400 untuk vf_coef=0,05; tidak ada klaim reuse produksi.
- Tidak membuka split validation/test konfirmatori.

## Keputusan sebelum P08

**Eksperimen selesai dengan hasil campuran; vf_coef=0,05 belum diadopsi sebagai default.** Config utama tetap lambda=0,95 dan vf_coef=0,5. P08 belum dijalankan.

Temuan mempersempit diagnosis: skala critic/global clipping memengaruhi lintasan dan bisa membantu satu seed, tetapi bukan penjelasan tunggal atau perbaikan yang konsisten. Jangan melanjutkan tuning koefisien tanpa batas hanya untuk mengejar mean dari tiga seed.

Sebelum pencarian besar, prioritas review berikutnya adalah keputusan policy deployment sampling–argmax dan keselarasan reward linear dengan D. Bila meninjau clipping-only, desain satu faktor terpisah dengan vf_coef tetap; hasil eksperimen ini tidak mengidentifikasi efek clipping-only. Semua revisi perlu ditetapkan pada namespace pilot sebelum test dibuka. Tidak ada eksperimen tersebut yang dilakukan pada batch ini.

## Accounting dan artefak

Training baru **83.968 keputusan** = 1.024 smoke + 61.440 enam pilot + 21.504 dua lintasan prefix. Evaluasi baru **360 episode / 349.146 keputusan**. Diagnosis gradient dan pergerakan parameter memakai artefak tersimpan tanpa rollout/optimizer step baru. Semua biaya merupakan biaya penelitian/pilot.

- [protocol.json](protocol.json): rencana dibekukan sebelum run.
- [ablation_verification.json](ablation_verification.json): audit dan hasil lengkap.
- [review_conclusions.json](review_conclusions.json): keputusan ringkas.
- [first_rollout_loss_decomposition.json](first_rollout_loss_decomposition.json): gradient pada input yang sama.
- [actual_parameter_movements.json](actual_parameter_movements.json): perpindahan actor/critic aktual.
- [tests_verification.json](tests_verification.json): 26 tes.
- [paired_D.svg](paired_D.svg), [advantage_std.svg](advantage_std.svg): grafik.

Reproduksi ke direktori baru; run melakukan training:

```bash
venv/bin/python -m research_v2.critic_ablation prepare --evidence-dir results/research_v2/P07_critic_scale_reproduced
venv/bin/python -m research_v2.critic_ablation run --evidence-dir results/research_v2/P07_critic_scale_reproduced
```

Audit ulang tanpa training/evaluasi online:

```bash
venv/bin/python -m research_v2.critic_ablation_report --evidence-dir results/research_v2/P07_critic_scale_ablation_1 --previous-evidence results/research_v2/P07_lambda_ablation_1/lambda095
```

Seluruh checkpoint/NPZ tersedia lokal; model.zip/rng.pt diabaikan Git oleh aturan lama. Arsip lengkap diperlukan bila memindahkan artefak ke mesin lain.
