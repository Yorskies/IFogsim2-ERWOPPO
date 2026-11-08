# P08 — NSGA-II/random search dan gerbang fidelity

Status: **implementasi tersedia; audit teknis lulus; gerbang fidelity GAGAL; K tidak dipilih**. Milestone tinjauan M2 belum lulus. Pencarian penuh 80 slot, P09 dan eksperimen konfirmatori tidak dijalankan.

Catatan lanjutan: [diagnosis dan ekstensi eksploratori](P08_learning_diagnosis.md) kemudian memilih K=30.720 melalui protokol terpisah yang diaudit. Status gate asli di halaman ini tetap gagal; pencarian penuh belum dijalankan.

## Implementasi

- `research_v2/search.py`: simplex minimum 0,02, proyeksi Euclidean, equal/manual anchors, delapan bobot pilot, NSGA-II dan random search 80 slot, arsip nondominated seluruh histori, seleksi D/tie-break dan hypervolume reference tetap [1.1]*5.
- `research_v2/search_runner.py`: evaluator dua PPO baru per slot, stream `train_candidate`, evaluasi `validation`, biaya aktual per slot. Bobot/metode tidak masuk seed. CLI memblokir gerbang gagal, audit hilang/berubah, perubahan config/JAR atau source training kritis.
- `research_v2/fidelity.py`: pilot dibekukan, 48 referensi dan model pendek independen pada ladder; tiga worker/JVM terisolasi.
- `research_v2/fidelity_report.py`: audit independen, arsip delapan bobot tetap, grafik, diagnosis pilihan bobot; tidak melatih model.
- Trainer lama mempertahankan default API; P08 menambahkan split kandidat, checkpoint terpilih dan mode RPC cepat dengan identitas JAR/config serta validasi episode tetap aktif.

Detail algoritma, pilihan operator, batasan dan perintah: [SEARCH.md](../SEARCH.md). NSGA-II/random search diuji dengan evaluator sintetis untuk anggaran, repair, anchor, RNG dan seleksi; belum dijalankan sebagai pencarian 80 kandidat pada simulator karena gerbang gagal. Arsip pilot delapan bobot bukan hasil optimizer tersebut.

## Protokol sebelum eksekusi

Baseline PPO tetap lambda=0,95; vf_coef=0,5; max_grad_norm=0,5; 108 fitur; tujuh aksi; CPU satu thread/model. Bobot: equal, manual, lima vertex (.92/.02), satu simplex seed 20261107.

Tiga outer pilot 100/101/102 dan dua model repeat 0/1 per bobot: total 48 model referensi × 51.200 keputusan. Model pendek pada setiap K dilatih **independen dari awal**, dengan seed/stream yang sama, lalu dibandingkan dengan checkpoint referensi pada K yang sama.

Untuk setiap outer, mean dua vektor biaya dihitung dahulu, kemudian D=RMS dan ranking delapan bobot. Bukan mean D dua model, bukan ranking reward antar-bobot. Semua evaluasi menggunakan lima trace/workload (20 episode/model) pada pilot_validation yang sama.

Gerbang: median Spearman tiga outer >=0,60 dan tidak ada korelasi negatif; pilih K terkecil yang lulus pada ladder 5.120 → 10.240 → 20.480. Ties memakai average rank. Undefined short ranking gagal pada K itu; constant reference menghentikan pilot sebagai tidak informatif. Tidak ada perubahan aturan setelah hasil terlihat.

## Hasil gerbang

| K | rho outer 100 | rho outer 101 | rho outer 102 | Median | Hasil |
|---|---:|---:|---:|---:|---|
| 5,120 | -0.404762 | -0.619048 | -0.071429 | -0.404762 | GAGAL |
| 10,240 | 0.000000 | -0.874267 | -0.214286 | -0.214286 | GAGAL |
| 20,480 | 0.023810 | -0.261905 | 0.428571 | 0.023810 | GAGAL |

**Tidak ada K yang lulus.** Pada K terakhir, median hanya 0,023810 dan outer 101 tetap negatif. Nilai awal candidate_decisions=5.120 dalam config adalah rancangan awal, bukan budget yang disahkan oleh pilot ini. Jangan menjadikannya fallback ketika gerbang gagal.

## Diagnosis terukur

Seluruh prefix model pendek identik dengan referensi pada jumlah keputusan yang sama. Jadi perbedaan ranking mencerminkan perubahan policy selama training, bukan ketidakcocokan optimizer/RNG/counter pada checkpoint. Ini belum membuktikan penyebab kausal tunggal dari ketidakstabilan belajar.

Pada K=20.480, pilihan bobot model pendek masih berbeda dari pilihan referensi pada ketiga outer:

| Outer | Pilihan pendek | Pilihan referensi | D referensi dari pilihan pendek | D terbaik referensi | Selisih |
|---|---|---|---:|---:|---:|
| 100 | vertex4 | vertex3 | 0.413191 | 0.383487 | 0.029705 |
| 101 | simplex | vertex1 | 0.472243 | 0.406708 | 0.065535 |
| 102 | equal | vertex1 | 0.464740 | 0.427998 | 0.036742 |

Tabel tersebut merupakan diagnosis pasca-pilot, bukan gerbang baru atau pemilihan policy akhir. Pilihan memakai aturan D/failure/violation/lexicographic yang sama pada delapan bobot tetap. Reference juga hanya budget 51.200; bukan bukti optimum atau konvergensi.

Implikasi: mengoptimalkan fitness pada budget pendek saat ini dapat mengarahkan pencarian ke bobot yang tidak terbaik setelah training lebih panjang. Memperpanjang kandidat sampai 20.480 belum membuat ranking stabil lintas tiga outer. Jangan menaikkan K ke 51.200 hanya untuk memperoleh korelasi self-reference=1; itu di luar ladder yang ditetapkan.

Diagnosis P07 tetap relevan: reward tertunda/critic yang lemah, perubahan sampling–argmax dan perbedaan reward linear terhadap D. Pilot ini tidak mengisolasi ketiganya. Tidak ada tuning tambahan, penggantian seed, normalisasi baru atau penurunan ambang gate setelah hasil diketahui.

## Bukti audit

- **41 tes lulus**, 0 failure/error/skip: regresi learner, GAE/clipping, role split, repair dan anchors, 80 slot termasuk duplikasi, common initial population, RNG optimizer terpisah dari reset PPO, hypervolume tetap, tie rules, Spearman dan pengaman source/JAR.
- **48 referensi + 144 model pendek** selesai dengan budget aktual yang tepat.
- **144 prefix checks** policy/optimizer/RNG/counter/stream lulus.
- Enam kombinasi outer/repeat memiliki initial policy berbeda; delapan bobot dalam masing-masing kombinasi memakai initial policy dan external stream yang sama.
- Semua 3.840 episode lengkap; payload validasi sama di semua model/budget/bobot. Reward, metrik fisik, macro-average dan RMS dihitung ulang oleh auditor.
- Baseline equal r100/repeat0 pada 51.200 identik dengan checkpoint P07 lama. Mode RPC cepat dan checkpoint selektif tidak mengubah trajectory tersebut. JAR/config handshake tetap aktif.
- Satu smoke preflight 512 keputusan juga identik dengan baseline lama.
- Tidak ada akses holdout/test atau validation konfirmatori.
- CLI full-search diuji pada gerbang gagal aktual dan menolak sebelum membuat run atau melatih kandidat.

Audit `status=pass` berarti integritas bukti lulus. Field `fidelity_pass=false` dan `selected_K=null` berarti syarat ilmiah P08 belum lulus. Keduanya tidak boleh disamakan.

## Accounting dan eksekusi

- Referensi: 48 × 51.200 = **2.457.600 keputusan training**.
- Pendek: 48 × (5.120+10.240+20.480) = **1.720.320 keputusan training**.
- Total pilot: **4.177.920 keputusan training**; preflight tambahan **512**.
- Validasi: **3.840 episode lengkap / 3.724.224 keputusan**.
- Tiga worker Python/JVM independen di port 5556–5558; Torch/interop/BLAS satu thread. Port 5555 milik simulator legacy tetap berjalan.
- Wall-clock paralel diberi label; jangan membandingkannya dengan waktu serial P07 sebagai bukti efisiensi algoritma.
- Seluruhnya biaya penelitian/pilot, bukan biaya salah satu metode konfirmatori. Arsip lokal pilot sekitar 21 GiB, termasuk snapshot mentah; model.zip/rng.pt di-ignore Git sesuai aturan lama.

## Keputusan dan pekerjaan berikutnya

**Berhenti untuk diagnosis sesuai spesifikasi §24.3.** K belum dipilih, M2 belum lulus, pencarian penuh dan studi konfirmatori tidak dijalankan. Kode optimizer tersedia tetapi gerbang eksekusinya tetap tertutup.

Sebelum mengulang P08, tinjau kembali stabilitas pembelajaran lintas bobot dan alignment reward/evaluasi pada namespace pilot, dengan revisi protokol eksplisit bila diperlukan. Jangan mencoba parameter NSGA-II untuk memperbaiki gate ini: kegagalannya terjadi sebelum optimizer digunakan. Jangan mengubah ambang Spearman, seed atau memakai test untuk mencari K yang tampak lulus.

## Artefak

Bukti lengkap berada pada [`results/research_v2/P08_fidelity_1/`](../../../results/research_v2/P08_fidelity_1/):

- [protocol.json](../../../results/research_v2/P08_fidelity_1/protocol.json): dibekukan sebelum run.
- [result.json](../../../results/research_v2/P08_fidelity_1/result.json): seluruh gate dan status stop.
- [fidelity_verification.json](../../../results/research_v2/P08_fidelity_1/fidelity_verification.json): audit independen.
- [review_conclusions.json](../../../results/research_v2/P08_fidelity_1/review_conclusions.json): keputusan ringkas.
- [pilot_archive.json](../../../results/research_v2/P08_fidelity_1/pilot_archive.json): fixed-pilot records, nondominated archives dan hypervolume.
- [selection_diagnostics.json](../../../results/research_v2/P08_fidelity_1/selection_diagnostics.json): perubahan pilihan dan action shares.
- [fidelity_correlations.svg](../../../results/research_v2/P08_fidelity_1/fidelity_correlations.svg), [ranking_scatter.svg](../../../results/research_v2/P08_fidelity_1/ranking_scatter.svg): grafik.
- [tests_verification.json](../../../results/research_v2/P08_fidelity_1/tests_verification.json): 41 tes.

Audit ulang tanpa training:

```bash
venv/bin/python -m research_v2.fidelity_report --evidence-dir results/research_v2/P08_fidelity_1
```

Perintah training/reproduksi dan batas resume ada di [SEARCH.md](../SEARCH.md). Tidak ada commit/push atau unggah artefak yang dilakukan pada tahap ini.
