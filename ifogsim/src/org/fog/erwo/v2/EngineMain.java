package org.fog.erwo.v2;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TimeZone;
import org.cloudbus.cloudsim.Log;
import org.cloudbus.cloudsim.core.CloudSim;
import org.json.simple.JSONObject;
import org.json.simple.JSONValue;
import org.json.simple.parser.JSONParser;

/**
 * Headless P02 driver: replays one scenario with fixed actions through the event engine, with no Python
 * policy and no socket. Scenario JSON (all keys explicit, nothing silently defaulted except config-sourced
 * constants):
 * <pre>
 * { "label": str, "tasks": [task...], "timing": {arrival_window_s, horizon_s, [epsilon_s]},
 *   "nodes": [node...] | "topology": {"homogeneous_fog": bool},
 *   "actions": "source_iot" | "nearest_fog" | "&lt;node id&gt;" | {"default": ..., "&lt;task id&gt;": ...},
 *   "fixture_transport": {"input_delay_s": x, "result_delay_s": y},      (P02 constant-delay fixture, or)
 *   "network": {"log_transfers": bool, "overrides": {"access"|"lan"|"wan": {field: value}}},   (P03 links)
 *   "repeat": n }
 * </pre>
 * Output is one JSON object on stdout. Any invariant failure prints a JSON error and exits non-zero.
 */
public final class EngineMain {
    private EngineMain() { }

    static JSONObject loadResource(String name) throws Exception {
        try (InputStream stream = EngineMain.class.getResourceAsStream(name)) {
            if (stream == null) throw new IllegalStateException("Missing resource " + name);
            return (JSONObject) new JSONParser().parse(new InputStreamReader(stream, StandardCharsets.UTF_8));
        }
    }

    static EngineCoordinator.Actions actions(Object spec) {
        if (spec instanceof String) return task -> resolve((String) spec, task);
        if (spec instanceof Map) {
            Map<?, ?> map = (Map<?, ?>) spec;
            return task -> {
                Object chosen = map.containsKey(Integer.toString(task.taskId)) ? map.get(Integer.toString(task.taskId)) : map.get("default");
                if (!(chosen instanceof String)) throw new IllegalArgumentException("No action for task " + task.taskId);
                return resolve((String) chosen, task);
            };
        }
        throw new IllegalArgumentException("Scenario needs 'actions'");
    }

    /** Copy of the config network section with per-link-type field overrides (used by tests to build small cases). */
    private static Map<String, Object> mergedNetwork(Map<?, ?> base, Map<?, ?> overrides) {
        Map<String, Object> merged = new LinkedHashMap<>();
        for (Map.Entry<?, ?> entry : base.entrySet()) {
            Object value = entry.getValue();
            merged.put((String) entry.getKey(), value instanceof Map ? new LinkedHashMap<>((Map<?, ?>) value) : value);
        }
        if (overrides != null) {
            for (Map.Entry<?, ?> entry : overrides.entrySet()) {
                Object target = merged.get(entry.getKey());
                if (!(target instanceof Map) || !(entry.getValue() instanceof Map)) {
                    throw new IllegalArgumentException("Unknown network override '" + entry.getKey() + "'");
                }
                @SuppressWarnings("unchecked") Map<String, Object> link = (Map<String, Object>) target;
                for (Map.Entry<?, ?> field : ((Map<?, ?>) entry.getValue()).entrySet()) {
                    if (!link.containsKey(field.getKey())) throw new IllegalArgumentException("Unknown link field '" + field.getKey() + "'");
                    link.put((String) field.getKey(), field.getValue());
                }
            }
        }
        return merged;
    }

    static String resolve(String action, TaskSpec task) {
        if ("source_iot".equals(action)) return "IoT-" + task.sourceIot;
        if ("nearest_fog".equals(action)) return "F" + task.accessFog;
        return action;
    }

    /** The single construction path for an episode, shared by the headless driver and the socket server. */
    static EngineCoordinator build(String episodeId, JSONObject scenario, JSONObject config, JSONObject wire,
                                   EngineCoordinator.Actions policy) {
        List<NodeSpec> nodes = new ArrayList<>();
        if (scenario.containsKey("nodes")) {
            for (Object o : (List<?>) scenario.get("nodes")) nodes.add(NodeSpec.fromJson((Map<?, ?>) o));
        } else {
            Map<?, ?> topology = (Map<?, ?>) scenario.get("topology");
            if (topology == null) throw new IllegalArgumentException("Scenario needs 'nodes' or 'topology'");
            nodes = NodeSpec.topology(config, Boolean.TRUE.equals(topology.get("homogeneous_fog")));
        }
        List<TaskSpec> tasks = new ArrayList<>();
        for (Object o : (List<?>) scenario.get("tasks")) tasks.add(TaskSpec.fromJson((Map<?, ?>) o));
        Map<?, ?> timing = (Map<?, ?>) scenario.get("timing");
        Map<?, ?> configTiming = (Map<?, ?>) config.get("timing");
        double epsilon = Json.optionalNumber(timing, "epsilon_s", Json.number(configTiming, "comparison_epsilon_s"));
        Map<?, ?> transport = scenario.containsKey("fixture_transport") ? (Map<?, ?>) scenario.get("fixture_transport") : new LinkedHashMap<>();
        if (scenario.containsKey("network") && scenario.containsKey("fixture_transport")) {
            throw new IllegalArgumentException("Choose either 'network' or 'fixture_transport', not both");
        }
        Map<String, Object> networkConfig = null;
        boolean logTransfers = false;
        if (scenario.containsKey("network")) {
            Map<?, ?> network = (Map<?, ?>) scenario.get("network");
            networkConfig = mergedNetwork((Map<?, ?>) config.get("network"), (Map<?, ?>) network.get("overrides"));
            logTransfers = Boolean.TRUE.equals(network.get("log_transfers"));
        }
        Map<?, ?> topologyConfig = (Map<?, ?>) config.get("topology");

        // Fresh clock and event queue per episode; min spacing is the contract value verified in P00.
        Calendar calendar = Calendar.getInstance(TimeZone.getTimeZone("UTC"));
        calendar.setTimeInMillis(0);
        CloudSim.init(1, calendar, false, Json.number(configTiming, "min_event_spacing_s"));
        return new EngineCoordinator(episodeId, nodes, tasks, policy,
                Json.number(timing, "arrival_window_s"), Json.number(timing, "horizon_s"), epsilon,
                Json.optionalNumber(transport, "input_delay_s", 0.0), Json.optionalNumber(transport, "result_delay_s", 0.0), wire,
                networkConfig, ((List<?>) topologyConfig.get("fogs")).size(), Json.integer(topologyConfig, "iot_per_access_fog"), logTransfers,
                (Map<?, ?>) config.get("evaluation"));
    }

    private static Map<String, Object> runEpisode(String episodeId, JSONObject scenario, JSONObject config, JSONObject wire) throws Exception {
        EngineCoordinator engine = build(episodeId, scenario, config, wire, actions(scenario.get("actions")));
        CloudSim.startSimulation();
        if (!engine.finished()) throw new IllegalStateException("Simulation ended before the horizon event");
        return engine.result();
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 2 || !"--run".equals(args[0])) {
            System.err.println("Usage: EngineMain --run <scenario.json>");
            System.exit(2);
        }
        boolean loggingWasDisabled = Log.isDisabled();
        Log.setDisabled(true);
        try {
            JSONObject scenario;
            try (Reader reader = Files.newBufferedReader(Paths.get(args[1]), StandardCharsets.UTF_8)) {
                scenario = (JSONObject) new JSONParser().parse(reader);
            }
            JSONObject config = loadResource("/research_v2/default.json");
            JSONObject wire = Contracts.load();
            int repeat = scenario.containsKey("repeat") ? Json.integer(scenario, "repeat") : 1;
            List<Map<String, Object>> episodes = new ArrayList<>();
            for (int i = 0; i < repeat; i++) {
                episodes.add(runEpisode(scenario.get("label") + "#" + i, scenario, config, wire));
            }
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("status", "pass");
            out.put("scope", "P02 headless engine with fixed actions; fixture transport; no network, energy, socket or policy");
            out.put("episodes", episodes);
            System.out.println(JSONValue.toJSONString(out));
        } catch (Throwable error) {
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("status", "error");
            out.put("error", error.getClass().getSimpleName());
            out.put("message", String.valueOf(error.getMessage()));
            System.out.println(JSONValue.toJSONString(out));
            System.exit(3);
        } finally {
            Log.setDisabled(loggingWasDisabled);
        }
    }
}
