# Research v2 — fondasi P00 dan generator trace P01

**P00 dan P01 sudah selesai**: config/schema, kontrak lintas bahasa, audit API,
build terpisah, probe native, serta generator/penyimpanan trace deterministik.
Training PPO, task engine, serta socket v2 belum tersedia. Panduan trace dan
guard split: [TRACES.md](TRACES.md); bukti [P01](milestones/P01_trace_validation.md).

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
