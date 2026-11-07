package org.fog.erwo.v2;

import java.util.Map;

/** Strict accessors: a missing or non-numeric field stops the run instead of defaulting silently. */
final class Json {
    private Json() { }

    static Number raw(Map<?, ?> o, String key) {
        Object value = o.get(key);
        if (!(value instanceof Number)) throw new IllegalArgumentException("Missing numeric field: " + key);
        double d = ((Number) value).doubleValue();
        if (Double.isNaN(d) || Double.isInfinite(d)) throw new IllegalArgumentException("Non-finite field: " + key);
        return (Number) value;
    }

    static double number(Map<?, ?> o, String key) {
        return raw(o, key).doubleValue();
    }

    static long longValue(Map<?, ?> o, String key) {
        Number n = raw(o, key);
        if (n instanceof Double || n instanceof Float) {
            double d = n.doubleValue();
            if (d != Math.rint(d)) throw new IllegalArgumentException("Field must be integral: " + key);
        }
        return n.longValue();
    }

    static int integer(Map<?, ?> o, String key) {
        return Math.toIntExact(longValue(o, key));
    }

    static double optionalNumber(Map<?, ?> o, String key, double fallback) {
        return o.containsKey(key) ? number(o, key) : fallback;
    }
}
