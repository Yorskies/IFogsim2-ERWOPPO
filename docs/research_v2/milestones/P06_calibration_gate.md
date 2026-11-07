# P06 — Baseline deterministik dan gerbang kalibrasi fisik

Status: **complete — semua gerbang lulus (verifikasi lokal)**.
Tanggal: 8 November 2026. Spesifikasi penelitian v0.2; wire `research-v2.1`.
Git HEAD awal `e4f6c5efc85e512fa52ce67d0b116faf2bbcf2a0` (P05); perubahan P06 masih di working tree, belum commit/push.

Laporan lengkap, grafik, dan data mentah: [`results/research_v2/P06_calibration/`](../../../results/research_v2/P06_calibration/calibration_report.md).

## Tujuan dan batas perubahan

Memastikan model fisik layak diteliti sebelum biaya training dikeluarkan: empat baseline deterministik dijalankan pada 20 trace
kalibrasi per workload, pada konfigurasi fog heterogen (utama) dan homogen (kontrol), lalu tiga gerbang §24.2 dievaluasi.
Tidak ada PPO, pencarian bobot, atau trace validasi/test. Tidak ada parameter yang diubah, dan tidak ada seed yang dipilih.

## Deliverable

| Deliverable | Lokasi |
|---|---|
| Always-local, Nearest-fog, Least Fog, Greedy-EFT dari snapshot publik 108 fitur | `research_v2/baselines.py` |
| Analisis solo-task, runner yang dapat dilanjutkan, agregasi, dan evaluasi gerbang | `research_v2/calibration.py` |
| Grafik dan laporan Markdown dari baris mentah, snapshot parameter | `research_v2/calibration_report.py` |
| 640 episode (2 konfigurasi × 4 workload × 20 trace × 4 baseline) | `results/research_v2/P06_calibration/rows-*.jsonl` |
| Laporan, ringkasan, snapshot parameter, lima grafik SVG | `calibration_report.md`, `calibration_summary.json`, `parameter_snapshot.json`, `*.svg` di folder yang sama |
| 19 tes | `tests/research_v2/test_calibration.py` |
| Audit milestone | `research_v2/verify_calibration.py`, [P06_verification.json](P06_verification.json) |
| Pin dependency grafik | `requirements-v2-calibration.txt` |

## Baseline (§20.3)

Semua kebijakan membaca hanya snapshot mentah publik yang sama dengan PPO. Tes memberi mereka dict yang berisi tepat 108 kunci
kontrak dan mencatat setiap pembacaan; tidak ada akses lain, tidak ada masker admission, tidak ada reservasi, dan tidak ada
pembacaan kedatangan masa depan.

- **Always-local**: aksi 0. **Nearest-fog**: fog tempat IoT terpasang.
- **Least Fog**: fog dengan `(sisa MI berjalan + MI antre) / total MIPS` terkecil; hanya lima fog. Tie dalam 1e-9 s memakai jalur
  transfer lebih singkat, dengan tafsir **jumlah estimasi delay input dan hasil** (spesifikasi tidak merinci arti "lebih singkat"),
  lalu ID node terkecil.
- **Greedy-EFT**: `Tin + W + MI/MIPS_per_PE + Tout`, `W = max(0, PE_bebas_pertama + MI_antre/MIPS − Tin)`, atas tujuh tujuan; tie
  ke ID terkecil.

## Gerbang dan tafsirnya (ditetapkan di kode sebelum gerbang dievaluasi)

Ambang diambil dari `config["pilot"]`, bukan angka baru. Tafsir berikut tertulis di docstring `evaluate_gates`:

1. **Kelengkapan**: seluruh 640 episode ada, agar gerbang tidak lulus pada run parsial.
2. **Distribusi trace**: pemeriksaan P01 yang sudah ditetapkan lulus pada 80 trace.
3. **Solo-task**: pada setiap konfigurasi, dipooling atas seluruh tugas kalibrasinya, ≥ 95% tugas punya tujuan yang menerima hasil
   sebelum deadline lunak `D` saat sendirian pada sistem kosong. Kedua konfigurasi harus lulus (bukan rata-ratanya).
4. **Tekanan heavy**: untuk sedikitnya satu (konfigurasi, baseline), rata-rata fraksi gagal heavy `> 1%` **dan** reliability `> 50%`.
   Klausa "tekanan resource terukur" saya tafsirkan sebagai tercakup oleh fraksi gagal > 1%; indikator deskriptif (utilisasi, antrean,
   penolakan) tetap dilaporkan.

**Pengungkapan.** Sebelum menulis kode evaluasi gerbang saya menjalankan uji asap satu trace (light dan heavy, trace 0, heterogen,
empat baseline) dan melihat hasilnya. Ambang dan kata-kata gerbang berasal dari spesifikasi dan config dan tidak diubah sesudahnya;
tafsir klausa (4) ditulis sebelum 640 episode selesai.

## Hasil

| Gerbang | Hasil | Rincian |
|---|---|---|
| Kelengkapan | LULUS | 640 dari 640 |
| Distribusi trace | LULUS | 80 trace |
| Solo-task ≥ 95% | LULUS | heterogen 98,8% (77.030 dari 77.936); homogen 98,8% (77.025 dari 77.936) |
| Tekanan heavy | LULUS | 4 dari 8 kondisi: always-local dan Greedy-EFT pada kedua konfigurasi |

**Solo-task per kelas**: light 100,0%, medium 98,5%, heavy 95,8% (kelas heavy hanya 0,8 poin di atas ambang). Sebanyak 906 tugas
(1,162%, heterogen) dan 911 tugas (1,169%, homogen) tidak punya rute yang memenuhi deadline walaupun sendirian, sehingga violation
tidak mungkin di bawah sekitar 1,2% pada trace ini untuk kebijakan apa pun.

**Heavy** (rata-rata 20 trace, heterogen): fraksi gagal / reliability = always-local 21,9% / 0,781; Greedy-EFT 4,6% / 0,954;
Nearest-fog 84,0% / 0,160; Least Fog 81,7% / 0,183. Dua yang terakhir runtuh karena kanal akses jenuh (utilisasi maksimum 0,90,
antrean 25 pesan dari batas 64) dan seluruh kegagalannya berupa timeout; kedua kondisi itu **tidak** memenuhi klausa reliability.

### Apakah masalahnya trivial, infeasible, atau kurang teridentifikasi?

- **Tidak infeasible**: 98,8% tugas layak saat sendirian, dan Greedy-EFT mencapai reliability 0,954–0,998.
- **Tidak trivial**: reliability seluruh sel berkisar 0,160–0,998 dan tidak satu pun kebijakan menang mudah pada beban berat
  (`D` heavy terbaik 0,405).
- **Pilihan aksi berpengaruh**: selisih `D` antar baseline 0,26–0,34 pada setiap kondisi. Pembagian aksi juga berbeda tajam:
  Greedy-EFT memakai cloud dan F5 pada light, tetapi 51% lokal pada heavy.
- **Kondisi dapat dibedakan secara empiris** (masukan milestone M1): pada Nearest-fog heterogen, utilisasi kanal akses maksimum
  0,22 / 0,59 / 0,90 untuk light / moderate / heavy; moderate dan dynamic (laju rata-rata sama) berbeda: gagal 33,1% vs 59,1%,
  antrean akses 12 vs 25.

## Temuan yang perlu diketahui pembaca hasil berikutnya

1. **`zB` bernilai 0 untuk kebijakan apa pun yang tidak memakai fog** (simpangan baku utilisasi fog nol). Akibatnya Always-local
   memperoleh `D` heavy 0,405 yang lebih kecil daripada Greedy-EFT (0,450), walaupun reliability-nya 0,781 berbanding 0,954, karena
   `zB` Greedy-EFT 0,762. Ini sifat definisi spesifikasi, bukan bug; saya tidak mengubahnya. Konsekuensinya: `D` saja dapat
   menghargai kebijakan yang menganggurkan fog, jadi laporan harus menyertakan lima biaya dan metrik fisik, sesuai §16.3.
2. **Pada analisis solo, tujuan terbaik hampir selalu cloud** (homogen 94,9%; heterogen 72,9% cloud dan 27,1% F5) dan **tidak pernah
   IoT lokal**. Fog F1–F4 baru menarik ketika cloud dan F5 terbebani.
3. **Antrean jaringan tidak pernah penuh pada baseline mana pun** (maksimum 25 dari 64 pesan); kegagalan berupa timeout atau penolakan
   antrean CPU IoT (Always-local: rata-rata 36,6 penolakan per trace heavy).
4. **Estimator EFT bersifat optimistis**: median |galat| 0,000–0,024 s (tepat bila tidak ada kontensi), tetapi p95 0,35–1,03 s dan
   latensi nyata ≥ estimasi pada 77–89% keputusan, karena estimasi tidak melihat kontensi yang belum terjadi. Pada tugas tunggal pada
   sistem kosong estimasinya sama dengan hasil engine hingga 1e-9 s (diuji).
5. Kelayakan heterogen dan homogen sama pada satu desimal (selisih 5 tugas); perbedaan konfigurasi baru muncul pada hasil berbeban,
   mis. Nearest-fog moderate gagal 33,1% (heterogen) vs 23,9% (homogen).

## Verifikasi

```powershell
$jdk = "$env:USERPROFILE\.jdks\jdk-21.0.13.0.2+1"
venv\Scripts\python.exe -m research_v2.calibration run --mode heterogeneous   # dan --mode homogeneous
venv\Scripts\python.exe -m research_v2.calibration_report
venv\Scripts\python.exe -m research_v2.verify_calibration --jdk-home $jdk
```

**19 tes lulus; 0 failure, 0 error, 0 skip.** Regresi pada build yang sama: P00 23/23, P01 49/49, P02 21/21, P03 17/17, P04 16/16,
P05 28/28.

- **Logika baseline** dengan angka hitungan tangan, termasuk W yang dibatasi nol, tie 1e-9, dan tidak adanya masker admission.
- **Audit snapshot**: setiap kebijakan hanya membaca kunci kontrak; kebijakan murni dan tidak memodifikasi snapshot.
- **Waktu solo analitis sama dengan engine**: 18 tugas × 7 tujuan × 2 konfigurasi dijalankan sendirian (jarak 10 s) dan waktu terima
  cocok hingga 1e-9 s, atau engine memang menghasilkan timeout bila analitis melebihi batas layanan.
- **Estimator EFT eksak pada tugas tunggal** dan sama dengan waktu solo terbaik pada sistem kosong.
- **Logika gerbang** pada baris sintetis, termasuk batas tepat (`> 1%`, `> 50%`, `≥ 95%`), run parsial, dan agregasi per trace.
- **Bukti tersimpan**: audit menghitung ulang seluruh gerbang dan angka laporan dari 640 baris dan trace yang dibangkitkan ulang, dan
  harus sama dengan `calibration_summary.json`; setiap baris membawa hash JAR build ini dan hash config kanonik.
- **Replikasi**: seluruh 640 episode dijalankan dua kali pada JVM berbeda. Seluruh nilai terukur identik pada semua baris (hanya waktu
  dinding berbeda, ditambah dua field provenance yang baru ditambahkan pada pass kedua).

### Pemeriksaan efektivitas tes (mutation)

Tujuh bug disuntikkan pada kode Python, lalu dikembalikan dan diverifikasi identik:

| Mutan | Hasil |
|---|---|
| Jalur solo fog lain kehilangan satu hop LAN | Dibunuh (147 entri, termasuk perbandingan dengan engine) |
| EFT mengabaikan transfer hasil | Dibunuh |
| Least Fog ikut menimbang cloud | Dibunuh |
| W pada EFT tidak dibatasi nol | Dibunuh |
| Gerbang heavy memakai `≥` pada ambang kegagalan | Dibunuh |
| Gerbang solo merata-ratakan dua konfigurasi | **Selamat pada percobaan pertama**: kasus uji saya (0,99 dan 0,90) juga gagal di bawah rata-rata. Diperbaiki dengan 1,0 dan 0,94 (rata-rata 0,97 lolos, satu konfigurasi gagal); kini dibunuh |
| Agregasi per tugas, bukan per trace | Dibunuh |

## Risiko dan keterbatasan tersisa

- Gerbang heavy lulus lewat 4 dari 8 kondisi; Nearest-fog dan Least Fog runtuh pada heavy. Gerbang hanya meminta satu kondisi.
- Analisis solo bersifat analitis pada sistem kosong dan deadline lunak, diverifikasi pada sampel tugas (bukan setiap tugas).
- Satu pass atas 20 trace kalibrasi yang sudah ditetapkan; tidak ada yang dipilih atau diganti. Ini bukan bukti tentang split validasi atau test.
- Ambang dan angka acuan adalah konvensi spesifikasi; "lulus" tidak membuktikan bahwa parameter sintetis realistis.
- Pass kalibrasi pertama (tanpa field provenance) tidak disimpan di repo; kesamaannya dengan pass kedua diverifikasi sebelum dibuang.
- Verifikasi hanya di Windows, Python 3.12.6, Microsoft OpenJDK 21.0.13. Ubuntu belum diuji.

## Keputusan dan phase berikutnya

- [x] Gerbang §24.2 dijalankan; semuanya lulus tanpa penyetelan parameter.
- [x] Tafsir gerbang dan pengungkapan uji asap dicatat.
- [x] Baseline hanya memakai snapshot publik yang sama dengan PPO (diaudit).
- [x] Evaluasi ulang independen dan replikasi 640 episode identik.
- [x] Efektivitas tes diperiksa; satu celah ditemukan dan ditutup.
- [x] Temuan yang tidak menyenangkan (`zB`, sekitar 1,2% tugas tak layak, estimator optimistis) dicatat, bukan disetel.

**Milestone M1 (tinjauan manusia)**: model fisik tervalidasi dan kondisi eksperimen dapat dibedakan secara empiris. Bukti ada di sini;
keputusan melanjutkan ke P07 adalah keputusan tinjauan. **Lanjut ke P07 — PPO dan pilot pembelajaran**: policy 108 fitur, Discrete(7),
MLP 128–128, training campuran empat workload, smoke 512 dan pilot 10.240 keputusan. Temuan 1 di atas penting untuk membaca hasil
PPO: `D` yang lebih kecil belum berarti layanan yang lebih baik.
