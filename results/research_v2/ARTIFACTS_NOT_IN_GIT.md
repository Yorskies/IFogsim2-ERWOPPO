# Artefak yang sengaja tidak masuk git

Hasil ringkas (JSON, laporan, manifest, profil, log kecil, baris episode) ada di repo. Artefak besar berikut disimpan lokal di server dan harus
diarsipkan terpisah dari repo source (butir P12), bukan di-commit:

| Artefak | Ukuran (8 Nov 2026) | Alasan |
|---|---:|---|
| `decisions.jsonl` / `decisions.jsonl.gz` (log audit per keputusan, P07–P09) | ≈ 43 GB mentah | batas ukuran GitHub; P09 menyimpannya sebagai gzip deterministik |
| `model.zip`, `rng.pt` (checkpoint SB3 dan RNG) | ≈ 1,1 GB | sudah dikecualikan `.gitignore` (`*.zip`, `*.pt`) |
| `ifogsim/build/` (JAR hasil build) | — | `.gitignore`; bangun ulang dengan `ifogsim/build_v2.py`. Protocol lock mencatat hash JAR |

Akibat: lock (`P10_protocol_lock/protocol_lock.json`) dapat diverifikasi di clone baru hanya setelah JAR dibangun ulang dan hash-nya sama;
bukti yang direferensikan lock (`P09_runner_evidence/live_evidence.json`, `P09_dry_run_full/budget_report.json`, hasil dan audit fidelity P08) ada di repo.
Hash byte `model.zip` tidak reprodusibel antar-run (header zip memuat timestamp); kesetaraan model dinilai pada tensor, optimizer, penghitung, dan RNG.
