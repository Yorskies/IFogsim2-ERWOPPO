# Reproduction package — research v2, protocol v0.4

Protocol lock `P10-lock-3`, sha256 `63d07e43c01ebfcbf65b4feac24f6be73650481d09752c6f5f99b89641517ca7`; source at git `0ecaf5bc91b75a58299b0f07f2b2ea6f28c122ca`.

## What is where

| Item | Location |
|---|---|
| Confirmatory result (P11) | `results/research_v2/v0.4/p11/test_evaluation/report.md` (+ `report.json`, per-episode rows in `episodes/`) |
| Protocol, lock, deviations | `docs/research_v2/PROTOCOL_v0.4.md`, `results/research_v2/v0.4/protocol_lock/protocol_lock.json`, `deviations_from_v02.json` |
| Test opening record | `results/research_v2/TEST_OPENED.json` |
| Sensitivity (exploratory) | `results/research_v2/v0.4/p12/sensitivity/report.md` |
| Final audit | `results/research_v2/v0.4/p12/audit/audit.json`, model index `audit/model_index.json` |
| Clean-clone reproduction | `results/research_v2/v0.4/p12/repro/result.json` |
| Claims and limits | `results/research_v2/v0.4/p12/claims.md` |
| Checksums | `SHA256SUMS`, `ARTIFACT_INDEX.json` (git-tracked files and the 120 evaluated checkpoints) |

Not in git (archive separately with `SHA256SUMS`): the 120 evaluated `model.zip` checkpoints and their per-checkpoint metadata,
6480 gzip decision logs (~480 GiB), and the remaining intermediate checkpoints (`results/research_v2/ARTIFACTS_NOT_IN_GIT.md`).

## Reproduce

```bash
git clone <repo> && cd IFogsim2-ERWOPPO && git checkout 0ecaf5bc91b75a58299b0f07f2b2ea6f28c122ca
python3.12 -m venv venv && venv/bin/pip install -r requirements-v2-learning.txt -r requirements-v2-analysis.txt
venv/bin/python ifogsim/build_v2.py --jdk-home /path/to/jdk-21          # JAR; entry contents must match the lock
PYTHONPATH=. venv/bin/python -m research_v2.analysis.lock verify --lock results/research_v2/v0.4/protocol_lock/protocol_lock.json
./run_p11_v04.sh go-open-test     # full P11 (~1.5-2.5 days on 16 CPUs): training, test evaluation, registered analysis
./run_p12.sh                      # sensitivity, audit, reproduction checks, package, claims (~8-10 h)
```

To re-check the published numbers without retraining: restore the archived checkpoints at the paths listed in
`ARTIFACT_INDEX.json` (verify with `sha256sum -c SHA256SUMS`), then run the P11 analysis from the stored episode rows
(`research_v2.p12` stage `audit` does exactly this and compares with `report.json`).

The analysis is deterministic (fixed bootstrap and sign-flip seeds). PPO training is deterministic on the same CPU build of
PyTorch with one thread; across machines, small numerical differences in training are possible and are not hidden.
