# Implementation plan dan milestone penelitian ERWO-PPO v2

Tanggal: 3 November 2026 (diperbarui 8 November 2026). Status: **P00–P04 selesai dan terverifikasi lokal; P05–P12 belum dimulai**.

Phase pertama yang telah dikerjakan adalah **P00 — Kontrak dan fondasi proyek**. Bukti: [catatan P00](docs/research_v2/milestones/P00_foundation.md) dan [laporan verifikasi](docs/research_v2/milestones/P00_verification.json): 23 tes lulus, tanpa failure/error/skip. Build menargetkan Java 21; lingkungan aktual Windows/Python 3.11/JDK 27. Pengujian langsung Ubuntu/Python 3.12/JDK 21 tetap menjadi preflight server sebelum penguncian protokol P10.

**P01 — Konfigurasi dan generator trace** juga selesai. Bukti: [laporan P01](docs/research_v2/milestones/P01_trace_validation.md) dan [verifikasi mesin](docs/research_v2/milestones/P01_verification.json): 49 tes lulus, 80 trace calibration, serta 468/468 pemeriksaan distribusi lulus. Test tetap tersegel; belum ada eksekusi offloading atau training v2.

**P02 — Event engine dan siklus tugas** selesai pada 8 November 2026. Bukti: [laporan P02](docs/research_v2/milestones/P02_engine_validation.md) dan [verifikasi mesin](docs/research_v2/milestones/P02_verification.json): 21 tes lulus, acceptance C01–C08 lulus, serta empat trace kalibrasi nyata berjalan sampai horizon dengan konservasi task. Transport P02 adalah fixture nol-jaringan.

**P03 — Transport jaringan** selesai pada 8 November 2026. Bukti: [laporan P03](docs/research_v2/milestones/P03_network_validation.md) dan [verifikasi mesin](docs/research_v2/milestones/P03_verification.json): 17 tes lulus, acceptance N01–N06 lulus, regresi P00–P02 lulus pada build yang sama. Belum ada ledger energi, socket, atau training.

**P04 — Ledger energi dan lima metrik** selesai pada 8 November 2026. Bukti: [laporan P04](docs/research_v2/milestones/P04_accounting_validation.md) dan [verifikasi mesin](docs/research_v2/milestones/P04_verification.json): 16 tes lulus, acceptance E01–E04 dan M01–M03 lulus, serta evaluator Python independen cocok dengan ledger Java pada trace kalibrasi nyata. Belum ada socket, reward, atau training.

Dasar teknis: [Kesepakatan Rancangan Penelitian v0.2](KESEPAKATAN_RANCANGAN_PENELITIAN.md). Latar temuan dan tujuan perbaikan: [Rencana Penelitian Lanjutan](RENCANA_PENELITIAN_LANJUTAN.md).

Dokumen ini mengatur urutan kerja, dependensi, deliverable, verifikasi, dan kriteria kelulusan. Nilai parameter mengikuti spesifikasi v0.2. Perubahan substansial setelah pilot harus dicatat sebagai revisi protokol sebelum hasil test dibuka.

## 1. Aturan pengerjaan

1. Kerjakan satu phase sampai mempunyai bukti kelulusan yang dapat ditinjau. Phase berikutnya dimulai setelah dependensinya terpenuhi.
2. Pertahankan kode, model, dan hasil lama sebagai implementasi legacy. Jangan mengganti label hasil lama menjadi hasil event engine v2.
3. Bangun jalur minimum yang benar terlebih dahulu, kemudian tambah skala, pembelajaran, dan optimasi. Training panjang bukan pengganti validasi simulator.
4. Setiap milestone menghasilkan artefak yang dapat diperiksa: source/config, hasil verifikasi, dan catatan batasan.
5. Validasi fisik dan kalibrasi tidak memilih parameter berdasarkan kemenangan ERWO.
6. Test final tetap terpisah dari pengembangan, kalibrasi, tuning, dan pemilihan bobot.
7. Tidak ada fallback diam-diam ke engine Python. Kegagalan teknis atau invariant menghentikan run dan dicatat.
8. Implementasi awal mendukung resume pada **batas run yang sudah selesai**. Run terputus diulang dari awal dengan seed sama; resume partial simulator bukan syarat awal.
9. Commit dibatasi pada milestone yang dikerjakan. Artefak eksperimen tidak diunggah bersama source tanpa keputusan terpisah.

## 2. Peta milestone

| Phase | Milestone | Hasil utama | Dependensi | Status |
|---|---|---|---|---|
| P00 | Kontrak dan fondasi proyek | Struktur v2, schema, rencana validasi, build dasar | Spesifikasi v0.2 | **Selesai — verifikasi lokal 23/23** |
| P01 | Konfigurasi dan trace | Generator empat workload yang deterministik | P00 | **Selesai — verifikasi lokal 49/49** |
| P02 | Event engine dan siklus tugas | CPU, FCFS, admission, deadline, timeout, horizon | P00–P01 | **Selesai — verifikasi lokal 21/21** |
| P03 | Transport jaringan | Queue, routing, transfer input/hasil, cancellation | P02 | **Selesai — verifikasi lokal 17/17** |
| P04 | Energi dan metrik | Ledger energi serta lima biaya tervalidasi | P02–P03 | **Selesai — verifikasi lokal 16/16** |
| P05 | Socket dan Gymnasium | Protokol v2, observasi 108, reward tertunda | P01–P04 | Belum dimulai |
| P06 | Baseline dan kalibrasi | Heuristik kuat dan kelulusan model fisik | P04–P05 | Belum dimulai |
| P07 | PPO dan pilot learning | Training campuran, checkpoint, bukti belajar | P06 | Belum dimulai |
| P08 | Pencarian bobot dan fidelity | NSGA-II/random search serta pemilihan K | P07 | Belum dimulai |
| P09 | Orkestrasi dan budget | Runner studi v2, accounting biaya, resume | P08 | Belum dimulai |
| P10 | Analisis dan penguncian protokol | Statistik teruji, konfigurasi terkunci, readiness review | P06–P09 | Belum dimulai |
| P11 | Eksperimen konfirmatori | Dua protokol, 20 outer run, hasil lengkap | P10 lulus | Belum dimulai |
| P12 | Sensitivitas dan paket publikasi | Robustness, audit, reproduksibilitas, batas klaim | P11 | Belum dimulai |

Dependensi utama bersifat berurutan. Perancangan schema dan pembacaan source boleh dilakukan lebih awal, tetapi hasil downstream tidak boleh dinyatakan valid sebelum engine yang mendasarinya lulus.

## 3. Arsitektur implementasi yang dituju

Struktur berikut adalah target. Fondasi config/schema/package/build, generator dan penyimpanan trace, engine CPU/lifecycle headless (P02), transport jaringan (P03), ledger energi dan metrik (P04), serta catatan P00–P04 sudah dibuat; Gym, training, search, runner studi, dan analisis merupakan pekerjaan phase selanjutnya. Pemetaan aktual dijelaskan pada [arsitektur](docs/research_v2/ARCHITECTURE.md) dan [kontrak trace](docs/research_v2/TRACES.md).

| Area | Lokasi yang direncanakan | Tanggung jawab |
|---|---|---|
| Spesifikasi/config | `configs/research_v2/` | Parameter sistem, training, studi, dan sensitivity overrides |
| Schema | `schemas/research_v2/` | Trace, RPC, outcome, metric, manifest |
| Simulator Java | `ifogsim/src/org/fog/erwo/v2/` | Integrasi event engine dan resource accounting |
| Python v2 | `research_v2/` | Config, trace, Gym, reward, PPO, search, budget, runner, analysis |
| Entry point | `run_research_v2.py` | Menjalankan tahap studi sesuai konfigurasi |
| Pengujian | `tests/research_v2/` dan harness Java | Kasus analitis, determinisme, integrasi, serta fault handling |
| Catatan milestone | `docs/research_v2/milestones/` | Bukti kelulusan dan keputusan perubahan |
| Hasil baru | `results/research_v2/<study_id>/` | Semua output v2 terisolasi dari suite legacy |

Komponen Java minimum:

- `TaskSpec`, `TaskRuntime`, dan `TaskOutcome`: atribut tetap, state berjalan, dan terminal outcome.
- `SimulationContext` dan `DecisionCoordinator`: lifecycle episode, clock, urutan event, keputusan Python.
- `ComputeNodeFactory` dan scheduler/admission adapter: host/VM/PE nyata, FCFS bounded, cancellation.
- `LinkEntity`/transport layer: kanal, antrean, byte, propagasi, dan jalur hasil balik.
- `EnergyLedger` dan `MetricAccumulator`: satu sumber accounting dan integral waktu.
- `V2SocketServer`: protokol berversi yang terpisah dari server legacy.

Java tetap menjadi sumber kebenaran kejadian dan outcome fisik. Python mengatur trace, tindakan policy, training, pencarian, dan analisis. Metrik dapat dihitung ulang dari log oleh evaluator independen untuk pemeriksaan silang.

## 4. P00 — Kontrak dan fondasi proyek

**Tujuan:** memastikan implementasi punya batas modul, unit, schema, dan build yang jelas.

Pekerjaan:

- [x] Catat Git SHA dan arsip konfigurasi/hash hasil legacy tanpa memindahkan atau menimpa suite lama.
- [x] Buat struktur package v2 dan namespace output terpisah.
- [x] Turunkan parameter dokumen kesepakatan menjadi config tervalidasi; satuan harus eksplisit.
- [x] Definisikan schema task, resource, route, event, outcome, cost vector, trace, dan manifest.
- [x] Tetapkan penamaan lima objektif serta urutan fitur/aksi secara konsisten lintas Java–Python.
- [x] Definisikan prioritas event bertimestamp sama, toleransi waktu, terminal state, dan aturan idempotensi.
- [x] Audit API CloudSim/FogDevice yang diperlukan: scheduler, penghentian cloudlet, reset state statis, dan pengiriman event.
- [x] Siapkan build portabel Ubuntu/Windows, target Java 21, dengan artefak khusus v2 serta main class berbeda; build dan runtime probe teruji pada Windows/JDK 27, belum dieksekusi di Ubuntu/JDK 21.
- [x] Catat lingkungan yang berhasil dipakai serta pin/inventaris hash dependency fondasi aktual; lock Python 3.12/Linux belum diklaim tersedia dan harus divalidasi di server sebelum P10.
- [x] Buat daftar acceptance test berdasarkan bagian 24 spesifikasi, sebelum menambah training.

Deliverable: config/schema awal, catatan arsitektur, build minimum, serta `P00_foundation.md`.

**Kriteria lulus:** config invalid ditolak, unit tidak ambigu, package v2 dapat dibangun, legacy tidak ikut berubah perilakunya, dan setiap acceptance test mempunyai hasil yang diharapkan.

**Hasil aktual:** lulus pada lingkungan lokal. Konfigurasi/schema tervalidasi, kontrak Java–Python identik, JAR foundation bytecode Java 21 berhasil dibangun, probe event native lulus, 17 tes fondasi dan 6 regression test legacy lulus. Hash 451 source legacy serta 1.286 file hasil lama tetap sama. JAR ini belum merupakan task simulator/socket v2. Rincian dan keterbatasan: [P00_foundation.md](docs/research_v2/milestones/P00_foundation.md).

## 5. P01 — Konfigurasi dan generator trace

**Tujuan:** menghasilkan workload eksternal yang sama untuk semua metode dan terpisah dari RNG policy.

Pekerjaan:

- [x] Implementasikan tiga kelas tugas beserta MI, ukuran input/hasil, deadline, working set, dan source IoT.
- [x] Implementasikan arrival Poisson tetap dan piecewise nonhomogeneous Poisson untuk dynamic melalui integrated hazard.
- [x] Implementasikan pemetaan 100 IoT ke lima fog akses.
- [x] Pisahkan RNG arrival, source, class, MI, data, dan deadline melalui namespace SHA-256/PCG64 yang ditetapkan.
- [x] Buat pemisahan calibration/pilot/train/validation/test dan larang peran yang salah mengakses split.
- [x] Ekspor trace immutable dengan task ID, satuan, konfigurasi, jumlah task, dan hash.
- [x] Tentukan representasi numerik timestamp yang dapat diputar ulang Java tanpa kehilangan presisi bermakna.
- [x] Buat laporan karakteristik trace: jumlah kedatangan, distribusi kelas/atribut, serta arrival per interval waktu.
- [x] Buat trace khusus validasi deterministik, termasuk kedatangan bersamaan dan batas deadline/timeout.

Deliverable: generator, trace schema, trace fixture, dan laporan `P01_trace_validation.md`.

**Kriteria lulus:** seed sama menghasilkan hash sama; aksi/metode tidak memengaruhi trace; jumlah task per profil konsisten dengan model; dynamic menunjukkan empat fase dan berbeda dari moderate; source dan task ID valid.

Batas tahap: test trace boleh disiapkan sebagai artefak terkunci, tetapi belum digunakan untuk membandingkan metode.

**Hasil aktual:** lulus pada lingkungan lokal, 49 tes tanpa failure/error/skip; 80 trace calibration berisi 77.936 task dan 468/468 pemeriksaan distribusi lulus. Rata-rata count light/moderate/heavy/dynamic = 307,6/907,4/1.797,5/884,3 per trace. Dynamic memperlihatkan empat fase dan atribut task berbeda dari moderate pada seluruh 20 ID. Replay timestamp Python–Java identik secara binary64. Bundle immutable dan guard split teruji. Rincian: [P01_trace_validation.md](docs/research_v2/milestones/P01_trace_validation.md). Kelulusan ini belum memvalidasi engine CPU/jaringan/QoS.

## 6. P02 — Event engine, CPU, dan siklus tugas

**Tujuan:** membuktikan bahwa tugas diproses melalui event engine, bukan rumus transisi custom.

Pekerjaan:

- [x] Bangun kasus satu IoT/satu node dahulu, kemudian factory topologi 100 IoT–5 fog–1 cloud.
- [x] Buat host, VM/module, PE, dan Cloudlet nyata; jangan mengaktifkan overbooking atau scheduler time-shared secara tidak sengaja.
- [x] Implementasikan FCFS satu PE per tugas, multi-PE per node, bounded waiting queue, dan admission RAM.
- [x] Implementasikan deadline flag, timeout proporsional, terminal outcome, dan penolakan tanpa rerouting.
- [x] Implementasikan pembatalan cloudlet/queue, pelepasan resource, serta invalidasi event usang.
- [x] Implementasikan T=60 s, drain sampai H=69 s, dan pencatatan tugas unresolved sebagai error. (Pencegahan saat load teruji; jalur error di event horizon tidak teruji langsung.)
- [x] Terapkan prioritas completion/delivery, deadline/timeout, lalu external arrival pada waktu sama.
- [x] Pastikan reset episode menghapus state statis yang relevan dan tidak meninggalkan event/resource. (Teruji untuk clock/queue CloudSim dan objek engine; `FogDevice`/`TimeKeeper`/`NetworkUsageMonitor` belum diinstansiasi.)
- [x] Sediakan headless driver dengan tindakan tetap agar validasi tidak bergantung pada Python/RL.

Deliverable: engine CPU dan lifecycle, task/event log awal, serta `P02_engine_validation.md`.

**Kriteria lulus:** MI/MIPS menghasilkan waktu yang benar; FCFS dan kapasitas PE benar; task tidak menyalip antrean; deadline tidak membatalkan tugas; timeout tidak menghidupkan kembali tugas; hasil tepat pada batas mengikuti aturan; konservasi task terpenuhi.

Validasi pada fase ini boleh menggunakan jalur lokal atau jaringan nol-delay yang jelas diberi label fixture. Hasil fixture bukan benchmark sistem lengkap.

**Hasil aktual:** lulus pada lingkungan lokal (Windows, Python 3.12.6, OpenJDK 21.0.13). 21 tes tanpa failure/error/skip; C01–C08 lulus; trace kalibrasi light/moderate/heavy/dynamic berjalan pada topologi 100+5+1 dengan busy PE-seconds yang cocok dengan penghitungan ulang independen. Tes diperiksa dengan bug yang disuntikkan: dua dari tiga mutan terbunuh, dan yang ketiga ekuivalen (lihat laporan). Rincian dan keputusan desain: [P02_engine_validation.md](docs/research_v2/milestones/P02_engine_validation.md).

## 7. P03 — Jaringan dan jalur offloading

**Tujuan:** keputusan tujuan menimbulkan serialization, propagasi, kontensi, dan energi komunikasi yang dapat ditelusuri.

Pekerjaan:

- [x] Implementasikan lima kanal akses half-duplex, link LAN full-duplex, dan WAN cloud.
- [x] Implementasikan queue transfer FCFS dengan kapasitas per server link sesuai spesifikasi.
- [x] Pisahkan serialization dari propagasi; propagasi tidak menahan server link.
- [x] Implementasikan routing lokal, fog akses, fog lain, cloud, dan jalur hasil balik.
- [x] Tugas offload masuk admission CPU setelah input tiba; tidak ada reservasi CPU pada saat aksi.
- [x] Implementasikan kegagalan queue link penuh dan pembatalan transfer aktif/menunggu/in-propagation saat timeout.
- [x] Catat byte aktual yang sudah dikirim serta event stale yang diabaikan.
- [x] Hindari menghitung file-transfer time lagi sebagai tambahan panjang Cloudlet.

Deliverable: transport layer, route ledger, serta `P03_network_validation.md`.

**Kriteria lulus:** contoh 1 MiB/20 Mbps menghasilkan serialization 0,4194304 s; multihop dan hasil balik sesuai perhitungan; kanal benar-benar berbagi kapasitas; timeout parsial tidak menggandakan completion atau menghitung byte yang belum terkirim.

**Hasil aktual:** lulus pada lingkungan lokal (Windows, Python 3.12.6, OpenJDK 21.0.13). 17 tes tanpa failure/error/skip; N01–N06 lulus; trace kalibrasi nyata berjalan tanpa tumpang tindih pada server dan mengikuti FCFS. Empat bug transport yang disuntikkan semuanya terbunuh oleh tes. Karakterisasi pada trace kalibrasi 0 menunjukkan kegagalan seluruhnya berupa timeout (antrean akses maksimum 25 dari batas 64), dan tidak ada ledger energi. Rincian dan keputusan desain: [P03_network_validation.md](docs/research_v2/milestones/P03_network_validation.md).

## 8. P04 — Ledger energi dan lima metrik

**Tujuan:** seluruh komponen energi dan biaya evaluasi dapat direkonstruksi tanpa mengandalkan reward.

Pekerjaan:

- [x] Integrasikan daya CPU-IT pada setiap perubahan utilisasi dan tutup integral tepat pada H.
- [x] Implementasikan radio/AP, LAN/WAN bit-hop, serta daya idle jaringan sesuai batas komponen.
- [x] Tentukan satu ledger resmi; counter default FogDevice tidak ditambahkan kembali.
- [x] Hitung energi parsial tugas gagal dan breakdown idle/dinamis per komponen.
- [x] Integrasikan standar deviasi utilisasi fog terhadap waktu.
- [x] Implementasikan latensi fisik completed tasks, latency penalty khusus evaluasi, violation, reliability, throughput, dan N/A yang benar.
- [x] Implementasikan zL/zE/zD/zB/zQ dan D, tanpa test-dependent normalization atau clipping yang menutupi error.
- [x] Buat evaluator ulang dari ledger untuk memeriksa hasil Java.

Deliverable: energy/metric ledger, summary fisik dan lima biaya, serta `P04_accounting_validation.md`.

**Kriteria lulus:** idle energy tidak nol; integral cocok dengan kasus analitis; total sama dengan jumlah komponen; failure tidak masuk latency fisik sebagai nol; penalti failure diberi label; `N=Nontime+Nlate+Nfailed`; nilai keluar batas utama memicu diagnosis.

**Hasil aktual:** lulus pada lingkungan lokal (Windows, Python 3.12.6, OpenJDK 21.0.13). 16 tes tanpa failure/error/skip; E01–E04 dan M01–M03 lulus; energi idle default 623,4333 W (43.016,8977 J untuk 69 s); evaluator independen cocok dengan ledger Java hingga toleransi relatif 1e-9 pada empat workload × tiga konfigurasi. Delapan bug akuntansi yang disuntikkan semuanya terbunuh oleh tes. Hanya biaya per trace yang ada; `Dglobal` adalah P10. Rincian dan keputusan desain: [P04_accounting_validation.md](docs/research_v2/milestones/P04_accounting_validation.md).

## 9. P05 — Socket v2, Gymnasium, observasi, dan reward

**Tujuan:** menyediakan kontrak Java–Python yang benar untuk hasil tertunda dan horizon fisik.

Pekerjaan:

- [ ] Implementasikan JSON Lines berversi dengan request/episode ID serta handshake source/JAR/config hash.
- [ ] Implementasikan reset ke arrival pertama, satu aksi per arrival, dan advance event engine ke keputusan berikutnya.
- [ ] Pastikan drain setelah arrival terakhir berlangsung tanpa meminta aksi palsu.
- [ ] Implementasikan observasi 108 fitur; snapshot mentah/transformasi terdokumentasi dan sama untuk semua metode.
- [ ] Implementasikan prediksi route dan queue yang hanya memakai informasi saat ini, serta EMA causal.
- [ ] Implementasikan cumulative cost dan reward `-100 × sum(w × delta_cost)` dari outcome aktual.
- [ ] Tentukan lifecycle `terminated/truncated`, koneksi putus, timeout RPC, heartbeat, dan cleanup.
- [ ] Tolak model/schema legacy 46 fitur dan konfigurasi empat bobot pada jalur v2 secara eksplisit.
- [ ] Implementasikan strict Java mode; tidak ada fallback Python pada hasil v2.

Deliverable: server v2, Gym environment v2, schema fixtures, serta `P05_gym_integration.md`.

**Kriteria lulus:** Gymnasium environment checker lolos; aksi dan observasi konsisten; jumlah step sama dengan arrival count; tidak ada future trace dalam observasi; total reward memenuhi identitas biaya; putus socket tidak menghasilkan episode sukses; dua episode berturut-turut tidak saling mencemari.

Uji end-to-end pertama menggunakan aksi tetap/random, tanpa PPO, untuk memisahkan kesalahan simulator dari kesalahan pembelajaran.

## 10. P06 — Baseline deterministik dan kalibrasi fisik

**Tujuan:** memastikan sistem layak diteliti sebelum biaya training dikeluarkan.

Pekerjaan:

- [ ] Implementasikan always-local dan nearest-fog sebagai baseline kalibrasi.
- [ ] Implementasikan Least Fog dan Greedy-EFT persis dari snapshot publik yang tersedia bagi PPO.
- [ ] Validasi estimator sebagai estimator, tanpa menggunakannya sebagai outcome nyata.
- [ ] Jalankan 20 trace kalibrasi per workload, pada homogen dan konfigurasi heterogen utama.
- [ ] Periksa solo-task feasibility, tekanan resource heavy, serta variasi reliability sesuai gerbang v0.2.
- [ ] Sajikan grafik arrival, antrean, utilisasi, energi, dan distribusi status tugas.
- [ ] Catat apakah profil daya/queue/deadline membuat masalah trivial, infeasible, atau kurang teridentifikasi.

Deliverable: `calibration_report.md`, trace/resource plots, parameter snapshot, serta `P06_calibration_gate.md`.

**Kriteria lulus:** gerbang kalibrasi pada dokumen kesepakatan terpenuhi dan belum ada pemilihan konfigurasi berdasarkan kemenangan ERWO. Jika gagal, revisi spesifikasi/config secara beralasan, beri versi, lalu ulangi kalibrasi; jangan meneruskan ke batch besar.

**Milestone tinjauan M1:** model fisik tervalidasi dan kondisi eksperimen dapat dibedakan secara empiris.

## 11. P07 — PPO dan pilot pembelajaran

**Tujuan:** memastikan model dapat belajar menggunakan lingkungan v2 dan reward lima objektif.

Pekerjaan:

- [ ] Implementasikan policy 108 fitur, Discrete(7), MLP 128–128, serta hyperparameter v0.2.
- [ ] Implementasikan training campuran workload round-robin dengan offset dan RNG yang ditetapkan.
- [ ] Pisahkan training stream dari validation/test serta dari RNG policy.
- [ ] Jalankan smoke 512 keputusan lalu pilot 10.240 pada tiga outer pilot run.
- [ ] Catat loss, entropy, KL, action distribution, cost vector, serta identitas reward.
- [ ] Pastikan gamma=1, delayed outcome, dan terminal drain tidak hilang dari return.
- [ ] Simpan model/optimizer/RNG dan checkpoint pada batas rollout.
- [ ] Pisahkan penghentian karena kuota training dari keberhasilan episode fisik. Task pending pada akhir kuota training tidak dihitung sebagai keberhasilan evaluasi.
- [ ] Validasi bahwa checkpoint F dari training lebih panjang konsisten dengan training berhenti di F pada konfigurasi konstan; evaluasi checkpoint memakai episode/server terpisah agar training stream tidak berubah.

Deliverable: smoke/pilot models, learning curves, prefix/checkpoint comparison, dan `P07_learning_pilot.md`.

**Kriteria lulus:** training finite, seed dapat diputar ulang, perubahan policy dapat ditelusuri, metric/reward konsisten, dan budget aktual cocok dengan rollout. Tidak diwajibkan PPO mengalahkan heuristik untuk menyatakan engine benar; kegagalan belajar harus didiagnosis sebelum optimasi bobot.

## 12. P08 — NSGA-II, random search, dan fidelity kandidat

**Tujuan:** mengisolasi manfaat pencarian bobot dan menguji apakah kandidat singkat cukup informatif.

Pekerjaan:

- [ ] Implementasikan lima bobot pada simplex berbatas minimum 0,02 dan repair yang mempertahankan jumlah satu.
- [ ] Implementasikan equal/manual anchors serta common initial population.
- [ ] Implementasikan candidate evaluation: dua PPO dari awal, K keputusan, validasi lima trace/workload/model, dan macro-average lima biaya.
- [ ] Implementasikan NSGA-II 20 populasi × 4 generasi serta random search total 80 slot, dengan RNG yang ditetapkan.
- [ ] Simpan semua kandidat, biaya, repeat, validation metrics, archive nondominated, D, dan pemilihan solusi seri.
- [ ] Implementasikan pemilihan solusi pada validation, bukan berdasarkan test atau reward dengan bobot masing-masing.
- [ ] Implementasikan hypervolume validasi sebagai metrik sekunder dengan reference point tetap.
- [ ] Jalankan ranking fidelity delapan bobot pada tiga outer pilot sesuai spesifikasi.
- [ ] Pilih K melalui ladder 5.120 → 10.240 → 20.480 menggunakan gerbang Spearman yang telah ditetapkan.

Deliverable: optimizer/baseline pencarian, candidate archive pilot, laporan fidelity, dan `P08_search_gate.md`.

**Kriteria lulus:** bobot feasible; slot duplikat tetap terhitung; dua pencarian mendapat biaya/validation/selection rule sama; candidate seeds tidak bercampur; K dipilih tanpa test. Jika fidelity gagal pada seluruh ladder, studi dihentikan untuk diagnosis.

**Milestone tinjauan M2:** metode pencarian dan resolusi kandidat siap dievaluasi; keberadaan Pareto archive tidak ditafsirkan sebagai jaminan optimum global.

## 13. P09 — Runner studi, accounting budget, dan pemulihan

**Tujuan:** mengotomatisasi rancangan baru tanpa membawa asumsi matriks legacy 80 run.

Pekerjaan:

- [ ] Susun manifest berdasarkan outer run, metode, search/final role, protocol A/B, dan checkpoint; workload menjadi bagian evaluasi satu policy campuran.
- [ ] Hitung Ntrace validasi, S, V, F, dan B sebelum menjalankan studi.
- [ ] Tampilkan estimasi biaya dan artefak pada dry-run; biaya validasi tidak boleh dianggap gratis.
- [ ] Implementasikan reuse search/model yang sah antara analisis A/B tanpa menghitung biaya studi dua kali.
- [ ] Implementasikan baseline B dan checkpoint F/51.200; jika prefix equivalence gagal, dokumentasikan kebutuhan training terpisah.
- [ ] Buat direktori run/attempt terisolasi, manifest atomik, checksum, serta validasi kelengkapan artefak sebelum status complete.
- [ ] Implementasikan resume completed-run, retry teknis terbatas dengan seed sama, dan penolakan resume jika source/config/JAR/trace berubah.
- [ ] Hindari dua proses menulis study/run yang sama melalui mekanisme ownership/lock yang dapat dipulihkan setelah crash.
- [ ] Ukur waktu, CPU, RAM, interaksi, update, inference/RPC, serta startup secara terpisah.
- [ ] Default satu worker; dukungan empat worker memerlukan JVM/port independen dan pembuktian hasil tidak berubah.
- [ ] Pastikan interruption tidak meninggalkan server yang salah dipakai run lain.

Deliverable: runner v2, dry-run budget report, fixture studi kecil, interruption/resume evidence, dan `P09_runner_validation.md`.

**Kriteria lulus:** studi mini dari beberapa seed selesai tanpa menimpa hasil; hasil complete tidak diulang; partial run tidak dianggap complete; crash dapat dilanjutkan sesuai kontrak; jumlah interaksi sesuai ledger; worker tidak berbagi singleton CloudSim.

Perhatian kapasitas: dengan ekspektasi trace pada spesifikasi awal, B sekitar **4,04 juta keputusan per baseline total-budget**. Angka aktual dihitung dari trace. Jangan menjalankan studi 20 outer run sebagai pengujian pertama runner.

## 14. P10 — Analisis statistik dan penguncian protokol

**Tujuan:** menetapkan seluruh aturan analisis sebelum test final dipakai membandingkan metode.

Pekerjaan:

- [ ] Implementasikan agregasi trace → workload → outer run → ringkasan antar-run.
- [ ] Implementasikan Dglobal, Dw, lima metrik fisik/biaya, uncertainty, dan biaya komputasi.
- [ ] Implementasikan tiga uji primer exact paired sign-flip dan koreksi Holm satu keluarga.
- [ ] Implementasikan 60 uji sekunder, Monte Carlo correction, serta pelabelan eksploratif yang benar.
- [ ] Implementasikan crossed paired bootstrap dengan indeks trace bersama pada model/run yang terpilih.
- [ ] Validasi dengan fixture: seluruh selisih nol, selisih bertanda sama, ties, pasangan ditukar, SD nol, dan data hilang.
- [ ] Periksa Holm terhadap contoh yang bisa dihitung manual dan implementasi referensi yang tervalidasi.
- [ ] Pastikan laporan tidak mem-pool task/episode menjadi training replicate dan tidak merata-ratakan p-value.
- [ ] Jalankan studi mini end-to-end pada namespace pilot, dengan anggaran kecil dan tanpa test final.
- [ ] Bekukan K hasil pilot, config sistem, seed/split, source/build hash, keluarga hipotesis, dan aturan sensitivity.
- [ ] Profil throughput pilot dan kapasitas penyimpanan; susun estimasi kebutuhan studi dari pengukuran, bukan perkiraan H200 semata.

Deliverable: analysis module teruji, contoh laporan mini, protocol lock, resource estimate, dan `P10_readiness_review.md`.

**Kriteria lulus:** validasi statistik dan studi mini benar; tidak ada konfigurasi tersisa yang dipilih dari hasil test; anggaran sumber daya layak; perubahan dari v0.2 tercatat.

**Milestone tinjauan M3 — go/no-go eksperimen utama:** semua invariant, kalibrasi, fidelity, budget, dan rencana analisis sudah mempunyai bukti. Jika tidak layak, revisi protokol sebelum test; jangan memangkas biaya atau seed secara diam-diam.

## 15. P11 — Eksperimen konfirmatori

**Tujuan:** menghasilkan bukti utama dari protokol yang sudah dikunci.

Pekerjaan:

- [ ] Jalankan search NSGA-II dan random search untuk outer run 0–19 dengan konfigurasi yang dibekukan.
- [ ] Latih model akhir baru dari awal; simpan checkpoint yang direncanakan.
- [ ] Latih PPO-Equal/PPO-Manual untuk protokol F sama dan total-budget sesuai kontrak reuse/checkpoint.
- [ ] Evaluasi semua model dan heuristik pada 100 trace test per workload, pasangan yang sama untuk seluruh metode/run.
- [ ] Tahan konfigurasi ketika test dibuka; temuan test dicatat, tidak digunakan untuk tuning ulang studi yang sama.
- [ ] Lakukan audit per-run pada task conservation, energi, byte, outcome, reward identity, dan biaya.
- [ ] Pertahankan seluruh hasil, termasuk seed buruk, metode kalah, dan kegagalan teknis/algoritmik.
- [ ] Susun analisis primer/sekunder sesuai P10, lengkap dengan effect dan CI.

Deliverable: seluruh model/log, dataset test per-trace/per-run, cost ledger, analysis output, dan laporan utama.

**Kriteria selesai:** 20 outer run yang direncanakan tervalidasi, artefak lengkap, tidak ada task hilang atau engine fallback, dan laporan dapat direkonstruksi dari data mentah. Bila ada run yang gagal permanen, laporkan studi belum lengkap dan alasannya; jangan mengganti seed tanpa revisi protokol.

Signifikansi atau kemenangan ERWO bukan kriteria kelulusan milestone. Bukti yang sah dan pelaporan lengkap adalah kriterianya.

## 16. P12 — Sensitivitas, audit akhir, dan paket publikasi

**Tujuan:** menentukan batas robustness dan menyediakan hasil yang bisa ditinjau ulang.

Pekerjaan:

- [ ] Evaluasi sensitivitas k, queue fog, propagasi WAN, daya dinamis, serta kapasitas/daya fog sesuai protokol.
- [ ] Gunakan model beku untuk sensitivitas zero-shot; jangan mencampurkannya dengan studi retraining.
- [ ] Tinjau sensitivitas normalisasi pada data validasi dan laporkan definisi utama secara tetap.
- [ ] Laporkan hasil metrik fisik bersama skor kompromi; label satuan dan penalti evaluasi secara eksplisit.
- [ ] Audit kesesuaian raw data, summary, statistik, model, trace, serta source/build/config hashes.
- [ ] Siapkan arsip hasil terpisah dari repo source, indeks artefak, README reproduksi, dan checksum.
- [ ] Uji reproduksi terpilih dari lingkungan bersih, sekurangnya satu kasus fisik dan satu run pembelajaran kecil.
- [ ] Susun tabel klaim didukung/tidak didukung dan batas observabilitas, model energi, workload, serta biaya.
- [ ] Perbarui pemetaan literatur terdekat sebelum menyatakan novelty atau state of the art.

Deliverable: sensitivity report, audit akhir, reproduction package, serta tabel/figur untuk manuskrip.

**Kriteria selesai:** pihak lain dapat menelusuri angka utama ke run/task/ledger; hasil lama dan v2 tidak tercampur; klaim sesuai bukti. Kesiapan paket tidak menjamin penerimaan jurnal atau p-value tertentu.

## 17. Definition of done setiap milestone

Gunakan checklist berikut pada catatan phase:

- [ ] Tujuan dan batas perubahan dinyatakan.
- [ ] File yang berubah serta config/source/build version dicatat.
- [ ] Acceptance test yang relevan dijalankan dan hasilnya disimpan.
- [ ] Jalur kegagalan penting diuji, bukan hanya successful path.
- [ ] Tidak ada perubahan diam-diam pada legacy, satuan, reward, atau denominator.
- [ ] Artefak bisa ditemukan dan dibaca ulang dari path yang dicatat.
- [ ] Keterbatasan/pekerjaan tertunda tidak disembunyikan sebagai status complete.
- [ ] Keputusan lanjut, diagnosis, atau revisi protokol dicatat.

Template catatan milestone:

```markdown
# Pxx — Nama milestone

Status: pending / in_progress / blocked / complete
Versi spesifikasi:
Git SHA / build hash:

## Tujuan dan perubahan
## Deliverable dan lokasi artefak
## Verifikasi dan hasil aktual
## Risiko/keterbatasan tersisa
## Keputusan dan phase berikutnya
```

Status `blocked` pada catatan proyek berarti dependensi/masalah milestone belum selesai; bukan instruksi untuk mengubah status goal atau meminta persetujuan tool secara otomatis.

## 18. Risiko yang harus ditangani lebih awal

| Risiko | Phase pengendalian | Bukti yang diminta |
|---|---|---|
| Scheduler default tidak menerapkan FCFS | P00–P02 | Urutan pelayanan dan resource trace |
| State statis CloudSim bocor antar-episode/worker | P02, P05, P09 | Replay dan isolasi proses |
| Completion/timeout bertimestamp sama menghasilkan outcome berbeda | P02–P03 | Fixture batas waktu dan idempotensi |
| Energi idle hilang atau energi jaringan dihitung dua kali | P04 | Kasus idle dan ledger komponen |
| Tugas gagal memperbaiki latency secara palsu | P04 | Latensi fisik terpisah dari penalti dan reliability |
| Reward prediksi menggantikan outcome aktual | P05 | Event outcome dan identitas return |
| Heuristik melihat informasi lebih banyak daripada PPO | P05–P06 | Audit shared public snapshot |
| Kandidat pendek tidak memprediksi kualitas akhir | P08 | Ranking fidelity dan aturan pemilihan K |
| Validasi pencarian tidak dihitung sebagai biaya | P09 | S/V/F/B ledger dan dry-run |
| Test dipakai untuk tuning atau memilih klaim | P10–P12 | Split guard, protocol lock, revision log |
| Episode dianggap training replicate independen | P10 | Analisis bertingkat/crossed yang tervalidasi |
| Kebutuhan komputasi melebihi alokasi server | P09–P10 | Estimasi berbasis throughput dan ukuran artefak pilot |

## 19. Pekerjaan pertama dan langkah berikutnya

**P00 sudah selesai** dengan lingkup berikut:

1. Buat struktur modul v2 dan config/schema versi awal dari spesifikasi.
2. Catat audit API event engine serta titik adaptasi scheduler/cancellation.
3. Pastikan build Java 21 dan import/config validation Python berhasil.
4. Tulis acceptance cases untuk P01–P05 beserta nilai analitis yang diharapkan.
5. Serahkan catatan P00 sebelum memperluas implementasi ke generator trace dan simulator.

P01 trace deterministik, P02 engine CPU/lifecycle, P03 transport jaringan, dan P04 ledger energi dan lima metrik juga sudah selesai. **Milestone berikutnya adalah P05: socket v2, Gymnasium, observasi 108 fitur, dan reward tertunda**, yang memakai biaya kumulatif dari ledger P04. Tidak langsung mengubah runner legacy menjadi training besar, memigrasikan model lama ke 108 fitur, atau menjalankan 20 outer run.

## 20. Batas dokumen ini

P00–P04 telah diimplementasikan dan diverifikasi secara lokal; P05–P12 belum dimulai. Config, schema, package fondasi, CLI validasi/generator, trace immutable, guard split, build terpisah, probe native/numerik, scheduler FCFS bounded, engine task headless, transport jaringan store-and-forward, serta ledger energi dan metrik per trace sudah tersedia. Server socket, Gym, analisis statistik konfirmatori, serta eksperimen utama belum tersedia. Status selesai P00–P04 tidak berarti simulator sudah siap untuk training; setiap phase berikutnya tetap harus memenuhi kriterianya sendiri.

Kriteria eksperimen dan parameter tetap merujuk pada dokumen kesepakatan. Jika ada konflik, perbaiki dokumen dan catat keputusan sebelum melanjutkan; jangan menyelesaikan konflik melalui perubahan kode yang tidak terdokumentasi.
