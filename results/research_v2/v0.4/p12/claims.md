# P12 — claims table (protocol v0.4)

Status follows the registered P11 analysis; sensitivity is exploratory and only qualifies robustness.

| # | Claim | Evidence | Status |
|---|---|---|---|
| RQ1 | NSGA-II reward weights make PPO better than equal weights at the same final budget F | diff 0.0198, 95% CI [-0.0284, 0.0639], Holm p 0.849; direction kept in 9/9 sensitivity variants | not supported (insufficient evidence; not equivalence) |
| RQ2 | NSGA-II reward weights make PPO better than random-search weights | diff 0.0064, 95% CI [-0.0279, 0.0459], Holm p 0.849; direction kept in 9/9 sensitivity variants | not supported (insufficient evidence; not equivalence) |
| RQ3 | Weight search + training at F is better than equal weights trained with the same total compute B | diff -0.0781, 95% CI [-0.1134, -0.0471], Holm p 2.86e-05; direction kept in 9/9 sensitivity variants | contradicted (significant in the opposite direction) |
| E | NSGA-II PPO vs `always_local` heuristic | diff 0.1262, CI [0.0876, 0.1600], raw p 3.62e-05 | exploratory: PPO better |
| E | NSGA-II PPO vs `nearest_fog` heuristic | diff 0.2685, CI [0.2301, 0.3023], raw p 1.91e-06 | exploratory: PPO better |
| E | NSGA-II PPO vs `least_fog` heuristic | diff 0.2308, CI [0.1923, 0.2645], raw p 1.91e-06 | exploratory: PPO better |
| E | NSGA-II PPO vs `greedy_eft` heuristic | diff 0.0174, CI [-0.0210, 0.0512], raw p 0.367 | exploratory: no clear difference |

## Limits of every claim

- Simulation only (iFogSim2/CloudSim, synthetic parameters; F3 power anchored to one example). No real testbed.
- Workloads are synthetic Poisson traces in four regimes; 100 test traces per workload; one topology (100 IoT, 5 fogs, 1 cloud).
- Energy model: linear idle/busy power plus per-bit network energy; idle energy identical across methods on a trace.
- Observability: the 108-feature public snapshot; heuristics see the same snapshot; no look-ahead.
- One learner configuration (PPO, gamma 0.97 from a pilot diagnosis; protocol v0.3), n = 20 outer training runs.
- The registered design changed twice before the test was opened (v0.2 -> v0.3 -> v0.4); all versions are archived.
- Compute: each weight search costs S + V = 19,534,400 decisions per outer run before the final model (F = 102,400); the compute-matched baseline trains for B = 19,637,248.
- Sensitivity is zero-shot and one factor at a time on frozen models (exploratory); it does not show retrained robustness.
- Non-significant results mean insufficient evidence, not equivalence. Test findings were not used to retune anything.
- Literature mapping / novelty statement: still to be updated by the authors before any state-of-the-art claim.
