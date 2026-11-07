package org.fog.erwo.v2;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.json.simple.JSONObject;

/**
 * The 108-feature public snapshot (specification section 17.1), built only from current state and from arrivals already
 * decided. Every feature is computed by name and then laid out in the order of the wire contract's
 * {@code observation_features}, so the Java and Python orderings cannot drift. Both the raw (untransformed) values and
 * the transformed vector are returned; heuristics may read the raw one, PPO the transformed one.
 *
 * <p>Nothing here reads the trace beyond the task being decided, the workload label, the seed, the reward weights or any
 * future arrival. N, the trace length, is never exposed.
 */
final class ObservationBuilder {
    /** Raw snapshot (null marks the empty-node deadline sentinel) and the transformed vector in contract order. */
    static final class Snapshot {
        final Map<String, Double> raw;
        final double[] vector;
        Snapshot(Map<String, Double> raw, double[] vector) {
            this.raw = raw;
            this.vector = vector;
        }
    }

    private static final String[] NODE_BLOCK = {"source_iot", "F1", "F2", "F3", "F4", "F5", "cloud"};

    private final List<String> featureNames = new ArrayList<>();
    private final double mipsRef, pesRef, cpuMiRef, inputRefBytes, outputRefBytes, deadlineRef, timeoutRef, bandwidthRef,
            cpuIncrementRef, timeSquashRef, arrivalSquashRef, communicationSquashRef, emaTau, remainingDeadlineRef;
    private final String[] classes;
    private double arrivalEma;
    private double lastDecisionS;

    ObservationBuilder(JSONObject wire, Map<?, ?> observationConfig, List<String> classIds) {
        for (Object name : (List<?>) wire.get("observation_features")) featureNames.add((String) name);
        mipsRef = Json.number(observationConfig, "mips_reference");
        pesRef = Json.number(observationConfig, "pes_reference");
        cpuMiRef = Json.number(observationConfig, "cpu_mi_reference");
        inputRefBytes = Json.number(observationConfig, "input_reference_mib") * (1 << 20);
        outputRefBytes = Json.number(observationConfig, "output_reference_mib") * (1 << 20);
        deadlineRef = Json.number(observationConfig, "deadline_reference_s");
        timeoutRef = Json.number(observationConfig, "timeout_reference_s");
        bandwidthRef = Json.number(observationConfig, "bandwidth_reference_bit_per_s");
        cpuIncrementRef = Json.number(observationConfig, "cpu_increment_reference_j_per_mi");
        timeSquashRef = Json.number(observationConfig, "time_squash_reference_s");
        arrivalSquashRef = Json.number(observationConfig, "arrival_squash_reference_per_s");
        communicationSquashRef = Json.number(observationConfig, "communication_squash_reference_j");
        emaTau = Json.number(observationConfig, "ema_time_constant_s");
        remainingDeadlineRef = Json.number(observationConfig, "remaining_deadline_reference_s");
        this.classes = classIds.toArray(new String[0]);
    }

    private double squash(double x, double reference) {
        return x / (x + reference);
    }

    /** Builds the snapshot for the task being decided now. Call once per arrival, in arrival order. */
    Snapshot build(EngineCoordinator engine, TaskSpec task) {
        double now = engine.nowS();
        // Causal EMA of the arrival rate: only arrivals already decided, plus this one.
        double interarrival = Math.max(0.0, now - lastDecisionS);
        arrivalEma = arrivalEma * Math.exp(-interarrival / emaTau) + 1.0 / emaTau;
        lastDecisionS = now;

        Map<String, Double> raw = new LinkedHashMap<>();
        Map<String, Double> obs = new HashMap<>();
        Map<String, EngineCoordinator.NodeLoad> loads = engine.nodeLoads();
        Map<String, ComputeNode> nodes = engine.nodeMap();

        for (String block : NODE_BLOCK) {
            String id = "source_iot".equals(block) ? "IoT-" + task.sourceIot : block;
            ComputeNode node = nodes.get(id);
            EngineCoordinator.NodeLoad load = loads.get(id);
            if (node == null || load == null) throw new IllegalStateException("Observation needs node " + id);
            String p = "node." + block + ".";
            double increment = (node.spec.busyW - node.spec.idleW) / node.spec.pes / node.spec.mipsPerPe;   // J per MI
            put(raw, obs, p + "busy_pe_fraction", load.busyFraction, load.busyFraction);
            put(raw, obs, p + "queue_fraction", load.queueFraction, load.queueFraction);
            put(raw, obs, p + "earliest_pe_free_delay_s", load.earliestFreeS, squash(load.earliestFreeS, timeSquashRef));
            put(raw, obs, p + "queued_mi_over_mips_s", load.queuedMiOverMipsS, squash(load.queuedMiOverMipsS, timeSquashRef));
            put(raw, obs, p + "mips_per_pe", node.spec.mipsPerPe, node.spec.mipsPerPe / mipsRef);
            put(raw, obs, p + "pes", node.spec.pes, node.spec.pes / pesRef);
            put(raw, obs, p + "cpu_increment_j_per_mi", increment, increment / cpuIncrementRef);
            put(raw, obs, p + "remaining_mi_over_mips_s", load.remainingMiOverMipsS, squash(load.remainingMiOverMipsS, timeSquashRef));
            Double remaining = load.minRemainingDeadlineS;
            // Empty node: sentinel 1 in the transformed vector; the raw value is null, and busy fraction 0 / queue 0 disambiguate.
            raw.put(p + "minimum_remaining_deadline_s", remaining);
            obs.put(p + "minimum_remaining_deadline_s", remaining == null ? 1.0 : remaining / (Math.abs(remaining) + remainingDeadlineRef));
        }

        NetworkModel network = engine.network();
        if (network == null) throw new IllegalStateException("The v2 observation requires the P03 network model");
        for (String block : NODE_BLOCK) {
            String p = "route." + block + ".";
            if ("source_iot".equals(block)) {
                // A local task crosses no link: all four route features are zero.
                for (String f : new String[] {"estimated_input_delay_s", "estimated_result_delay_s", "bottleneck_bit_per_s", "estimated_dynamic_energy_j"}) {
                    put(raw, obs, p + f, 0.0, 0.0);
                }
                continue;
            }
            double[] in = network.estimate(NetworkModel.Phase.INPUT, task.accessFog, block, task.inputBytes, now);
            double[] out = network.estimate(NetworkModel.Phase.RESULT, task.accessFog, block, task.outputBytes, now);
            double energy = in[2] + out[2];
            put(raw, obs, p + "estimated_input_delay_s", in[0], squash(in[0], timeSquashRef));
            put(raw, obs, p + "estimated_result_delay_s", out[0], squash(out[0], timeSquashRef));
            put(raw, obs, p + "bottleneck_bit_per_s", Math.min(in[1], out[1]), Math.min(in[1], out[1]) / bandwidthRef);
            put(raw, obs, p + "estimated_dynamic_energy_j", energy, squash(energy, communicationSquashRef));
        }

        put(raw, obs, "task.cpu_mi", task.cpuMi, task.cpuMi / cpuMiRef);
        put(raw, obs, "task.input_bytes", task.inputBytes, task.inputBytes / inputRefBytes);
        put(raw, obs, "task.output_bytes", task.outputBytes, task.outputBytes / outputRefBytes);
        put(raw, obs, "task.deadline_relative_s", task.deadlineRelativeS, task.deadlineRelativeS / deadlineRef);
        put(raw, obs, "task.timeout_relative_s", task.timeoutRelativeS, task.timeoutRelativeS / timeoutRef);
        for (String c : classes) {
            double hot = c.equals(task.classId) ? 1.0 : 0.0;
            put(raw, obs, "task.class." + c, hot, hot);
        }
        for (int fog = 1; fog <= 5; fog++) {
            double hot = fog == task.accessFog ? 1.0 : 0.0;
            put(raw, obs, "source.access_fog.F" + fog, hot, hot);
        }
        double iotUtilization = 0.0;
        int iots = 0;
        for (ComputeNode node : nodes.values()) {
            if (node.spec.id.startsWith("IoT-")) {
                iotUtilization += node.utilization();
                iots++;
            }
        }
        double meanIot = iots == 0 ? 0.0 : iotUtilization / iots;
        double timeFraction = now / engine.arrivalWindowS();
        put(raw, obs, "global.time_fraction", timeFraction, timeFraction);
        put(raw, obs, "global.arrival_ema_per_s", arrivalEma, squash(arrivalEma, arrivalSquashRef));
        put(raw, obs, "global.mean_iot_utilization", meanIot, meanIot);
        put(raw, obs, "global.interarrival_s", interarrival, squash(interarrival, timeSquashRef));

        double[] vector = new double[featureNames.size()];
        Map<String, Double> ordered = new LinkedHashMap<>();
        for (int i = 0; i < vector.length; i++) {
            String name = featureNames.get(i);
            Double value = obs.get(name);
            if (value == null) throw new IllegalStateException("Contract feature not produced: " + name);
            vector[i] = value;
            ordered.put(name, raw.get(name));
        }
        if (obs.size() != vector.length) throw new IllegalStateException("Produced " + obs.size() + " features for a contract of " + vector.length);
        return new Snapshot(ordered, vector);
    }

    private static void put(Map<String, Double> raw, Map<String, Double> obs, String name, double rawValue, double transformed) {
        if (Double.isNaN(transformed) || Double.isInfinite(transformed)) throw new IllegalStateException("Non-finite feature " + name);
        raw.put(name, rawValue);
        obs.put(name, transformed);
    }
}
