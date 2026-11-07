package org.fog.erwo.v2;

import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TimeZone;
import org.cloudbus.cloudsim.Log;
import org.cloudbus.cloudsim.core.CloudSim;
import org.json.simple.JSONObject;
import org.json.simple.JSONValue;
import org.json.simple.parser.JSONParser;

/**
 * Research v2 socket server: UTF-8 JSON Lines on the loopback interface, one object per line, protocol {@code research-v2.1}.
 *
 * <p>One JVM serves one simulation at a time (CloudSim has static state). A {@code reset} runs the whole episode inside
 * {@code CloudSim.startSimulation()}; the policy's {@code decide} is called at every arrival and blocks on the socket, so
 * the simulated clock stands still while Python thinks. A decision is answered by the <em>next</em> decision's response
 * (or by the terminal response after the drain to H), which is how delayed outcomes reach the reward without any
 * look-ahead. There is no fallback engine: a wire, hash or invariant failure ends the episode with an error response, and
 * a dropped connection aborts it without a result.
 */
public final class V2SocketServer {
    static final String SCHEMA = "research-v2.1";
    private static final int MAX_FRAME_BYTES = 16 * 1024 * 1024;

    /** The episode was cut short because the client reset, closed or vanished; never a successful ending. */
    static final class EpisodeAborted extends RuntimeException {
        final JSONObject next;       // a reset request to start immediately, or null
        final boolean closeSession;
        EpisodeAborted(JSONObject next, boolean closeSession, String reason) {
            super(reason, null, false, false);
            this.next = next;
            this.closeSession = closeSession;
        }
    }

    /** Socket EOF, timeout or I/O failure. */
    static final class ConnectionLost extends RuntimeException {
        ConnectionLost(String message) { super(message, null, false, false); }
    }

    private final JSONObject config;
    private final JSONObject wire;
    private final String boundConfigSha256;
    private final long rpcTimeoutMs;
    private final Map<String, Object> handshake;
    private final List<String> actionNames = new ArrayList<>();

    private V2SocketServer(JSONObject config, JSONObject wire, String boundConfigSha256, long rpcTimeoutMs, String jarSha256) throws Exception {
        this.config = config;
        this.wire = wire;
        this.boundConfigSha256 = boundConfigSha256;
        this.rpcTimeoutMs = rpcTimeoutMs;
        for (Object a : (List<?>) wire.get("actions")) actionNames.add((String) a);
        Map<String, Object> h = new LinkedHashMap<>();
        h.put("server", "erwo-v2-socket");
        h.put("schema_version", SCHEMA);
        h.put("jar_sha256", jarSha256);
        h.put("config_file_sha256", sha256(resourceBytes("/research_v2/default.json")));
        h.put("wire_contract_file_sha256", sha256(resourceBytes("/research_v2/wire_contract.json")));
        h.put("bound_config_sha256", boundConfigSha256);
        h.put("observation_dimension", ((List<?>) wire.get("observation_features")).size());
        h.put("actions", actionNames);
        h.put("max_frame_bytes", MAX_FRAME_BYTES);
        h.put("rpc_timeout_s", rpcTimeoutMs / 1000.0);
        this.handshake = h;
    }

    // ---- helpers ---------------------------------------------------------------------------------------

    private static byte[] resourceBytes(String name) throws IOException {
        try (InputStream stream = V2SocketServer.class.getResourceAsStream(name)) {
            if (stream == null) throw new IllegalStateException("Missing resource " + name);
            return stream.readAllBytes();
        }
    }

    static String sha256(byte[] data) throws Exception {
        StringBuilder sb = new StringBuilder();
        for (byte b : MessageDigest.getInstance("SHA-256").digest(data)) sb.append(String.format("%02x", b));
        return sb.toString();
    }

    private static String ownJarSha256() {
        try {
            Path location = Paths.get(V2SocketServer.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            return Files.isRegularFile(location) ? sha256(Files.readAllBytes(location)) : null;
        } catch (Exception e) {
            return null;
        }
    }

    // ---- one client connection -------------------------------------------------------------------------

    private final class Session {
        private final InputStream in;
        private final OutputStream out;
        private String lastDecisionId;
        private String lastDecisionLine;

        Session(Socket socket) throws IOException {
            socket.setSoTimeout((int) rpcTimeoutMs);
            socket.setTcpNoDelay(true);
            this.in = new BufferedInputStream(socket.getInputStream());
            this.out = socket.getOutputStream();
        }

        private String readLine() {
            ByteArrayOutputStream line = new ByteArrayOutputStream();
            try {
                int b;
                while ((b = in.read()) != -1) {
                    if (b == '\n') return line.toString(StandardCharsets.UTF_8);
                    line.write(b);
                    if (line.size() > MAX_FRAME_BYTES) throw new ConnectionLost("frame larger than " + MAX_FRAME_BYTES + " bytes");
                }
            } catch (SocketTimeoutException e) {
                throw new ConnectionLost("RPC timeout after " + rpcTimeoutMs + " ms");
            } catch (IOException e) {
                throw new ConnectionLost("I/O error: " + e.getMessage());
            }
            throw new ConnectionLost("peer closed the connection");
        }

        void writeLine(String line) {
            try {
                out.write((line + "\n").getBytes(StandardCharsets.UTF_8));
                out.flush();
            } catch (IOException e) {
                throw new ConnectionLost("write failed: " + e.getMessage());
            }
        }

        Map<String, Object> base(String requestId, String episodeId, String operation, String status) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("schema_version", SCHEMA);
            m.put("request_id", requestId);
            m.put("episode_id", episodeId);
            m.put("operation", operation);
            m.put("status", status);
            m.put("error", null);
            m.put("terminated", false);
            m.put("truncated", false);
            m.put("step_index", 0);
            m.put("task_id", null);
            m.put("sim_time_s", null);
            m.put("observation", null);
            m.put("observation_valid", false);
            m.put("raw_snapshot", null);
            m.put("cost_cumulative", null);
            m.put("cost_delta", null);
            m.put("handshake", null);
            m.put("summary", null);
            m.put("result", null);
            return m;
        }

        void error(JSONObject req, String code, String message) {
            Map<String, Object> m = base(str(req, "request_id", "?"), str(req, "episode_id", "?"), operationOrHeartbeat(req), "error");
            Map<String, Object> e = new LinkedHashMap<>();
            e.put("code", code);
            e.put("message", message);
            m.put("error", e);
            writeLine(JSONValue.toJSONString(m));
        }

        private String operationOrHeartbeat(JSONObject req) {
            String op = str(req, "operation", "heartbeat");
            return List.of("hello", "reset", "step", "close", "heartbeat").contains(op) ? op : "heartbeat";
        }

        /** Sends the response to a reset/step/close request and remembers it so an identical retry gets the same bytes. */
        void respondDecision(JSONObject req, Map<String, Object> response) {
            String line = JSONValue.toJSONString(response);
            lastDecisionId = str(req, "request_id", null);
            lastDecisionLine = line;
            writeLine(line);
        }

        /**
         * Next reset/step/close request. hello and heartbeat are answered here, a retried request id gets its cached answer, and
         * malformed or legacy frames get an error response without ever reaching the episode logic.
         */
        JSONObject nextRequest() {
            while (true) {
                String line = readLine();
                JSONObject req;
                try {
                    Object parsed = new JSONParser().parse(line);
                    if (!(parsed instanceof JSONObject)) throw new IllegalArgumentException("frame is not an object");
                    req = (JSONObject) parsed;
                } catch (Exception e) {
                    error(new JSONObject(), "BAD_JSON", String.valueOf(e.getMessage()));
                    continue;
                }
                if (!SCHEMA.equals(req.get("schema_version"))) {
                    error(req, "UNSUPPORTED_SCHEMA", "this server speaks " + SCHEMA + " (v2: 108 features, 5 objectives, 7 actions); legacy requests are refused, got "
                            + req.get("schema_version"));
                    continue;
                }
                String id = str(req, "request_id", null);
                String op = str(req, "operation", null);
                if (id == null || op == null) {
                    error(req, "BAD_REQUEST", "request_id and operation are required");
                    continue;
                }
                if (id.equals(lastDecisionId) && lastDecisionLine != null && List.of("reset", "step", "close").contains(op)) {
                    writeLine(lastDecisionLine);   // idempotent retry: same answer, nothing applied twice
                    continue;
                }
                if ("hello".equals(op)) {
                    Map<String, Object> m = base(id, str(req, "episode_id", "hello"), "hello", "ok");
                    m.put("handshake", handshake);
                    writeLine(JSONValue.toJSONString(m));
                    continue;
                }
                if ("heartbeat".equals(op)) {
                    writeLine(JSONValue.toJSONString(base(id, str(req, "episode_id", "-"), "heartbeat", "ok")));
                    continue;
                }
                return req;
            }
        }
    }

    private static String str(JSONObject o, String key, String fallback) {
        Object v = o.get(key);
        return v instanceof String ? (String) v : fallback;
    }

    // ---- the interactive policy: blocks at every arrival -----------------------------------------------

    private final class InteractivePolicy implements EngineCoordinator.Actions {
        final Session session;
        final String episodeId;
        final String configSha;
        final String traceSha;
        final ObservationBuilder builder;
        JSONObject pending;
        double[] lastCost = new double[5];
        int steps;

        InteractivePolicy(Session session, JSONObject reset, ObservationBuilder builder) {
            this.session = session;
            this.pending = reset;
            this.episodeId = str(reset, "episode_id", "");
            this.configSha = str(reset, "config_sha256", "");
            this.traceSha = str(reset, "trace_sha256", "");
            this.builder = builder;
        }

        @Override public String targetFor(TaskSpec task) {
            throw new UnsupportedOperationException("interactive policy decides through decide()");
        }

        @Override public String decide(TaskSpec task, EngineCoordinator engine) {
            ObservationBuilder.Snapshot snapshot = builder.build(engine, task);
            double[] cost = engine.costVector(engine.nowS());
            Map<String, Object> m = session.base(str(pending, "request_id", "?"), episodeId, str(pending, "operation", "step"), "ok");
            m.put("step_index", steps);
            m.put("task_id", task.taskId);
            m.put("sim_time_s", engine.nowS());
            m.put("observation", toList(snapshot.vector));
            m.put("observation_valid", true);
            m.put("raw_snapshot", snapshot.raw);
            putCosts(m, cost);
            session.respondDecision(pending, m);

            while (true) {
                JSONObject req = session.nextRequest();
                String op = str(req, "operation", "");
                if ("reset".equals(op)) throw new EpisodeAborted(req, false, "reset during episode");
                if ("close".equals(op)) {
                    session.respondDecision(req, session.base(str(req, "request_id", "?"), episodeId, "close", "ok"));
                    throw new EpisodeAborted(null, true, "close during episode");
                }
                if (!"step".equals(op)) {
                    session.error(req, "BAD_OPERATION", "unexpected operation '" + op + "' while an episode awaits a step");
                    continue;
                }
                String problem = hashProblem(req);
                Object action = req.get("action");
                if (problem == null && !(action instanceof Long && (Long) action >= 0 && (Long) action < actionNames.size())) {
                    problem = "action must be an integer in 0.." + (actionNames.size() - 1);
                }
                if (problem != null) {
                    session.error(req, "BAD_STEP", problem);   // the episode keeps waiting for a valid step
                    continue;
                }
                pending = req;
                steps++;
                return EngineMain.resolve(actionNames.get(((Long) action).intValue()), task);
            }
        }

        private String hashProblem(JSONObject req) {
            if (!episodeId.equals(str(req, "episode_id", null))) return "episode_id differs from the running episode";
            if (!configSha.equals(str(req, "config_sha256", null))) return "config_sha256 differs from the running episode";
            if (!traceSha.equals(str(req, "trace_sha256", null))) return "trace_sha256 differs from the running episode";
            return null;
        }

        void putCosts(Map<String, Object> m, double[] cost) {
            double[] delta = new double[5];
            for (int j = 0; j < 5; j++) delta[j] = cost[j] - lastCost[j];
            lastCost = cost;
            m.put("cost_cumulative", toList(cost));
            m.put("cost_delta", toList(delta));
        }
    }

    private static List<Double> toList(double[] values) {
        List<Double> out = new ArrayList<>(values.length);
        for (double v : values) out.add(v);
        return out;
    }

    // ---- reset -> episode ------------------------------------------------------------------------------

    /** Returns the next request to process immediately (a reset that interrupted this episode) or null. */
    private JSONObject runEpisode(Session session, JSONObject reset) {
        String episodeId = str(reset, "episode_id", "?");
        Object traceObject = reset.get("trace");
        if (!(traceObject instanceof JSONObject)) {
            session.error(reset, "TRACE_REQUIRED", "reset must carry the trace object");
            return null;
        }
        JSONObject trace = (JSONObject) traceObject;
        String problem = null;
        if (boundConfigSha256 != null && !boundConfigSha256.equals(reset.get("config_sha256"))) {
            problem = "config_sha256 differs from the hash this server was started with";
        } else if (!Objects.equals(reset.get("trace_sha256"), trace.get("payload_sha256")) || reset.get("trace_sha256") == null) {
            problem = "trace_sha256 differs from the trace's declared payload_sha256";
        } else if (!Objects.equals(reset.get("config_sha256"), trace.get("config_sha256"))) {
            problem = "trace was generated under a different config_sha256";
        } else if (!SCHEMA.equals(trace.get("schema_version"))) {
            problem = "trace schema_version is not " + SCHEMA;
        }
        if (problem != null) {
            session.error(reset, "HASH_MISMATCH", problem);
            return null;
        }
        Map<?, ?> options = reset.get("options") instanceof Map ? (Map<?, ?>) reset.get("options") : new LinkedHashMap<>();
        JSONObject scenario = new JSONObject();
        scenario.put("label", episodeId);
        scenario.put("tasks", trace.get("tasks"));
        JSONObject timing = new JSONObject();
        timing.put("arrival_window_s", trace.get("arrival_window_s"));
        timing.put("horizon_s", trace.get("horizon_s"));
        scenario.put("timing", timing);
        JSONObject topology = new JSONObject();
        topology.put("homogeneous_fog", Boolean.TRUE.equals(options.get("homogeneous_fog")));
        scenario.put("topology", topology);
        JSONObject network = new JSONObject();
        network.put("log_transfers", Boolean.TRUE.equals(options.get("log_transfers")));
        scenario.put("network", network);
        boolean detail = Boolean.TRUE.equals(options.get("detail"));

        InteractivePolicy policy = null;
        try {
            List<String> classIds = new ArrayList<>();
            for (Object c : (List<?>) ((Map<?, ?>) config.get("tasks")).get("classes")) classIds.add((String) ((Map<?, ?>) c).get("id"));
            ObservationBuilder builder = new ObservationBuilder(wire, (Map<?, ?>) config.get("observation"), classIds);
            policy = new InteractivePolicy(session, reset, builder);
            EngineCoordinator engine = EngineMain.build(episodeId, scenario, config, wire, policy);
            CloudSim.startSimulation();
            if (!engine.finished()) throw new IllegalStateException("Simulation ended before the horizon event");

            double[] cost = engine.costVector(engine.horizonS());
            Map<String, Object> result = engine.result();
            Map<String, Object> m = session.base(str(policy.pending, "request_id", "?"), episodeId, "step", "ok");
            m.put("terminated", true);
            m.put("truncated", false);
            m.put("step_index", policy.steps);
            m.put("sim_time_s", engine.horizonS());
            m.put("observation", toList(new double[((List<?>) wire.get("observation_features")).size()]));
            m.put("observation_valid", false);
            policy.putCosts(m, cost);
            Map<String, Object> summary = new LinkedHashMap<>();
            summary.put("energy", result.get("energy"));
            summary.put("metrics", result.get("metrics"));
            summary.put("task_count", result.get("task_count"));
            m.put("summary", summary);
            // The per-event log is large (thousands of rows for heavy traces); it is sent only on request.
            if (!Boolean.TRUE.equals(options.get("include_events"))) result.remove("events");
            if (detail) m.put("result", result);
            session.respondDecision(policy.pending, m);
            return null;
        } catch (EpisodeAborted aborted) {
            if (aborted.closeSession) throw aborted;
            return aborted.next;
        } catch (ConnectionLost lost) {
            throw lost;
        } catch (Throwable failure) {
            // Strict mode: report the engine failure; there is no substitute simulation and no partial result.
            System.err.println("engine failure in episode " + episodeId + ": " + failure);
            JSONObject target = policy != null && policy.pending != null ? policy.pending : reset;
            session.error(target, "ENGINE_ERROR", failure.getClass().getSimpleName() + ": " + failure.getMessage());
            return null;
        }
    }

    private void serve(Socket socket) {
        Session session;
        try {
            session = new Session(socket);
        } catch (IOException e) {
            return;
        }
        try {
            JSONObject req = session.nextRequest();
            while (true) {
                String op = str(req, "operation", "");
                if ("reset".equals(op)) {
                    try {
                        req = runEpisode(session, req);
                    } catch (EpisodeAborted | ConnectionLost passThrough) {
                        throw passThrough;
                    } catch (RuntimeException malformed) {
                        // A malformed reset must not take the server down; the client gets a precise error instead.
                        session.error(req, "BAD_REQUEST", malformed.getClass().getSimpleName() + ": " + malformed.getMessage());
                        req = null;
                    }
                    if (req == null) req = session.nextRequest();
                } else if ("close".equals(op)) {
                    session.respondDecision(req, session.base(str(req, "request_id", "?"), str(req, "episode_id", "-"), "close", "ok"));
                    return;
                } else {
                    session.error(req, "NO_EPISODE", "'" + op + "' needs a running episode; send reset first");
                    req = session.nextRequest();
                }
            }
        } catch (EpisodeAborted closed) {
            // client closed the session mid-episode; the close response was already sent
        } catch (ConnectionLost lost) {
            System.err.println("connection ended: " + lost.getMessage());
        } finally {
            try { socket.close(); } catch (IOException ignored) { }
        }
    }

    // ---- entry point -----------------------------------------------------------------------------------

    public static void main(String[] args) throws Exception {
        int port = -1;
        String configSha = null;
        double rpcTimeoutS = -1;
        boolean anyPort = false;
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--port": port = Integer.parseInt(args[++i]); break;
                case "--config-sha256": configSha = args[++i]; break;
                case "--rpc-timeout-s": rpcTimeoutS = Double.parseDouble(args[++i]); break;
                case "--allow-any-port": anyPort = true; break;
                default: throw new IllegalArgumentException("Unknown argument " + args[i]);
            }
        }
        Log.setDisabled(true);
        JSONObject config = EngineMain.loadResource("/research_v2/default.json");
        JSONObject wire = Contracts.load();
        Map<?, ?> execution = (Map<?, ?>) config.get("execution");
        if (port < 0) throw new IllegalArgumentException("--port is required");
        if (!anyPort) {
            boolean allowed = false;
            for (Object p : (List<?>) execution.get("allowed_ports")) allowed |= ((Number) p).intValue() == port;
            if (!allowed) throw new IllegalArgumentException("Port " + port + " is not in execution.allowed_ports " + execution.get("allowed_ports"));
        }
        if (rpcTimeoutS < 0) rpcTimeoutS = Json.number(execution, "rpc_timeout_wall_s");
        V2SocketServer server = new V2SocketServer(config, wire, configSha, Math.round(rpcTimeoutS * 1000), ownJarSha256());
        ServerSocket listener = new ServerSocket();
        listener.setReuseAddress(true);
        listener.bind(new InetSocketAddress(InetAddress.getLoopbackAddress(), port));
        Map<String, Object> ready = new LinkedHashMap<>();
        ready.put("event", "listening");
        ready.put("host", "127.0.0.1");
        ready.put("port", listener.getLocalPort());
        System.out.println(JSONValue.toJSONString(ready));
        System.out.flush();
        while (true) {
            // One client at a time: a second simulation in this JVM would share CloudSim's static state.
            server.serve(listener.accept());
        }
    }
}
