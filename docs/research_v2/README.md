# Research v2 — fondasi P00, trace P01, engine P02, jaringan P03, dan akuntansi P04

**P00 sampai P04 sudah selesai**: config/schema, kontrak lintas bahasa, audit API,
build terpisah, probe native, generator/penyimpanan trace deterministik, engine
task headless (CPU FCFS bounded, admission, deadline/timeout, horizon) di atas CloudSim,
dan transport store-and-forward (kanal akses half-duplex, link LAN/WAN, antrean transfer,
pembatalan parsial), serta ledger energi dan lima metrik per trace dengan evaluator independen.
Training PPO, reward, dan socket v2 belum tersedia. Mode fixture
nol-jaringan P02 tetap ada dan berlabel. Panduan trace dan guard split: [TRACES.md](TRACES.md);
bukti [P01](milestones/P01_trace_validation.md), [P02](milestones/P02_engine_validation.md),
[P03](milestones/P03_network_validation.md), dan [P04](milestones/P04_accounting_validation.md).

## Menjalankan engine P02 (headless, aksi tetap)

Setelah build JAR (lihat bagian build), skenario dibuat dari trace P01 dan dijalankan di JVM:

```python
from research_v2.engine_runner import run_engine, scenario_from_trace
episode = run_engine(scenario_from_trace(trace, "nearest_fog", topology={"homogeneous_fog": False}))["episodes"][0]
```

Atau audit milestone lengkap (21 tes, C01–C08), yang menulis `milestones/P02_verification.json`:

```text
python -m research_v2.verify_engine --jdk-home <JDK 21+>
```

Hasil engine memuat outcome per task, log event dengan generasi/sequence, dan ringkasan per node
(maks PE sibuk, maks antrean, puncak RAM, `busy_pe_seconds`). Label `FIXTURE_ZERO_NETWORK` pada hasil
berarti angka tersebut bukan benchmark sistem.

Untuk transport jaringan P03, tambahkan kunci `network` pada skenario (menggantikan `fixture_transport`):

```python
value = scenario_from_trace(trace, "nearest_fog", topology={"homogeneous_fog": False})
value["network"] = {"log_transfers": False}   # opsional: {"overrides": {"access": {"queue_waiting": 1}}}
episode = run_engine(value)["episodes"][0]   # menambah episode["links"] (byte, detik serialization, antrean per server)
```

Audit milestone P03 (17 tes, N01–N06), yang menulis `milestones/P03_verification.json`:

```text
python -m research_v2.verify_network --jdk-home <JDK 21+>
```

Setiap episode kini memuat `energy` (idle/dinamis/total, per komponen dan grup) dan `metrics` (violation, reliability,
latensi mean/median/p95, throughput, lima biaya `zL..zQ`, `D`). Untuk memeriksa ledger secara independen:

```python
from research_v2.evaluator import evaluate, compare
assert compare(episode, evaluate(episode, config)) == []   # [] = Java dan evaluator sepakat
```

Audit milestone P04 (16 tes, E01–E04, M01–M03, evaluator), yang menulis `milestones/P04_verification.json`:

```text
python -m research_v2.verify_accounting --jdk-home <JDK 21+>
```

## Memeriksa config

Dari root repository, dengan virtual environment proyek aktif:

```text
python -m pip install -r requirements-v2-traces.txt
python -m research_v2 validate
python -m research_v2 export-schemas --check
```

Config: [default.json](../../configs/research_v2/default.json).
CLI `python run_research_v2.py validate` setara. Edit config tidak mengubah
parameter runtime training legacy. Kandidat v2 adalah5.120 dan final102.400
keputusan sesuai kelipatan rollout, belum menjalankan training pada P00–P01.

Untuk menghasilkan empat workload pada satu ID calibration:

```text
python -m research_v2 generate-traces --split calibration --role calibrator --trace-id 0
```

Audit lengkap P01, setelah build dengan JAVA_HOME yang benar:

```text
python -m research_v2.verify_traces
```

Audit ini mencakup49 tes serta80 trace calibration dan468 pemeriksaan distribusi.
Perintah `verify_foundation` di bawah tetap dibatasi23 tes fondasi/legacy P00.

## Build Windows

Contoh menggunakan JDK yang tersedia di mesin pengembangan:

```powershell
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-27'
python ifogsim/build_v2.py --self-test
python -m research_v2.verify_foundation
```

Build memakai `javac --release 21` meskipun compiler lokal lebih baru. Tidak
memerlukan `java` di PATH jika JAVA_HOME atau `--jdk-home` diberikan. Sesuaikan
JAVA_HOME dengan lokasi JDK21 atau lebih baru yang benar-benar terpasang.

### Lingkungan yang diverifikasi ulang (8 November 2026)

Semua perintah di bawah dijalankan dari root repository di Windows 11:

```powershell
py -3.12 -m venv venv                       # venv/ sudah di-ignore Git
venv\Scripts\python.exe -m pip install -r requirements-v2-traces.txt
venv\Scripts\python.exe -m pip install -r requirements.txt   # dependency legacy
$jdk = "$env:USERPROFILE\.jdks\jdk-21.0.13.0.2+1"             # Microsoft OpenJDK 21 (ZIP)
venv\Scripts\python.exe ifogsim\build_v2.py --jdk-home $jdk --self-test
venv\Scripts\python.exe -m research_v2.verify_foundation --jdk-home $jdk
venv\Scripts\python.exe -m research_v2.verify_traces --jdk-home $jdk
```

| Komponen | Versi | Catatan |
|---|---|---|
| Python | 3.12.6 | Target server sama (3.12). Verifikasi awal memakai 3.11.0. |
| JDK | Microsoft OpenJDK 21.0.13 | Sama dengan target `--release 21`; tidak perlu `--release` lebih rendah. |
| numpy / jsonschema | 2.4.6 / 4.26.0 | Pin `requirements-v2-*.txt` tidak berubah. |

Hasil: P00 **23/23**, P01 **49/49**, P02 **21/21**, P03 **17/17**, dan P04 **16/16** tes lulus (P02 sampai P04
ditambahkan kemudian pada hari yang sama dengan `verify_engine`, `verify_network`, dan `verify_accounting`), 0 failure/error/skip. Seluruh 80
`trace.json` dan `config.json` yang dibangkitkan ulang identik byte-per-byte dengan
bundle yang ter-commit di `results/research_v2/P01_calibration/`, jadi trace tidak
berubah antara Python 3.11 dan 3.12.

Tiga catatan:

- `verify_foundation` dan `verify_traces` menulis laporan ke `docs/research_v2/milestones/`
  secara default dan akan menimpa bukti yang sudah ter-commit. Untuk verifikasi ulang
  gunakan `--output <path_lain>` (dan `--trace-root` untuk `verify_traces`).
- `producer.source_sha256` pada `manifest.json` bundle menghash **byte mentah** file
  Python. Dengan `core.autocrlf=true` (default Git for Windows) file berakhiran CRLF
  dan hash berbeda (`72877414…`) dari fingerprint terdokumentasi (`e920381c…`), yang
  sama dengan hash isi Git (LF). Isi trace tidak terpengaruh; hanya
  `manifest.json` berbeda. Sebelum membandingkan manifest antar-mesin, samakan akhir
  baris (misalnya checkout LF, atau `.gitattributes` dengan `eol=lf`).
- `verify_foundation --baseline` gagal pada salinan repository ini (diuji 8 November
  2026, berhenti di `experiment_suite.json`). Snapshot menghash byte mentah, sehingga
  ada dua penyebab yang terpisah dari perubahan isi: (1) akhir baris. Dari 451 source
  legacy, 447 cocok setelah CRLF→LF, 3 cocok apa adanya, dan 1
  (`IFogSimSocketServer.java`) cocok hanya sebagai CRLF. Isi seluruhnya identik; (2) arsip
  hasil. Salinan `results/` yang ter-commit hanya berisi 325 dari 1.286 file suite lama
  (961 hilang, lihat `RENCANA_PENELITIAN_LANJUTAN.md` bagian 2), dan 243 dari 325 yang
  ada hanya cocok setelah normalisasi LF. Opsi ini memerlukan arsip lengkap dengan
  byte yang sama; jangan membuat ulang snapshot untuk menyiasatinya.

## Build Ubuntu — perintah untuk validasi server

Dengan JDK21 dan Python3.12 di virtual environment proyek:

```bash
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
python ifogsim/build_v2.py --self-test
python -m research_v2.verify_foundation
```

Perintah Ubuntu disiapkan memakai build script yang sama; **belum dieksekusi
pada server Ubuntu oleh milestone lokal ini**. Pastikan dependency legacy
`requirements.txt` juga tersedia untuk enam regression test legacy.
Lock Python3.12/Linux hanya boleh dibekukan dari environment server yang lulus.

## Artefak dan evidence

- JAR: `ifogsim/dist/research-v2-foundation.jar`; main
  `org.fog.erwo.v2.FoundationMain`. Dependency tetap di `ifogsim/jars/` relatif
  terhadap dist, bukan fat JAR yang berdiri sendiri.
- `java -jar ifogsim/dist/research-v2-foundation.jar --describe` mengeluarkan
  kontrak; `--self-test` menguji event native/API. Memberi port bukan perintah
  menjalankan server v2 dan akan gagal dengan pesan jelas.
- Receipt: `ifogsim/build/research_v2/build_receipt.json`; mencatat hash seluruh
  input Java/JAR/config/schema dan hasil probe. Direktori compile baru disimpan
  di bawah build untuk inspeksi; kelas lama tidak dipakai ulang. JAR/classes
  merupakan hasil build yang di-ignore Git dan harus dibangun lagi di server.
- JAR juga memuat `org.fog.erwo.v2.TraceTimestampProbe` untuk pemeriksaan numerik
  P01, bukan task engine. Receipt/hash JAR P00 pada catatan lama bersifat historis;
  build yang mencakup P01 dicatat di [P01_verification.json](milestones/P01_verification.json).
- Verifikasi: [P00_verification.json](milestones/P00_verification.json).
  `verify_foundation` memeriksa drift build/schema dan menjalankan semua23 tes;
  hasil dengan Java dilewati tidak dianggap lulus.
- Snapshot lokal: [P00_baseline_snapshot.json](milestones/P00_baseline_snapshot.json).
  Untuk memeriksa file legacy lokal yang sama:

```text
python -m research_v2.verify_foundation --baseline docs/research_v2/milestones/P00_baseline_snapshot.json
```

Snapshot merupakan hash byte checkout/hasil lokal, bukan manifest download
hasil yang belum ada di server. Opsi baseline digunakan jika suite lama lengkap
tersedia dengan byte yang sama; jangan regenerasi snapshot untuk menyembunyikan
perubahan. Verification biasa tidak memerlukan file hasil lama.

Lihat [arsitektur](ARCHITECTURE.md), [audit API](API_AUDIT.md),
[acceptance catalog](ACCEPTANCE_TESTS.md), dan [catatan P00](milestones/P00_foundation.md).
