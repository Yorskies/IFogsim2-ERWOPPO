# P10 — Analisis statistik, penguncian protokol, dan tinjauan kesiapan (M3)

Status: **deliverable teknis P10 selesai dan terverifikasi; keputusan go/no-go M3 belum diambil — milik peneliti.**
Tanggal: 8 November 2026. Bukti mesin: [P10_verification.json](P10_verification.json) (lulus). Test split **tidak dievaluasi**.

## Deliverable

| Deliverable | Lokasi |
|---|---|
| Modul analisis: agregasi, sign-flip exact, Monte Carlo, Holm, bootstrap crossed, dz, laporan | `research_v2/analysis/stats.py`, `loader.py`, `report.py` ([ANALYSIS.md](../ANALYSIS.md)) |
| 28 tes analisis | `tests/research_v2/test_analysis.py` |
| Contoh laporan mini end-to-end (namespace validasi, fixture P09) | `results/research_v2/P10_mini_report/report.md` dan `report.json` |
| Protocol lock (83 file ber-hash) | `results/research_v2/P10_protocol_lock/protocol_lock.json` |
| Modul lock dan mekanisme unseal test (7 tes) | `research_v2/analysis/lock.py`, `trace_access.unseal_test`, `tests/research_v2/test_protocol_lock.py` |
| Estimasi sumber daya dari pengukuran | `results/research_v2/P10_resource_estimate.json` |
| Perubahan dari v0.2 (11 butir) | `results/research_v2/P10_deviations_from_v02.json` |
| Verifikasi milestone | `research_v2/analysis/verify.py p10` |

## Validasi statistik

- Agregasi trace → workload → run: dihitung manual pada contoh kecil (Dglobal = 0,5; Dw sama dengan mean workload). Workload dengan
  lebih banyak trace tidak mendapat bobot tambahan.
- **Sign-flip exact** dibandingkan dengan brute force (termasuk ties) dan dengan `scipy.stats.permutation_test`: identik. Selisih
  semuanya berarah sama pada n=20 menghasilkan tepat `2/2^20`. Semua selisih nol → p=1, CI=[0,0], dz tidak terdefinisi.
  Pasangan ditukar → p sama, mean/dz berbalik tanda, CI tercermin. SD nol dengan mean ≠ 0 → dz "undefined", bukan nol.
- **Holm**: contoh hitung tangan (`[.01,.04,.03,.005] → [.03,.06,.06,.02]`) dan 200 kasus acak terhadap implementasi independen
  (closed testing dengan lokal Bonferroni, bukan rumus yang sama).
- **Monte Carlo**: |p_MC − p_exact| < 0,01 pada n=10; `p ≥ 1/(M+1)` selalu.
- **Bootstrap**: indeks trace dibagikan ke semua model — dua model identik memberi CI tepat [0,0] di setiap draw; reprodusibel pada seed
  20261105 dan berubah pada seed lain; CI mengurung efek sebenarnya pada data sintetis.
- **Keluarga & pelaporan**: 3 primer (satu keluarga Holm) + 60 sekunder (keluarga Holm sendiri, berlabel *secondary, pre-specified*) +
  eksploratif berlabel tanpa kontrol multiplisitas; unit = 20 outer run; tidak ada pooling task/episode dan tidak ada rata-rata p-value.
- **Data hilang/NaN/trace tidak berpasangan/run tidak lengkap = error** (tidak ada imputasi). Pemuat hanya membaca split `validation`.
- Satu cacat ditemukan oleh tes dan diperbaiki: SD "nol" hasil floating point (~1e-17) tidak dikenali sehingga dz meledak (7×10^15);
  kini memakai toleransi relatif 1e-12.
- Skala penuh (20 outer × 100 trace × 4 workload, 10.000 bootstrap + 100.000 sign-flip): **~5 s, ~125 MiB**.

## Studi mini end-to-end

Dijalankan pada studi fixture P09 (4 outer run, namespace `validation`, 20 episode/model). Label metode adalah *placeholder* pipeline
(`nsga2` = final fixture, `random` = baseline manual); hasilnya **bukan** bukti metode. Menariknya `equal_F` identik dengan `nsga2`:
slot tunggal fixture berbobot equal dan seed-nya sama, sehingga ini sekaligus pemeriksaan ekuivalensi prefix di level studi. Dengan n=4
p exact minimum adalah 2/16, sehingga tidak ada uji yang dapat signifikan — wajar dan tidak diinterpretasikan.

## Protocol lock

Membekukan (diverifikasi ulang dari disk, termasuk regenerasi hash 400 trace test): 83 file source/test/schema/config/requirements, JAR
(`ba5a7ca8…`), config kanonik, versi Python 3.12.3 / OpenJDK 21.0.12 / paket (AMD EPYC 9135; host 64 core, tetapi kuota container 16 core / 64 GiB), **K=30.720**, F=102.400, B=8.168.448,
seed dan split, normalisasi, manifest 20 trace validasi, hash input 400 trace test (390.154 tugas; `outcomes_observed: false`), registri
hipotesis (3 primer, 60 sekunder, larangan: tidak ada fallback uji, tidak ada one-sided pasca-hoc, tidak ada penambahan seed, tidak
ada tuning pada test), aturan sensitivitas §25, bukti P09, estimasi sumber daya, dan perubahan dari v0.2. Hash lock:
`0854491d…`; `verify --deep`: 0 masalah, 0 peringatan.

Test hanya dapat dibuka lewat `trace_access.unseal_test(lock)` (role `test_evaluator`): lock yang tidak valid ditolak dan role lain tidak
pernah dapat membaca test. File yang **ditambahkan** setelah lock (mis. evaluator test P11) hanya diperingatkan dan wajib diaudit di P12;
file terkunci yang berubah/hilang membatalkan lock.

## Sumber daya (P11)

Lihat tabel di [P09](P09_runner_validation.md#kapasitas-studi-penuh-ekstrapolasi-bukan-pengukuran-studi-penuh): ~198 jam pada satu worker;
**10 worker ≈ 22 jam** (direkomendasikan; 20 worker tidak mungkin pada kuota 16 core container); disk ~216 GiB dengan log gzip; evaluasi test ≈ 6,2 jam
satu worker. Semua angka adalah ekstrapolasi dari fixture; efisiensi paralel hanya terukur pada 4 worker (89%).

## Tinjauan M3 — go/no-go (keputusan peneliti)

Kriteria M3: *semua invariant, kalibrasi, fidelity, budget, dan rencana analisis sudah mempunyai bukti.*

| Area | Bukti | Penilaian |
|---|---|---|
| Invariant engine/jaringan/energi/Gym (P02–P05) | 21+17+16+28 tes, acceptance lulus | **Siap** |
| Kalibrasi fisik (P06) | semua gerbang lulus, 19 tes | **Siap** |
| Runner, budget, resume (P09) | 12 tes + 6 skenario live lulus | **Siap** (diuji pada fixture) |
| Rencana analisis (P10) | 28 tes, lock terverifikasi | **Siap** |
| Budget/sumber daya | terukur dan layak (22 jam @10 worker, 216 GiB) | **Siap** (ekstrapolasi) |
| **Fidelity kandidat (P08)** | gerbang asli **GAGAL** pada 5.120/10.240/20.480; K=30.720 dipilih lewat ekstensi eksploratif bersertifikasi audit independen | **Dengan catatan** — bukan lulus gerbang yang terdaftar semula |
| **Pembelajaran PPO (P07)** | tiga pilot memburuk pada D; didiagnosis, belum terselesaikan; "pembelajaran efektif belum terbukti" | **Risiko terbuka** |
| **Pencarian penuh (P08)** | 80 slot NSGA-II/random belum pernah dijalankan pada simulator | **Belum diuji pada skala** |

Rekomendasi saya: **kesiapan teknis dan statistik terpenuhi; kesiapan ilmiah bersyarat.** Eksperimen konfirmatori tetap sah apa pun
hasilnya (kriteria P11 adalah bukti yang valid dan pelaporan lengkap, bukan kemenangan ERWO), tetapi go sebaiknya mengakui secara eksplisit:

1. K=30.720 berasal dari ekstensi eksploratif, bukan gerbang asli (tercatat di lock).
2. Efektivitas pembelajaran PPO belum terbukti; hasil negatif atau null sangat mungkin dan harus dilaporkan penuh.
3. Jalur search non-fixture belum pernah dijalankan di dalam runner.

Opsi: **(a) go** dengan penerimaan butir di atas; **(b) no-go** — revisi protokol (mis. memperbaiki masalah pembelajaran lebih dulu) dan buat versi
lock baru; **(c) go bertahap** — jalankan satu shard (outer run 0) sebagai staging nyata, ukur throughput dan kegagalan, lalu perluas.
Sesuai rencana, jangan memangkas biaya atau seed secara diam-diam.

## Prasyarat operasional sebelum P11

- **Commit working tree.** Lock mencatat `dirty: true` (74 entri belum di-commit; HEAD `4a0f2c2` = P06). Reproduksibilitas bertumpu pada hash
  per-file di lock, tetapi commit diperlukan untuk arsip. (Tidak dilakukan tanpa permintaan.)
- Evaluator test (file baru) harus memanggil `unseal_test(lock)` dan memakai role `test_evaluator`; ia akan muncul sebagai file tambahan
  pada `verify_lock` dan diaudit di P12.
- Evaluator test harus menulis `results/research_v2/TEST_OPENED.json` saat test dibuka (`verify_lock` memperingatkan bila berkas ada); temuan test tidak boleh dipakai men-tuning ulang studi yang sama.
- Hindari mengubah file terkunci; perubahan apa pun memerlukan lock/protokol versi baru dengan alasan tercatat.

## Addendum — pemeriksaan pembelajaran pra-peluncuran (8 November 2026)

[`results/research_v2/P10_learning_check/`](../../../results/research_v2/P10_learning_check/check.json) (skrip `run_check.py`; 2 menit 22 detik; **validasi saja,
test tidak disentuh**; tidak ada konfigurasi yang diubah, hanya masukan untuk keputusan go/no-go). PPO-Equal, outer run 0, F=102.400 (komputasi yang sama dengan
`equal_F` outer 0 pada studi konfirmatori), dievaluasi pada 20 trace validasi dan dibandingkan dengan heuristik pada trace yang sama.

| Policy | D (makro) | aksi lokal / fog / cloud |
|---|---:|---|
| PPO-Equal @ 2.048 (update pertama) | 0,527 | 0 / 83 / 17 % |
| PPO-Equal @ 10.240 | 0,366 | 75 / 25 / 0 % |
| PPO-Equal @ 51.200 | 0,370 | 38 / 62 / 2 % |
| **PPO-Equal @ 102.400** | **0,261** | 14 / 30 / 56 % |
| Greedy-EFT (heuristik terbaik) | 0,267 | 40 / 32 / 28 % |
| Always-local | 0,370 | 100 / 0 / 0 % |
| Acak seragam | 0,448 | 14 / 71 / 14 % |
| Least-fog / Nearest-fog | 0,484 / 0,515 | 0 / 100 / 0 % |

Pembacaan yang sah: pada satu seed, PPO **belajar** pada F (D turun dari 0,527 ke 0,261, lebih baik dari acak dan always-local, setara Greedy-EFT; selisih 0,006 terhadap
Greedy-EFT tidak bermakna pada 20 episode). Kurva tidak monoton: pada 10.240 dan 51.200 policy hanya setara always-local (0,366–0,370), sesuai pilot P07 yang gagal membaik
pada 10.240. Pembelajaran baru terlihat antara 51.200 dan 102.400, artinya F berada dekat titik awal pembelajaran dan bisa rapuh antar seed.

Belum dapat disimpulkan: satu seed, 20 episode, belum ada informasi apakah bobot mengubah hasil pada F (sensitivitas bobot), sehingga pengaruh NSGA-II belum teruji.

### Koreksi — konsistensi antar-seed dan sensitivitas bobot (8 November 2026)

[`sensitivity.json`](../../../results/research_v2/P10_learning_check/sensitivity.json) (skrip `run_sensitivity.py`; 26 run F=102.400, 8 pekerja paralel, 428 s; validasi saja).
Kesimpulan "PPO belajar pada F" dari satu seed di atas **tidak berlaku umum**: outer run 0 adalah seed terbaik.

- **PPO-Equal pada F, outer 0–4:** D = 0,261 / 0,486 / 0,419 / 0,437 / 0,486 (mean 0,418; SD 0,092). Pembanding pada trace yang sama: Greedy-EFT 0,267;
  always-local 0,370; acak 0,448. Hanya 1 dari 5 seed mengalahkan always-local. Outer 0 direproduksi persis (0,26121628), jadi eksekusi deterministik.
- **Policy runtuh ke aksi tunggal:** 7 dari 52 evaluasi checkpoint memilih ≥98% satu aksi (always-cloud, D = 0,4858 identik antar seed; atau always-local). Dari 26 run F,
  hanya 7 yang lebih baik dari always-local dan 3 yang lebih baik dari Greedy-EFT.
- **Bobot berpengaruh per seed tetapi tidak konsisten antar seed:** SD antar-bobot dalam satu outer run 0,06–0,13 (sebanding SD antar-seed equal 0,092). Korelasi
  peringkat bobot antar outer run: 0,00 / −0,62 / +0,33. Bobot terbaik berbeda tiap outer run (vertex2, simplex, vertex3); selisih terhadap equal bertanda campuran.
  Keuntungan "oracle" per outer run (0,027 / 0,034 / 0,207) dipilih in-sample pada trace validasi yang sama, sehingga optimistis.
- **Implikasi:** keunggulan sebuah bobot pada satu seed tampak terutama sebagai ketidakstabilan training, bukan sifat bobot. Pencarian yang memilih bobot dari dua model kandidat
  berisiko mengejar derau, dan model final dengan seed baru tidak akan mereproduksi keunggulannya. Gerbang fidelity P08 membandingkan ranking pada seed yang sama (prefix identik),
  bukan ketahanan antar-seed; temuan ini menunjukkan hal terakhir itulah yang belum terpenuhi. Sampel kecil (3 seed × 8 bobot), tetapi arahnya konsisten dengan kegagalan gerbang asli P08.
- **Penilaian M3 diperbarui:** premis RQ1 (bobot hasil pencarian menghasilkan agen yang lebih baik) tidak didukung data pra-peluncuran; hasil null di P11 sangat mungkin, dan
  sebagian besar akan mencerminkan kegagalan stabilitas PPO, bukan jawaban tentang bobot. Rekomendasi bergeser dari "go bertahap" ke **diagnosis stabilitas pembelajaran lebih dulu**
  (lock baru bila perlu).

### Diagnosis stabilitas pembelajaran (8 November 2026)

[Laporan diagnosis](../../../results/research_v2/P10_learning_diagnosis/report.md) — ablasi satu faktor pada namespace pilot (36 run). **Gamma = 1 adalah penyebab utama**:
gamma 0,97 memperbaiki keenam seed (D 0,443 → 0,250), tanpa policy runtuh, seluruhnya mengalahkan always-local dan rata-rata setara/lebih baik dari Greedy-EFT; entropi, ukuran
rollout, dan learning rate tidak memperbaiki. Gamma terkunci = 1,0 pada schema v0.2, sehingga perbaikan ini berarti **revisi protokol (v0.3)**: lock P10 tidak berlaku untuk P11,
gerbang fidelity/K dan budget harus diulang dengan learner baru. M3: **no-go untuk v0.2**.

## Protokol v0.3 (8 November 2026)

Lihat [PROTOCOL_v0.3.md](../PROTOCOL_v0.3.md). v0.2 diarsipkan pada tag `protocol-v0.2` (lock v0.2 terverifikasi di sana). v0.3 mempertahankan simulasi v0.2
dan mengganti learner (gamma 0,97). Gerbang fidelity v0.3 (aturan terdaftar sebelum dijalankan, ambang sama dengan v0.2, referensi F) **gagal pada semua K**
(median Spearman tertinggi 0,476 pada 30.720); audit lulus. **M3 v0.3: no-go.** Tidak ada lock v0.3; P11 tidak dijalankan. Keputusan berikutnya (desain v0.4
atau penghentian dengan laporan hasil) ada pada peneliti.
