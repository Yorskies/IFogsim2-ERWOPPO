# P02 — Event engine, CPU, dan siklus tugas

Status: **complete — verifikasi lokal**.
Tanggal: 8 November 2026. Spesifikasi penelitian v0.2; wire `research-v2.1`.
Git HEAD awal `667eb4220c6ca5fb9a3fb487bb92c5cdd9e62dbc`; perubahan P02 masih di
working tree, belum commit/push.

## Tujuan dan batas perubahan

Membuktikan bahwa tugas diproses melalui event engine CloudSim dengan host/VM/PE/Cloudlet
nyata, FCFS bounded, admission, deadline/timeout, pembatalan, dan horizon, bukan melalui rumus
transisi custom seperti socket legacy. Tidak ada jaringan nyata (P03), ledger energi (P04),
socket/Gym (P05), atau policy. Source dan hasil legacy tidak diubah.

## Deliverable

| Deliverable | Lokasi |
|---|---|
| Adapter scheduler: antrean bounded, FCFS, PE dipin (ID terkecil), cancel yang melepas PE | `ifogsim/src/org/fog/erwo/v2/BoundedFcfsScheduler.java` |
| Node: `Host` + `VmSchedulerSpaceShared` + `Vm`, admission CPU lalu RAM, akuntansi RAM dan busy PE-seconds | `ComputeNode.java` |
| Koordinator episode: antrean berurutan `(at_s, prioritas, task_id, sequence)`, generasi event, commit terminal tunggal, horizon | `EngineCoordinator.java` |
| Driver headless dengan aksi tetap dan factory topologi 100+5+1 | `EngineMain.java`, `NodeSpec.java`, `TaskSpec.java`, `Json.java` |
| Akses Python (hanya membuat skenario dan membaca hasil) | `research_v2/engine_runner.py` |
| 21 tes: C01–C08 dan jalur kegagalan | `tests/research_v2/test_engine.py` |
| Audit milestone dan laporan mesin | `research_v2/verify_engine.py`, [P02_verification.json](P02_verification.json) |

## Keputusan desain

1. **Peran CloudSim.** CloudSim menyediakan clock, future-event queue, objek `Host`/`Vm`/`Pe`/`Cloudlet`,
   dan scheduler space-shared yang diadaptasi. Antrean event CloudSim mengurutkan waktu sama menurut
   serial penyisipan dan `clock + delay` dapat menggeser waktu mutlak satu ulp. Koordinator karena itu
   memegang antrean sendiri dengan timestamp persis dan hanya meminta satu event WAKE dari CloudSim;
   seluruh kelompok waktu yang sama (termasuk rantai zero-delay) diproses sebelum tidur lagi. Log dan
   outcome memakai nilai tersimpan, bukan `CloudSim.clock()`. Clock native dicatat saat event horizon
   (`native_clock_at_horizon_s`, selisih ≤ 1e-9 dari 69 s) karena CloudSim me-reset clock statisnya di akhir run.
2. **Progres CPU tidak memakai penghitung native.** `Cloudlet.getRemainingCloudletLength` membulatkan
   ke bawah ke MI, sehingga sisa kurang dari 1 MI dianggap selesai (hingga 2 ms pada 500 MIPS). Waktu
   selesai dijadwalkan persis sebagai `mulai + MI / MIPS`; objek Cloudlet membawa status, daftar
   exec/waiting, dan `usedPes`.
3. **Adapter menonaktifkan jalur native yang berbahaya.** `cloudletSubmit` (waiting tak terbatas, tambah
   file-transfer ke panjang), `cloudletCancel` (tidak melepas `usedPes`), pause/resume, dan
   `updateWaitingCloudlets` melempar `UnsupportedOperationException`. Admission dan cancel hanya lewat
   `admit()` / `cancel()` / `finish()`.
4. **Urutan admission:** antrean CPU/PE dahulu (`CPU_QUEUE_FULL`), kemudian RAM (`RAM_EXHAUSTED`).
   Spesifikasi tidak menetapkan urutan ini; jika keduanya terpenuhi sekaligus, alasan yang dicatat adalah
   antrean CPU. Tolak tidak menahan PE, antrean, atau RAM, dan tidak ada rerouting.
5. **RAM** = `working_set + input + output` byte, ditahan dari admission sampai CPU selesai atau dibatalkan
   (spesifikasi: "dilepas saat selesai/gagal"). Buffer hasil selama pengembalian hasil belum dimodelkan;
   P03 perlu memutuskan apakah buffer output ditahan sampai hasil terkirim.
   *Diputuskan di P03:* buffer hasil tidak ditahan setelah CPU selesai; batasnya adalah antrean link.
6. **Toleransi 1e-9 s.** Urutan antrean memakai waktu persis. Untuk task yang sama, completion/delivery
   dalam 1e-9 s setelah instan deadline/timeout diproses lebih dulu (`boundary_tolerance_drains`), sehingga
   keberhasilan tepat di batas konsisten dengan spesifikasi tanpa comparator berbasis epsilon.
7. **Transport fixture berlabel.** Task yang targetnya IoT asal tidak melewati jaringan. Task offload
   melewati konstanta `input_delay_s`/`result_delay_s` (default 0) dan hasil engine memuat label
   `FIXTURE_ZERO_NETWORK`. Hasil ini bukan benchmark sistem.

## Verifikasi dan hasil aktual

```powershell
$jdk = "$env:USERPROFILE\.jdks\jdk-21.0.13.0.2+1"
venv\Scripts\python.exe ifogsim\build_v2.py --jdk-home $jdk --self-test
venv\Scripts\python.exe -m research_v2.verify_engine --jdk-home $jdk
```

**21 tes lulus; 0 failure, 0 error, 0 skip.** Jalur penting:

- **C01–C08** lulus sesuai nilai analitis di [ACCEPTANCE_TESTS.md](../ACCEPTANCE_TESTS.md): CPU 0,2 s
  dan Cloudlet native berstatus `SUCCESS`; mulai 0/0,2/0,4; dua PE (PE 0/1/0); antrean penuh; RAM 101>100
  byte; ON_TIME/LATE/LATE-di-timeout; timeout memotong 300 MI dan melepas PE; horizon 69 s.
- **Prioritas** completion dan timeout sebelum arrival, dengan ID task yang datang lebih kecil daripada yang
  selesai, agar hanya lapisan prioritas yang dapat memberi hasil benar. Kedatangan serentak dilayani menurut ID.
- **Toleransi batas** 5e-10 s dan 2e-9 s di sekitar deadline dan timeout.
- **Timeout saat transfer input dan saat pengembalian hasil**: event usang dibatalkan, node tidak tersentuh,
  RAM kembali nol.
- **Input tidak valid ditolak, bukan diperbaiki**: kedatangan di `t >= T`, timeout setelah horizon, N=0, ID ganda,
  target tidak dikenal, IoT menerima offload IoT lain, node ganda, field antrean hilang, `cpu_mi` pecahan.
- **Determinisme**: tiga episode berurutan dalam satu JVM identik, dan identik dengan JVM terpisah.
- **Topologi**: 106 node (100 IoT, F1–F5, cloud); total MIPS fog 14.000 pada mode heterogen maupun homogen.
- **Trace kalibrasi P01 nyata** (light, moderate, heavy, dynamic) pada topologi penuh: konservasi
  `N = ontime + late + failed`; tidak ada node yang melampaui PE, antrean, atau RAM; semua node kosong di akhir;
  busy PE-seconds setiap node cocok dengan jumlah `MI dieksekusi / MIPS` yang dihitung ulang dari catatan task.
  Memaksa semua heavy ke F1 menghasilkan `CPU_QUEUE_FULL` dan antrean F1 tepat 16.

### Pemeriksaan efektivitas tes (mutation)

Tiga bug disuntikkan satu per satu pada salinan kerja, lalu dikembalikan dan JAR dibangun ulang:

| Mutan | Hasil |
|---|---|
| Urutan event mengabaikan prioritas domain | Dibunuh oleh 3 tes (C06 dan dua tes prioritas). Sebelum tes prioritas diperkuat, hanya C06 yang membunuhnya karena ID kecil kebetulan selaras dengan prioritas. |
| `cancel` tidak melepas `usedPes` (hazard audit P00) | Dibunuh oleh 6 tes berbeda (9 entri error termasuk subtest), di antaranya C07 dan tes trace nyata. |
| Promosi satu waiting per update (perilaku stock) | **Selamat.** Mutan ini ekuivalen: setiap pelepasan membebaskan tepat satu PE, sehingga hazard stock itu tidak dapat muncul pada desain berbasis event ini. Loop promote-all bersifat defensif. Nama dan komentar tes C03b diperbaiki agar tidak mengklaim lebih. |

## Risiko dan keterbatasan tersisa

- Jalur error "tugas unresolved saat horizon" ada di kode tetapi tidak dapat dicapai lewat skenario valid
  (timeout setelah horizon sudah ditolak saat load); jalur pemeriksaan itu sendiri tidak diuji langsung.
- Isolasi state statis hanya dibuktikan untuk clock/queue CloudSim dan objek engine. `FogDevice`, `TimeKeeper`,
  `FogUtils`, dan `NetworkUsageMonitor` belum diinstansiasi dan harus diaudit ulang bila dimasukkan (P03–P04).
- Tidak ada model jaringan, energi, atau metrik fisik. `busy_pe_seconds` dicatat sebagai prasyarat integral
  daya P04, belum ledger energi.
- Waktu CPU dihitung eksak sebagai MI/MIPS, bukan lewat progres native. Cloudlet dipakai untuk status dan
  daftar scheduler.
- Verifikasi dilakukan di Windows, Python 3.12.6, dan Microsoft OpenJDK 21.0.13. Ubuntu belum diuji.
- JAR masih bernama `research-v2-foundation.jar` dengan main class `FoundationMain`; engine dijalankan lewat
  `org.fog.erwo.v2.EngineMain` pada classpath yang sama.

## Keputusan dan phase berikutnya

- [x] Tujuan, batas, dan keputusan desain dicatat.
- [x] Acceptance C01–C08 dan jalur kegagalan dijalankan dengan hasil tersimpan.
- [x] Efektivitas tes diperiksa dengan bug yang disuntikkan.
- [x] Legacy tidak diubah; trace P01 tidak diubah.
- [x] Keterbatasan dinyatakan.

**Lanjut ke P03 — transport jaringan:** lima kanal akses half-duplex, link LAN/WAN full-duplex, antrean
transfer FCFS, serialization terpisah dari propagasi, rute lokal/fog/cloud dan hasil balik, serta pembatalan
transfer parsial saat timeout. P03 menggantikan transport fixture dan harus memutuskan perlakuan buffer
output (lihat keputusan 5).
