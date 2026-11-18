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

## P11 v0.4 (`results/research_v2/v0.4/p11/`, ≈ 491 GB lokal, 9 Nov 2026)

Di repo: `test_evaluation/` (report.md/json, baris episode test per model), `shard_NN.log`, `protocol.json`, `budget_report.json`,
`summary.json` per shard, `complete.json` per job, dan per attempt `profile.json`, `status.json`, `worker.log`, `data/protocol.json`,
`data/result.json` (memuat seluruh record kandidat search dan bobot terpilih).
Tidak di repo: `decisions.jsonl.gz` (+ `.meta.json`), `model.zip`, `rng.pt`, dan per checkpoint/kandidat `manifest.json`,
`episodes.jsonl`, `learning_curve.jsonl`, `traces.jsonl`, `progress.json`, `outcome.json`, `candidate.json`, `summary.json`,
`initial_policy.json`, `environment-freeze.txt`, `effective_learner_config.json` (≈ 6,1 GB metadata + checkpoint/log).

## P12 v0.4 (`results/research_v2/v0.4/p12/`, ≈ 650 MB lokal, 15 Nov 2026)

Di repo: `sensitivity/report.md|json`, episode varian `identity` (kontrol mekanisme), `validation_main/episodes/` (dasar analisis normalisasi),
`audit/`, `repro/result.json`, `repro/worker.py`, `repro/*_physical.json` dan log, `package/` (ARTIFACT_INDEX.json, SHA256SUMS,
README_REPRODUCTION.md), `claims.md`, `variants/` (config dan `index.json`), `pipeline/` (state, log, task_logs).
Tidak di repo: baris episode sensitivitas per varian (`sensitivity/<varian>/episodes/`, 9 × ≈ 71 MB), run PPO kecil uji reproduksi
(`repro/main_learn/`, `repro/clone_learn/`: checkpoint dan log keputusan), dan JAR varian (`ifogsim/dist_p12/`, dibangun ulang otomatis oleh
`research_v2/p12.py`; hash tercatat di `variants/index.json`). Laporan sensitivitas dapat diregenerasi dengan `./run_p12.sh` dari model P11.
