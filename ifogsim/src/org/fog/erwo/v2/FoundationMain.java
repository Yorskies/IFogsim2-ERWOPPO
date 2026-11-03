package org.fog.erwo.v2;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TimeZone;
import org.cloudbus.cloudsim.Cloudlet;
import org.cloudbus.cloudsim.CloudletSchedulerSpaceShared;
import org.cloudbus.cloudsim.Log;
import org.cloudbus.cloudsim.UtilizationModelFull;
import org.cloudbus.cloudsim.core.CloudSim;
import org.cloudbus.cloudsim.core.CloudSimTags;
import org.cloudbus.cloudsim.core.SimEntity;
import org.cloudbus.cloudsim.core.SimEvent;
import org.fog.utils.FogLinearPowerModel;
import org.json.simple.JSONObject;

/** P00 build/API probe only. The task engine and v2 socket are later milestones. */
public final class FoundationMain {
    private static final double MIN_SPACING = 1e-6;
    private enum ProbeTag implements CloudSimTags { CHECK }

    private static final class Probe extends SimEntity {
        private final List<Double> times = new ArrayList<>();
        private final List<String> labels = new ArrayList<>();
        Probe() { super("ResearchV2FoundationProbe"); }
        @Override public void startEntity() {
            schedule(getId(), MIN_SPACING, ProbeTag.CHECK, "minimum-spacing");
            // Deliberately inserted in reverse domain priority: audit native serial ordering.
            schedule(getId(), .4194304, ProbeTag.CHECK, "arrival-inserted-first");
            schedule(getId(), .4194304, ProbeTag.CHECK, "completion-inserted-second");
        }
        @Override public void processEvent(SimEvent event) {
            times.add(CloudSim.clock());
            labels.add((String) event.getData());
        }
    }

    private static final class SchedulerProbe extends CloudletSchedulerSpaceShared {
        int busyPes() { return usedPes; }
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new IllegalStateException(message);
    }

    private static List<Double> episode() {
        Calendar calendar = Calendar.getInstance(TimeZone.getTimeZone("UTC"));
        calendar.setTimeInMillis(0);
        CloudSim.init(1, calendar, false, MIN_SPACING);
        check(CloudSim.clock() == 0 && CloudSim.getMinTimeBetweenEvents() == MIN_SPACING, "CloudSim init/reset failed");
        Probe probe = new Probe();
        double end = CloudSim.startSimulation();
        check(probe.times.equals(List.of(MIN_SPACING, .4194304, .4194304)), "Native event time/spacing drift");
        check(probe.labels.equals(List.of("minimum-spacing", "arrival-inserted-first", "completion-inserted-second")), "Native tie-order changed; re-audit required");
        check(Math.abs(end - .4194304) <= 1e-12, "Native end time drift");
        return probe.times;
    }

    private static Map<String, Object> selfTest(JSONObject wire) {
        boolean loggingWasDisabled = Log.isDisabled();
        Log.setDisabled(true);
        try {
            List<Double> first = episode();
            List<Double> second = episode();
            check(first.equals(second), "Sequential native episodes differ");
            FogLinearPowerModel power = new FogLinearPowerModel(2.5, .5);
            check(power.getPower(0) == .5 && power.getPower(1) == 2.5, "Idle/busy power semantics changed");
            // Reproduce the upstream cancellation hazard; do not alter the scheduler in P00.
            SchedulerProbe scheduler = new SchedulerProbe();
            scheduler.updateCloudletsProcessing(0, new ArrayList<>(List.of(500.0)));
            UtilizationModelFull model = new UtilizationModelFull();
            Cloudlet task = new Cloudlet(0, 100, 1, 1, 1, model, model, model);
            scheduler.cloudletSubmit(task, 0);
            check(scheduler.busyPes() == 1, "Scheduler probe did not start task");
            check(scheduler.cloudletCancel(0) != null, "Scheduler cancellation API unavailable");
            check(scheduler.busyPes() == 1, "Upstream cancellation behavior changed; re-audit required");
            check(Contracts.priority(wire, "RESULT_DELIVERED") < Contracts.priority(wire, "DEADLINE")
                && Contracts.priority(wire, "TIMEOUT") < Contracts.priority(wire, "ARRIVAL"), "Domain priority contract broken");
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("status", "pass");
            result.put("scope", "P00 native event/API probe; no task engine, training or RPC");
            result.put("native_event_times_s", first);
            result.put("sequential_episodes", 2);
            result.put("min_event_spacing_s", MIN_SPACING);
            result.put("native_same_time_order", "insertion serial; domain priorities still require P02 coordinator");
            result.put("native_cancel_releases_used_pes", false);
            result.put("idle_probe_energy_j", power.getPower(0) * 69);
            result.put("observation_features", ((List<?>) wire.get("observation_features")).size());
            return result;
        } finally {
            Log.setDisabled(loggingWasDisabled);
        }
    }

    public static void main(String[] args) throws Exception {
        JSONObject wire = Contracts.load();
        if (args.length == 1 && "--describe".equals(args[0])) {
            System.out.println(wire.toJSONString());
        } else if (args.length == 1 && "--self-test".equals(args[0])) {
            System.out.println(JSONObject.toJSONString(selfTest(wire)));
        } else {
            System.err.println("P00 foundation only. Use --describe or --self-test. Task simulation/socket not implemented yet.");
            System.exit(2);
        }
    }
}
