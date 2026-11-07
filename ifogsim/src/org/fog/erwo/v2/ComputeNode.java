package org.fog.erwo.v2;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.cloudbus.cloudsim.Cloudlet;
import org.cloudbus.cloudsim.Host;
import org.cloudbus.cloudsim.Pe;
import org.cloudbus.cloudsim.Vm;
import org.cloudbus.cloudsim.VmSchedulerSpaceShared;
import org.cloudbus.cloudsim.provisioners.BwProvisionerSimple;
import org.cloudbus.cloudsim.provisioners.PeProvisionerSimple;
import org.cloudbus.cloudsim.provisioners.RamProvisionerSimple;

/**
 * One compute node: a real CloudSim {@link Host} (pinned space-shared PEs, no overbooking) running one
 * {@link Vm} whose cloudlet scheduler is the {@link BoundedFcfsScheduler}. Task-level RAM admission is
 * kept in bytes here; the Host's int-MiB RAM provisioner only sizes the VM and is not the admission authority.
 */
final class ComputeNode {
    enum Verdict { RUN, WAIT, CPU_QUEUE_FULL, RAM_EXHAUSTED }

    final NodeSpec spec;
    final Host host;
    final Vm vm;
    final BoundedFcfsScheduler scheduler;

    private final Map<Integer, Long> ramHeld = new HashMap<>();
    private long ramUsed;
    private long ramPeak;
    private double busyPeSeconds;
    private double lastAccountedS;
    private int admitted;
    private int rejectedCpu;
    private int rejectedRam;
    private int completed;
    private int cancelledRunning;
    private int cancelledWaiting;
    private double cancelledExecutedMi;

    ComputeNode(NodeSpec spec, int nodeIndex, int ownerId) {
        this.spec = spec;
        List<Pe> pes = new ArrayList<>();
        for (int i = 0; i < spec.pes; i++) pes.add(new Pe(i, new PeProvisionerSimple(spec.mipsPerPe)));
        int ramMiB = (int) Math.min(Integer.MAX_VALUE, (spec.ramBytes + (1L << 20) - 1) >> 20);
        this.host = new Host(nodeIndex, new RamProvisionerSimple(ramMiB), new BwProvisionerSimple(10_000_000L),
                1_048_576L, pes, new VmSchedulerSpaceShared(pes));
        this.scheduler = new BoundedFcfsScheduler(spec.pes, spec.queueWaiting);
        this.vm = new Vm(nodeIndex, ownerId, spec.mipsPerPe, spec.pes, ramMiB, 10_000_000L, 1000L, "erwo-v2", scheduler);
        if (!host.vmCreate(vm)) throw new IllegalStateException("Host rejected VM for node " + spec.id);
        List<Double> share = new ArrayList<>(host.getVmScheduler().getAllocatedMipsForVm(vm));
        if (share.size() != spec.pes) throw new IllegalStateException("PE allocation differs from spec for " + spec.id);
        // Safe with empty lists: only installs the MIPS share (native update returns before touching tasks).
        scheduler.updateCloudletsProcessing(0.0, share);
        if (scheduler.getCurrentPEs() != spec.pes || scheduler.getCurrentCapacity() != spec.mipsPerPe) {
            throw new IllegalStateException("Scheduler capacity differs from spec for " + spec.id);
        }
    }

    private void account(double now) {
        if (now > lastAccountedS) {
            busyPeSeconds += scheduler.busyPes() * (now - lastAccountedS);
            lastAccountedS = now;
        }
    }

    /** CPU queue/PE check first, then RAM. A rejected task holds nothing and is never rerouted. */
    Verdict admit(double now, TaskSpec task, Cloudlet cloudlet) {
        if (!scheduler.wouldAccept()) {
            rejectedCpu++;
            return Verdict.CPU_QUEUE_FULL;
        }
        long need = task.ramRequiredBytes();
        if (ramUsed + need > spec.ramBytes) {
            rejectedRam++;
            return Verdict.RAM_EXHAUSTED;
        }
        account(now);
        ramUsed += need;
        ramPeak = Math.max(ramPeak, ramUsed);
        ramHeld.put(task.taskId, need);
        admitted++;
        return scheduler.admit(cloudlet) == BoundedFcfsScheduler.Admission.STARTED ? Verdict.RUN : Verdict.WAIT;
    }

    private void releaseRam(int taskId) {
        Long held = ramHeld.remove(taskId);
        if (held == null) throw new IllegalStateException("RAM release for a task that holds none: " + taskId);
        ramUsed -= held;
        if (ramUsed < 0) throw new IllegalStateException("RAM accounting negative on " + spec.id);
    }

    /** CPU completed: frees the PE and RAM, then promotes waiting tasks onto every free PE. */
    List<BoundedFcfsScheduler.Started> finish(double now, int taskId) {
        account(now);
        List<BoundedFcfsScheduler.Started> promoted = scheduler.finish(taskId);
        releaseRam(taskId);
        completed++;
        return promoted;
    }

    /** Timeout: releases whatever the task holds on this node. */
    BoundedFcfsScheduler.Cancelled cancel(double now, int taskId, double executedMi) {
        account(now);
        BoundedFcfsScheduler.Cancelled result = scheduler.cancel(taskId);
        if (!result.wasRunning && !result.wasWaiting) throw new IllegalStateException("Cancel for a task not on node " + spec.id);
        releaseRam(taskId);
        if (result.wasRunning) {
            cancelledRunning++;
            cancelledExecutedMi += executedMi;
        } else {
            cancelledWaiting++;
        }
        return result;
    }

    /** Closes the busy-PE integral exactly at the observation horizon. */
    void close(double horizonS) {
        account(horizonS);
    }

    boolean idle() {
        return scheduler.busyPes() == 0 && scheduler.waiting() == 0 && ramUsed == 0 && ramHeld.isEmpty();
    }

    /** Ledger group of this node: cpu_iot, cpu_fog, cpu_cloud, or cpu_other for fixture names. */
    String energyGroup() {
        if (spec.id.startsWith("IoT-")) return "cpu_iot";
        if (isFog()) return "cpu_fog";
        if ("cloud".equals(spec.id)) return "cpu_cloud";
        return "cpu_other";
    }

    boolean isFog() {
        return spec.id.length() >= 2 && spec.id.charAt(0) == 'F' && spec.id.substring(1).chars().allMatch(Character::isDigit);
    }

    double utilization() {
        return (double) scheduler.busyPes() / spec.pes;
    }

    /**
     * CPU-IT energy over [0, H]: P(u) = Pidle + (Pbusy - Pidle) u with u = busy PE / PE, integrated exactly because the
     * busy-PE count is piecewise constant. Call after {@link #close(double)} so the integral ends at H.
     */
    Map<String, Object> energyComponent(double horizonS) {
        Map<String, Object> m = new java.util.LinkedHashMap<>();
        m.put("id", "cpu:" + spec.id);
        m.put("group", energyGroup());
        m.put("idle_j", spec.idleW * horizonS);
        m.put("dynamic_j", (spec.busyW - spec.idleW) / spec.pes * busyPeSeconds);
        return m;
    }

    /** Dynamic CPU energy of a busy interval on one PE of this node (used for per-task attribution). */
    double dynamicJoules(double busySeconds) {
        return (spec.busyW - spec.idleW) / spec.pes * busySeconds;
    }

    Map<String, Object> report(double horizonS) {
        Map<String, Object> m = new java.util.LinkedHashMap<>();
        m.put("id", spec.id);
        m.put("pes", spec.pes);
        m.put("mips_per_pe", spec.mipsPerPe);
        m.put("idle_w", spec.idleW);
        m.put("busy_w", spec.busyW);
        m.put("queue_waiting_limit", spec.queueWaiting);
        m.put("ram_bytes", spec.ramBytes);
        m.put("admitted", admitted);
        m.put("rejected_cpu_queue_full", rejectedCpu);
        m.put("rejected_ram_exhausted", rejectedRam);
        m.put("cpu_completed", completed);
        m.put("cancelled_running", cancelledRunning);
        m.put("cancelled_waiting", cancelledWaiting);
        m.put("cancelled_executed_mi", cancelledExecutedMi);
        m.put("max_busy_pes", scheduler.maxBusyPes());
        m.put("max_waiting", scheduler.maxWaitingObserved());
        m.put("ram_peak_bytes", ramPeak);
        m.put("busy_pe_seconds", busyPeSeconds);
        m.put("cpu_utilization", busyPeSeconds / (spec.pes * horizonS));
        m.put("native_finished_cloudlets", scheduler.finishedCloudlets());
        m.put("native_used_pes_end", scheduler.busyPes());
        m.put("native_waiting_end", scheduler.waiting());
        m.put("ram_used_end_bytes", ramUsed);
        return m;
    }
}
