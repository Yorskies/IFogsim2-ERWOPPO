# P10 analysis report

> **FIXTURE / PILOT DATA — NOT STUDY EVIDENCE.** Labels nsga2/random are placeholders for the P09 fixture jobs (one weight vector, 1,024 decisions; 'random' is the manual-weight baseline). Only the pipeline is being exercised, on the validation namespace.

Unit of inference: **outer training run** (n = 4). Traces per workload: {'light': 5, 'moderate': 5, 'heavy': 5, 'dynamic': 5}. Tasks/episodes are never pooled into replicates and p-values are never averaged.
Sign convention: difference = D(comparator) − D(NSGA-II); **positive = NSGA-II better**. Bootstrap: 10000 crossed paired draws (seed 20261105); secondary sign-flip: 100000 Monte Carlo draws (seed 20261106).
Assumption of the sign-flip tests: the paired differences are symmetric about zero under the null; pairing does not by itself guarantee this. Non-significant means insufficient evidence, not equivalence.

## 1. Primary comparisons — confirmatory (3 tests, one Holm family, alpha 0.05)

| Test | Comparator vs NSGA-II | mean diff | 95% CI | rel. improvement (95% CI) | ≥1% screen | dz | raw p (exact) | Holm p |
|---|---|---:|---|---|:-:|---:|---:|---:|
| RQ1 | equal_F | 0.0000 | [0.0000, 0.0000] | 0.00% ([0.00, 0.00]) | no | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ2 | random | -0.0162 | [-0.0346, 0.0009] | -2.67% ([-7.33, 0.12]) | no | -0.767 | 0.5000 | 1.0000 |
| RQ3 | equal_B | -0.2295 | [-0.3585, -0.0052] | -58.31% ([-106.61, -1.15]) | no | -1.016 | 0.2500 | 0.7500 |

The ≥1% screen is a reporting convention, not an SLA and not evidence of practical benefit by itself.

## 2. Method summary (Dglobal, between-run uncertainty)

| Method | Dglobal mean | SD between runs | SE | Dw light | Dw moderate | Dw heavy | Dw dynamic |
|---|---:|---:|---:|---:|---:|---:|---:|
| nsga2 | 0.6230 | 0.2057 | 0.1028 | 0.4305 | 0.6853 | 0.7428 | 0.6658 |
| random | 0.6068 | 0.2162 | 0.1081 | 0.4105 | 0.6629 | 0.7343 | 0.6488 |
| equal_F | 0.6230 | 0.2057 | 0.1028 | 0.4305 | 0.6853 | 0.7428 | 0.6658 |
| equal_B | 0.3935 | 0.0850 | 0.0425 | 0.1506 | 0.3789 | 0.6030 | 0.4681 |
| manual_F | 0.6068 | 0.2162 | 0.1081 | 0.4105 | 0.6629 | 0.7343 | 0.6488 |
| manual_B | 0.4960 | 0.0847 | 0.0424 | 0.1933 | 0.5295 | 0.7298 | 0.5631 |

Mean cost vector F per method (workload macro-average):

| Method | zL | zE | zD | zB | zQ | worst workload (run counts) |
|---|---:|---:|---:|---:|---:|---|
| nsga2 | 0.6478 | 0.0679 | 0.8376 | 0.6374 | 0.5825 | {'light': 0, 'moderate': 0, 'heavy': 4, 'dynamic': 0} |
| random | 0.6212 | 0.0674 | 0.8185 | 0.6419 | 0.5559 | {'light': 0, 'moderate': 0, 'heavy': 4, 'dynamic': 0} |
| equal_F | 0.6478 | 0.0679 | 0.8376 | 0.6374 | 0.5825 | {'light': 0, 'moderate': 0, 'heavy': 4, 'dynamic': 0} |
| equal_B | 0.4055 | 0.0515 | 0.6569 | 0.1911 | 0.3084 | {'light': 0, 'moderate': 0, 'heavy': 4, 'dynamic': 0} |
| manual_F | 0.6212 | 0.0674 | 0.8185 | 0.6419 | 0.5559 | {'light': 0, 'moderate': 0, 'heavy': 4, 'dynamic': 0} |
| manual_B | 0.4990 | 0.0647 | 0.7291 | 0.4154 | 0.4170 | {'light': 0, 'moderate': 0, 'heavy': 4, 'dynamic': 0} |

## 3. Secondary — secondary, pre-specified (60 tests, own Holm family; not confirmatory)

All 60 results are reported. Monte Carlo p = (b+1)/(M+1).

| id | mean diff | 95% CI | dz | raw p | Holm p |
|---|---:|---|---:|---:|---:|
| RQ1:light:zL | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:light:zE | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:light:zD | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:light:zB | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:light:zQ | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:moderate:zL | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:moderate:zE | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:moderate:zD | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:moderate:zB | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:moderate:zQ | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:heavy:zL | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:heavy:zE | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:heavy:zD | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:heavy:zB | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:heavy:zQ | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:dynamic:zL | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:dynamic:zE | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:dynamic:zD | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:dynamic:zB | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ1:dynamic:zQ | 0.0000 | [0.0000, 0.0000] | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ2:light:zL | -0.0085 | [-0.0266, 0.0074] | -0.504 | 0.5021 | 1.0000 |
| RQ2:light:zE | -0.0047 | [-0.0165, 0.0017] | -0.404 | 1.0000 | 1.0000 |
| RQ2:light:zD | -0.0178 | [-0.1091, 0.0481] | -0.190 | 1.0000 | 1.0000 |
| RQ2:light:zB | -0.0227 | [-0.1092, 0.0329] | -0.262 | 1.0000 | 1.0000 |
| RQ2:light:zQ | -0.0064 | [-0.0252, 0.0047] | -0.447 | 0.7500 | 1.0000 |
| RQ2:moderate:zL | -0.0475 | [-0.0991, -0.0095] | -0.891 | 0.2516 | 1.0000 |
| RQ2:moderate:zE | 0.0018 | [-0.0001, 0.0044] | 0.633 | 0.5021 | 1.0000 |
| RQ2:moderate:zD | -0.0295 | [-0.0619, 0.0000] | -0.818 | 0.2516 | 1.0000 |
| RQ2:moderate:zB | 0.0229 | [-0.0005, 0.0688] | 0.510 | 0.5021 | 1.0000 |
| RQ2:moderate:zQ | -0.0489 | [-0.1095, -0.0078] | -0.803 | 0.2516 | 1.0000 |
| RQ2:heavy:zL | -0.0240 | [-0.0499, -0.0010] | -0.841 | 0.2516 | 1.0000 |
| RQ2:heavy:zE | 0.0009 | [-0.0003, 0.0025] | 0.563 | 0.5021 | 1.0000 |
| RQ2:heavy:zD | -0.0124 | [-0.0268, 0.0002] | -0.784 | 0.5021 | 1.0000 |
| RQ2:heavy:zB | 0.0211 | [-0.0052, 0.0663] | 0.470 | 0.7521 | 1.0000 |
| RQ2:heavy:zQ | -0.0246 | [-0.0545, 0.0000] | -0.762 | 0.2516 | 1.0000 |
| RQ2:dynamic:zL | -0.0265 | [-0.0543, -0.0017] | -0.852 | 0.2516 | 1.0000 |
| RQ2:dynamic:zE | 0.0001 | [-0.0005, 0.0009] | 0.212 | 0.7500 | 1.0000 |
| RQ2:dynamic:zD | -0.0167 | [-0.0440, 0.0033] | -0.589 | 0.5021 | 1.0000 |
| RQ2:dynamic:zB | -0.0031 | [-0.0390, 0.0310] | -0.079 | 1.0000 | 1.0000 |
| RQ2:dynamic:zQ | -0.0267 | [-0.0607, -0.0019] | -0.760 | 0.2516 | 1.0000 |
| RQ3:light:zL | -0.2236 | [-0.6305, 0.0084] | -0.551 | 0.2508 | 1.0000 |
| RQ3:light:zE | -0.0537 | [-0.0872, -0.0080] | -1.089 | 0.2501 | 1.0000 |
| RQ3:light:zD | -0.3302 | [-0.6871, -0.0047] | -0.873 | 0.2508 | 1.0000 |
| RQ3:light:zB | -0.4378 | [-0.7113, -0.0434] | -1.107 | 0.2501 | 1.0000 |
| RQ3:light:zQ | -0.2200 | [-0.6264, -0.0024] | -0.540 | 0.1249 | 1.0000 |
| RQ3:moderate:zL | -0.4023 | [-0.6478, -0.0977] | -1.204 | 0.2501 | 1.0000 |
| RQ3:moderate:zE | -0.0095 | [-0.0251, 0.0060] | -0.510 | 0.5016 | 1.0000 |
| RQ3:moderate:zD | -0.2139 | [-0.3712, -0.0589] | -1.191 | 0.1249 | 1.0000 |
| RQ3:moderate:zB | -0.5342 | [-0.8102, -0.0360] | -1.077 | 0.2501 | 1.0000 |
| RQ3:moderate:zQ | -0.4476 | [-0.6958, -0.0982] | -1.221 | 0.2501 | 1.0000 |
| RQ3:heavy:zL | -0.1312 | [-0.5483, 0.3576] | -0.236 | 0.6255 | 1.0000 |
| RQ3:heavy:zE | 0.0050 | [-0.0041, 0.0125] | 0.527 | 0.5002 | 1.0000 |
| RQ3:heavy:zD | -0.0474 | [-0.2666, 0.1509] | -0.202 | 0.6255 | 1.0000 |
| RQ3:heavy:zB | -0.3706 | [-0.6538, 0.0388] | -0.877 | 0.2501 | 1.0000 |
| RQ3:heavy:zQ | -0.1786 | [-0.6462, 0.3815] | -0.282 | 0.6255 | 1.0000 |
| RQ3:dynamic:zL | -0.2118 | [-0.4919, 0.1754] | -0.523 | 0.3749 | 1.0000 |
| RQ3:dynamic:zE | -0.0073 | [-0.0139, -0.0022] | -1.038 | 0.1249 | 1.0000 |
| RQ3:dynamic:zD | -0.1313 | [-0.2395, 0.0088] | -0.890 | 0.2501 | 1.0000 |
| RQ3:dynamic:zB | -0.4428 | [-0.6995, -0.0420] | -1.074 | 0.2501 | 1.0000 |
| RQ3:dynamic:zQ | -0.2504 | [-0.5681, 0.1961] | -0.538 | 0.3749 | 1.0000 |

## 4. Exploratory — exploratory (unregistered family, no multiplicity control)

| comparator vs treatment | mean diff | 95% CI | dz | raw p |
|---|---:|---|---:|---:|
| manual_B vs equal_B | 0.1025 | [0.0577, 0.1318] | 2.240 | 0.1250 |
| manual_F vs equal_F | -0.0162 | [-0.0346, 0.0009] | -0.767 | 0.5000 |

## 5. Practical meaning (paired, comparator − NSGA-II, mean over runs)

Dynamic energy J = zE × 50 J × N per trace; idle energy is identical for all methods on a trace, so total-Joule differences equal dynamic differences. Violation/reliability are percentage points.

| comparison | Δ dynamic energy (J/trace) | Δ violation (pp) | Δ reliability (pp) |
|---|---:|---:|---:|
| equal_F − nsga2 | 0.00 | 0.000 | 0.000 |
| random − nsga2 | 26.30 | -1.909 | 2.665 |
| equal_B − nsga2 | -269.32 | -18.070 | 27.417 |

## 6. Computational cost (one worker, from P09 profiles)

| job | training decisions | validation decisions | wall s | CPU s | peak RSS GiB | gradient updates |
|---|---:|---:|---:|---:|---:|---:|
| r00_mini_search | 1024 | 39380 | 19.2 | 26.6 | 0.74 | 20 |
| r00_mini_final | 1024 | 0 | 10.8 | 15.8 | 0.75 | 20 |
| r00_equal | 41472 | 0 | 51.1 | 59.9 | 0.74 | 810 |
| r00_manual | 41472 | 0 | 54.1 | 61.5 | 0.75 | 810 |
| r01_mini_search | 1024 | 39380 | 19.3 | 27.6 | 0.74 | 20 |
| r01_mini_final | 1024 | 0 | 10.4 | 15.0 | 0.75 | 20 |
| r01_equal | 41472 | 0 | 50.9 | 59.6 | 0.76 | 810 |
| r01_manual | 41472 | 0 | 51.2 | 60.2 | 0.75 | 810 |
| r02_mini_search | 1024 | 39380 | 19.7 | 27.8 | 0.76 | 20 |
| r02_mini_final | 1024 | 0 | 10.4 | 15.6 | 0.77 | 20 |
| r02_equal | 41472 | 0 | 51.5 | 61.6 | 0.75 | 810 |
| r02_manual | 41472 | 0 | 51.1 | 60.3 | 0.76 | 810 |
| r03_mini_search | 1024 | 39380 | 19.1 | 27.7 | 0.75 | 20 |
| r03_mini_final | 1024 | 0 | 10.3 | 15.1 | 0.74 | 20 |
| r03_equal | 41472 | 0 | 51.0 | 59.4 | 0.75 | 810 |
| r03_manual | 41472 | 0 | 52.1 | 61.0 | 0.75 | 810 |
