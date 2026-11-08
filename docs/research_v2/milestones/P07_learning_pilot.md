# P07 — PPO dan pilot pembelajaran

Status: **complete — validasi teknis Linux; hasil pilot pembelajaran negatif, telah didiagnosis**.
Training/evaluasi diotorisasi pengguna dan sudah dijalankan. Tidak ada klaim konvergensi atau superioritas PPO.
Tanggal eksekusi server: 7 November 2026 UTC.

## Hasil aktual dan keputusan

Bukti lengkap: [`results/research_v2/P07_completion_20261107T205826Z/`](../../../results/research_v2/P07_completion_20261107T205826Z/).
Laporan mesin: [P07_verification.json](../../../results/research_v2/P07_completion_20261107T205826Z/P07_verification.json).
Grafik: [learning_curves.svg](../../../results/research_v2/P07_completion_20261107T205826Z/learning_curves.svg).

- Smoke 512 keputusan dan replay seed yang sama lulus (bukti smoke berada pada folder P07_smoke_r100 dan P07_smoke_r100_replay).
- Tiga pilot equal-weight/repeat 0 masing-masing tepat 10.240 keputusan, 20 rollout/update; parameter policy berubah.
- Loss, entropy, KL dan parameter finite; 14 tes persiapan lulus, tanpa failure/error/skip.
- Episode training lengkap diaudit ulang dari log keputusan: jumlah delta biaya sama dengan biaya akhir, reward dan terminal drain konsisten. Episode parsial tidak dihitung sebagai evaluasi sukses.
- 220 episode evaluasi lengkap selesai: smoke 20, checkpoint 512/10.240 tiga seed 120, diagnosis F 20, diagnosis stochastic 60.
- Prefix 512 vs 1.024 serta **F=102.400 vs 102.912** lulus. Policy, optimizer, RNG dan counter/stream identik pada prefix.
- Checkpoint 512 dan 10.240 pilot r100 juga identik dengan checkpoint run F yang baru: replay tetap sama meskipun evaluasi di proses terpisah telah dilakukan di antaranya.
- Semua split tetap pilot_train/pilot_validation, tidak ada validation/test konfirmatori. Hyperparameter, bobot equal dan parameter fisik tidak diubah.

Skor D dihitung sebagai RMS lima biaya **setelah** macro-average empat workload; lebih kecil lebih baik:

| Outer | D pada 512 | D pada 10.240 | Reliability macro akhir | Violation macro akhir |
|---|---:|---:|---:|---:|
| 100 | 0.319460 | 0.362634 | 0.8942 | 0.7370 |
| 101 | 0.655956 | 0.670584 | 0.3194 | 0.8705 |
| 102 | 0.443074 | 0.474897 | 0.4950 | 0.7318 |

**Ketiga pilot memburuk pada evaluasi deterministik.** Ini temuan negatif yang dipertahankan, bukan gerbang teknis yang disembunyikan.

Diagnosis berdasarkan bukti:

1. Pilot hanya menghasilkan 9–10 episode training lengkap, walaupun 20 update. Entropy training akhir masih 1,77–1,82 (maksimum tujuh aksi ~1,946); sampling selama training masih beragam.
2. Evaluasi argmax r101 selalu memilih F5, r102 selalu cloud, r100 90–98% lokal tergantung workload. Ini **degenerasi pilihan deterministik**, bukan bukti distribusi probabilitas sudah menjadi satu aksi. Pada 12 snapshot awal, probabilitas aksi modal hanya sekitar 0,25–0,53; bukti `policy_probabilities.json` bersifat sampel awal saja.
3. Diagnosis sampling memakai seed tetap 200000+2r, episode pilot validation yang sama, dan direktori terpisah berlabel `diagnostic_stochastic`. Tidak mengganti evaluasi utama. D deterministik vs sampled pada 10.240:

| Outer | D deterministik | D sampled (diagnosis) |
|---|---:|---:|
| 100 | 0.362634 | 0.408303 |
| 101 | 0.670584 | 0.450163 |
| 102 | 0.474897 | 0.422692 |

Sampling membantu D pada r101/r102, tetapi tidak r100. Pada r100 violation membaik namun zB naik, sehingga D justru memburuk. Ini menunjukkan interaksi argmax dengan trade-off biaya; tidak membuktikan mengganti evaluasi akan memperbaiki semua seed.
4. Diagnosis tambahan r100 pada F=102.400 tetap selalu cloud dan D=0,474897, reliability heavy ~0,099. Jadi menambah budget saja belum terbukti memperbaiki policy deterministik. Uji F ini untuk audit prefix/diagnosis, bukan eksperimen konfirmatori baru.
5. Dugaan sisa: estimasi advantage/credit assignment pada reward tertunda, observasi agregat, dan perubahan distribusi state antara policy sampling dan argmax. Penyebab kausal tersebut **belum dibuktikan**. Audit mekanik reward/drain, seed, budget dan checkpoint lulus; belum ada alasan untuk mengubah engine fisik.

**Keputusan:** kriteria teknis P07 lulus dengan diagnosis hasil negatif yang tercatat. Pembelajaran efektif belum terbukti. Jangan menyimpulkan PPO/ERWO unggul atau langsung menjalankan pencarian besar. Sebelum P08, tinjau diagnosis pada namespace pilot dan protokol deterministik; perubahan protokol memerlukan alasan dan versi, dan gerbang ranking fidelity P08 tetap wajib. Tidak ada tuning otomatis atau penggantian seed setelah melihat hasil.

### Koreksi implementasi yang ditemukan saat verifikasi

Ringkasan evaluasi awal keliru memakai mean(z) untuk `D_macro`. Diperbaiki menjadi `sqrt(mean(z²))` setelah macro-average. Tes RMS dan bobot workload sama ditambahkan. Episode mentah, reward, policy dan training tidak berubah. Ringkasan awal smoke/r100-512 dipertahankan sebagai `summary_before_rms_fix.json`, sedangkan `summary.json` dihitung ulang dari episode mentah. Tidak ada run gagal atau hasil yang dibuang.

### Accounting dan reproduksi audit

Batch penyelesaian ini mengeluarkan **237.568 keputusan training**: pilot utama 30.720, prefix pendek 1.536, prefix F 205.312. Dua smoke sebelumnya menambah 1.024 keputusan, sehingga total P07 yang tersimpan **238.592 keputusan training**. Evaluasi batch ini **213.367 keputusan dalam 220 episode**; 12 reset snapshot diagnosis bukan episode lengkap dan tidak ditambahkan sebagai evaluasi. Seluruhnya biaya penelitian/pilot, bukan biaya hasil utama salah satu metode. Waktu dinding tiap training ada pada outcome.json; biaya fase yang paralel tidak boleh dijumlahkan sebagai makespan serial.

Auditor hasil tidak melatih atau menjalankan evaluasi ulang:

```bash
venv/bin/python -m research_v2.learning_report --evidence-dir results/research_v2/P07_completion_20261107T205826Z
```

Checkpoint model.zip dan rng.pt ada secara lokal dan di-ignore Git oleh aturan yang sudah ada. Source/laporan saja tidak cukup untuk mengunduh model; arsipkan direktori bukti lengkap jika dipindahkan ke mesin lain. Tidak ada resume state simulator parsial. Bukti hanya mencakup environment/config/seed yang diperiksa.

## Implementasi

- `research_v2/learning.py`: CLI terpisah `plan`, `train`, `evaluate`, `prefix-check`.
- PPO CPU, satu environment dan satu thread Torch; seluruh hyperparameter dibaca dari config v0.2.
  Actor/critic terpisah 128–128, Tanh; 108 fitur, Discrete(7), gamma=1.
- Training hanya mengakses `pilot_train`, outer 100/101/102, repeat 0/1.
  Seed model mengikuti 200000+2r+m. Offset workload `(r+m)%4`; trace ID per workload
  dimulai dari 0 dan bertambah tanpa tergantung aksi, seed reset, atau RNG policy.
  Ini pemetaan eksplisit pilot ke aturan seed/offset kandidat pada spesifikasi.
- `evaluate` memuat checkpoint di proses/perintah terpisah, membuat JVM terpisah,
  memakai deterministic argmax dan 20 episode lengkap `pilot_validation` (5 per workload).
  Macro-average lima biaya memberi bobot sama pada empat workload. Holdout test tidak diakses.
- Reward dan cost vector diperiksa pada episode lengkap, termasuk delayed reward dan terminal drain.
- Setiap update menulis checkpoint **sesudah** update optimizer (callback rollout-end SB3 terjadi sebelum update).
  Checkpoint menyimpan model/optimizer, RNG Python/NumPy/Torch CPU, counters, state stream, dan hash artefak.
- Learning curve JSONL memuat loss, entropy loss, KL, clip fraction, value loss, dan epoch count.
  `explained_variance=null` berarti tidak terdefinisi, bukan nilai nol. Loss nonfinite menghentikan run.
- Trace/hash, snapshot mentah setiap keputusan, aksi, reward, cost delta, histogram aksi,
  keputusan per workload, serta metrik episode lengkap disimpan untuk audit.
- Akhir kuota tidak memaksa episode selesai. Snapshot episode parsial dan biaya kumulatif dicatat;
  jumlah outcome tugas yang masih pending tidak tersedia dari snapshot agregat dan diberi label unknown.
  Jumlah tugas yang belum datang dilaporkan terpisah. Episode parsial tidak menjadi hasil evaluasi.
- Tidak ada resume simulator parsial. Checkpoint adalah artefak evaluasi/audit, bukan klaim pemulihan simulator.
  Run terputus harus diulang dari awal ke direktori baru. Direktori output yang sudah ada ditolak.
- `prefix-check` melatih dua model dari awal, membandingkan policy, optimizer, RNG dan counters/stream
  pada checkpoint dengan jumlah keputusan sama. Seluruh schedule konstan. Jika berbeda, reuse dilarang.

## Pemeriksaan yang sudah dilakukan tanpa training

`venv/bin/python -m research_v2.verify_learning --output results/research_v2/P07_preparation/verification.json`

Hasil terbaru: **14 tes lulus, 0 failure/error/skip**. Verifier memblokir `PPO.learn`, `PPO.train`,
dan startup JVM. Tes membuat/menyimpan/memuat policy yang belum dilatih, menguji guard budget/split/bobot,
seed/offset/round-robin, isolasi RNG, audit reward tertunda memakai fake environment,
penolakan reward tidak konsisten, dan pembanding state. Tidak ada rollout ataupun optimizer step.
Pin dependency P07 sudah terpenuhi di venv; `pip check` lulus.
Bukti ini **tidak** memvalidasi training end-to-end, determinisme training, atau gerbang pembelajaran P07.

## Perintah reproduksi (rangkaian ini sudah dijalankan)

Jalankan dari root repository. Gunakan direktori baru jika nama di bawah sudah ada.
Dependency dan build Java sudah disiapkan pada sesi implementasi ini. Bila Java/config berubah,
bangun ulang dan ulangi regresi sebelum training. Jangan membangun ulang JAR antara training dan evaluasi,
karena evaluasi memeriksa identitas JAR checkpoint.

Persiapan shell (belum menjalankan training):

```bash
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
venv/bin/python -m research_v2.learning plan --stage pilot --outer 100
```

**Langkah 1: smoke training**, 512 keputusan, satu update PPO, bobot equal:

```bash
venv/bin/python -m research_v2.learning train --stage smoke --outer 100 \
  --output-dir results/research_v2/P07_smoke_r100
```

Periksa `outcome.json`: status complete, decisions=512, policy_changed=true, budget aktual sesuai.
Periksa `learning_curve.jsonl`: loss/entropy/KL finite. Smoke dapat berakhir sebelum satu episode lengkap;
keberhasilan smoke hanya teknis. Lalu evaluasi checkpoint smoke pada episode lengkap:

```bash
venv/bin/python -m research_v2.learning evaluate \
  --checkpoint results/research_v2/P07_smoke_r100/checkpoint_00000512 \
  --output-dir results/research_v2/P07_smoke_r100_validation
```

Evaluasi tidak melakukan training. Periksa `summary.json` (20 episode), `episodes.jsonl`,
kelima biaya dan metrik fisik. Jangan menggunakan D sendirian (lihat temuan zB pada P06).

**Langkah 2: prefix check awal**, command ini menjalankan training 512 dan 1024 keputusan:

```bash
venv/bin/python -m research_v2.learning prefix-check \
  --output-dir results/research_v2/P07_prefix_smoke
```

Semua flag pada `comparison.json` harus true. Ini bukti pada prefix pendek saja.
Untuk prefix pilot gunakan `--prefix-decisions 10240 --long-decisions 10752` dengan output baru.
Sebelum reuse checkpoint F produksi, ulangi pada F yang dipakai (misalnya 102400 vs 102912);
uji prefix pendek tidak membuktikan equivalence F panjang.

**Langkah 3: pilot**, setelah smoke dan pemeriksaan awal berhasil. Loop ini menjalankan
training tiga model baru, masing-masing 10.240 keputusan; total 30.720 keputusan training,
di luar smoke/prefix dan validasi:

```bash
for r in 100 101 102; do
  venv/bin/python -m research_v2.learning train --stage pilot --outer "$r" \
    --output-dir "results/research_v2/P07_pilot_r${r}" || break
done
```

Evaluasi setiap model secara terpisah:

```bash
for r in 100 101 102; do
  venv/bin/python -m research_v2.learning evaluate \
    --checkpoint "results/research_v2/P07_pilot_r${r}/checkpoint_00010240" \
    --output-dir "results/research_v2/P07_pilot_r${r}_validation" || break
done
```

Repeat default 0; repeat 1 tersedia lewat `--repeat 1` jika diperlukan dengan direktori output baru.
Bobot manual tersedia lewat `--weights 0.30 0.15 0.25 0.10 0.20`; pencarian delapan bobot/fidelity tetap P08.

## Kriteria yang telah diperiksa (lihat bukti aktual di atas)

- Training finite, policy berubah, actual decisions sama dengan kuota dan rollout.
- Kurva loss/entropy/KL, histogram aksi, antrean/outcome serta lima biaya diperiksa.
- Identitas reward dan episode drain benar pada episode lengkap.
- Replay seed dan perbandingan prefix lulus; biaya semua percobaan dicatat.
- Evaluasi lengkap tiga outer pilot tersedia; hasil negatif tetap disimpan.

PPO tidak harus mengalahkan heuristik untuk lulus validasi teknis. Perilaku tidak belajar
atau collapse perlu didiagnosis sebelum P08. Status teknis selesai di atas didasarkan pada eksekusi dan audit hasil, bukan tes persiapan saja.

## Peninjauan lanjutan penyebab hasil

[Review P07 berbasis replay dan kontrol pada trace yang sama](../../../results/research_v2/P07_review/review.md) tersedia. Review tidak melakukan training baru. Temuan tambahan: heavy median lag outcome 43–49 keputusan, critic EV negatif 28/60 update, serta seed 102 memperbaiki objektif linear walau skor RMS D memburuk. Sebutan hasil negatif P07 mengacu pada D deterministik; bukan bukti bahwa tidak ada pembelajaran sama sekali.

## P07 ulang: ablation lambda dengan instrumentasi

[Hasil ablation lambda 0,95 versus 1,0](../../../results/research_v2/P07_lambda_ablation_1/review.md) selesai: 83.968 keputusan training dan 360 episode evaluasi. Seluruh audit teknis lulus, 22 tes lulus, dan baseline instrumented identik dengan hasil lama. Lambda=1 memperburuk D pada ketiga seed; default tidak diubah. Diagnosis baru memprioritaskan skala target/loss critic dan global clipping, serta perbedaan sampling–argmax. Policy efektif belum terbukti dan P08 belum dijalankan.

## Eksperimen satu faktor skala critic

[Ablation vf_coef 0,5 versus 0,05](../../../results/research_v2/P07_critic_scale_ablation_1/review.md) selesai: 26 tes dan audit 360 episode evaluasi lulus, dengan 83.968 keputusan training baru. Lambda=0,95 dan clipping tetap. D membaik pada satu seed, memburuk pada satu, dan sama pada satu; median selisih nol. Skala gradient/clipping berkurang, tetapi hasil tidak konsisten. Default tidak diubah dan P08 belum dijalankan.
