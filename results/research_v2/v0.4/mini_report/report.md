# P10 analysis report

> **FIXTURE / PILOT DATA — NOT STUDY EVIDENCE.** Labels nsga2/random are placeholders for the P09 fixture jobs (one weight vector, 1,024 decisions; 'random' is the manual-weight baseline). Only the pipeline is being exercised, on the validation namespace.

Unit of inference: **outer training run** (n = 4). Traces per workload: {'light': 5, 'moderate': 5, 'heavy': 5, 'dynamic': 5}. Tasks/episodes are never pooled into replicates and p-values are never averaged.
Sign convention: difference = D(comparator) − D(NSGA-II); **positive = NSGA-II better**. Bootstrap: 10000 crossed paired draws (seed 20261105); secondary sign-flip: 100000 Monte Carlo draws (seed 20261106).
Assumption of the sign-flip tests: the paired differences are symmetric about zero under the null; pairing does not by itself guarantee this. Non-significant means insufficient evidence, not equivalence.

## 1. Primary comparisons — confirmatory (3 tests, one Holm family, alpha 0.05)

| Test | Comparator vs NSGA-II | mean diff | 95% CI | rel. improvement (95% CI) | ≥1% screen | dz | raw p (exact) | Holm p |
|---|---|---:|---|---|:-:|---:|---:|---:|
| RQ1 | equal_F | 0.0000 | [0.0000, 0.0000] | 0.00% ([0.00, 0.00]) | no | undefined_zero_sd_zero_mean | 1.0000 | 1.0000 |
| RQ2 | random | 0.0266 | [-0.0326, 0.0970] | 4.21% ([-4.63, 18.48]) | yes | 0.349 | 0.7500 | 1.0000 |
| RQ3 | equal_B | -0.2335 | [-0.4561, -0.0122] | -62.83% ([-175.55, -2.54]) | no | -0.881 | 0.2500 | 0.7500 |

The ≥1% screen is a reporting convention, not an SLA and not evidence of practical benefit by itself.

## 2. Method summary (Dglobal, between-run uncertainty)

| Method | Dglobal mean | SD between runs | SE | Dw light | Dw moderate | Dw heavy | Dw dynamic |
|---|---:|---:|---:|---:|---:|---:|---:|
| nsga2 | 0.6050 | 0.1789 | 0.0894 | 0.3544 | 0.6760 | 0.7554 | 0.6650 |
| random | 0.6317 | 0.1039 | 0.0520 | 0.3324 | 0.7159 | 0.8089 | 0.7025 |
| equal_F | 0.6050 | 0.1789 | 0.0894 | 0.3544 | 0.6760 | 0.7554 | 0.6650 |
| equal_B | 0.3716 | 0.1463 | 0.0731 | 0.1563 | 0.4097 | 0.5137 | 0.4227 |
| manual_F | 0.6317 | 0.1039 | 0.0520 | 0.3324 | 0.7159 | 0.8089 | 0.7025 |
| manual_B | 0.3881 | 0.0910 | 0.0455 | 0.1119 | 0.3600 | 0.6414 | 0.4729 |

Mean cost vector F per method (workload macro-average):

| Method | zL | zE | zD | zB | zQ | worst workload (run counts) |
|---|---:|---:|---:|---:|---:|---|
| nsga2 | 0.6701 | 0.0594 | 0.8031 | 0.5388 | 0.6149 | {'light': 0, 'moderate': 0, 'heavy': 4, 'dynamic': 0} |
| random | 0.7162 | 0.0569 | 0.8232 | 0.5346 | 0.6645 | {'light': 0, 'moderate': 0, 'heavy': 4, 'dynamic': 0} |
| equal_F | 0.6701 | 0.0594 | 0.8031 | 0.5388 | 0.6149 | {'light': 0, 'moderate': 0, 'heavy': 4, 'dynamic': 0} |
| equal_B | 0.3717 | 0.0543 | 0.6166 | 0.1736 | 0.2746 | {'light': 0, 'moderate': 0, 'heavy': 4, 'dynamic': 0} |
| manual_F | 0.7162 | 0.0569 | 0.8232 | 0.5346 | 0.6645 | {'light': 0, 'moderate': 0, 'heavy': 4, 'dynamic': 0} |
| manual_B | 0.3980 | 0.0590 | 0.5875 | 0.3449 | 0.3149 | {'light': 0, 'moderate': 0, 'heavy': 4, 'dynamic': 0} |

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
| RQ2:light:zL | -0.0340 | [-0.1252, 0.0278] | -0.373 | 0.6235 | 1.0000 |
| RQ2:light:zE | 0.0001 | [-0.0036, 0.0040] | 0.035 | 0.7488 | 1.0000 |
| RQ2:light:zD | -0.0300 | [-0.1220, 0.0402] | -0.321 | 0.6235 | 1.0000 |
| RQ2:light:zB | 0.0021 | [-0.0029, 0.0076] | 0.364 | 0.7488 | 1.0000 |
| RQ2:light:zQ | -0.0355 | [-0.1281, 0.0261] | -0.383 | 0.7488 | 1.0000 |
| RQ2:moderate:zL | 0.0732 | [-0.0393, 0.1849] | 0.527 | 0.3762 | 1.0000 |
| RQ2:moderate:zE | -0.0044 | [-0.0089, 0.0004] | -0.768 | 0.2516 | 1.0000 |
| RQ2:moderate:zD | 0.0361 | [-0.0326, 0.1143] | 0.405 | 0.7527 | 1.0000 |
| RQ2:moderate:zB | -0.0093 | [-0.0240, 0.0019] | -0.609 | 0.5016 | 1.0000 |
| RQ2:moderate:zQ | 0.0777 | [-0.0394, 0.1930] | 0.542 | 0.3762 | 1.0000 |
| RQ2:heavy:zL | 0.0840 | [-0.0117, 0.2557] | 0.491 | 0.6268 | 1.0000 |
| RQ2:heavy:zE | -0.0030 | [-0.0054, -0.0001] | -0.935 | 0.2516 | 1.0000 |
| RQ2:heavy:zD | 0.0439 | [-0.0059, 0.1362] | 0.474 | 0.7527 | 1.0000 |
| RQ2:heavy:zB | -0.0060 | [-0.0152, 0.0023] | -0.617 | 0.5016 | 1.0000 |
| RQ2:heavy:zQ | 0.0901 | [-0.0127, 0.2726] | 0.496 | 0.6268 | 1.0000 |
| RQ2:dynamic:zL | 0.0612 | [-0.0290, 0.1839] | 0.476 | 0.6268 | 1.0000 |
| RQ2:dynamic:zE | -0.0028 | [-0.0050, 0.0006] | -0.828 | 0.2516 | 1.0000 |
| RQ2:dynamic:zD | 0.0301 | [-0.0271, 0.1063] | 0.379 | 0.7527 | 1.0000 |
| RQ2:dynamic:zB | -0.0035 | [-0.0090, 0.0004] | -0.705 | 0.2501 | 1.0000 |
| RQ2:dynamic:zQ | 0.0657 | [-0.0292, 0.1942] | 0.488 | 0.5015 | 1.0000 |
| RQ3:light:zL | -0.1808 | [-0.4921, -0.0055] | -0.579 | 0.1249 | 1.0000 |
| RQ3:light:zE | -0.0355 | [-0.0681, -0.0031] | -0.952 | 0.1249 | 1.0000 |
| RQ3:light:zD | -0.2125 | [-0.4432, -0.0390] | -0.880 | 0.1249 | 1.0000 |
| RQ3:light:zB | -0.3343 | [-0.6407, -0.0263] | -0.911 | 0.2501 | 1.0000 |
| RQ3:light:zQ | -0.1859 | [-0.4990, -0.0060] | -0.591 | 0.2501 | 1.0000 |
| RQ3:moderate:zL | -0.3615 | [-0.7135, -0.0098] | -0.831 | 0.2501 | 1.0000 |
| RQ3:moderate:zE | -0.0009 | [-0.0119, 0.0086] | -0.079 | 0.8748 | 1.0000 |
| RQ3:moderate:zD | -0.2016 | [-0.4857, 0.0428] | -0.620 | 0.3748 | 1.0000 |
| RQ3:moderate:zB | -0.3896 | [-0.7645, -0.0163] | -0.906 | 0.2501 | 1.0000 |
| RQ3:moderate:zQ | -0.4093 | [-0.7843, -0.0318] | -0.873 | 0.2501 | 1.0000 |
| RQ3:heavy:zL | -0.3251 | [-0.6707, 0.0130] | -0.814 | 0.2501 | 1.0000 |
| RQ3:heavy:zE | 0.0136 | [0.0038, 0.0246] | 1.159 | 0.1249 | 1.0000 |
| RQ3:heavy:zD | -0.1515 | [-0.4118, 0.0430] | -0.566 | 0.3748 | 1.0000 |
| RQ3:heavy:zB | -0.3797 | [-0.7756, 0.0152] | -0.837 | 0.3748 | 1.0000 |
| RQ3:heavy:zQ | -0.3880 | [-0.7569, -0.0106] | -0.881 | 0.2501 | 1.0000 |
| RQ3:dynamic:zL | -0.3262 | [-0.6008, -0.0163] | -0.909 | 0.2501 | 1.0000 |
| RQ3:dynamic:zE | 0.0022 | [-0.0049, 0.0112] | 0.233 | 0.7486 | 1.0000 |
| RQ3:dynamic:zD | -0.1804 | [-0.4018, 0.0127] | -0.719 | 0.3748 | 1.0000 |
| RQ3:dynamic:zB | -0.3570 | [-0.7031, -0.0151] | -0.901 | 0.2501 | 1.0000 |
| RQ3:dynamic:zQ | -0.3782 | [-0.6785, -0.0357] | -0.956 | 0.2501 | 1.0000 |

## 4. Exploratory — exploratory (unregistered family, no multiplicity control)

| comparator vs treatment | mean diff | 95% CI | dz | raw p |
|---|---:|---|---:|---:|
| manual_B vs equal_B | 0.0165 | [-0.1786, 0.1776] | 0.076 | 1.0000 |
| manual_F vs equal_F | 0.0266 | [-0.0326, 0.0970] | 0.349 | 0.7500 |

## 5. Practical meaning (paired, comparator − NSGA-II, mean over runs)

Dynamic energy J = zE × 50 J × N per trace; idle energy is identical for all methods on a trace, so total-Joule differences equal dynamic differences. Violation/reliability are percentage points.

| comparison | Δ dynamic energy (J/trace) | Δ violation (pp) | Δ reliability (pp) |
|---|---:|---:|---:|
| equal_F − nsga2 | 0.00 | 0.000 | 0.000 |
| random − nsga2 | -149.62 | 2.003 | -4.951 |
| equal_B − nsga2 | 198.06 | -18.651 | 34.037 |

## 6. Computational cost (one worker, from P09 profiles)

| job | training decisions | validation decisions | wall s | CPU s | peak RSS GiB | gradient updates |
|---|---:|---:|---:|---:|---:|---:|
| r00_mini_search | 1024 | 39380 | 19.2 | 27.2 | 0.77 | 20 |
| r00_mini_final | 1024 | 0 | 10.4 | 15.2 | 0.76 | 20 |
| r00_equal | 41472 | 0 | 48.3 | 58.7 | 0.76 | 810 |
| r00_manual | 41472 | 0 | 48.1 | 57.5 | 0.75 | 810 |
| r01_mini_search | 1024 | 39380 | 19.3 | 27.8 | 0.75 | 20 |
| r01_mini_final | 1024 | 0 | 10.4 | 15.3 | 0.74 | 20 |
| r01_equal | 41472 | 0 | 48.6 | 58.1 | 0.74 | 810 |
| r01_manual | 41472 | 0 | 48.1 | 57.8 | 0.75 | 810 |
| r02_mini_search | 1024 | 39380 | 19.4 | 27.7 | 0.74 | 20 |
| r02_mini_final | 1024 | 0 | 10.3 | 15.2 | 0.76 | 20 |
| r02_equal | 41472 | 0 | 48.2 | 57.4 | 0.76 | 810 |
| r02_manual | 41472 | 0 | 48.3 | 57.4 | 0.77 | 810 |
| r03_mini_search | 1024 | 39380 | 19.3 | 27.6 | 0.76 | 20 |
| r03_mini_final | 1024 | 0 | 10.2 | 15.0 | 0.74 | 20 |
| r03_equal | 41472 | 0 | 48.2 | 57.8 | 0.76 | 810 |
| r03_manual | 41472 | 0 | 48.1 | 57.1 | 0.74 | 810 |
