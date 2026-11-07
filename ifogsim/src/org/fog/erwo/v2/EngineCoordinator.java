package org.fog.erwo.v2;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.TreeSet;
import org.cloudbus.cloudsim.Cloudlet;
import org.cloudbus.cloudsim.UtilizationModelFull;
import org.cloudbus.cloudsim.core.CloudSim;
import org.cloudbus.cloudsim.core.CloudSimTags;
import org.cloudbus.cloudsim.core.SimEntity;
import org.cloudbus.cloudsim.core.SimEvent;
import org.json.simple.JSONObject;

/**
 * One episode of the task lifecycle driven by the native CloudSim future-event queue.
 *
 * <p>CloudSim only supplies the clock and the wake-up event (its queue orders equal times by insertion
 * serial, and {@code clock + delay} can move an absolute time by one ulp). The coordinator therefore keeps
 * its own exact-timestamp queue ordered by {@code (at_s, domain priority, task_id, sequence)} from the wire
 * contract and processes a whole timestamp class, including zero-delay chains, before sleeping again.
 * Times in logs and outcomes are the exact stored values, never {@code CloudSim.clock()}.
 *
 * <p>Network is out of scope here (P03). Offloaded tasks cross a labeled fixture transport with constant
 * input/result delays (default zero); a task whose target is its own IoT node crosses nothing.
 */
final class EngineCoordinator extends SimEntity {
    private enum Tag implements CloudSimTags { WAKE }

    /**
     * Event kinds. The two network kinds are engine-internal refinements of the contract's TRANSFER_COMPLETE and
     * share its priority; every kind's priority is looked up from the wire contract by {@link #wire}.
     */
    enum Kind {
        CPU_COMPLETE("CPU_COMPLETE"), TRANSFER_COMPLETE("TRANSFER_COMPLETE"), RESULT_DELIVERED("RESULT_DELIVERED"),
        DEADLINE("DEADLINE"), TIMEOUT("TIMEOUT"), ARRIVAL("ARRIVAL"), HORIZON("HORIZON"),
        SERIALIZATION_DONE("TRANSFER_COMPLETE"), HOP_ARRIVED("TRANSFER_COMPLETE");

        final String wire;
        Kind(String wire) { this.wire = wire; }
    }
    enum State { PENDING, TRANSFER_IN, CPU_WAIT, CPU_RUN, TRANSFER_OUT, DONE }
    enum Terminal { ON_TIME, LATE_SUCCESS, FAILED }

    /** Maps a task to its target node id. */
    interface Actions {
        String targetFor(TaskSpec task);
    }

    private static final class Ev implements Comparable<Ev> {
        final double at;
        final int priority;
        final int taskId;
        final long sequence;
        final Kind kind;
        final int generation;
        final Object payload;

        Ev(double at, int priority, int taskId, long sequence, Kind kind, int generation, Object payload) {
            this.at = at;
            this.priority = priority;
            this.taskId = taskId;
            this.sequence = sequence;
            this.kind = kind;
            this.generation = generation;
            this.payload = payload;
        }

        @Override public int compareTo(Ev o) {
            int c = Double.compare(at, o.at);
            if (c != 0) return c;
            c = Integer.compare(priority, o.priority);
            if (c != 0) return c;
            c = Integer.compare(taskId, o.taskId);
            if (c != 0) return c;
            return Long.compare(sequence, o.sequence);
        }
    }

    private static final class Runtime {
        final TaskSpec spec;
        final Cloudlet cloudlet;
        State state = State.PENDING;
        int generation;
        ComputeNode node;
        boolean local;
        int pe = -1;
        NetworkModel.Transfer transfer;
        boolean deadlineFlag;
        Double arrivedAt;
        Double inputAt;
        Double admittedAt;
        Double cpuStart;
        Double cpuFinish;
        Double deliveredAt;
        Double terminalAt;
        double executedMi;
        Terminal terminal;
        String reason;

        Runtime(TaskSpec spec) {
            this.spec = spec;
            this.cloudlet = new Cloudlet(spec.taskId, spec.cpuMi, 1, spec.inputBytes, spec.outputBytes,
                    new UtilizationModelFull(), new UtilizationModelFull(), new UtilizationModelFull());
        }
    }

    private final String episodeId;
    private final double arrivalWindowS;
    private final double horizonS;
    private final double epsilonS;
    private final double inputDelayS;
    private final double resultDelayS;
    private final Actions actions;
    private final JSONObject wire;
    private final NetworkModel network;
    private final int iotPerAccessFog;
    private final Map<String, ComputeNode> nodes = new LinkedHashMap<>();
    private final TreeMap<Integer, Runtime> tasks = new TreeMap<>();
    private final TreeSet<Ev> pending = new TreeSet<>();
    private final List<Map<String, Object>> eventLog = new ArrayList<>();
    private long sequence;
    private double now;
    private int staleIgnored;
    private final Map<String, Integer> staleByKind = new TreeMap<>();
    private int boundaryDrains;
    private boolean finished;
    private double finishedAt = Double.NaN;
    private double nativeClockAtHorizon = Double.NaN;

    /**
     * @param networkConfig null selects the labeled fixture transport (constant delays); otherwise the P03 network
     *        model built from this {@code network} config section
     */
    EngineCoordinator(String episodeId, List<NodeSpec> nodeSpecs, List<TaskSpec> taskSpecs, Actions actions,
                      double arrivalWindowS, double horizonS, double epsilonS, double inputDelayS, double resultDelayS,
                      JSONObject wire, Map<?, ?> networkConfig, int fogCount, int iotPerAccessFog, boolean logTransfers) {
        super("ErwoV2Engine");
        this.episodeId = episodeId;
        this.arrivalWindowS = arrivalWindowS;
        this.horizonS = horizonS;
        this.epsilonS = epsilonS;
        this.inputDelayS = inputDelayS;
        this.resultDelayS = resultDelayS;
        this.actions = actions;
        this.wire = wire;
        this.iotPerAccessFog = iotPerAccessFog;
        this.network = networkConfig == null ? null : new NetworkModel(networkConfig, fogCount, this::scheduleNetwork, logTransfers);
        if (!(arrivalWindowS > 0) || !(horizonS >= arrivalWindowS) || !(epsilonS > 0) || inputDelayS < 0 || resultDelayS < 0) {
            throw new IllegalArgumentException("Invalid timing parameters");
        }
        int index = 0;
        for (NodeSpec spec : nodeSpecs) {
            if (nodes.put(spec.id, new ComputeNode(spec, index++, getId())) != null) {
                throw new IllegalArgumentException("Duplicate node id " + spec.id);
            }
        }
        if (taskSpecs.isEmpty()) throw new IllegalArgumentException("N=0 trace rejected; no resampling or forced task");
        for (TaskSpec spec : taskSpecs) {
            if (spec.arrivalS >= arrivalWindowS) throw new IllegalArgumentException("Arrival at or after T: task " + spec.taskId);
            if (network != null && spec.accessFog != spec.sourceIot / iotPerAccessFog + 1) {
                throw new IllegalArgumentException("Task " + spec.taskId + " access_fog " + spec.accessFog + " contradicts source_iot " + spec.sourceIot);
            }
            if (spec.timeoutAbsoluteS > horizonS + epsilonS) {
                throw new IllegalArgumentException("Timeout after horizon would leave the task unresolved: task " + spec.taskId);
            }
            Runtime rt = new Runtime(spec);
            rt.cloudlet.setResourceParameter(getId(), 0.0);
            if (tasks.put(spec.taskId, rt) != null) throw new IllegalArgumentException("Duplicate task id " + spec.taskId);
        }
    }

    // ---- CloudSim entity hooks -------------------------------------------------------------------------

    @Override public void startEntity() {
        for (Runtime rt : tasks.values()) enqueue(rt.spec.arrivalS, Kind.ARRIVAL, rt.spec.taskId, 0);
        enqueue(horizonS, Kind.HORIZON, -1, 0);
        scheduleWake();
    }

    @Override public void processEvent(SimEvent event) {
        if (event.getTag() != Tag.WAKE) throw new IllegalStateException("Unexpected CloudSim event " + event.getTag());
        double limit = CloudSim.clock() + epsilonS;
        while (!pending.isEmpty() && pending.first().at <= limit) {
            dispatch(pending.pollFirst());
        }
        scheduleWake();
    }

    @Override public void shutdownEntity() { }

    private void scheduleWake() {
        if (pending.isEmpty()) return;
        schedule(getId(), Math.max(0.0, pending.first().at - CloudSim.clock()), Tag.WAKE);
    }

    // ---- ordered event queue ---------------------------------------------------------------------------

    private void enqueue(double at, Kind kind, int taskId, int generation) {
        enqueue(at, kind, taskId, generation, null);
    }

    private void enqueue(double at, Kind kind, int taskId, int generation, Object payload) {
        if (!(at >= now - epsilonS)) throw new IllegalStateException("Event scheduled in the past: " + kind + " at " + at + " < " + now);
        pending.add(new Ev(at, Contracts.priority(wire, kind.wire), taskId < 0 ? Integer.MAX_VALUE : taskId, sequence++, kind, generation, payload));
    }

    private void scheduleNetwork(double at, Kind kind, int taskId, int generation, Object payload) {
        enqueue(at, kind, taskId, generation, payload);
    }

    private void log(Ev e, boolean stale, String note) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("sequence", e.sequence);
        m.put("at_s", e.at);
        m.put("kind", e.kind.name());
        m.put("task_id", e.taskId == Integer.MAX_VALUE ? null : e.taskId);
        m.put("generation", e.generation);
        if (stale) m.put("stale", true);
        if (note != null) m.put("note", note);
        eventLog.add(m);
    }

    private void dispatch(Ev e) {
        now = Math.max(now, e.at);
        Runtime rt = e.taskId == Integer.MAX_VALUE ? null : tasks.get(e.taskId);
        if (rt != null && e.generation != rt.generation) {
            staleIgnored++;
            staleByKind.merge(e.kind.name(), 1, Integer::sum);
            log(e, true, null);
            return;
        }
        log(e, false, null);
        switch (e.kind) {
            case ARRIVAL: onArrival(rt, e); break;
            case TRANSFER_COMPLETE: onInputArrived(rt, e); break;
            case CPU_COMPLETE: onCpuComplete(rt, e); break;
            case RESULT_DELIVERED: onDelivered(rt, e); break;
            case DEADLINE: onDeadline(rt, e); break;
            case TIMEOUT: onTimeout(rt, e); break;
            case HORIZON: onHorizon(e); break;
            case SERIALIZATION_DONE: network.serializationDone(e.at, (NetworkModel.Transfer) e.payload); break;
            case HOP_ARRIVED: onHopArrived(rt, e); break;
            default: throw new IllegalStateException("Unhandled kind " + e.kind);
        }
    }

    /**
     * A completion or delivery for the same task within the comparison tolerance after a deadline/timeout
     * instant still counts as on the boundary, so it is processed first (spec: boundary within 1e-9 s).
     */
    private void drainBoundary(Runtime rt, double boundary) {
        double upTo = boundary + epsilonS;
        boolean again = true;
        while (again) {
            again = false;
            Ev probe = new Ev(upTo, Integer.MAX_VALUE, Integer.MAX_VALUE, Long.MAX_VALUE, Kind.HORIZON, 0, null);
            for (Ev x : new ArrayList<>(pending.headSet(probe, true))) {
                if (x.taskId == rt.spec.taskId && x.priority == 0 && x.generation == rt.generation) {
                    pending.remove(x);
                    boundaryDrains++;
                    dispatch(x);
                    again = true;
                    break;
                }
            }
        }
    }

    // ---- lifecycle handlers ----------------------------------------------------------------------------

    private void onArrival(Runtime rt, Ev e) {
        TaskSpec t = rt.spec;
        rt.arrivedAt = e.at;
        enqueue(t.deadlineAbsoluteS, Kind.DEADLINE, t.taskId, rt.generation);
        enqueue(t.timeoutAbsoluteS, Kind.TIMEOUT, t.taskId, rt.generation);
        String own = "IoT-" + t.sourceIot;
        String target = actions.targetFor(t);
        ComputeNode node = nodes.get(target);
        if (node == null) throw new IllegalArgumentException("Action targets unknown node '" + target + "' for task " + t.taskId);
        if (target.startsWith("IoT-") && !target.equals(own)) {
            throw new IllegalArgumentException("IoT node " + target + " cannot receive offloaded task " + t.taskId + " from " + own);
        }
        rt.node = node;
        rt.local = target.equals(own);
        if (rt.local) {
            admit(rt, e.at);
        } else if (network == null) {
            rt.state = State.TRANSFER_IN;
            enqueue(e.at + inputDelayS, Kind.TRANSFER_COMPLETE, t.taskId, rt.generation);
        } else {
            rt.state = State.TRANSFER_IN;
            rt.transfer = network.start(e.at, t.taskId, rt.generation, NetworkModel.Phase.INPUT, t.inputBytes,
                    network.route(NetworkModel.Phase.INPUT, t.accessFog, target));
            if (rt.transfer == null) fail(rt, "NETWORK_QUEUE_FULL", e.at);
        }
    }

    /** A message reached the far end of a hop: forward it, fail it on a full queue, or finish the whole route. */
    private void onHopArrived(Runtime rt, Ev e) {
        NetworkModel.Transfer transfer = (NetworkModel.Transfer) e.payload;
        switch (network.hopArrived(e.at, transfer)) {
            case ACCEPTED: break;
            case REJECTED: fail(rt, "NETWORK_QUEUE_FULL", e.at); break;
            case COMPLETE:
                if (transfer.phase == NetworkModel.Phase.INPUT) enqueue(e.at, Kind.TRANSFER_COMPLETE, rt.spec.taskId, rt.generation);
                else enqueue(e.at, Kind.RESULT_DELIVERED, rt.spec.taskId, rt.generation);
                break;
            default: throw new IllegalStateException("Unhandled network status");
        }
    }

    private void onInputArrived(Runtime rt, Ev e) {
        requireState(rt, State.TRANSFER_IN, e);
        rt.inputAt = e.at;
        admit(rt, e.at);
    }

    private void admit(Runtime rt, double at) {
        rt.admittedAt = at;
        ComputeNode.Verdict verdict = rt.node.admit(at, rt.spec, rt.cloudlet);
        switch (verdict) {
            case CPU_QUEUE_FULL: fail(rt, "CPU_QUEUE_FULL", at); break;
            case RAM_EXHAUSTED: fail(rt, "RAM_EXHAUSTED", at); break;
            case RUN: startRunning(rt, at, rt.node.scheduler.peOf(rt.spec.taskId)); break;
            case WAIT: rt.state = State.CPU_WAIT; break;
            default: throw new IllegalStateException("Unhandled verdict " + verdict);
        }
    }

    private void startRunning(Runtime rt, double at, int pe) {
        rt.state = State.CPU_RUN;
        rt.cpuStart = at;
        rt.pe = pe;
        enqueue(at + rt.spec.cpuMi / rt.node.spec.mipsPerPe, Kind.CPU_COMPLETE, rt.spec.taskId, rt.generation);
    }

    private void startPromoted(List<BoundedFcfsScheduler.Started> promoted, double at) {
        for (BoundedFcfsScheduler.Started s : promoted) {
            Runtime next = tasks.get(s.cloudlet.getCloudletId());
            requireState(next, State.CPU_WAIT, null);
            startRunning(next, at, s.peId);
        }
    }

    private void onCpuComplete(Runtime rt, Ev e) {
        requireState(rt, State.CPU_RUN, e);
        rt.cpuFinish = e.at;
        rt.executedMi = rt.spec.cpuMi;
        startPromoted(rt.node.finish(e.at, rt.spec.taskId), e.at);
        rt.state = State.TRANSFER_OUT;
        if (rt.local) {
            enqueue(e.at, Kind.RESULT_DELIVERED, rt.spec.taskId, rt.generation);
        } else if (network == null) {
            enqueue(e.at + resultDelayS, Kind.RESULT_DELIVERED, rt.spec.taskId, rt.generation);
        } else {
            rt.transfer = network.start(e.at, rt.spec.taskId, rt.generation, NetworkModel.Phase.RESULT, rt.spec.outputBytes,
                    network.route(NetworkModel.Phase.RESULT, rt.spec.accessFog, rt.node.spec.id));
            if (rt.transfer == null) fail(rt, "NETWORK_QUEUE_FULL", e.at);
        }
    }

    private void onDelivered(Runtime rt, Ev e) {
        requireState(rt, State.TRANSFER_OUT, e);
        rt.deliveredAt = e.at;
        if (e.at > rt.spec.timeoutAbsoluteS + epsilonS) {
            throw new IllegalStateException("Result delivered after timeout for task " + rt.spec.taskId);
        }
        commit(rt, e.at <= rt.spec.deadlineAbsoluteS + epsilonS ? Terminal.ON_TIME : Terminal.LATE_SUCCESS, null, e.at);
    }

    private void onDeadline(Runtime rt, Ev e) {
        drainBoundary(rt, e.at);
        if (rt.state != State.DONE) rt.deadlineFlag = true; // flag only: the task keeps running
    }

    private void onTimeout(Runtime rt, Ev e) {
        drainBoundary(rt, e.at);
        if (rt.state == State.DONE) return;
        if (rt.state == State.CPU_WAIT || rt.state == State.CPU_RUN) {
            double executed = rt.state == State.CPU_RUN
                    ? Math.min((double) rt.spec.cpuMi, (e.at - rt.cpuStart) * rt.node.spec.mipsPerPe) : 0.0;
            rt.executedMi = executed;
            BoundedFcfsScheduler.Cancelled cancelled = rt.node.cancel(e.at, rt.spec.taskId, executed);
            startPromoted(cancelled.promoted, e.at);
        }
        // Transfers hold link servers or queue slots, not node resources: release them and count partial bytes.
        // Fixture transport holds nothing; the generation bump below voids its pending event.
        if (network != null && rt.transfer != null) network.cancel(e.at, rt.transfer);
        fail(rt, "SERVICE_TIMEOUT", e.at);
    }

    private void onHorizon(Ev e) {
        List<Integer> unresolved = new ArrayList<>();
        for (Runtime rt : tasks.values()) if (rt.state != State.DONE) unresolved.add(rt.spec.taskId);
        if (!unresolved.isEmpty()) throw new IllegalStateException("Unresolved tasks at horizon: " + unresolved);
        for (ComputeNode node : nodes.values()) {
            node.close(horizonS);
            if (!node.idle()) throw new IllegalStateException("Node not idle at horizon: " + node.spec.id);
        }
        if (network != null && !network.idle()) throw new IllegalStateException("Network not idle at horizon");
        finished = true;
        finishedAt = e.at;
        // CloudSim resets its static clock when the run ends, so the native clock is sampled here.
        nativeClockAtHorizon = CloudSim.clock();
    }

    private void fail(Runtime rt, String reason, double at) {
        commit(rt, Terminal.FAILED, reason, at);
    }

    /** Exactly one terminal commit per task; later events for it are stale through the generation bump. */
    private void commit(Runtime rt, Terminal terminal, String reason, double at) {
        if (rt.terminal != null) throw new IllegalStateException("Second terminal commit for task " + rt.spec.taskId);
        rt.terminal = terminal;
        rt.reason = reason;
        rt.terminalAt = at;
        rt.state = State.DONE;
        rt.generation++;
    }

    private void requireState(Runtime rt, State expected, Ev e) {
        if (rt.state != expected) {
            throw new IllegalStateException("Task " + rt.spec.taskId + " in " + rt.state + ", expected " + expected
                    + (e == null ? "" : " for " + e.kind));
        }
    }

    // ---- reporting -------------------------------------------------------------------------------------

    boolean finished() { return finished; }

    Map<String, Object> result() {
        Map<String, Object> out = new LinkedHashMap<>();
        int onTime = 0, late = 0, failed = 0;
        Map<String, Integer> reasons = new TreeMap<>();
        List<Map<String, Object>> outcomes = new ArrayList<>();
        for (Runtime rt : tasks.values()) {
            if (rt.terminal == Terminal.ON_TIME) onTime++;
            else if (rt.terminal == Terminal.LATE_SUCCESS) late++;
            else { failed++; reasons.merge(rt.reason, 1, Integer::sum); }
            Map<String, Object> o = new LinkedHashMap<>();
            o.put("task_id", rt.spec.taskId);
            o.put("node", rt.node == null ? null : rt.node.spec.id);
            o.put("local", rt.local);
            o.put("terminal", rt.terminal.name());
            o.put("failure_reason", rt.reason);
            o.put("arrival_s", rt.arrivedAt);
            o.put("input_arrived_s", rt.inputAt);
            o.put("admitted_s", rt.admittedAt);
            o.put("cpu_start_s", rt.cpuStart);
            o.put("pe", rt.cpuStart == null ? null : rt.pe);
            o.put("cpu_finish_s", rt.cpuFinish);
            o.put("delivered_s", rt.deliveredAt);
            o.put("terminal_s", rt.terminalAt);
            o.put("deadline_abs_s", rt.spec.deadlineAbsoluteS);
            o.put("timeout_abs_s", rt.spec.timeoutAbsoluteS);
            o.put("deadline_flag", rt.deadlineFlag);
            o.put("cpu_executed_mi", rt.executedMi);
            o.put("native_cloudlet_status", rt.cloudlet.getStatus().name());
            outcomes.add(o);
        }
        out.put("episode_id", episodeId);
        if (network == null) {
            out.put("transport", "FIXTURE_ZERO_NETWORK: constant input/result delays; local tasks cross no link. Not a system benchmark.");
            out.put("input_delay_s", inputDelayS);
            out.put("result_delay_s", resultDelayS);
        } else {
            out.put("transport", "NETWORK_P03: store-and-forward links, FCFS bounded queues, serialization separate from propagation.");
        }
        out.put("arrival_window_s", arrivalWindowS);
        out.put("horizon_s", horizonS);
        out.put("finished", finished);
        out.put("finished_at_s", finishedAt);
        out.put("native_clock_at_horizon_s", nativeClockAtHorizon);
        out.put("task_count", tasks.size());
        out.put("on_time", onTime);
        out.put("late_success", late);
        out.put("failed", failed);
        out.put("failure_reasons", reasons);
        out.put("conservation_ok", onTime + late + failed == tasks.size());
        out.put("stale_events_ignored", staleIgnored);
        out.put("stale_by_kind", staleByKind);
        out.put("boundary_tolerance_drains", boundaryDrains);
        out.put("tasks", outcomes);
        List<Map<String, Object>> nodeReports = new ArrayList<>();
        for (ComputeNode node : nodes.values()) nodeReports.add(node.report());
        out.put("nodes", nodeReports);
        if (network != null) {
            out.put("links", network.report());
            if (network.transferLog() != null) out.put("transfers", network.transferLog());
        }
        out.put("events", eventLog);
        return out;
    }
}
