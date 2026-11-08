# P09 — Runner studi, accounting budget, dan pemulihan

Status: **complete — semua kriteria lulus pada studi mini (fixture); studi penuh 20 outer run belum dijalankan.**
Tanggal: 8 November 2026. Bukti mesin: [P09_verification.json](P09_verification.json) dan
[`results/research_v2/P09_runner_evidence/`](../../../results/research_v2/P09_runner_evidence/live_evidence.json).
Test split tidak dibuka. Git HEAD awal `4a0f2c2` (P06); seluruh pekerjaan P07–P10 masih di working tree, belum di-commit.

## Deliverable

| Deliverable | Lokasi |
|---|---|
| Accounting budget dan manifest job | `research_v2/study_budget.py` |
| Runner (plan / prepare / run / resume), lock kepemilikan, attempt terisolasi, pointer completion ber-checksum | `research_v2/study_runner.py` |
| Worker satu attempt, profil waktu/CPU/RAM/RPC/inferensi | `research_v2/study_worker.py` |
| Trainer final pada namespace `train_final` dan evaluasi validasi | `research_v2/study_final.py` |
| Bukti live (prefix, referensi, interupsi/crash, drift, paralel, kapasitas) | `research_v2/verify_study.py`, `results/research_v2/P09_runner_evidence/` |
| Dry-run budget penuh (K=30.720, 20 outer run) | `results/research_v2/P09_dry_run_full/budget_report.json` |
| 12 tes | `tests/research_v2/test_study_runner.py` |
| Verifikasi milestone | `research_v2/analysis/verify.py p09` → `P09_verification.json` |

## Kontrak

- **Job per outer run (6):** search NSGA-II, search random, final NSGA-II (bergantung pada search-nya), final random, baseline
  `equal`, baseline `manual`. Protokol A dan B memakai **job yang sama**: search dan model final dibagi, sehingga biaya tidak dihitung
  dua kali. Protokol A memakai checkpoint F dari run B baseline; protokol B memakai checkpoint B (dan 51.200 bila B ≥ 51.200).
- **Budget dihitung sebelum menjalankan** dari trace validasi nyata: `Ntrace=19.690`, `S=80×2×K`, `V=80×2×Ntrace`, `F=102.400`,
  `C=S+V+F`, `B=ceil(C/2048)×2048`. Biaya validasi dihitung (tidak gratis). Pada K=30.720: S=4.915.200, V=3.150.400, C=8.168.000,
  **B=8.168.448** per baseline (rancangan awal memperkirakan ~4,04 juta pada K=5.120). Total fisik 32.672.896 keputusan per outer run,
  653.457.920 untuk 20 outer run.
- **Isolasi dan atomisitas:** tiap attempt di `jobs/<id>/attempt_NNN/`; `complete.json` ditulis atomik (`os.replace` + fsync) setelah semua
  artefak wajib ada dan akuntansinya cocok; checksum SHA-256 setiap artefak; status `running/interrupted/failed/complete`.
- **Resume:** job complete diverifikasi ulang (hash result dan artefak, manifest = artefak) dan dilewati; job parsial tidak pernah dianggap
  complete; attempt yang tertinggal `running` ditandai `interrupted`. Resume **ditolak** bila config, JAR, source `research_v2/*.py`,
  manifest trace validasi, atau bukti fidelity berubah. PPO tidak di-resume di tengah run (simulator tidak dapat dipulihkan): job
  terputus diulang dari awal sebagai attempt baru dengan seed yang sama.
- **Retry:** maksimal 2 retry untuk kegagalan **teknis**, seed/trace sama. Attempt `interrupted` (dihentikan operator) **tidak**
  menghabiskan retry. Kegagalan algoritmik (`ContractError`, loss non-finite) tidak diulang otomatis dan memblokir resume sampai ditinjau.
- **Ownership:** `.owner.lock` (host, boot id, pid, waktu start proses, pid/start child). Penulis kedua ditolak; lock dari proses yang mati
  diarsipkan (`.owner.stale.*.json`) lalu dipulihkan; lock dari host/boot lain ditolak. Proses zombie dihitung mati.
- **Pembersihan:** SIGTERM/SIGINT menghentikan seluruh process group worker (termasuk JVM); setelah tiap attempt grup dibersihkan (SIGKILL)
  agar tidak ada JVM yatim.
- **Satu worker per studi** (default). Paralelisme = beberapa studi/shard, masing-masing dengan runner, lock, worker, dan JVM sendiri pada
  port ephemeral loopback (bukan port 5555–5558 pada spesifikasi); lihat batas di bawah.
- **Log keputusan** (`decisions.jsonl`, ~5,2 KB/keputusan) dikompresi menjadi gzip deterministik (mtime 0) di akhir job (~426 B/keputusan,
  12×). Tanpa ini studi penuh membutuhkan ~2,5 TiB.

## Bukti

| Skenario | Hasil |
|---|---|
| **prefix** — F-only 1.024 vs checkpoint 1.024 dari run 2.048 (bobot & seed sama) | policy, optimizer, counter/stream, RNG identik |
| **reference** — studi mini 4 outer run (0–3), sekuensial | 16 job, satu attempt tiap job; 339.968 keputusan training dan 157.520 keputusan validasi = ledger |
| **interrupt** — penulis kedua; SIGTERM; resume; SIGKILL runner; SIGKILL worker; resume lagi | penulis kedua ditolak; exit 75 dan grup worker mati; job lengkap `REUSED`; lock diblokir selama child hidup; lock basi diarsipkan; attempt `interrupted → failed (technical) → complete`; tidak ada JVM tersisa; resume pada studi complete tidak membuat attempt baru; **konten akhir (policy, optimizer, RNG, baris validasi) identik dengan run tanpa gangguan** |
| **drift** — salinan studi dengan hash source/config/JAR/manifest trace diubah, dan satu artefak complete dimodifikasi | kelimanya ditolak sebelum ada attempt baru |
| **parallel** — 4 runner bersamaan (satu per outer run) | 4 JVM bersamaan dengan port berbeda, 16 perbandingan konten vs referensi tanpa selisih, 160 s vs 569 s sekuensial (**speedup 3,55×, efisiensi 89%**), tidak ada server tersisa |
| **capacity** — ekstrapolasi dari profil terukur | lihat tabel di bawah |

Catatan temuan selama pengujian (semuanya diperbaiki sebelum bukti final, bukti diulang dari awal):

1. Interupsi ikut menghabiskan jatah retry teknis → dipisahkan (`attempt_history`).
2. Proses worker yang mati menjadi zombie karena PID 1 kontainer tidak mereap → lock tidak pernah dapat dipulihkan → zombie dianggap mati.
3. Worker yang di-SIGKILL dapat meninggalkan JVM → grup dibersihkan setelah tiap attempt.
4. Hash byte `model.zip` tidak reprodusibel antar-run (header zip memuat timestamp). Kesetaraan model dinilai pada tensor policy, state
   optimizer, penghitung, dan RNG — bukan pada hash file.
5. Log keputusan mentah 2,5 TiB melebihi disk → gzip.

## Kapasitas studi penuh (ekstrapolasi, bukan pengukuran studi penuh)

Throughput terukur: training 804 keputusan/s per worker (termasuk update PPO), validasi kandidat 2.181 keputusan/s, ~1,17 core dan
~0,76 GiB RAM per worker.

| | Per outer run | 20 outer run |
|---|---:|---:|
| Waktu, satu worker | 9,9 jam (search 2,1 jam ×2, baseline 2,8 jam ×2, final 2 menit ×2) | 198 jam (8,3 hari) |
| Disk (log gzip) | 10,8 GiB | 216 GiB (mentah: 2,5 TiB) |

| Worker | Waktu P11 (training) | Catatan |
|---:|---:|---|
| 4 | 2,3 hari | efisiensi 89% **terukur** |
| 10 | **22 jam** | 2 outer run per worker; **direkomendasikan** |
| 13 | 22 jam | sama dengan 10 (tetap 2 putaran); batas disk |
| 20 | 11 jam | **tidak mungkin di container ini** (kuota 16 core); juga ~790 GiB log mentah sementara |

Efisiensi di atas 4 worker belum diukur dan diasumsikan sama. Batas: desain sharding per outer run (20), disk (14 dengan log mentah
sampai job selesai), dan **kuota CPU container 16 core / memori 64 GiB** (≈12 worker; `nproc` menampilkan 64 core host — koreksi 8 Nov 2026). Evaluasi test (P11) ≈ 48,4 juta keputusan ≈ 6,2 jam pada satu worker.

## Batasan

- Hanya studi mini (1 slot kandidat, K=512, F=1.024) yang dijalankan. Pencarian 80 slot, baseline 8,17 juta keputusan, dan 20 outer
  run belum pernah dijalankan; waktu dan disk adalah ekstrapolasi.
- Runner tidak memiliki scheduler multi-worker di dalam satu studi; paralelisme adalah multi-studi. Paralelisme di atas 20 membutuhkan
  pemecahan per job.
- Fixture tidak membuktikan bahwa NSGA-II atau PPO bekerja dengan baik; hanya orkestrasi, akuntansi, dan pemulihan.
- Perubahan sesudah bukti live: hanya `research_v2/trace_access.py` (mekanisme unseal P10); berkas runner tidak berubah
  (`runner_critical_files_unchanged_since_evidence` = true pada verifikasi).
