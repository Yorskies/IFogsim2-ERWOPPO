# P00 — Kontrak dan fondasi proyek

Tanggal: 3 November 2026. Status: **complete — verifikasi lokal**.
Spesifikasi penelitian: v0.2. Schema/wire: `research-v2.1`.
Git HEAD awal: `02bcd1ebf6a645625b7d6c43af8a31023e12d03a`.
Perubahan P00 masih berada di working tree; belum dibuat commit atau push.

## Tujuan dan batas perubahan

Menyiapkan konfigurasi yang dapat diperiksa mesin, kontrak data lintas bahasa,
audit API native, build terpisah, dan acceptance cases sebelum generator/engine.
Ini phase pertama roadmap, **bukan P01 generator trace**. Tidak menjalankan
training, pencarian bobot, atau eksperimen ulang. Source dan hasil legacy utuh.

## Deliverable

| Deliverable | Lokasi |
|---|---|
| Seluruh parameter awal v0.2 dan satuan eksplisit | `configs/research_v2/default.json` |
| Objective/action/108-feature ordering, prioritas event, versi, idempotensi | `configs/research_v2/wire_contract.json` |
| JSON Schema 2020-12 config dan sembilan jenis record | `schemas/research_v2/` |
| Schema export, config/cross-field validation, canonical hashing | `research_v2/config.py`, `contracts.py`, `schema_definitions.py` |
| CLI validate/export/snapshot dan entry point | `research_v2/__main__.py`, `run_research_v2.py` |
| Audit scheduler/cancellation/reset/power/native events | [API_AUDIT.md](../API_AUDIT.md) |
| Batas modul, unit, lifecycle dan pemetaan JSON | [ARCHITECTURE.md](../ARCHITECTURE.md) |
| Kasus deterministik dan hasil analitis yang diharapkan | [ACCEPTANCE_TESTS.md](../ACCEPTANCE_TESTS.md) |
| Build Python portabel, isolated full compile, release21, receipt SHA input | `ifogsim/build_v2.py` |
| Java wire loader dan probe native | `ifogsim/src/org/fog/erwo/v2/Contracts.java`, `FoundationMain.java` |
| JAR foundation lokal, berbeda dari server legacy | `ifogsim/dist/research-v2-foundation.jar` |
| Dependency pin P00 yang benar-benar terpasang | `requirements-v2-foundation.txt` |
| Git SHA, hash 451 source dan 1.286 hasil legacy, versi/hash RECORD paket | [P00_baseline_snapshot.json](P00_baseline_snapshot.json) |
| Verifier dan laporan tes/build/integritas aktual | `research_v2/verify_foundation.py`, [P00_verification.json](P00_verification.json) |
| Cara menjalankan lokal/server | [README v2](../README.md) |

Output simulator masa depan dibatasi `results/research_v2/<study_id>/`.
Direktori hasil kosong tidak dibuat sebagai bukti eksperimen. JAR/classes
di-ignore Git; receipt beserta hasil probe disalin ke laporan agar dapat ditinjau.

## Verifikasi aktual

Perintah terakhir, dari root dengan virtual environment proyek:

```powershell
python ifogsim/build_v2.py --jdk-home 'C:\Program Files\Java\jdk-27' --self-test
python -m research_v2.verify_foundation --jdk-home 'C:\Program Files\Java\jdk-27' --baseline docs/research_v2/milestones/P00_baseline_snapshot.json
```

Hasil: **23 tes lulus; 0 failure, 0 error, 0 skip**:

- 17 tes fondasi, termasuk invalid config, semantic invariants, schema drift,
  hash tampering, route terputus, status QoS/deadline, manifest complete palsu,
  RPC action, bytecode, dan persamaan kontrak Java–Python.
- 6 tes regression suite legacy lulus.
- Semua 451 source legacy dan 1.286 file hasil suite awal cocok byte-per-byte
  dengan snapshot; tidak ada file hasil ditambah/dihapus dalam suite lama.
- Config canonical SHA-256:
  `3e32379ebd2e8770e025ff9cce11be28cbffe7e535b269a070030ce6d9dae025`.
- JAR hasil build terakhir SHA-256:
  `972093a4dfbdb5d67fdc7d5e853b1f1584bae3c564eb9df442e2d1c66d83376b`.
  Build ulang dapat mengubah hash JAR karena metadata waktu ZIP; receipt menyimpan
  hash setiap input untuk mendeteksi perubahan source/config/dependency.
- Class major65: target Java21. Probe menjalankan dua episode CloudSim nyata,
  event pada1e-6/0,4194304 s, replay identik, idle IoT34,5J selama69s.
- `--describe` berjalan dari direktori lain yang memiliki spasi; manifest
  dependency tidak bergantung current working directory proyek.

## Temuan penting untuk phase berikutnya

1. Scheduler upstream tidak membatasi antrean/RAM, mengisi paling banyak satu
   waiting task per update, dan cancellation aktif tidak melepas `usedPes`.
   P00 mereproduksi hazard, **belum** memperbaikinya. Adapter P02 wajib diuji.
2. Event CloudSim sama waktu mengikuti serial penyisipan. P02 perlu coordinator
   completion/delivery → deadline/timeout → arrival dan zero-delay closure;
   enum prioritas pada kontrak saja belum menerapkan semantik itu di engine.
3. `FogLinearPowerModel` mempertahankan idle; `PowerModelLinear` upstream
   mengembalikan0 pada u=0. P04 wajib satu ledger dan menghindari double count.
4. Global `TimeKeeper/FogUtils/NetworkUsageMonitor` memerlukan audit isolasi
   lebih lanjut saat P02 memasukkan host/VM/FogDevice. Probe dua episode P00
   belum membuktikan reset seluruh simulator offloading.

## Lingkungan dan keterbatasan

- Teruji: Windows AMD64, CPython3.11.0, JDK27, compiler `--release 21`.
- Target server tetap Ubuntu/Python3.12/OpenJDK21. Build script dan perintah
  disiapkan untuk keduanya, tetapi eksekusi langsung pada target belum diuji.
  **Verifikasi server wajib sebelum pembekuan protokol P10**, dan sebaiknya
  dijalankan ketika P00 ditarik ke server agar masalah dependency diketahui awal.
- Pin dan hash `RECORD` mendeskripsikan paket fondasi lokal, bukan hash wheel
  untuk `pip --require-hashes` dan bukan lock lingkungan training Linux. Lock
  target harus berasal dari paket server yang lolos, bukan menyalin klaim lokal.
- Kompilasi mencatat dua warning `Integer(int)` deprecated/removal pada source
  legacy ControllerComponent; build tetap berhasil. Source tersebut tidak diedit.
- JAR foundation belum menjalankan host/VM/Cloudlet sampai outcome fisik,
  jaringan, energi total, socket, Gym, PPO, NSGA-II, ataupun analisis statistik.
  Kasus acceptance downstream masih berupa spesifikasi, bukan hasil lulus.

## Definition of done dan keputusan

- [x] Tujuan, batas, modul dan perubahan dicatat.
- [x] Config/source/build version dan lokasi artefak dicatat.
- [x] Acceptance P00 dijalankan dan hasil aktual disimpan.
- [x] Jalur kegagalan input/kontrak diuji.
- [x] Legacy, satuan, reward runtime lama dan hasil tidak diubah.
- [x] Bukti dapat dibaca ulang dan perintah reproduksi tersedia.
- [x] Target platform dan pekerjaan downstream yang belum diuji dinyatakan.
- [x] Keputusan lanjut dicatat: **lanjut P01 — konfigurasi dan generator trace**.

P01 harus memakai config/schema ini, memisahkan RNG tiap komponen, membuktikan
determinisme/hash serta perbedaan moderate/dynamic, dan belum membuka test untuk
memilih metode. Jangan langsung menjalankan batch training dari fondasi P00.
