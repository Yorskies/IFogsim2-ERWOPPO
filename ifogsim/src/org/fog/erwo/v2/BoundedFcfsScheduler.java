package org.fog.erwo.v2;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.cloudbus.cloudsim.Cloudlet;
import org.cloudbus.cloudsim.CloudletSchedulerSpaceShared;

/**
 * Adapter over the native {@link CloudletSchedulerSpaceShared} implementing the v2 rules:
 * FCFS non-preemptive, one task per PE, PE pinned to the smallest free id, and a bounded waiting
 * queue. It repairs the hazards reproduced by the P00 audit instead of relying on the stock class:
 * <ul>
 * <li>stock waiting list is unbounded and has no admission result;</li>
 * <li>stock {@code updateWaitingCloudlets} wakes at most one waiting task per update;</li>
 * <li>stock {@code cloudletCancel} leaves {@code usedPes} unchanged for a running task.</li>
 * </ul>
 * Native submit/cancel/pause/resume are disabled so nothing can bypass the accounting here. Progress is
 * not tracked by the native floor-MI counters: the coordinator schedules exact completion events.
 * The native lists, status and {@code usedPes} stay authoritative for what runs and what waits.
 */
final class BoundedFcfsScheduler extends CloudletSchedulerSpaceShared {
    enum Admission { STARTED, QUEUED, REJECTED }

    /** A cloudlet that began executing, with the PE it is pinned to. */
    static final class Started {
        final Cloudlet cloudlet;
        final int peId;
        Started(Cloudlet cloudlet, int peId) {
            this.cloudlet = cloudlet;
            this.peId = peId;
        }
    }

    /** Outcome of a cancel: where the task was, and whom the freed PE promoted. */
    static final class Cancelled {
        final boolean wasRunning;
        final boolean wasWaiting;
        final int peId;
        final List<Started> promoted;
        Cancelled(boolean wasRunning, boolean wasWaiting, int peId, List<Started> promoted) {
            this.wasRunning = wasRunning;
            this.wasWaiting = wasWaiting;
            this.peId = peId;
            this.promoted = promoted;
        }
    }

    private final int peCount;
    private final int queueLimit;
    private final int[] peOwner;
    private final Map<Integer, Integer> peOfCloudlet = new HashMap<>();
    private int maxUsedPes;
    private int maxWaiting;
    private int finishedCount;

    BoundedFcfsScheduler(int peCount, int queueLimit) {
        super();
        if (peCount < 1 || queueLimit < 0) throw new IllegalArgumentException("Invalid scheduler bounds");
        this.peCount = peCount;
        this.queueLimit = queueLimit;
        this.peOwner = new int[peCount];
        Arrays.fill(peOwner, -1);
    }

    int busyPes() { return usedPes; }
    int waiting() { return getCloudletWaitingList().size(); }
    int maxBusyPes() { return maxUsedPes; }
    int maxWaitingObserved() { return maxWaiting; }
    int finishedCloudlets() { return finishedCount; }
    int peOf(int cloudletId) { return peOfCloudlet.getOrDefault(cloudletId, -1); }

    boolean wouldAccept() {
        return firstFreePe() >= 0 || waiting() < queueLimit;
    }

    private int firstFreePe() {
        for (int i = 0; i < peCount; i++) if (peOwner[i] < 0) return i;
        return -1;
    }

    private void start(Cloudlet cl, int pe) {
        cl.updateStatus(Cloudlet.CloudletStatus.INEXEC);
        List<Cloudlet> exec = getCloudletExecList();
        exec.add(cl);
        usedPes += 1;
        peOwner[pe] = cl.getCloudletId();
        peOfCloudlet.put(cl.getCloudletId(), pe);
        maxUsedPes = Math.max(maxUsedPes, usedPes);
    }

    /** Admission result for one single-PE cloudlet. A free PE implies an empty waiting list (FCFS invariant). */
    Admission admit(Cloudlet cl) {
        if (cl.getNumberOfPes() != 1) throw new IllegalArgumentException("v2 tasks use exactly one PE");
        int free = firstFreePe();
        if (free >= 0) {
            if (waiting() != 0) throw new IllegalStateException("FCFS invariant broken: free PE with waiting tasks");
            start(cl, free);
            return Admission.STARTED;
        }
        if (waiting() < queueLimit) {
            cl.updateStatus(Cloudlet.CloudletStatus.QUEUED);
            List<Cloudlet> queue = getCloudletWaitingList();
            queue.add(cl);
            maxWaiting = Math.max(maxWaiting, queue.size());
            return Admission.QUEUED;
        }
        return Admission.REJECTED;
    }

    /** Wakes waiting heads in FCFS order onto every free PE (smallest id first), unlike the stock one-per-update rule. */
    private List<Started> promote() {
        List<Started> started = new ArrayList<>();
        List<Cloudlet> queue = getCloudletWaitingList();
        while (!queue.isEmpty()) {
            int free = firstFreePe();
            if (free < 0) break;
            Cloudlet next = queue.remove(0);
            start(next, free);
            started.add(new Started(next, free));
        }
        return started;
    }

    /** CPU phase ended for a running cloudlet: record SUCCESS natively, free its PE, and promote waiting tasks. */
    List<Started> finish(int cloudletId) {
        Cloudlet cl = removeRunning(cloudletId);
        if (cl == null) throw new IllegalStateException("Finish requested for a cloudlet that is not running: " + cloudletId);
        cloudletFinish(cl);
        return promote();
    }

    /** Timeout cancellation of a running or waiting cloudlet. Returns null state if the cloudlet is in neither list. */
    Cancelled cancel(int cloudletId) {
        int pe = peOf(cloudletId);
        Cloudlet cl = removeRunning(cloudletId);
        if (cl != null) {
            cl.updateStatus(Cloudlet.CloudletStatus.CANCELED);
            return new Cancelled(true, false, pe, promote());
        }
        List<Cloudlet> queue = getCloudletWaitingList();
        for (int i = 0; i < queue.size(); i++) {
            if (queue.get(i).getCloudletId() == cloudletId) {
                Cloudlet waiting = queue.remove(i);
                waiting.updateStatus(Cloudlet.CloudletStatus.CANCELED);
                return new Cancelled(false, true, -1, new ArrayList<>());
            }
        }
        return new Cancelled(false, false, -1, new ArrayList<>());
    }

    private Cloudlet removeRunning(int cloudletId) {
        List<Cloudlet> exec = getCloudletExecList();
        for (int i = 0; i < exec.size(); i++) {
            if (exec.get(i).getCloudletId() == cloudletId) {
                Cloudlet cl = exec.remove(i);
                Integer pe = peOfCloudlet.remove(cloudletId);
                if (pe == null || peOwner[pe] != cloudletId) throw new IllegalStateException("PE ownership corrupted");
                peOwner[pe] = -1;
                usedPes -= 1;
                if (usedPes < 0) throw new IllegalStateException("usedPes negative");
                return cl;
            }
        }
        return null;
    }

    @Override
    public void cloudletFinish(Cloudlet cl) {
        // Native bookkeeping only (status SUCCESS, finished list). usedPes was already released in removeRunning.
        cl.updateStatus(Cloudlet.CloudletStatus.SUCCESS);
        cl.finalizeCloudlet();
        getCloudletFinishedList().add(cl);
        finishedCount++;
    }

    @Override
    public double cloudletSubmit(Cloudlet cl, double fileTransferTime) {
        throw new UnsupportedOperationException("Use admit(); native submit would bypass bounded admission and add transfer time");
    }

    @Override
    public Cloudlet cloudletCancel(int cloudletId) {
        throw new UnsupportedOperationException("Use cancel(); native cancel leaves usedPes unchanged");
    }

    @Override
    public boolean cloudletPause(int cloudletId) {
        throw new UnsupportedOperationException("Non-preemptive scheduler: pause is not part of the v2 model");
    }

    @Override
    public double cloudletResume(int cloudletId) {
        throw new UnsupportedOperationException("Non-preemptive scheduler: resume is not part of the v2 model");
    }

    @Override
    protected void updateWaitingCloudlets(double currentTime, Object info) {
        throw new UnsupportedOperationException("Waiting tasks are promoted by finish()/cancel(), not by native time updates");
    }
}
