"""Descriptive trace checks only: never estimates method performance or QoS."""

from collections import Counter
import math
import statistics

from .config import require, sha256
from .schema_definitions import WORKLOADS
from .trace_access import authorize
from .traces import Trace

# Fixed before inspecting calibration results. Union bound across 468 checks:
# 4 workloads * (1 total count + 4 interval counts + 3 class counts
#                + 3 classes * 3 attribute means + 100 source counts).
FAMILY_ALPHA = .001
CHECK_COUNT = 468


def interval_edges(config):
    return [config["timing"]["arrival_window_s"] * i / 4 for i in range(5)]


def expected_count(segments, start, end):
    return math.fsum(max(0, min(end, s["end_s"]) - max(start, s["start_s"])) * s["rate_per_s"] for s in segments)


def _summary(values):
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None}
    return {"count": len(values), "min": min(values), "max": max(values),
            "mean": statistics.fmean(values), "median": statistics.median(values)}


def _describe(data, config):
    tasks = data["tasks"]
    edges = interval_edges(config)
    by_class = {}
    for profile in config["tasks"]["classes"]:
        selected = [t for t in tasks if t["class_id"] == profile["id"]]
        by_class[profile["id"]] = {"count": len(selected), "fraction": len(selected) / len(tasks),
            **{field: _summary([t[field] for t in selected]) for field in ("cpu_mi", "input_bytes", "deadline_relative_s")}}
    sources = Counter(t["source_iot"] for t in tasks)
    return {"task_count": len(tasks), "cpu_mi": _summary([t["cpu_mi"] for t in tasks]),
            "input_bytes": _summary([t["input_bytes"] for t in tasks]), "by_class": by_class,
            "source_counts": [sources[i] for i in range(100)],
            "access_fog_counts": [sum(t["access_fog"] == i for t in tasks) for i in range(1, 6)],
            "arrival_intervals": [{"start_s": a, "end_s": b, "count": sum(a <= t["arrival_s"] < b for t in tasks)}
                                  for a, b in zip(edges, edges[1:])]}


def describe_trace(trace, config, *, role):
    data = trace.to_dict()
    authorize(role, data["seed_namespace"]["split"], "describe")
    Trace.from_dict(data, config)
    return {"seed_namespace": data["seed_namespace"], "payload_sha256": trace.payload_sha256,
            "units": config["units"], **_describe(data, config)}


def calibration_report(traces, config):
    """Aggregate all predeclared calibration IDs. No adaptive seed selection."""
    grouped = {w: [] for w in WORKLOADS}
    expected_ids = set(range(config["seeds"]["calibration_trace_ids"][0], config["seeds"]["calibration_trace_ids"][1] + 1))
    for trace in traces:
        data = trace.to_dict()
        authorize("calibrator", data["seed_namespace"]["split"], "describe")
        Trace.from_dict(data, config)
        grouped[data["seed_namespace"]["workload"]].append(data)
    log_bound = math.log(2 * CHECK_COUNT / FAMILY_ALPHA)
    checks = []

    def count_check(name, observed, expected, variance):
        tolerance = math.sqrt(2 * variance * log_bound) + 2 * log_bound / 3
        checks.append({"name": name, "kind": "Bernstein count bound", "observed": observed,
                       "expected": expected, "tolerance": tolerance, "pass": abs(observed - expected) <= tolerance})

    def mean_check(name, values, low, high, rounding_allowance=0):
        require(bool(values), f"Missing samples for calibration class: {name}")
        tolerance = (high - low) * math.sqrt(log_bound / (2 * len(values))) + rounding_allowance
        observed = statistics.fmean(values)
        expected = (low + high) / 2
        checks.append({"name": name, "kind": "Hoeffding bounded-mean bound", "observed": observed,
                       "expected": expected, "tolerance": tolerance, "pass": abs(observed - expected) <= tolerance})

    profiles = {}
    trace_inventory = []
    for workload, entries in grouped.items():
        ids = [e["seed_namespace"]["trace_id"] for e in entries]
        require(len(ids) == len(expected_ids) and set(ids) == expected_ids, f"{workload}: incomplete/duplicate calibration IDs")
        tasks = [task for entry in entries for task in entry["tasks"]]
        n = len(tasks)
        aggregate = _describe({"tasks": tasks}, config)
        means = [len(e["tasks"]) for e in entries]
        expected_total = len(entries) * expected_count(config["workloads"][workload], 0, config["timing"]["arrival_window_s"])
        count_check(f"{workload}.total", n, expected_total, expected_total)
        for interval in aggregate["arrival_intervals"]:
            mu = len(entries) * expected_count(config["workloads"][workload], interval["start_s"], interval["end_s"])
            count_check(f"{workload}.arrival[{interval['start_s']},{interval['end_s']})", interval["count"], mu, mu)
            interval["expected_count"] = mu
            interval["observed_rate_per_s"] = interval["count"] / (len(entries) * (interval["end_s"] - interval["start_s"]))
        for profile in config["tasks"]["classes"]:
            selected = [t for t in tasks if t["class_id"] == profile["id"]]
            p = profile["probability"]
            count_check(f"{workload}.class.{profile['id']}", len(selected), n * p, n * p * (1 - p))
            for field, bounds, rounding in (("cpu_mi", profile["cpu_mi"], 0),
                    ("input_bytes", [v * 2**20 for v in profile["input_mib"]], 1),
                    ("deadline_relative_s", profile["deadline_s"], 0)):
                mean_check(f"{workload}.{profile['id']}.{field}", [t[field] for t in selected], *bounds, rounding)
        for source, observed in enumerate(aggregate["source_counts"]):
            count_check(f"{workload}.source.{source}", observed, n / 100, n * .01 * .99)
        profiles[workload] = {**aggregate, "trace_count": len(entries), "tasks_per_trace": _summary(means),
                              "expected_tasks_per_trace": expected_total / len(entries)}
        trace_inventory.extend({"workload": workload, "trace_id": e["seed_namespace"]["trace_id"],
                                "task_count": e["task_count"], "payload_sha256": e["payload_sha256"]} for e in entries)
    moderate = {e["seed_namespace"]["trace_id"]: e for e in grouped["moderate"]}
    dynamic_distinct = all(sha256(e["tasks"]) != sha256(moderate[e["seed_namespace"]["trace_id"]]["tasks"]) for e in grouped["dynamic"])
    require(len(checks) == CHECK_COUNT, "Calibration check family changed; revise declared validation protocol")
    return {"config_sha256": sha256(config), "split": "calibration", "test_accessed": False,
            "validation_protocol": {"family_alpha": FAMILY_ALPHA, "checks": CHECK_COUNT,
                "count_bound": "sqrt(2*variance*log(2M/alpha))+2*log(2M/alpha)/3",
                "mean_bound": "(high-low)*sqrt(log(2M/alpha)/(2*n)); input rounding allowance 1 byte",
                "note": "Distribution diagnostics, not method-significance tests; no resampling until pass"},
            "profiles": profiles, "checks": checks, "trace_inventory": trace_inventory,
            "dynamic_distinct_from_moderate_for_all_ids": dynamic_distinct,
            "status": "pass" if all(c["pass"] for c in checks) and dynamic_distinct else "failed"}
