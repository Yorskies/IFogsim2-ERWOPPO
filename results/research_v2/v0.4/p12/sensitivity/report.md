# P12 — sensitivity analysis (protocol v0.4)

**All results here are exploratory_unadjusted**: effect, 95% crossed-bootstrap CI, raw exact sign-flip p; no multiplicity
control and no confirmatory status. The confirmatory result is P11 (`p11/test_evaluation/report.md`).
Frozen P11 models, zero-shot, one factor at a time, test split; normalization always the main definition.
Difference = D(comparator) - D(NSGA-II); positive = NSGA-II better.

Variant mechanism control: identity variant reproduced 1200 P11 test episodes exactly.

## 1. Physical factors (test split)

| variant | nsga2 | random | equal_F | equal_B | manual_F | manual_B | always_local | nearest_fog | least_fog | greedy_eft | rank rho vs main | flagged episodes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| main (P11) | 0.2454 | 0.2518 | 0.2652 | 0.1673 | 0.2595 | 0.1693 | 0.3716 | 0.5139 | 0.4762 | 0.2628 | 1.000 | 0 |
| timeout_k2 | 0.2625 | 0.2668 | 0.2833 | 0.1802 | 0.2769 | 0.1851 | 0.4050 | 0.5369 | 0.5007 | 0.2734 | 0.988 | 0 |
| timeout_k4 | 0.2412 | 0.2497 | 0.2586 | 0.1674 | 0.2545 | 0.1654 | 0.3663 | 0.5023 | 0.4643 | 0.2570 | 0.988 | 0 |
| fog_queue_8 | 0.2453 | 0.2516 | 0.2651 | 0.1673 | 0.2596 | 0.1693 | 0.3716 | 0.5138 | 0.4768 | 0.2627 | 1.000 | 0 |
| fog_queue_32 | 0.2454 | 0.2518 | 0.2653 | 0.1673 | 0.2595 | 0.1694 | 0.3716 | 0.5139 | 0.4762 | 0.2628 | 1.000 | 0 |
| wan_prop_0.01 | 0.2415 | 0.2485 | 0.2613 | 0.1631 | 0.2561 | 0.1660 | 0.3716 | 0.5139 | 0.4762 | 0.2561 | 0.988 | 0 |
| wan_prop_0.04 | 0.2540 | 0.2593 | 0.2739 | 0.1771 | 0.2677 | 0.1774 | 0.3716 | 0.5139 | 0.4762 | 0.2777 | 0.988 | 0 |
| dyn_power_x0.75 | 0.2471 | 0.2513 | 0.2663 | 0.1676 | 0.2601 | 0.1696 | 0.3712 | 0.5126 | 0.4748 | 0.2620 | 1.000 | 0 |
| dyn_power_x1.25 | 0.2449 | 0.2523 | 0.2649 | 0.1679 | 0.2596 | 0.1698 | 0.3720 | 0.5156 | 0.4780 | 0.2638 | 1.000 | 0 |
| homogeneous_fog | 0.2464 | 0.2548 | 0.2624 | 0.1695 | 0.2641 | 0.1789 | 0.3716 | 0.4790 | 0.4677 | 0.2294 | 0.903 | 0 |

Dglobal mean over the 20 outer runs (lower is better). Flagged = episodes with a cost outside [0, 1] (kept unclipped, out-of-reference).

### Registered comparisons under each variant

| variant | test | comparator | mean diff | 95% CI | dz | raw p | same sign as main |
|---|---|---|---:|---|---:|---:|:-:|
| main (P11) | RQ1 | equal_F | 0.0198 | [-0.0284, 0.0639] | 0.185 | 0.4244 | yes |
| main (P11) | RQ2 | random | 0.0064 | [-0.0279, 0.0459] | 0.072 | 0.7682 | yes |
| main (P11) | RQ3 | equal_B | -0.0781 | [-0.1134, -0.0471] | -1.006 | 9.537e-06 | yes |
| main (P11) | heuristic | always_local | 0.1262 | [0.0876, 0.1600] | 1.497 | 3.624e-05 | yes |
| main (P11) | heuristic | nearest_fog | 0.2685 | [0.2301, 0.3023] | 3.186 | 1.907e-06 | yes |
| main (P11) | heuristic | least_fog | 0.2308 | [0.1923, 0.2645] | 2.739 | 1.907e-06 | yes |
| main (P11) | heuristic | greedy_eft | 0.0174 | [-0.0210, 0.0512] | 0.207 | 0.3667 | yes |
| timeout_k2 | RQ1 | equal_F | 0.0208 | [-0.0249, 0.0630] | 0.202 | 0.3832 | yes |
| timeout_k2 | RQ2 | random | 0.0043 | [-0.0295, 0.0422] | 0.050 | 0.8338 | yes |
| timeout_k2 | RQ3 | equal_B | -0.0823 | [-0.1155, -0.0528] | -1.118 | 5.722e-06 | yes |
| timeout_k2 | heuristic | always_local | 0.1425 | [0.1059, 0.1750] | 1.770 | 1.144e-05 | yes |
| timeout_k2 | heuristic | nearest_fog | 0.2744 | [0.2379, 0.3069] | 3.407 | 1.907e-06 | yes |
| timeout_k2 | heuristic | least_fog | 0.2382 | [0.2015, 0.2707] | 2.957 | 1.907e-06 | yes |
| timeout_k2 | heuristic | greedy_eft | 0.0109 | [-0.0256, 0.0434] | 0.135 | 0.5516 | yes |
| timeout_k4 | RQ1 | equal_F | 0.0175 | [-0.0303, 0.0600] | 0.167 | 0.4741 | yes |
| timeout_k4 | RQ2 | random | 0.0086 | [-0.0253, 0.0482] | 0.098 | 0.6862 | yes |
| timeout_k4 | RQ3 | equal_B | -0.0738 | [-0.1101, -0.0423] | -0.934 | 2.289e-05 | yes |
| timeout_k4 | heuristic | always_local | 0.1252 | [0.0859, 0.1591] | 1.471 | 4.005e-05 | yes |
| timeout_k4 | heuristic | nearest_fog | 0.2611 | [0.2221, 0.2952] | 3.068 | 1.907e-06 | yes |
| timeout_k4 | heuristic | least_fog | 0.2231 | [0.1838, 0.2573] | 2.622 | 1.907e-06 | yes |
| timeout_k4 | heuristic | greedy_eft | 0.0158 | [-0.0233, 0.0499] | 0.186 | 0.4139 | yes |
| fog_queue_8 | RQ1 | equal_F | 0.0198 | [-0.0280, 0.0637] | 0.186 | 0.4216 | yes |
| fog_queue_8 | RQ2 | random | 0.0063 | [-0.0280, 0.0458] | 0.071 | 0.7715 | yes |
| fog_queue_8 | RQ3 | equal_B | -0.0780 | [-0.1131, -0.0471] | -1.010 | 9.537e-06 | yes |
| fog_queue_8 | heuristic | always_local | 0.1263 | [0.0878, 0.1600] | 1.502 | 3.624e-05 | yes |
| fog_queue_8 | heuristic | nearest_fog | 0.2686 | [0.2303, 0.3023] | 3.195 | 1.907e-06 | yes |
| fog_queue_8 | heuristic | least_fog | 0.2315 | [0.1929, 0.2651] | 2.754 | 1.907e-06 | yes |
| fog_queue_8 | heuristic | greedy_eft | 0.0174 | [-0.0211, 0.0512] | 0.207 | 0.3655 | yes |
| fog_queue_32 | RQ1 | equal_F | 0.0199 | [-0.0284, 0.0642] | 0.185 | 0.4246 | yes |
| fog_queue_32 | RQ2 | random | 0.0064 | [-0.0280, 0.0460] | 0.073 | 0.7673 | yes |
| fog_queue_32 | RQ3 | equal_B | -0.0781 | [-0.1135, -0.0471] | -1.005 | 9.537e-06 | yes |
| fog_queue_32 | heuristic | always_local | 0.1262 | [0.0876, 0.1600] | 1.496 | 3.624e-05 | yes |
| fog_queue_32 | heuristic | nearest_fog | 0.2685 | [0.2300, 0.3023] | 3.184 | 1.907e-06 | yes |
| fog_queue_32 | heuristic | least_fog | 0.2308 | [0.1923, 0.2645] | 2.737 | 1.907e-06 | yes |
| fog_queue_32 | heuristic | greedy_eft | 0.0174 | [-0.0210, 0.0511] | 0.206 | 0.3677 | yes |
| wan_prop_0.01 | RQ1 | equal_F | 0.0198 | [-0.0289, 0.0642] | 0.183 | 0.4295 | yes |
| wan_prop_0.01 | RQ2 | random | 0.0069 | [-0.0274, 0.0466] | 0.079 | 0.7484 | yes |
| wan_prop_0.01 | RQ3 | equal_B | -0.0784 | [-0.1143, -0.0471] | -0.999 | 9.537e-06 | yes |
| wan_prop_0.01 | heuristic | always_local | 0.1300 | [0.0910, 0.1642] | 1.525 | 3.433e-05 | yes |
| wan_prop_0.01 | heuristic | nearest_fog | 0.2723 | [0.2334, 0.3066] | 3.195 | 1.907e-06 | yes |
| wan_prop_0.01 | heuristic | least_fog | 0.2346 | [0.1956, 0.2686] | 2.753 | 1.907e-06 | yes |
| wan_prop_0.01 | heuristic | greedy_eft | 0.0146 | [-0.0245, 0.0488] | 0.171 | 0.4526 | yes |
| wan_prop_0.04 | RQ1 | equal_F | 0.0199 | [-0.0270, 0.0629] | 0.190 | 0.413 | yes |
| wan_prop_0.04 | RQ2 | random | 0.0053 | [-0.0288, 0.0446] | 0.061 | 0.8049 | yes |
| wan_prop_0.04 | RQ3 | equal_B | -0.0769 | [-0.1109, -0.0469] | -1.023 | 1.144e-05 | yes |
| wan_prop_0.04 | heuristic | always_local | 0.1175 | [0.0804, 0.1503] | 1.442 | 4.578e-05 | yes |
| wan_prop_0.04 | heuristic | nearest_fog | 0.2599 | [0.2228, 0.2927] | 3.187 | 1.907e-06 | yes |
| wan_prop_0.04 | heuristic | least_fog | 0.2222 | [0.1849, 0.2549] | 2.725 | 1.907e-06 | yes |
| wan_prop_0.04 | heuristic | greedy_eft | 0.0237 | [-0.0135, 0.0563] | 0.290 | 0.2068 | yes |
| dyn_power_x0.75 | RQ1 | equal_F | 0.0192 | [-0.0282, 0.0625] | 0.182 | 0.4329 | yes |
| dyn_power_x0.75 | RQ2 | random | 0.0042 | [-0.0293, 0.0423] | 0.049 | 0.8384 | yes |
| dyn_power_x0.75 | RQ3 | equal_B | -0.0794 | [-0.1138, -0.0495] | -1.052 | 5.722e-06 | yes |
| dyn_power_x0.75 | heuristic | always_local | 0.1242 | [0.0867, 0.1569] | 1.513 | 3.433e-05 | yes |
| dyn_power_x0.75 | heuristic | nearest_fog | 0.2655 | [0.2281, 0.2984] | 3.235 | 1.907e-06 | yes |
| dyn_power_x0.75 | heuristic | least_fog | 0.2277 | [0.1901, 0.2605] | 2.775 | 1.907e-06 | yes |
| dyn_power_x0.75 | heuristic | greedy_eft | 0.0150 | [-0.0226, 0.0477] | 0.182 | 0.4238 | yes |
| dyn_power_x1.25 | RQ1 | equal_F | 0.0201 | [-0.0284, 0.0647] | 0.186 | 0.4235 | yes |
| dyn_power_x1.25 | RQ2 | random | 0.0075 | [-0.0271, 0.0475] | 0.084 | 0.7312 | yes |
| dyn_power_x1.25 | RQ3 | equal_B | -0.0769 | [-0.1129, -0.0455] | -0.976 | 1.717e-05 | yes |
| dyn_power_x1.25 | heuristic | always_local | 0.1271 | [0.0879, 0.1616] | 1.483 | 3.624e-05 | yes |
| dyn_power_x1.25 | heuristic | nearest_fog | 0.2707 | [0.2315, 0.3052] | 3.159 | 1.907e-06 | yes |
| dyn_power_x1.25 | heuristic | least_fog | 0.2331 | [0.1938, 0.2676] | 2.720 | 1.907e-06 | yes |
| dyn_power_x1.25 | heuristic | greedy_eft | 0.0189 | [-0.0202, 0.0534] | 0.221 | 0.3377 | yes |
| homogeneous_fog | RQ1 | equal_F | 0.0161 | [-0.0313, 0.0603] | 0.152 | 0.5135 | yes |
| homogeneous_fog | RQ2 | random | 0.0084 | [-0.0253, 0.0471] | 0.098 | 0.6849 | yes |
| homogeneous_fog | RQ3 | equal_B | -0.0769 | [-0.1121, -0.0461] | -0.994 | 7.629e-06 | yes |
| homogeneous_fog | heuristic | always_local | 0.1252 | [0.0861, 0.1593] | 1.474 | 4.387e-05 | yes |
| homogeneous_fog | heuristic | nearest_fog | 0.2327 | [0.1937, 0.2668] | 2.739 | 1.907e-06 | yes |
| homogeneous_fog | heuristic | least_fog | 0.2214 | [0.1823, 0.2555] | 2.606 | 1.907e-06 | yes |
| homogeneous_fog | heuristic | greedy_eft | -0.0170 | [-0.0562, 0.0171] | -0.200 | 0.3929 | **no** |

## 2. Normalization and penalty (validation split only)

Recomputed from the same validation episodes (5 traces x 4 workloads, main physics). The main definition is the first row.

| definition | nsga2 | random | equal_F | equal_B | manual_F | manual_B | always_local | nearest_fog | least_fog | greedy_eft | RQ1 diff (raw p) | RQ2 diff (raw p) | RQ3 diff (raw p) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| main definition | 0.2475 | 0.2548 | 0.2679 | 0.1675 | 0.2626 | 0.1694 | 0.3703 | 0.5150 | 0.4835 | 0.2670 | 0.0204 (0.434) | 0.0073 (0.744) | -0.0800 (9.54e-06) |
| latency_ref_x0.8 | 0.2526 | 0.2597 | 0.2731 | 0.1723 | 0.2676 | 0.1740 | 0.3758 | 0.5195 | 0.4879 | 0.2693 | 0.0205 (0.43) | 0.0071 (0.75) | -0.0802 (7.63e-06) |
| failure_penalty_x0.8 | 0.2430 | 0.2494 | 0.2621 | 0.1659 | 0.2578 | 0.1680 | 0.3663 | 0.4964 | 0.4678 | 0.2666 | 0.0191 (0.439) | 0.0063 (0.76) | -0.0771 (9.54e-06) |
| energy_ref_x0.8 | 0.2482 | 0.2554 | 0.2685 | 0.1683 | 0.2633 | 0.1704 | 0.3707 | 0.5166 | 0.4853 | 0.2680 | 0.0203 (0.437) | 0.0072 (0.744) | -0.0799 (9.54e-06) |
| imbalance_ref_x0.8 | 0.2531 | 0.2592 | 0.2690 | 0.1678 | 0.2707 | 0.1761 | 0.3703 | 0.5406 | 0.5111 | 0.3009 | 0.0159 (0.571) | 0.0061 (0.783) | -0.0852 (5.72e-06) |
| latency_ref_x1.2 | 0.2445 | 0.2518 | 0.2648 | 0.1646 | 0.2595 | 0.1667 | 0.3670 | 0.5121 | 0.4807 | 0.2657 | 0.0203 (0.437) | 0.0074 (0.74) | -0.0798 (9.54e-06) |
| failure_penalty_x1.2 | 0.2525 | 0.2608 | 0.2744 | 0.1692 | 0.2679 | 0.1710 | 0.3748 | 0.5362 | 0.5015 | 0.2675 | 0.0219 (0.43) | 0.0083 (0.728) | -0.0833 (9.54e-06) |
| energy_ref_x1.2 | 0.2472 | 0.2544 | 0.2676 | 0.1671 | 0.2622 | 0.1689 | 0.3701 | 0.5141 | 0.4826 | 0.2665 | 0.0205 (0.433) | 0.0073 (0.744) | -0.0801 (9.54e-06) |
| imbalance_ref_x1.2 | 0.2444 | 0.2523 | 0.2673 | 0.1673 | 0.2579 | 0.1656 | 0.3703 | 0.5006 | 0.4679 | 0.2467 | 0.0229 (0.36) | 0.0079 (0.722) | -0.0771 (1.14e-05) |

## 3. Definitions

- `main (P11)`: main configuration (registered P11 result, recomputed from its episodes)
- `timeout_k2`: timeout factor k = 2 (main 3); horizon T + k*Dmax; latency reference and penalty unchanged
- `timeout_k4`: timeout factor k = 4 (main 3); horizon T + k*Dmax; latency reference and penalty unchanged
- `fog_queue_8`: fog waiting-queue capacity 8 on F1-F5 (main 16)
- `fog_queue_32`: fog waiting-queue capacity 32 on F1-F5 (main 16)
- `wan_prop_0.01`: WAN propagation 0.01 s (main 0.02 s)
- `wan_prop_0.04`: WAN propagation 0.04 s (main 0.02 s)
- `dyn_power_x0.75`: dynamic power x0.75: node busy-idle increments, radio/AP increments and per-bit network energy; idle power and the energy reference unchanged
- `dyn_power_x1.25`: dynamic power x1.25: node busy-idle increments, radio/AP increments and per-bit network energy; idle power and the energy reference unchanged
- `homogeneous_fog`: homogeneous fog control: every fog uses the F3 profile (main JAR, reset option)
- `main definition`: main normalization (registered)
- `latency_ref_x0.8`: latency reference and failure penalty x0.8
- `failure_penalty_x0.8`: failure latency penalty only x0.8
- `energy_ref_x0.8`: energy reference x0.8
- `imbalance_ref_x0.8`: imbalance reference x0.8
- `latency_ref_x1.2`: latency reference and failure penalty x1.2
- `failure_penalty_x1.2`: failure latency penalty only x1.2
- `energy_ref_x1.2`: energy reference x1.2
- `imbalance_ref_x1.2`: imbalance reference x1.2
