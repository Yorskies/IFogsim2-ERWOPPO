package org.fog.erwo.v2;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Store-and-forward transport between IoT, fog access points, the fog switch and the cloud (specification section 15).
 *
 * <p>Each link server serves one message at a time, FCFS, with a bounded waiting queue. A message holds a server only
 * while it is being serialized ({@code 8 * bytes / bit_per_s}); propagation afterwards does not hold the server.
 * Access channels are half duplex (one server shared by upload and download); LAN and WAN links are full duplex
 * (one server per direction). Messages are never retransmitted and a full queue is a service failure.
 *
 * <p>The model owns no clock: it asks the coordinator to schedule {@code SERIALIZATION_DONE} and
 * {@code HOP_ARRIVED} events through {@link Sink}, so ordering and stale-event handling stay in one place.
 */
final class NetworkModel {
    enum Phase { INPUT, RESULT }
    enum Status { ACCEPTED, REJECTED, COMPLETE }

    static final int UP = 0;    // toward the fog switch / cloud (IoT -> fog access -> switch -> cloud)
    static final int DOWN = 1;  // toward the IoT

    interface Sink {
        void schedule(double at, EngineCoordinator.Kind kind, int taskId, int generation, Object payload);
    }

    static final class Server {
        final String id;
        final String linkType;
        final double bitPerS;
        final double propagationS;
        final int queueWaiting;
        Transfer active;
        final ArrayDeque<Transfer> waiting = new ArrayDeque<>();
        final double[] busyS = new double[2];
        final double[] bytesSent = new double[2];
        final int[] started = new int[2];
        final int[] completed = new int[2];
        final int[] cancelled = new int[2];
        final int[] rejected = new int[2];
        int maxWaiting;

        Server(String id, String linkType, double bitPerS, double propagationS, int queueWaiting) {
            if (!(bitPerS > 0) || propagationS < 0 || queueWaiting < 0) throw new IllegalArgumentException("Invalid link " + id);
            this.id = id;
            this.linkType = linkType;
            this.bitPerS = bitPerS;
            this.propagationS = propagationS;
            this.queueWaiting = queueWaiting;
        }
    }

    static final class Hop {
        final Server server;
        final int direction;
        Hop(Server server, int direction) {
            this.server = server;
            this.direction = direction;
        }
    }

    static final class Transfer {
        final int taskId;
        final int generation;
        final Phase phase;
        final long bytes;
        final List<Hop> route;
        int hop;
        double enteredS = Double.NaN;
        double serializationStartS = Double.NaN;
        boolean inService;
        boolean inPropagation;
        boolean done;

        Transfer(int taskId, int generation, Phase phase, long bytes, List<Hop> route) {
            this.taskId = taskId;
            this.generation = generation;
            this.phase = phase;
            this.bytes = bytes;
            this.route = route;
        }

        Hop current() { return route.get(hop); }
    }

    private final int fogCount;
    private final Server[] access;
    private final Server[][] lan;   // [fog][direction]
    private final Server[] wan;     // [direction]
    private final List<Server> all = new ArrayList<>();
    private final Sink sink;
    private final List<Map<String, Object>> log;
    private final double radioIdleW, radioTxW, radioRxW, apIdleW, apTxW, apRxW, lanIdleW, wanIdleW, lanJPerBitHop, wanJPerBitHop;
    private final Map<Integer, Double> taskDynamicJ = new java.util.HashMap<>();
    private double settledJ;

    /**
     * @param config validated {@code network} section, optionally with per-type overrides already merged
     * @param logTransfers keep a per-hop record (large for heavy traces; aggregates are always kept)
     */
    NetworkModel(Map<?, ?> config, int fogCount, Sink sink, boolean logTransfers) {
        this.fogCount = fogCount;
        this.sink = sink;
        this.log = logTransfers ? new ArrayList<>() : null;
        radioIdleW = Json.number(config, "radio_idle_w");
        radioTxW = Json.number(config, "radio_tx_increment_w");
        radioRxW = Json.number(config, "radio_rx_increment_w");
        apIdleW = Json.number(config, "ap_idle_w");
        apTxW = Json.number(config, "ap_tx_increment_w");
        apRxW = Json.number(config, "ap_rx_increment_w");
        lanIdleW = Json.number(config, "lan_idle_w");
        wanIdleW = Json.number(config, "wan_idle_w");
        lanJPerBitHop = Json.number(config, "lan_j_per_bit_hop");
        wanJPerBitHop = Json.number(config, "wan_j_per_bit_hop");
        Map<?, ?> a = (Map<?, ?>) config.get("access");
        Map<?, ?> l = (Map<?, ?>) config.get("lan");
        Map<?, ?> w = (Map<?, ?>) config.get("wan");
        requireDuplex(a, "half", "access");
        requireDuplex(l, "full", "lan");
        requireDuplex(w, "full", "wan");
        access = new Server[fogCount + 1];
        lan = new Server[fogCount + 1][2];
        wan = new Server[2];
        for (int f = 1; f <= fogCount; f++) {
            access[f] = add(new Server("access-F" + f, "access", Json.number(a, "bandwidth_bit_per_s"), Json.number(a, "propagation_s"), Json.integer(a, "queue_waiting")));
            lan[f][UP] = add(new Server("lan-F" + f + "-up", "lan", Json.number(l, "bandwidth_bit_per_s"), Json.number(l, "propagation_s"), Json.integer(l, "queue_waiting")));
            lan[f][DOWN] = add(new Server("lan-F" + f + "-down", "lan", Json.number(l, "bandwidth_bit_per_s"), Json.number(l, "propagation_s"), Json.integer(l, "queue_waiting")));
        }
        wan[UP] = add(new Server("wan-up", "wan", Json.number(w, "bandwidth_bit_per_s"), Json.number(w, "propagation_s"), Json.integer(w, "queue_waiting")));
        wan[DOWN] = add(new Server("wan-down", "wan", Json.number(w, "bandwidth_bit_per_s"), Json.number(w, "propagation_s"), Json.integer(w, "queue_waiting")));
    }

    private static void requireDuplex(Map<?, ?> link, String expected, String name) {
        if (!expected.equals(link.get("duplex"))) throw new IllegalArgumentException("Link '" + name + "' must be " + expected + " duplex in the v2 model");
    }

    private Server add(Server s) {
        all.add(s);
        return s;
    }

    // ---- routes ------------------------------------------------------------------------------------------

    /** Fog index 1..n for "F<k>", 0 for the cloud; anything else is not routable. */
    private int fogIndex(String nodeId) {
        if ("cloud".equals(nodeId)) return 0;
        if (nodeId.length() >= 2 && nodeId.charAt(0) == 'F') {
            try {
                int k = Integer.parseInt(nodeId.substring(1));
                if (k >= 1 && k <= fogCount) return k;
            } catch (NumberFormatException ignored) { }
        }
        throw new IllegalArgumentException("Node '" + nodeId + "' is not routable in network mode (expected F1.." + "F" + fogCount + " or cloud)");
    }

    /** Local: no hops. Fog access: wireless only. Other fog and cloud as in section 15.1; results use the reverse path. */
    List<Hop> route(Phase phase, int accessFog, String targetNodeId) {
        if (accessFog < 1 || accessFog > fogCount) throw new IllegalArgumentException("Invalid access fog " + accessFog);
        int target = fogIndex(targetNodeId);
        List<Hop> hops = new ArrayList<>();
        boolean input = phase == Phase.INPUT;
        if (target == accessFog) {
            hops.add(new Hop(access[accessFog], input ? UP : DOWN));
        } else if (target > 0) {
            if (input) {
                hops.add(new Hop(access[accessFog], UP));
                hops.add(new Hop(lan[accessFog][UP], UP));
                hops.add(new Hop(lan[target][DOWN], DOWN));
            } else {
                hops.add(new Hop(lan[target][UP], UP));
                hops.add(new Hop(lan[accessFog][DOWN], DOWN));
                hops.add(new Hop(access[accessFog], DOWN));
            }
        } else {
            if (input) {
                hops.add(new Hop(access[accessFog], UP));
                hops.add(new Hop(lan[accessFog][UP], UP));
                hops.add(new Hop(wan[UP], UP));
            } else {
                hops.add(new Hop(wan[DOWN], DOWN));
                hops.add(new Hop(lan[accessFog][DOWN], DOWN));
                hops.add(new Hop(access[accessFog], DOWN));
            }
        }
        return hops;
    }

    // ---- transfer lifecycle ------------------------------------------------------------------------------

    /** Starts a message on its first hop. Returns the transfer, or null if the first queue is full. */
    Transfer start(double now, int taskId, int generation, Phase phase, long bytes, List<Hop> route) {
        if (bytes < 1 || route.isEmpty()) throw new IllegalArgumentException("Nothing to transfer for task " + taskId);
        Transfer t = new Transfer(taskId, generation, phase, bytes, route);
        return offer(now, t) == Status.REJECTED ? null : t;
    }

    private Status offer(double now, Transfer t) {
        Hop h = t.current();
        Server s = h.server;
        t.enteredS = now;
        if (s.active == null) {
            serve(now, t, s, h.direction);
            return Status.ACCEPTED;
        }
        if (s.waiting.size() < s.queueWaiting) {
            s.waiting.addLast(t);
            s.maxWaiting = Math.max(s.maxWaiting, s.waiting.size());
            return Status.ACCEPTED;
        }
        s.rejected[h.direction]++;
        t.done = true;
        record(t, h, "rejected_queue_full", 0.0, Double.NaN, Double.NaN, 0.0);
        return Status.REJECTED;
    }

    private void serve(double now, Transfer t, Server s, int direction) {
        s.active = t;
        t.inService = true;
        t.serializationStartS = now;
        s.started[direction]++;
        sink.schedule(now + serialization(t.bytes, s), EngineCoordinator.Kind.SERIALIZATION_DONE, t.taskId, t.generation, t);
    }

    static double serialization(long bytes, Server s) {
        return 8.0 * bytes / s.bitPerS;
    }

    /** Serialization finished: the server is free now, even though the message is still propagating. */
    void serializationDone(double now, Transfer t) {
        Hop h = t.current();
        Server s = h.server;
        if (s.active != t) throw new IllegalStateException("Serialization finished on a server not held by task " + t.taskId);
        double duration = serialization(t.bytes, s);
        s.active = null;
        t.inService = false;
        t.inPropagation = true;
        s.busyS[h.direction] += duration;
        s.bytesSent[h.direction] += t.bytes;
        s.completed[h.direction]++;
        record(t, h, "serialized", t.bytes, t.serializationStartS, t.serializationStartS + duration, hopJoules(s, h.direction, duration, t.bytes, t));
        sink.schedule(now + s.propagationS, EngineCoordinator.Kind.HOP_ARRIVED, t.taskId, t.generation, t);
        startNext(now, s);
    }

    private void startNext(double now, Server s) {
        if (s.active == null && !s.waiting.isEmpty()) {
            Transfer next = s.waiting.pollFirst();
            serve(now, next, s, next.current().direction);
        }
    }

    /** The message reached the far end of its current hop: forward it, or report that the whole route is complete. */
    Status hopArrived(double now, Transfer t) {
        t.inPropagation = false;
        t.hop++;
        if (t.hop == t.route.size()) {
            t.done = true;
            return Status.COMPLETE;
        }
        return offer(now, t);
    }

    /**
     * Timeout cancellation. A message being serialized has sent {@code elapsed * rate / 8} bytes; a waiting one has sent
     * nothing; one already propagating was fully serialized and was counted when serialization ended.
     */
    void cancel(double now, Transfer t) {
        if (t == null || t.done) return;
        Hop h = t.current();
        Server s = h.server;
        if (t.inService) {
            double elapsed = Math.max(0.0, now - t.serializationStartS);
            double sent = Math.min((double) t.bytes, elapsed * s.bitPerS / 8.0);
            s.busyS[h.direction] += elapsed;
            s.bytesSent[h.direction] += sent;
            s.cancelled[h.direction]++;
            s.active = null;
            t.inService = false;
            record(t, h, "cancelled_in_service", sent, t.serializationStartS, now, hopJoules(s, h.direction, elapsed, sent, t));
            startNext(now, s);
        } else if (s.waiting.remove(t)) {
            s.cancelled[h.direction]++;
            record(t, h, "cancelled_waiting", 0.0, Double.NaN, Double.NaN, 0.0);
        } else if (!t.inPropagation) {
            throw new IllegalStateException("Transfer of task " + t.taskId + " is in no server state");
        }
        t.done = true;
    }

    boolean idle() {
        for (Server s : all) if (s.active != null || !s.waiting.isEmpty()) return false;
        return true;
    }

    /**
     * Dynamic energy of one hop and attribution to its task. Wireless: TX of the sender plus RX of the receiver during
     * serialization (upload: IoT TX + AP RX; download: AP TX + IoT RX). Wired: joules per bit-hop on bits actually sent.
     * No dynamic power during propagation.
     */
    private double hopJoules(Server s, int direction, double serializationSeconds, double bytesSent, Transfer t) {
        double joules = hopEnergy(s, direction, serializationSeconds, bytesSent);
        taskDynamicJ.merge(t.taskId, joules, Double::sum);
        settledJ += joules;
        return joules;
    }

    /** Pure energy of sending {@code bytesSent} bytes over {@code serializationSeconds} on a server in one direction. */
    private double hopEnergy(Server s, int direction, double serializationSeconds, double bytesSent) {
        if ("access".equals(s.linkType)) {
            return serializationSeconds * (direction == UP ? radioTxW + apRxW : apTxW + radioRxW);
        }
        return bytesSent * 8.0 * ("lan".equals(s.linkType) ? lanJPerBitHop : wanJPerBitHop);
    }

    /**
     * Dynamic communication energy accrued up to {@code now}: hops already settled plus the part of every message
     * currently being serialized. Stateless, so reward intervals can be cut at any decision time exactly.
     */
    double dynamicJoulesAt(double now) {
        double joules = settledJ;
        for (Server s : all) {
            Transfer t = s.active;
            if (t == null) continue;
            int direction = t.current().direction;
            double elapsed = Math.min(Math.max(0.0, now - t.serializationStartS), serialization(t.bytes, s));
            joules += hopEnergy(s, direction, elapsed, Math.min((double) t.bytes, elapsed * s.bitPerS / 8.0));
        }
        return joules;
    }

    /** Bytes still to be serialized ahead of a new message: residual of the active one plus everything waiting. */
    private double backlogBytes(Server s, double now) {
        double bytes = 0.0;
        if (s.active != null) {
            double sent = Math.min((double) s.active.bytes, Math.max(0.0, now - s.active.serializationStartS) * s.bitPerS / 8.0);
            bytes += s.active.bytes - sent;
        }
        for (Transfer t : s.waiting) bytes += t.bytes;
        return bytes;
    }

    /**
     * Estimate for a new message of {@code bytes} on the route to {@code target}, using only the queues that exist now:
     * per hop (backlog + message) serialization plus propagation. Returns {delay_s, bottleneck_bit_per_s, dynamic_energy_j}.
     * An estimate, never an outcome.
     */
    double[] estimate(Phase phase, int accessFog, String target, long bytes, double now) {
        double delay = 0.0, bottleneck = Double.POSITIVE_INFINITY, energy = 0.0;
        for (Hop h : route(phase, accessFog, target)) {
            Server s = h.server;
            delay += (backlogBytes(s, now) + bytes) * 8.0 / s.bitPerS + s.propagationS;
            bottleneck = Math.min(bottleneck, s.bitPerS);
            energy += hopEnergy(s, h.direction, serialization(bytes, s), bytes);
        }
        return new double[] {delay, bottleneck, energy};
    }

    double taskDynamicJoules(int taskId) {
        return taskDynamicJ.getOrDefault(taskId, 0.0);
    }

    /**
     * Communication energy components over [0, H]: radio and AP (idle for every IoT device and AP, dynamic from access
     * serialization seconds), switch (LAN) and WAN gateway idle plus bit-hop dynamic energy. Idle is counted once here.
     */
    List<Map<String, Object>> energyComponents(double horizonS, int iotDevices) {
        double radioDyn = 0, apDyn = 0, lanDyn = 0, wanDyn = 0;
        for (Server s : all) {
            if ("access".equals(s.linkType)) {
                radioDyn += radioTxW * s.busyS[UP] + radioRxW * s.busyS[DOWN];
                apDyn += apRxW * s.busyS[UP] + apTxW * s.busyS[DOWN];
            } else {
                double bits = 8.0 * (s.bytesSent[UP] + s.bytesSent[DOWN]);
                if ("lan".equals(s.linkType)) lanDyn += bits * lanJPerBitHop; else wanDyn += bits * wanJPerBitHop;
            }
        }
        List<Map<String, Object>> out = new ArrayList<>();
        out.add(component("radio", radioIdleW * iotDevices * horizonS, radioDyn));
        out.add(component("ap", apIdleW * fogCount * horizonS, apDyn));
        out.add(component("lan", lanIdleW * horizonS, lanDyn));
        out.add(component("wan", wanIdleW * horizonS, wanDyn));
        return out;
    }

    private static Map<String, Object> component(String group, double idleJ, double dynamicJ) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("id", "net:" + group);
        m.put("group", group);
        m.put("idle_j", idleJ);
        m.put("dynamic_j", dynamicJ);
        return m;
    }

    private void record(Transfer t, Hop h, String status, double bytesSent, double serStart, double serEnd, double dynamicJ) {
        if (log == null) return;
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("task_id", t.taskId);
        m.put("phase", t.phase.name());
        m.put("hop", t.hop);
        m.put("server", h.server.id);
        m.put("direction", h.direction == UP ? "up" : "down");
        m.put("status", status);
        m.put("bytes_total", t.bytes);
        m.put("bytes_sent", bytesSent);
        m.put("dynamic_j", dynamicJ);
        m.put("queue_enter_s", t.enteredS);
        m.put("serialization_start_s", Double.isNaN(serStart) ? null : serStart);
        m.put("serialization_end_s", Double.isNaN(serEnd) ? null : serEnd);
        m.put("arrival_s", "serialized".equals(status) ? serEnd + h.server.propagationS : null);
        log.add(m);
    }

    List<Map<String, Object>> transferLog() { return log; }

    List<Map<String, Object>> report(double horizonS) {
        List<Map<String, Object>> out = new ArrayList<>();
        for (Server s : all) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", s.id);
            m.put("link_type", s.linkType);
            m.put("bit_per_s", s.bitPerS);
            m.put("propagation_s", s.propagationS);
            m.put("queue_waiting_limit", s.queueWaiting);
            m.put("max_waiting", s.maxWaiting);
            for (int d = 0; d < 2; d++) {
                String p = d == UP ? "up_" : "down_";
                m.put(p + "bytes_sent", s.bytesSent[d]);
                m.put(p + "busy_s", s.busyS[d]);
                m.put(p + "started", s.started[d]);
                m.put(p + "completed", s.completed[d]);
                m.put(p + "cancelled", s.cancelled[d]);
                m.put(p + "rejected_queue_full", s.rejected[d]);
            }
            m.put("busy_s_total", s.busyS[UP] + s.busyS[DOWN]);
            m.put("utilization", (s.busyS[UP] + s.busyS[DOWN]) / horizonS);
            m.put("active_end", s.active != null);
            m.put("waiting_end", s.waiting.size());
            out.add(m);
        }
        return out;
    }
}
