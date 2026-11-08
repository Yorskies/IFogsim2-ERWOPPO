# P08 — Search implementation and pilot fidelity

The original experiment is `results/research_v2/P08_fidelity_1/` and its gate failed. A separately frozen exploratory extension at `results/research_v2/P08_fidelity_extension_1/` selected K=30,720 with the same threshold, 48 independent prefix confirmations, and an independent episode audit. See [the diagnosis](milestones/P08_learning_diagnosis.md). The original result remains failed.

## Modules

- `search.py`: Euclidean projection to the lower-bounded simplex, frozen eight pilot weights, NSGA-II and random search, nondominated archive, tie selection, fixed-reference hypervolume, Spearman gate.
- `fidelity.py`: 48 reference models (eight weights × two repeats × three outer pilots), independent short models on the fixed budget ladder, complete pilot-validation episodes and prefix comparisons.
- `fidelity_report.py`: independent evidence audit, paired ranking plots, and the fixed-pilot archive. It does not train or start Java.
- `search_runner.py`: a two-fresh-model candidate evaluator for the `train_candidate`/`validation` namespaces, guarded by a passing audited fidelity gate. No final-policy training or test evaluation.

## Frozen algorithm contract

Weights have five components in latency/energy/deadline/imbalance/failure order, each >=0.02 and sum=1. Repair is projection, not clipping followed by ad hoc normalization. Already feasible points are preserved exactly, including equal/manual anchors.

Both search methods start with the same 20 vectors: equal, manual and 18 simplex draws, seed 300000+r. Random search adds 60 draws using 500000+r. NSGA-II uses 20 population × four generations including the initial population, variation seed 400000+r, SBX probability .9/eta 15 and polynomial mutation probability 1/eta 20/probability per coordinate .2. SBX uses pymoo's .5 per-coordinate crossover default. Mutation does not force at least one coordinate to change. Both operators are followed by simplex repair.

Every slot is charged, including repeated weights. There is no free duplicate cache. The objective vector is the mean of two model cost vectors, each already macro-averaged equally over four workloads; D is RMS of that vector. Reward totals with different weights are never compared as fitness.

Archive all evaluated records and derive the nondominated archive from the full history, not only the last generation. Selection minimizes D, then within 1e-9 uses lower failure, lower violation, lexicographically smaller weights. Hypervolume uses the fixed [1.1]*5 reference; it is not changed after seeing results. Equal/manual anchors are preserved in the initial pool and evaluation records; subsequent survival follows NSGA-II, without forcing dominated anchors to remain elites.

Optimizer RNG is separate from the global RNG reset by PPO; a regression test deliberately resets global Python/NumPy RNG inside the objective callback and verifies identical proposals.

## Fidelity design

Reference: 51,200 decisions per model. Candidate ladder: 5,120 → 10,240 → 20,480. Each tested short model is trained independently from scratch and compared with the corresponding reference checkpoint (policy, optimizer, RNG and counters/stream).

Eight weights: equal, manual, five vertices (.92/.02), one lower-bounded simplex draw with seed 20261107. Pilot outer IDs 100/101/102, repeats 0/1. No method ID/weight is put into trace or model seeds. Training uses pilot_train; all models see the same 20 pilot_validation payloads.

For each outer, average the two objective vectors before calculating D and ranking the eight weights. Spearman uses average ranks for exact ties. Select the smallest K with median of three correlations >=.60 and none negative. An undefined short ranking fails that K. A constant reference ranking stops the experiment as uninformative; otherwise proceed through the fixed ladder. If no K passes, stop for diagnosis and block full search.

Up to three independent workers/JVMs use free configured ports 5556–5558 because legacy port 5555 is occupied. Each model uses one Torch/interop/BLAS thread. Parallel wall-clock is labelled and is not compared with earlier serial timings. Config/JAR/PPO parameters remain the baseline .95 lambda/.5 vf_coef/.5 gradient clip.

Per-RPC JSON Schema checking is disabled only for the large experiment's transport overhead. Trace generation validation and JAR/config handshake remain active, complete episode/reward checks remain active, and the auditor rechecks identity and aggregates. A preflight model and the equal reference are compared against earlier baseline checkpoints to verify unchanged trajectories.

Only required reference checkpoints (512, 5120, 10240, 20480, 51200) and each short final checkpoint are retained. Loss logs and raw public decision snapshots are retained at every step. Old P07 APIs retain their default behavior.

## Commands

Prepare writes a new protocol but does not train. `run` performs the training and validation budget described above:

```bash
venv/bin/python -m research_v2.fidelity prepare --evidence-dir results/research_v2/P08_fidelity_reproduced
venv/bin/python -m research_v2.fidelity run --evidence-dir results/research_v2/P08_fidelity_reproduced
```

A resume reuses completed runs only after identity/hash checks. A partial training run is not restored or counted as complete; preserve/inspect it and retry from the beginning in a new attempt. Do not change frozen source/config while a pilot is active.

After the experiment finishes, audit without training:

```bash
venv/bin/python -m research_v2.fidelity_report --evidence-dir results/research_v2/P08_fidelity_1
```

The full-search CLI is available but was not launched by the fidelity pilot. It refuses a failed/unaudited/modified gate, source drift or JAR/config mismatch:

```bash
venv/bin/python -m research_v2.search_runner --method nsga2 --outer 0 --output-dir results/research_v2/SEARCH_NEW_DIR --fidelity-evidence results/research_v2/P08_fidelity_1 --jdk-home /usr/lib/jvm/java-21-openjdk-amd64
```

For the audited extension, use `search_runner_extension` with `P08_fidelity_extension_1` as evidence. Its gate verifies the extension audit, all 48 prefix checks, the original failed result, and unchanged config/JAR/critical training sources. This command has **not** been launched for a full search:

```bash
venv/bin/python -m research_v2.search_runner_extension --method nsga2 --outer 0 --output-dir results/research_v2/SEARCH_NEW_DIR --fidelity-evidence results/research_v2/P08_fidelity_extension_1 --jdk-home /usr/lib/jvm/java-21-openjdk-amd64
```

The original CLI remains blocked for the failed original pilot. K=30,720 raises per-slot training cost from 10,240 to 61,440 decisions (two models). Its gate predicts aggregate ranking on the fixed pilot weights and seeds; it does not establish stable policy learning across repeats.

That command performs 80 charged candidate evaluations and must be scheduled according to the later runner/freeze protocol. Random search uses `--method random` with the same budget and selection rule. A selected weight is not a trained final policy; final policy training is fresh and belongs to later phases.

## Accounting and limits

Reference training is 2,457,600 decisions. With independent short models, total fidelity training is 2,703,360 to 4,177,920 depending on the stopping point. Validation is 1,920 to 3,840 complete episodes and is charged separately using actual task counts. A 512-decision preflight is additional development cost.

The fixed eight-weight archive is a pilot diagnostic, not a result of NSGA-II/random optimization. Fidelity only checks whether short rankings predict the longer reference; it does not prove learned policies provide good service, convergence, superiority, or a Pareto optimum. Confirmatory and test splits remain unopened.
