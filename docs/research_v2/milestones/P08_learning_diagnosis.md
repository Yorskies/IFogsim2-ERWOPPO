# P08 — Diagnosis pembelajaran dan ekstensi K

## Diagnosis dari pilot yang gagal

Artefak awal: `results/research_v2/P08_fidelity_1/`. Audit 144 pasangan model pendek dan checkpoint referensi lulus identik, sehingga seed, stream dan implementasi ulang awalan training bukan penyebab kegagalan ranking.

| K | Median korelasi Spearman tiga outer | Median selisih absolut D per model terhadap referensi | Median total variation porsi aksi per episode |
| ---: | ---: | ---: | ---: |
| 5.120 | −0,405 | 0,104 | 0,726 |
| 10.240 | −0,214 | 0,087 | 0,666 |
| 20.480 | 0,024 | 0,067 | 0,394 |

Pada K=20.480, 15/48 model memperbaiki D sampai 51.200, 28/48 memburuk, dan lima sama persis. Dilihat dari objektif reward berbobot, 25/48 membaik; 10 dari 25 itu justru memburuk pada D. Sebanyak 23/48 memburuk pada kedua ukuran. Jadi ketidakselarasan reward–D merupakan salah satu penyebab, tetapi tidak menjelaskan seluruh drift. Ini adalah perbandingan hasil validasi deterministik pada trace yang sama, bukan bukti sebab tunggal pada PPO.

Ranking dua repeat pada budget referensi juga lemah: korelasi Spearman antarrepeat untuk outer 100/101/102 adalah −0,419 / 0,310 / 0,048. Median selisih D antarrepeat per delapan bobot adalah 0,124 / 0,068 / 0,041. Dua repeat tidak memberi estimasi peringkat yang stabil; kelulusan gate saja tidak membuktikan kebijakan konvergen. Median explained variance critic pada update setelah K=20.480 adalah sekitar 0,980, sehingga diagnosis lama mengenai critic awal tidak bisa diterapkan langsung pada fase akhir.

## Revisi eksploratori yang dibekukan

Pilot P08 awal **tetap gagal**, dan hasilnya tidak ditulis ulang. Sebelum menjalankan data ekstensi, protokol `results/research_v2/P08_fidelity_extension_1/protocol.json` membekukan ladder baru 30.720 → 40.960 → 46.080 dengan referensi 51.200, delapan bobot dan tiga outer yang sama. Ambang tetap median Spearman ≥0,60 serta semua outer ≥0. Setiap lintasan baru dilatih dari awal dengan checkpoint tambahan; checkpoint akhirnya wajib identik dengan referensi lama. Jika ada K yang lulus, 48 model pendek independen pada K tersebut wajib identik dengan checkpoint awalan lintasan baru. Ini revisi setelah melihat kegagalan lama, sehingga statusnya *eksploratori* dan harus dibedakan dari gate P08 asli.

## Hasil ekstensi

| K | ρ outer 100 | ρ outer 101 | ρ outer 102 | Median | Gate revisi |
| ---: | ---: | ---: | ---: | ---: | --- |
| 30.720 | 0,714 | 0,790 | 0,619 | 0,714 | **Lulus; K terkecil** |
| 40.960 | 0,357 | 0,952 | 0,762 | 0,762 | Lulus, tetapi lebih mahal |
| 46.080 | 0,000 | 0,905 | 0,952 | 0,905 | Lulus, tetapi lebih mahal |

**K revisi yang dipilih adalah 30.720 keputusan/model.** 48 lintasan 51.200 keputusan baru cocok persis dengan checkpoint akhir referensi lama. Setelah pemilihan, 48 training pendek independen 30.720 keputusan cocok persis dengan checkpoint awal lintasan baru, termasuk policy, optimizer, RNG dan counter. Auditor terpisah lulus untuk 48 referensi, 144 validasi lengkap (2.880 episode), 48 prefix independen, serta perhitungan gate dari biaya makro. Total training ekstensi adalah 3.932.160 keputusan; evaluasi menghabiskan 2.793.168 keputusan dalam 2.880 episode lengkap. Bukti: `results/research_v2/P08_fidelity_extension_1/protocol.json`, `result.json`, dan `audit.json`.

Pada K=30.720, median selisih absolut D tiap model terhadap referensi adalah 0,034 dan median total variation porsi aksi per episode 0,306; 25 model membaik pada D sampai 51.200, 19 memburuk, empat sama. Ranking dua repeat pada K=30.720 tetap lemah (ρ −0,024 / −0,123 / 0,108 untuk ketiga outer). Korelasi pada K yang lebih besar juga tidak monoton pada outer 100. Karena itu hasil ini memenuhi **gate prediksi ranking agregat yang direvisi**, bukan klaim bahwa PPO telah konvergen atau dua repeat cukup untuk ketepatan inferensial. Lintasan P08 asli tetap gagal; pembenaran memakai K=30.720 harus menyebut protokol ekstensi dan biaya kandidat yang lebih besar.

Tidak ada test atau pencarian penuh yang dipakai untuk memilih K. Pilot ekstensi menggunakan ulang bobot/outer yang telah dilihat pada pilot awal, sehingga hasilnya eksploratori dan memerlukan pengamanan terhadap klaim konfirmatori yang terlalu kuat.
