# P01 — Konfigurasi dan generator trace

Tanggal: 3 November 2026. Status: **complete — verifikasi lokal**.
Spesifikasi penelitian v0.2; wire `research-v2.1` tetap; generator
`research-v2.trace-1`; bundle sidecar `research-v2.trace-bundle-1`.
Git HEAD awal `02bcd1ebf6a645625b7d6c43af8a31023e12d03a`. Pembaruan 8 November
2026: perubahan P01 sudah di-commit pada `6670200` dan sudah ada di `origin/main`.

## Tujuan dan implementasi

Menghasilkan workload eksternal yang sama untuk semua metode pada key yang
sama, dengan kelas/atribut tugas, pola arrival yang benar, immutable export,
dan pemisahan calibration/pilot/train/validation/test. Tidak menjalankan
offloading, menghasilkan outcome fisik, atau melatih policy.

| Deliverable | Lokasi |
|---|---|
| Frozen namespace, seed SHA-256, aturan split/role/ID | `research_v2/trace_access.py` |
| Generator PCG64, integrated hazard, atribut task, bytes immutable | `research_v2/traces.py` |
| Atomic bundle, config/unit/hash/provenance, no overwrite, guarded read | `research_v2/trace_store.py` |
| Sidecar schema tanpa mengubah trace envelope P00 | `schemas/research_v2/trace_bundle.schema.json` |
| Ringkasan atribut, arrival, dan pemeriksaan distribusi terdefinisi | `research_v2/trace_report.py` |
| CLI generate/describe empat workload | `python -m research_v2`, `run_research_v2.py` |
| Fixture simultaneous arrival, mapping dan batas waktu | `research_v2/trace_fixtures.py`, `tests/research_v2/fixtures/` |
| Probe parsing binary64 Java | `ifogsim/src/org/fog/erwo/v2/TraceTimestampProbe.java` |
| Unit/integration tests | `tests/research_v2/test_traces.py` |
| Pin environment NumPy aktual | `requirements-v2-traces.txt` |
| Audit reproducible dan bukti lengkap | `research_v2/verify_traces.py`, [P01_verification.json](P01_verification.json) |
| Aturan algoritma/akses/export dan cara menjalankan | [TRACES.md](../TRACES.md) |

Config default/nilai ilmiah tidak diubah. Validasi kontrak task pada trace
dioptimalkan dengan cached validator dan tidak mengulangi schema task yang
sudah diperiksa oleh schema trace; semua invariant semantik tetap diterapkan.
Audit P00 sekarang memilih `test_foundation.py` secara eksplisit, sehingga
laporan fondasi tetap23 tes ketika suite P01 bertambah.

## Verifikasi aktual

```powershell
python ifogsim/build_v2.py --jdk-home 'C:\Program Files\Java\jdk-27' --self-test
python -m research_v2.verify_traces --jdk-home 'C:\Program Files\Java\jdk-27' --baseline docs/research_v2/milestones/P00_baseline_snapshot.json
```

**49 tes lulus; 0 failure, 0 error, 0 skip**: 26 tes P01, 17 tes fondasi,
dan6 regression test legacy. Jalur penting yang diuji:

- Seed vector diketahui, hash golden, determinisme lintas proses dan method
  order; RNG global policy tidak disentuh generator.
- Perubahan rentang MI tidak mengubah atribut lain; perubahan config reward
  tidak mengubah task stream, sementara config hash tetap mencatat perubahan.
- Integrated hazard mempertahankan residual melewati satu/beberapa batas fase;
  arrival tepat batas berasal dari hazard aktual, bukan task tambahan paksa.
- Semua source/ID/atribut/timeouts valid; N0 menghentikan generator tanpa retry.
- Read/write idempotent, tampering ditolak tanpa ditimpa, concurrent writers
  identik menghasilkan satu bundle lengkap, dan object trace tidak dapat dimutasi.
- Role yang salah, ID split yang salah, dan read/describe test ditolak. Unit
  guard membuat test trace sementara untuk membuktikan seal; tidak ada evaluasi
  metode atau pemilihan parameter dari holdout.
- Probe Java membaca4 task fixture dan328 task calibration light0; bit arrival,
  relative deadline/timeout serta waktu absolut hasil penjumlahan identik dengan
  Python. Ini bukti representasi numerik, belum eksekusi scheduler.

Contoh golden: namespace `20261103|calibration|-|-|0|light|arrival` mempunyai
seed `10715774301338505746`. Trace light0 mempunyai328 task dan payload SHA:
`837b180f9a354ef413c68efba3de4de1657d25142e50d0931c6b266e8d34babd`.

## Karakteristik 80 trace calibration

Seluruh ID0–19 di setiap workload disertakan: **77.936 tugas**, expected78.000.
Tidak ada penggantian seed, tuning arrival rate, atau resampling setelah melihat
hasil. Semua **468/468** pemeriksaan distribusi lulus dengan protokol union-bound
family alpha .001 yang dijelaskan pada [TRACES.md](../TRACES.md). Ini diagnostic
generator, bukan uji signifikansi penelitian metode.

| Workload | Total task | Mean per trace | Expected per trace | Laju observed empat interval15s, task/s |
|---|---:|---:|---:|---|
| Light | 6.152 | 307,6 | 300 | 5,1833; 5,1000; 5,2233; 5,0000 |
| Moderate | 18.148 | 907,4 | 900 | 14,9900; 14,8900; 15,7767; 14,8367 |
| Heavy | 35.950 | 1.797,5 | 1.800 | 30,0233; 29,9700; 30,2400; 29,6000 |
| Dynamic | 17.686 | 884,3 | 900 | 4,9700; 14,6800; 34,4867; 4,8167 |

Profil dynamic menunjukkan burst dan pemulihan sesuai5→15→35→5. Seluruh20
pasangan dynamic/moderate memiliki atribut tugas berbeda, bukan hanya perbedaan
label/hash envelope. Jumlah actual tidak harus sama antar-pasangan walaupun
ekspektasi keduanya sama900.

Laporan mesin juga memuat proporsi kelas, conditional mean/range MI/input/
deadline, source/fog counts, setiap468 check dan80 payload hash. Bundle calibration
tersimpan di `results/research_v2/P01_calibration/traces/`. Pembaruan 8 November
2026: `results/` tidak lagi di-ignore Git, dan 80 bundle ini (240 file) sudah
di-commit pada `667eb42`. Source/golden fixture/laporan ringkas tetap dapat
ditarik ke server dan bundle dibangkitkan ulang. Tidak ada hasil training v2 pada direktori ini.

## Provenance dan integritas

- Generator source fingerprint:
  `e920381c4c3e803f43eb2c42c6c46e7b6fc42a1e126e080bbe441ca9dad18c8f`.
- JAR build yang menambahkan timestamp probe:
  `6e164f5826618dec5896686283a5557a65f01fbc1691e92b00573ce04de4e7ee`.
  Hash receipt P00 lama tetap historis; receipt P01 memuat input/build saat ini.
- Bytecode targetJava21, compiler/runtime aktualJDK27. Versi environment
  CPython3.11.0, NumPy2.4.6 dan hash RECORD dependency disimpan dalam laporan.
- Seluruh **451 source legacy dan1.286 file hasil lama** tetap cocok dengan
  snapshot P00; tidak dipindah, ditimpa, ditambah, atau dihapus dari suite lama.
- Build mencatat dua warning deprecated/removal Integer(int) legacy yang sama;
  build dan probe native tetap lulus.

## Batasan dan keputusan lanjut

Ubuntu/Python3.12/OpenJDK21 belum diuji langsung. Pin/hash paket ini menyatakan
environment lokal, bukan lock wheel Linux. Guard split merupakan aturan API,
bukan enkripsi atau sandbox terhadap pengguna yang mengubah source. Final
evaluator belum tersedia; pembukaan test harus mengikuti freeze protokol P10.

Fixture expected outcome masih bersifat hypothetical. Kelulusan P01 tidak
membuktikan FCFS, bounded admission, cancellation, resource accounting, energi,
atau QoS fisik. Implementasi itu dimulai pada **P02 — event engine dan siklus
tugas**, dari satu IoT/satu node, memakai fixture yang sudah dibekukan.

- [x] Generator/akses/format dan batas perubahan ditetapkan.
- [x] Source/config/build/provenance dan lokasi artefak dicatat.
- [x] Acceptance T01–T03 dan jalur kegagalan diverifikasi.
- [x] Empirical characteristics seluruh calibration ID disimpan, tanpa tuning test.
- [x] Representasi waktu lintas bahasa diperiksa secara bit-exact.
- [x] Kode dan hasil legacy tetap utuh.
- [x] Keterbatasan serta keputusan melanjutkan ke P02 dinyatakan.
