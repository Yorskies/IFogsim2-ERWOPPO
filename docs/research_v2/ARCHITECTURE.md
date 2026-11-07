# Kontrak arsitektur P00

Status implementasi: fondasi P00, trace P01, engine headless P02, transport jaringan P03, dan ledger energi/metrik P04.
Arsitektur ini memetakan fase lanjutan; socket, Gym, reward, dan training belum tersedia.

Pembaruan P02 (8 November 2026): `BoundedFcfsScheduler` (adapter CloudSim space-shared), `ComputeNode`
(Host/Vm/Pe nyata), `EngineCoordinator` (antrean berurutan dengan prioritas domain, generasi event,
commit terminal tunggal), dan driver `EngineMain` ada di `org.fog.erwo.v2`. Lifecycle di bawah sudah
berjalan dengan transport fixture nol-jaringan; keputusan desain dan batasannya ada di
[P02_engine_validation.md](milestones/P02_engine_validation.md).

Pembaruan P01: generator `traces.py`, guard `trace_access.py`, bundle atomik
`trace_store.py`, laporan distribusi `trace_report.py`, dan audit `verify_traces.py`
sudah tersedia. Detail: [TRACES.md](TRACES.md). Task engine tetap pekerjaan P02.

| Area | File/package | Batas tanggung jawab |
|---|---|---|
| Config dan unit | `configs/research_v2/default.json`, `research_v2/config.py` | Parameter v0.2; validasi JSON Schema ditambah invariant antar-field; input salah menghentikan run |
| Vocabulary | `schema_definitions.py`, `wire_contract.json`, Java `Contracts` | Satu export urutan objektif/aksi/108 fitur; Java membaca resource yang sama; jangan salin urutan secara manual |
| Record | `schemas/research_v2/contracts.schema.json`, `contracts.py` | Task tetap, resource, route, event, outcome, biaya, trace, manifest, request RPC; validasi tidak menjalankan simulator |
| Java P00 | `org.fog.erwo.v2.FoundationMain` | Probe event native, reinit dua episode, daya idle, audit cancellation; tidak membuka socket |
| Build | `ifogsim/build_v2.py` | Full compile ke direktori baru, `--release 21`, main berbeda, JAR foundation terpisah; receipt menyimpan SHA input dan dependency |
| Future engine P02–P04 | `org.fog.erwo.v2` | Host/VM/PE/Cloudlet, bounded FCFS, lifecycle/transport, satu ledger energi/metrik |
| Future adapter P05 | `research_v2` dan `V2SocketServer` | Snapshot publik, step arrival, delayed reward; kegagalan Java tidak diganti engine Python |
| Future study P07–P12 | `research_v2`, `run_research_v2.py` | Training/search/runner/statistik; CLI sekarang hanya validate/export/snapshot |

## Unit dan representasi

- Detik, MI integer, MIPS/PE, byte integer, bit/s, W, J. Tidak ada konversi Mbps
  implisit; `MiB=2^20 byte`, `Mbps=10^6 bit/s`.
- Timestamp disimpan round-trip binary64 melalui JSON, tanpa rounding untuk
  display. Hash menggunakan UTF-8 canonical JSON, sorted keys, separators `, :`
  tanpa spasi, tanpa NaN/Infinity; duplicate JSON key ditolak.
- Hash trace adalah seluruh envelope kecuali field `payload_sha256` sendiri.
  SHA256 config memakai config lengkap. Hash file adalah byte file aktual,
  berbeda dari canonical object hash; keduanya diberi nama jelas.
- Data task tetap; outcome terminal tepat satu dari ON_TIME/LATE_SUCCESS/FAILED.
  FAILED memiliki alasan CPU_QUEUE_FULL/RAM_EXHAUSTED/NETWORK_QUEUE_FULL/
  SERVICE_TIMEOUT. Error teknis bukan outcome fisik.

## Lifecycle dan prioritas untuk P02

State internal yang direncanakan:
`WAIT_DECISION → INPUT_TRANSFER → CPU_WAIT/CPU_RUNNING → RESULT_TRANSFER`;
jalur lokal melewati transfer; setiap cabang dapat berakhir FAILED. Completion
CPU belum berarti sukses: sukses saat hasil diterima IoT. Deadline flag terpisah
dari state dan tidak membatalkan task. Timeout membatalkan seluruh resource.

Urutan event sama waktu: completion/transfer/result, deadline/timeout, arrival,
kemudian horizon. Dalam kelompok gunakan task ID, lalu sequence episode yang
unik. Jangan gunakan comparator berbasis epsilon yang tidak transitif; simpan
timestamp tepat dan gunakan toleransi hanya untuk klasifikasi batas fisik.
Coordinator P02 harus memproses completion zero-delay sampai tidak ada lagi
event yang dapat menghasilkan delivery di timestamp tersebut sebelum timeout
atau arrival. Native insertion order tidak cukup.

Stale event ditolak lewat generation token task; duplicate event memiliki
sequence identik. Idempotency event mencakup episode/task/generation/kind/
sequence, sehingga completion pada dua hop yang sah tidak dianggap duplikat.
Terminal commit memiliki key episode/task dan hanya dapat dilakukan sekali.
Pembuktian pelepasan resource dan conservation belum diimplementasikan P00.

## Rute untuk P03 (diimplementasikan pada `NetworkModel`; lihat [P03](milestones/P03_network_validation.md))

Local: kosong. Fog akses: wireless. Fog lain: wireless → LAN fog asal → LAN
fog tujuan. Cloud: wireless → LAN fog asal → WAN. Result memakai rute balik.
Half-duplex wireless memakai server sama untuk dua arah; kabel server per arah.
Serializer dilepas sebelum propagasi. Node menerima task CPU setelah input tiba;
tidak ada reservasi saat keputusan. Ledger menghitung energi yang telah dipakai
meskipun task akhirnya gagal. `fileTransferTime=0` pada scheduler native.

## Isolasi dan versi

- Source legacy tidak diedit; JAR legacy dan hasil suite lama tidak ditimpa.
- Output v2 hanya di `results/research_v2/<study_id>/`; JAR P00 adalah
  `ifogsim/dist/research-v2-foundation.jar`, bukan server production.
- Schema wire `research-v2.1`, spesifikasi ilmiah `0.2`. Versi wire dan versi
  parameter berbeda fungsi. Kompatibilitas harus diperiksa saat RPC P05.
- Satu episode aktif per JVM. Paralelisme hanya antar-JVM; satu worker default.
- Resume mula-mula hanya batas completed run. Tidak ada klaim partial-state
  simulator dapat direstore.
- Nilai training/search di config adalah persiapan kontrak, belum fitur CLI.
- `system.yaml`/`training.yaml` pada spesifikasi dipetakan pada section JSON
  `topology/timing/tasks/network` dan `ppo/training/search`; JSON menjadi sumber
  tunggal P00 agar tidak ada dua konfigurasi yang drift. Runner P09 akan mengarsip
  effective config per run dan mencatat pemetaan ini.
