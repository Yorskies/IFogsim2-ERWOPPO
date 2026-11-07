package org.fog.erwo.v2;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** Static description of one compute node (IoT, fog or logical cloud). Units: MIPS per PE, bytes, W. */
final class NodeSpec {
    final String id;
    final int pes;
    final double mipsPerPe;
    final long ramBytes;
    final int queueWaiting;
    final double idleW;
    final double busyW;

    NodeSpec(String id, int pes, double mipsPerPe, long ramBytes, int queueWaiting, double idleW, double busyW) {
        if (id == null || id.isEmpty() || pes < 1 || !(mipsPerPe > 0) || ramBytes < 1 || queueWaiting < 0
                || !(idleW >= 0) || !(busyW >= idleW)) {
            throw new IllegalArgumentException("Invalid node spec: " + id);
        }
        this.id = id;
        this.pes = pes;
        this.mipsPerPe = mipsPerPe;
        this.ramBytes = ramBytes;
        this.queueWaiting = queueWaiting;
        this.idleW = idleW;
        this.busyW = busyW;
    }

    static NodeSpec fromJson(Map<?, ?> o) {
        return fromJson(o, (String) o.get("id"));
    }

    static NodeSpec fromJson(Map<?, ?> o, String id) {
        return new NodeSpec(id, Json.integer(o, "pes"), Json.number(o, "mips_per_pe"), Json.longValue(o, "ram_bytes"),
                Json.integer(o, "queue_waiting"), Json.number(o, "idle_w"), Json.number(o, "busy_w"));
    }

    double capacityMips() {
        return pes * mipsPerPe;
    }

    /**
     * Builds the 100 IoT + 5 fog + 1 cloud topology from the validated v2 config. Homogeneous mode
     * gives every fog the F3 profile (CPU, RAM, queue and power together), as the specification requires.
     */
    static List<NodeSpec> topology(Map<?, ?> config, boolean homogeneousFog) {
        Map<?, ?> topology = (Map<?, ?>) config.get("topology");
        int iotCount = Json.integer(topology, "iot_count");
        List<NodeSpec> nodes = new ArrayList<>();
        Map<?, ?> iot = (Map<?, ?>) topology.get("iot");
        for (int i = 0; i < iotCount; i++) nodes.add(fromJson(iot, "IoT-" + i));
        List<?> fogs = (List<?>) topology.get("fogs");
        Map<?, ?> f3 = null;
        for (Object fog : fogs) if ("F3".equals(((Map<?, ?>) fog).get("id"))) f3 = (Map<?, ?>) fog;
        if (f3 == null) throw new IllegalStateException("Config has no F3 fog profile");
        for (Object fog : fogs) {
            Map<?, ?> source = (Map<?, ?>) fog;
            nodes.add(fromJson(homogeneousFog ? f3 : source, (String) source.get("id")));
        }
        nodes.add(fromJson((Map<?, ?>) topology.get("cloud"), "cloud"));
        return nodes;
    }
}
