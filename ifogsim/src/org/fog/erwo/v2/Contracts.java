package org.fog.erwo.v2;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;

/** Reads the same immutable wire resource that Python exports. No copied feature ordering. */
public final class Contracts {
    private Contracts() { }

    public static JSONObject load() throws Exception {
        try (InputStream stream = Contracts.class.getResourceAsStream("/research_v2/wire_contract.json")) {
            if (stream == null) throw new IllegalStateException("Missing v2 wire contract");
            JSONObject wire = (JSONObject) new JSONParser().parse(new InputStreamReader(stream, StandardCharsets.UTF_8));
            List<?> features = (List<?>) wire.get("observation_features");
            if (!"research-v2.1".equals(wire.get("schema_version")) || features.size() != 108
                    || new HashSet<>(features).size() != 108 || ((List<?>) wire.get("actions")).size() != 7
                    || ((List<?>) wire.get("objective_order")).size() != 5) {
                throw new IllegalStateException("Incompatible v2 wire contract");
            }
            return wire;
        }
    }

    public static int priority(JSONObject wire, String kind) {
        Object priority = ((Map<?, ?>) wire.get("event_priorities")).get(kind);
        if (!(priority instanceof Number)) throw new IllegalArgumentException("Unknown event kind: " + kind);
        return ((Number) priority).intValue();
    }
}
