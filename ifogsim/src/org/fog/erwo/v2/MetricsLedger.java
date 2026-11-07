package org.fog.erwo.v2;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * Official energy ledger and evaluation metrics for one episode (specification section 16).
 *
 * <p>Energy is counted once per component: CPU-IT power integrated over [0, H], radio/AP/switch/gateway idle for the
 * whole horizon, and dynamic communication energy from serialization seconds and bit-hops. FogDevice's default energy
 * counters are never read, so nothing is added twice. Reference scales come from the validated config and are never
 * derived from the data being scored; out-of-range costs are flagged, not clipped.
 *
 * <p>Latency of a failed task is not measured: it is excluded from the physical latency statistics, and only the
 * evaluation cost zL substitutes the labeled penalty.
 */
final class MetricsLedger {
    private MetricsLedger() { }

    /** nearest-rank percentile of a sorted list: element ceil(p * n) (1-based). */
    static double nearestRank(List<Double> sorted, double p) {
        int rank = (int) Math.ceil(p * sorted.size());
        return sorted.get(Math.max(1, rank) - 1);
    }

    static double median(List<Double> sorted) {
        int n = sorted.size();
        return n % 2 == 1 ? sorted.get(n / 2) : (sorted.get(n / 2 - 1) + sorted.get(n / 2)) / 2.0;
    }

    /**
     * @param outcomes per-task records as published (terminal, arrival_s, delivered_s, cpu_dynamic_j, comm_dynamic_j)
     * @param components energy components (id, group, idle_j, dynamic_j)
     * @param fogUtilizationStdIntegral integral over [0, H] of the population std of fog utilizations, in seconds
     */
    static Map<String, Object> build(List<Map<String, Object>> outcomes, List<Map<String, Object>> components, double horizonS,
                                     double arrivalWindowS, Map<?, ?> evaluation, double fogUtilizationStdIntegral, int fogCount,
                                     boolean communicationModeled) {
        int n = outcomes.size();
        if (n == 0) throw new IllegalArgumentException("N=0 trace rejected; no division by zero or resampling");
        int onTime = 0, late = 0, failed = 0, inWindow = 0, afterWindow = 0;
        double attributed = 0.0;
        List<Double> latencies = new ArrayList<>();
        for (Map<String, Object> o : outcomes) {
            String terminal = (String) o.get("terminal");
            attributed += ((Number) o.get("cpu_dynamic_j")).doubleValue() + ((Number) o.get("comm_dynamic_j")).doubleValue();
            if ("FAILED".equals(terminal)) {
                failed++;
                continue;
            }
            if ("ON_TIME".equals(terminal)) onTime++; else late++;
            double delivered = ((Number) o.get("delivered_s")).doubleValue();
            latencies.add(delivered - ((Number) o.get("arrival_s")).doubleValue());
            if (delivered < arrivalWindowS) inWindow++; else afterWindow++;
        }
        if (onTime + late + failed != n) throw new IllegalStateException("N != Nontime + Nlate + Nfailed");
        int success = onTime + late;
        Collections.sort(latencies);

        // ---- energy ledger
        double idleJ = 0, dynamicJ = 0;
        Map<String, double[]> byGroup = new TreeMap<>();
        for (Map<String, Object> c : components) {
            double i = ((Number) c.get("idle_j")).doubleValue(), d = ((Number) c.get("dynamic_j")).doubleValue();
            idleJ += i;
            dynamicJ += d;
            double[] g = byGroup.computeIfAbsent((String) c.get("group"), k -> new double[2]);
            g[0] += i;
            g[1] += d;
        }
        double totalJ = idleJ + dynamicJ;
        Map<String, Object> groups = new LinkedHashMap<>();
        for (Map.Entry<String, double[]> e : byGroup.entrySet()) {
            Map<String, Object> g = new LinkedHashMap<>();
            g.put("idle_j", e.getValue()[0]);
            g.put("dynamic_j", e.getValue()[1]);
            g.put("total_j", e.getValue()[0] + e.getValue()[1]);
            groups.put(e.getKey(), g);
        }
        Map<String, Object> energy = new LinkedHashMap<>();
        energy.put("horizon_s", horizonS);
        energy.put("communication_modeled", communicationModeled);
        energy.put("idle_j", idleJ);
        energy.put("dynamic_j", dynamicJ);
        energy.put("total_j", totalJ);
        energy.put("idle_power_w", idleJ / horizonS);
        energy.put("by_group", groups);
        energy.put("components", components);
        energy.put("dynamic_attributed_to_tasks_j", attributed);
        energy.put("attribution_gap_j", dynamicJ - attributed);
        energy.put("joules_per_arrived_task", totalJ / n);
        energy.put("joules_per_successful_task", success == 0 ? null : (Object) (totalJ / success));

        // ---- physical metrics
        Map<String, Object> latency = new LinkedHashMap<>();
        latency.put("completed_tasks", success);
        latency.put("failed_tasks_excluded", failed);
        latency.put("percentile_method", "nearest_rank: element ceil(p*n) of the sorted completed latencies; median averages the two middle values for even n");
        double mean = Double.NaN;
        if (success == 0) {
            latency.put("mean_s", null);
            latency.put("median_s", null);
            latency.put("p95_s", null);
        } else {
            double sum = 0;
            for (double v : latencies) sum += v;
            mean = sum / success;
            latency.put("mean_s", mean);
            latency.put("median_s", median(latencies));
            latency.put("p95_s", nearestRank(latencies, 0.95));
        }
        Map<String, Object> throughput = new LinkedHashMap<>();
        throughput.put("results_received", success);
        throughput.put("results_per_s", success / horizonS);
        throughput.put("results_during_arrival_window", inWindow);
        throughput.put("results_after_arrival_window", afterWindow);

        Map<String, Object> metrics = new LinkedHashMap<>();
        metrics.put("task_count", n);
        metrics.put("on_time", onTime);
        metrics.put("late_success", late);
        metrics.put("failed", failed);
        metrics.put("success_count", success);
        metrics.put("violation", (late + failed) / (double) n);
        metrics.put("reliability", success / (double) n);
        metrics.put("latency", latency);
        metrics.put("throughput", throughput);

        // ---- five costs (labeled evaluation convention: failed tasks carry the latency penalty in zL only)
        double latencyRef = Json.number(evaluation, "latency_reference_s");
        double penalty = Json.number(evaluation, "failure_latency_penalty_s");
        double energyRef = Json.number(evaluation, "energy_reference_j_per_arrival");
        double imbalanceRef = Json.number(evaluation, "imbalance_reference");
        double latencySum = 0;
        for (double v : latencies) latencySum += v;
        double zL = (latencySum + failed * penalty) / (n * latencyRef);
        double zE = dynamicJ / (energyRef * n);
        double zD = (late + failed) / (double) n;
        double zQ = failed / (double) n;
        Double zB = fogCount == 0 ? null : fogUtilizationStdIntegral / (horizonS * imbalanceRef);
        Map<String, Object> costs = new LinkedHashMap<>();
        costs.put("zL", zL);
        costs.put("zE", zE);
        costs.put("zD", zD);
        costs.put("zB", zB);
        costs.put("zQ", zQ);
        metrics.put("costs", costs);
        double sumSq = zL * zL + zE * zE + zD * zD + zQ * zQ + (zB == null ? 0 : zB * zB);
        metrics.put("D", zB == null ? null : (Object) Math.sqrt(sumSq / 5.0));
        List<String> outOfReference = new ArrayList<>();
        for (Map.Entry<String, Object> e : costs.entrySet()) {
            if (e.getValue() != null && (((Number) e.getValue()).doubleValue() < 0 || ((Number) e.getValue()).doubleValue() > 1)) {
                outOfReference.add(e.getKey());
            }
        }
        metrics.put("out_of_reference", outOfReference);
        metrics.put("diagnosis_required", !outOfReference.isEmpty());
        metrics.put("latency_penalty_s_applied_to_failed_in_zL", penalty);
        metrics.put("latency_penalty_is_evaluation_convention_not_measured_latency", true);
        metrics.put("fog_count", fogCount);
        metrics.put("fog_utilization_std_integral_s", fogUtilizationStdIntegral);

        Map<String, Object> out = new LinkedHashMap<>();
        out.put("energy", energy);
        out.put("metrics", metrics);
        return out;
    }
}
