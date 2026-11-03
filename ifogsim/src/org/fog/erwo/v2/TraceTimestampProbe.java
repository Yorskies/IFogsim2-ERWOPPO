package org.fog.erwo.v2;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

/** P01 numeric replay probe. Parses trace timestamps; does not simulate tasks. */
public final class TraceTimestampProbe {
    private static String bits(double value) {
        if (!Double.isFinite(value)) throw new IllegalArgumentException("Non-finite timestamp");
        return String.format("%016x", Double.doubleToRawLongBits(value));
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("Expected one exported trace.json path");
        JSONObject trace;
        try (var reader = Files.newBufferedReader(Path.of(args[0]), StandardCharsets.UTF_8)) {
            trace = (JSONObject) new JSONParser().parse(reader);
        }
        if (!"research-v2.1".equals(trace.get("schema_version"))) {
            throw new IllegalArgumentException("Incompatible trace schema version");
        }
        List<Map<String, Object>> rows = new ArrayList<>();
        for (Object item : (List<?>) trace.get("tasks")) {
            Map<?, ?> task = (Map<?, ?>) item;
            double arrival = ((Number) task.get("arrival_s")).doubleValue();
            double deadline = ((Number) task.get("deadline_relative_s")).doubleValue();
            double timeout = ((Number) task.get("timeout_relative_s")).doubleValue();
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("task_id", task.get("task_id"));
            row.put("arrival_s", bits(arrival));
            row.put("deadline_relative_s", bits(deadline));
            row.put("timeout_relative_s", bits(timeout));
            row.put("absolute_deadline_s", bits(arrival + deadline));
            row.put("absolute_timeout_s", bits(arrival + timeout));
            rows.add(row);
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("scope", "P01 binary64 timestamp replay; no task execution");
        result.put("payload_sha256", trace.get("payload_sha256"));
        result.put("task_count", rows.size());
        result.put("timestamp_bits", rows);
        System.out.println(JSONObject.toJSONString(result));
    }
}
