# Winner's curse dalam pencarian bobot PPO: temuan P11 dan rencana pengujian P14

## Ringkasan

*Winner's curse* adalah kecenderungan hasil terbaik yang **dipilih berdasarkan pengukuran bising** terlihat lebih baik daripada performanya pada pengukuran independen. Dalam research_v2, nilai `Dglobal` yang lebih kecil berarti lebih baik. Jika pencarian menguji banyak bobot reward PPO, bobot dengan `Dglobal` validasi terendah dapat terpilih karena bobotnya memang baik, karena seed PPO atau trace validasi kebetulan menguntungkan, atau karena gabungan ketiganya. Setelah bobot itu dipakai untuk melatih model baru dan dievaluasi pada trace baru, bagian keuntungan yang berasal dari kebetulan tidak harus bertahan. Ini adalah bias seleksi; keberadaan dan besarnya harus diuji, bukan disimpulkan hanya dari satu selisih validasi–test.

## Bagaimana mekanismenya pada P11

Untuk satu bobot $w$, bayangkan nilai yang terukur sebagai:

$$
\widehat D(w)=D_{\mathrm{harapan}}(w)+\varepsilon_{\mathrm{training}}(w)+\varepsilon_{\mathrm{trace}}(w).
$$

`D_harapan` berarti performa rata-rata bobot tersebut jika PPO dilatih ulang dengan banyak seed dan diuji pada banyak trace independen. Dua suku lainnya mewakili variasi hasil training dan keterbatasan trace evaluasi. Persamaan ini adalah model penjelas konseptual. Bagian [Estimasi dari data P11](#estimasi-dari-data-p11) di bawah mengestimasi suku training dari data yang ada; dekomposisi lengkap ketiga suku belum dilakukan.

Pada [implementasi P11](../../research_v2/search.py), setiap pencarian mengevaluasi **80 slot kandidat**. [Evaluator kandidat](../../research_v2/search_runner.py) melatih **dua model PPO per slot**, menghitung rata-rata lima biaya makro kedua model, lalu menghitung `Dglobal` dari vektor rata-rata tersebut. Kandidat akhir adalah kandidat dengan `Dglobal` terkecil di *non-dominated front*. Karena semua biaya tidak negatif dan `Dglobal` meningkat jika salah satu biaya meningkat sementara biaya lain tetap, minimum `Dglobal` ini juga merupakan minimum di antara kandidat yang dievaluasi, kecuali ada ikatan nilai.

Dalam satu pencarian P11, semua kandidat memakai **bilangan acak bersama** (*common random numbers*): seed model yang sama (`200000 + 2·outer + repeat`), stream trace training yang sama (`train_candidate`, repeat 0 dan 1), dan 20 trace validasi yang sama. Jadi kesalahan pengukuran antar-kandidat tidak independen; yang membedakan kandidat adalah bobot dan **interaksi bobot × seed × trace**. Interaksi inilah sumber noise yang relevan untuk seleksi.

Seleksi minimum tersebut menimbulkan bias walaupun kesalahan pengukuran tiap kandidat secara individual berpusat di nol. Sebagai ilustrasi, tiga bobot yang sebenarnya sama-sama memiliki $D_{\mathrm{harapan}}=0{,}24$ bisa memperoleh nilai validasi 0,17; 0,23; dan 0,28. Pencarian memilih 0,17, padahal penilaian independen atas bobot terpilih cenderung kembali mendekati 0,24. Makin banyak kandidat yang diperiksa, makin besar peluang menemukan nilai ekstrem karena kebetulan; besarnya efek bergantung pada variasi pengukuran dan korelasi antar-kandidat. Pada MOEA, hasil evaluasi bising juga dipakai untuk membentuk generasi berikutnya, sehingga kesalahan pengukuran dapat ikut mengarahkan pencarian.

Sumber variasi yang relevan adalah:

1. **Seed dan lintasan training PPO.** Bobot yang sama bisa menghasilkan kebijakan berbeda pada training ulang. Dua model per kandidat mengurangi sebagian variasi, tetapi tidak menghapusnya.
2. **Trace validasi yang terbatas.** Kandidat bisa tampak unggul pada trace yang berulang kali dipakai pencarian, tanpa unggul pada trace baru.
3. **Banyaknya kesempatan seleksi.** P11 memilih yang terbaik dari 80 slot; P14 merancang 90 slot per algoritma. Peringkat teratas lebih rentan terhadap nilai pengukuran yang kebetulan terlalu rendah.
4. **Training final yang independen.** P11 membawa *bobot terpilih* ke training final dari awal, bukan dua model PPO yang membuat bobot itu terlihat unggul saat pencarian.

## Apa yang ditunjukkan hasil P11

[Rancangan P14](P14_MOEA_PILOT_DESIGN.md) merangkum bahwa `Dglobal` validasi kandidat terpilih sekitar **0,174**, sedangkan `Dglobal` test model final sekitar **0,245**, mendekati median kandidat sekitar **0,247**. Ringkasan itu juga mencatat simpangan baku `D` antar-run sekitar **0,085** dan selisih rerata NSGA-II terhadap `equal_F` sekitar **0,020**. [Laporan hasil P11](milestones/P11_results.md) menyatakan bahwa keunggulan NSGA-II terhadap `equal_F` belum meyakinkan secara statistik, dan NSGA-II juga belum terbukti lebih baik daripada random search.

Angka 0,174 → 0,245 **konsisten dengan dugaan winner's curse**, tetapi selisih itu sendiri **bukan estimasi murni besarnya bias seleksi**. Di antara validasi kandidat dan test, model PPO dilatih ulang serta trace evaluasi berubah. Perbedaan itu bisa memuat variasi training, variasi trace, dan perubahan performa nyata di luar kondisi validasi. Angka simpangan baku 0,085 juga tidak boleh langsung dianggap sebagai simpangan baku kesalahan evaluator kandidat: keduanya mengukur variasi pada tingkat yang berbeda. Estimasi yang lebih bersih dibuat di bagian berikut.

## Estimasi dari data P11

Setiap kandidat P11 dinilai oleh **dua model PPO dengan bobot yang sama** (`model_0` dan `model_1`: seed dan stream training berbeda, 20 trace
validasi sama), dan hasil validasi tiap model disimpan terpisah (`candidates/slot_NNN/validation_{0,1}/summary.json`). Selisih kedua model
mengukur noise training secara langsung, tanpa mencampur perubahan trace atau training final. Perhitungan dari 40 pencarian × 80 kandidat
(NSGA-II dan random search, outer 0–19) dapat diulang dengan `PYTHONPATH=. venv/bin/python -m research_v2.winners_curse_p11`
(keluaran: `results/research_v2/v0.4/p11/winners_curse_estimate.json`).

| Besaran | Nilai |
|---|---:|
| SD noise satu model PPO | 0,075 |
| SD noise skor kandidat (rata-rata dua model) | 0,053 |
| SD skor kandidat dalam satu pencarian | 0,052 |
| SD sinyal bobot yang tersirat (√(variansi skor − variansi noise)) | ≈ 0 |
| Korelasi D `model_0` dan `model_1` untuk bobot yang sama, dalam pencarian | 0,11 |
| Reliabilitas skor kandidat (dari variansi; dari korelasi via Spearman-Brown) | ≈ 0; 0,19 |

Variansi skor antar-kandidat dalam satu pencarian hampir sama dengan variansi noise skor itu sendiri, dan dua model dengan bobot yang sama
nyaris tidak sepakat tentang kandidat mana yang baik. Dengan reliabilitas *r*, nilai harapan kualitas kandidat terpilih adalah
rata-rata kandidat ditambah *r* × (skor terpilih − rata-rata):

| Skor terpilih saat pencarian | Rata-rata kandidat | Prediksi kualitas sebenarnya (*r* = 0 sampai 0,19) | `Dglobal` test model final (teramati) |
|---:|---:|---:|---:|
| 0,174 | 0,256 | 0,256 – 0,240 | 0,249 |

(Rata-rata atas NSGA-II dan random search; test NSGA-II saja 0,245, random 0,252.)

Penurunan dari 0,174 ke sekitar 0,25 **hampir seluruhnya terjelaskan oleh seleksi atas noise**: prediksi shrinkage dan hasil test teramati
cocok dalam ±0,01. Batas interpretasi:

- `model_0` dan `model_1` dinilai pada trace validasi yang sama, sehingga interaksi bobot × trace ikut terhitung sebagai "sinyal";
  reliabilitas sebenarnya paling tinggi sebesar estimasi ini.
- Estimasi berlaku untuk kondisi evaluator P11 (budget F, dua model, 20 trace); evaluator lain (lebih banyak seed atau trace, budget lebih
  panjang) bisa memiliki reliabilitas berbeda. Itulah yang diukur pertanyaan Q2 di P14.
- Implikasi untuk gerbang P14: dengan korelasi antar-model 0,11, reliabilitas peringkat 0,8 baru tercapai dengan puluhan model per kandidat
  (Spearman-Brown: m = 4·(1 − r₁)/r₁ ≈ 34 model untuk r₁ = 0,11, dengan trace yang sama). Gerbang G2 (≤ 4 seed) diperkirakan gagal pada F; pilot
  tetap diperlukan karena mengukur hal ini dengan bobot yang ditetapkan di awal, 100 trace, dan titik 4 × F.

## Bagaimana P14 mengujinya lebih jelas

[Pilot P14 yang dirancang](P14_MOEA_PILOT_DESIGN.md) memisahkan beberapa pertanyaan yang pada P11 masih tercampur:

| Langkah | Yang diperiksa | Batas interpretasi |
|---|---|---|
| Bobot yang telah ditetapkan diuji dengan beberapa seed PPO | Apakah variasi antar-bobot lebih besar daripada variasi antar-seed | Reliabilitas pada kondisi pilot; bukan otomatis berlaku untuk semua lingkungan |
| Peringkat bobot dari separuh seed dicek pada separuh seed lain | Apakah bobot yang tampak terbaik tetap baik tanpa memakai seed pemilihan | Trace yang sama belum menguji generalisasi ke trace baru |
| Tiga kandidat elit per pencarian dilatih ulang dengan seed baru pada trace pencarian yang sama | Seberapa jauh pemilihan elit dipengaruhi keberuntungan training | Masih bisa terpengaruh kecocokan dengan trace pencarian |
| Bobot terpilih dilatih lagi dengan empat seed baru dan diuji pada 80 trace pengembangan yang tidak dipakai pencarian | Apakah keunggulan bertahan pada seed **dan** trace independen | Ini tetap hasil pilot; tiga outer run hanya deskriptif |

Untuk benchmark penuh v0.5, rancangan tersebut juga menyediakan split test baru yang tetap tertutup sampai aturan analisis dikunci. Test dipakai untuk menilai kualitas akhir metode setelah seluruh pilihan algoritma, aturan seleksi, dan parameter evaluasi ditetapkan.

## Implikasi untuk v0.5 dan disertasi

Perbandingan NSGA-II, NSGA-III, MOEA/D, dan SPEA2 akan lebih bermakna jika memisahkan **kualitas yang terlihat saat pencarian** dari **kualitas bobot pada training dan trace baru**. Nilai validasi yang makin rendah atau *front* yang tampak makin baik belum cukup untuk menyatakan suatu MOEA menghasilkan PPO yang lebih baik. Hasil utama sebaiknya menunjukkan apakah bobot pilihan tiap metode mempertahankan keunggulan pada evaluasi independen, serta berapa biaya tambahan untuk membuat evaluasi kandidat cukup andal. Jika peringkat kandidat tidak stabil, temuan itu sendiri menjelaskan batas metodologi pencarian bobot PPO pada lingkungan ini.

## Rujukan metodologis

- Smith, J. E., & Winkler, R. L. (2006). The Optimizer's Curse: Skepticism and Postdecision Surprise in Decision Analysis. *Management Science, 52*(3), 311–322. Membuktikan bahwa memilih alternatif dengan estimasi terbaik menghasilkan bias walaupun setiap estimasi tak bias, dan mengusulkan koreksi shrinkage Bayesian (model yang dipakai pada bagian estimasi di atas).
- Rakshit, P., Konar, A., & Das, S. (2017). Noisy evolutionary optimization algorithms – A comprehensive survey. *Swarm and Evolutionary Computation, 33*, 18–45. Merangkum obat untuk fitness bising pada EC: resampling, estimasi fitness, ukuran populasi dinamis, adaptasi strategi, dan modifikasi seleksi (dasar re-evaluasi elite di P14).

- Andrews, I., Kitagawa, T., & McCloskey, A. (2024). [Inference on Winners](https://academic.oup.com/qje/article/139/1/305/7276491). *The Quarterly Journal of Economics, 139*(1), 305–358. Menjelaskan bias inferensi ketika pilihan terbaik ditentukan dari estimasi yang tidak pasti.
- Eimer, T., Lindauer, M., & Raileanu, R. (2023). [Hyperparameters in Reinforcement Learning and How to Tune Them](https://proceedings.mlr.press/v202/eimer23a.html). *Proceedings of the 40th International Conference on Machine Learning*, 9104–9149. Menunjukkan ketergantungan lanskap penyetelan RL pada seed dan pentingnya memisahkan seed tuning dan testing.
