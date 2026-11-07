"""P06 calibration: solo-task feasibility, resumable baseline runs on calibration traces, and gate evaluation.

Runs only the four deterministic reference policies on the `calibration` split. ERWO/PPO is never used to choose a scenario,
and no parameter is adjusted here: a failed gate is reported, not repaired (specification 24.2).
"""

import argparse
import json
import math
import os
from pathlib import Path
import statistics
import time

import numpy as np

from .baselines import ACTIONS, POLICIES, AuditedSnapshot, eft_scores, greedy_eft
from .config import ROOT, load_config, sha256
from .gym_env import OffloadingEnv
from .schema_definitions import WORKLOADS
from .trace_access import TraceKey
from .traces import TraceGenerator

OUTPUT_DIR = ROOT / "results/research_v2/P06_calibration"
MODES = {"heterogeneous": False, "homogeneous": True}
TIE = 1e-9


# ---- solo-task analysis (no queueing) -------------------------------------------------------------------------

def _links(config):
    n = config["network"]
    return (n["access"]["bandwidth_bit_per_s"], n["access"]["propagation_s"]), \
           (n["lan"]["bandwidth_bit_per_s"], n["lan"]["propagation_s"]), \
           (n["wan"]["bandwidth_bit_per_s"], n["wan"]["propagation_s"])


def _node_mips(config, action, homogeneous):
    topo = config["topology"]
    if action == 0:
        return topo["iot"]["mips_per_pe"]
    if action == 6:
        return topo["cloud"]["mips_per_pe"]
    fogs = {f["id"]: f for f in topo["fogs"]}
    return (fogs["F3"] if homogeneous else fogs[f"F{action}"])["mips_per_pe"]


def solo_time(task, action, config, homogeneous):
    """Time from arrival to result receipt for one task alone in an idle system, on destination `action` (0..6)."""
    mips = _node_mips(config, action, homogeneous)
    cpu = task["cpu_mi"] / mips
    if action == 0:
        return cpu
    access, lan, wan = _links(config)
    a = task["access_fog"]
    if action == a:
        forward = backward = [access]
    elif action == 6:
        forward, backward = [access, lan, wan], [wan, lan, access]
    else:
        forward, backward = [access, lan, lan], [lan, lan, access]
    path = lambda size, hops: sum(8.0 * size / bps + prop for bps, prop in hops)
    return path(task["input_bytes"], forward) + cpu + path(task["output_bytes"], backward)


def solo_feasibility(traces, config, homogeneous):
    """Share of tasks with at least one destination whose solo completion meets the soft deadline D (<= D + 1e-9)."""
    total = feasible = 0
    by_class, by_workload = {}, {}
    for trace in traces:
        workload = trace["seed_namespace"]["workload"]
        for task in trace["tasks"]:
            ok = any(solo_time(task, action, config, homogeneous) <= task["deadline_relative_s"] + TIE for action in range(7))
            total += 1
            feasible += ok
            for table, key in ((by_class, task["class_id"]), (by_workload, workload)):
                counts = table.setdefault(key, [0, 0])
                counts[0] += 1
                counts[1] += ok
    share = lambda counts: counts[1] / counts[0]
    return {"tasks": total, "feasible": feasible, "fraction": feasible / total,
            "by_class": {k: {"tasks": v[0], "fraction": share(v)} for k, v in sorted(by_class.items())},
            "by_workload": {k: {"tasks": v[0], "fraction": share(v)} for k, v in sorted(by_workload.items())}}


# ---- running the baselines -----------------------------------------------------------------------------------

def calibration_trace(generator, config, workload, trace_id):
    key = TraceKey(config["seeds"]["master"], "calibration", None, None, trace_id, workload)
    return generator.generate(key, role="calibrator").to_dict()


def _group(prefix_ids, nodes, field):
    return [n[field] for n in nodes if prefix_ids(n["id"])]


def record_episode(mode, policy, workload, trace_id, trace, info, actions, predictions, steps, wall_s, provenance=None):
    result, metrics = info["result"], info["result"]["metrics"]
    nodes, links, tasks = result["nodes"], result["links"], {t["task_id"]: t for t in result["tasks"]}
    is_fog = lambda i: i[0] == "F" and i[1:].isdigit()
    is_iot = lambda i: i.startswith("IoT-")
    access = [l for l in links if l["link_type"] == "access"]
    wan = [l for l in links if l["link_type"] == "wan"]
    record = {
        "mode": mode, "policy": policy, "workload": workload, "trace_id": trace_id, "tasks": metrics["task_count"],
        "on_time": metrics["on_time"], "late_success": metrics["late_success"], "failed": metrics["failed"],
        "failure_fraction": metrics["failed"] / metrics["task_count"], "reliability": metrics["reliability"],
        "violation": metrics["violation"], "failure_reasons": result["failure_reasons"],
        "costs": metrics["costs"], "D": metrics["D"], "latency": metrics["latency"],
        "energy_total_j": result["energy"]["total_j"], "energy_dynamic_j": result["energy"]["dynamic_j"],
        "pressure": {
            "fog_cpu_utilization_max": max(_group(is_fog, nodes, "cpu_utilization")),
            "fog_cpu_utilization_mean": statistics.fmean(_group(is_fog, nodes, "cpu_utilization")),
            "iot_cpu_utilization_max": max(_group(is_iot, nodes, "cpu_utilization")),
            "cloud_cpu_utilization": next(n["cpu_utilization"] for n in nodes if n["id"] == "cloud"),
            "fog_queue_max": max(_group(is_fog, nodes, "max_waiting")),
            "iot_queue_max": max(_group(is_iot, nodes, "max_waiting")),
            "cpu_queue_rejections": sum(n["rejected_cpu_queue_full"] for n in nodes),
            "ram_rejections": sum(n["rejected_ram_exhausted"] for n in nodes),
            "access_utilization_max": max(l["utilization"] for l in access),
            "access_utilization_mean": statistics.fmean(l["utilization"] for l in access),
            "access_queue_max": max(l["max_waiting"] for l in access),
            "wan_utilization_max": max(l["utilization"] for l in wan),
            "network_queue_rejections": sum(l["up_rejected_queue_full"] + l["down_rejected_queue_full"] for l in links),
        },
        "action_counts": [int(c) for c in np.bincount(actions, minlength=7)],
        "steps": steps, "wall_s": wall_s, "trace_payload_sha256": trace["payload_sha256"], "provenance": provenance,
    }
    if predictions is not None:
        pairs = [(predictions[i], tasks[tid]["delivered_s"] - tasks[tid]["arrival_s"]) for i, tid in enumerate(sorted(tasks))
                 if tasks[tid]["terminal"] != "FAILED"]
        if pairs:
            error = np.array([realized - predicted for predicted, realized in pairs])
            record["eft_estimator"] = {"compared": len(pairs), "mean_error_s": float(error.mean()), "mean_abs_error_s": float(np.abs(error).mean()),
                                       "median_abs_error_s": float(np.median(np.abs(error))), "p95_abs_error_s": float(np.percentile(np.abs(error), 95)),
                                       "share_realized_not_below_estimate": float((error >= -TIE).mean())}
    return record


def run_calibration(output_dir, mode, policies, workloads, trace_ids, *, jdk_home=None, log=print):
    """Append one JSON line per episode to rows-<mode>.jsonl, skipping episodes already recorded (safe to resume)."""
    config = load_config()
    generator = TraceGenerator(config)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"rows-{mode}.jsonl"
    done = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            done.add((row["policy"], row["workload"], row["trace_id"]))
    holder = {}
    env = OffloadingEnv(lambda seed, index: holder["trace"], [0.2] * 5, config=config, jdk_home=jdk_home, any_port=True, validate=False,
                        detail=True, homogeneous_fog=MODES[mode])
    try:
        with path.open("a", encoding="utf-8") as sink:
            for workload in workloads:
                for trace_id in trace_ids:
                    trace = calibration_trace(generator, config, workload, trace_id)
                    for policy in policies:
                        if (policy, workload, trace_id) in done:
                            continue
                        holder["trace"] = trace
                        started = time.time()
                        obs, info = env.reset(seed=0)
                        actions, predictions, steps = [], [] if policy == "greedy_eft" else None, 0
                        while True:
                            snapshot = AuditedSnapshot(info["raw_snapshot"])
                            action = POLICIES[policy](snapshot)
                            if predictions is not None:
                                predictions.append(eft_scores(snapshot)[action])
                            actions.append(action)
                            obs, reward, terminated, truncated, info = env.step(action)
                            steps += 1
                            if terminated:
                                break
                        row = record_episode(mode, policy, workload, trace_id, trace, info, actions, predictions, steps, time.time() - started,
                                             {"jar_sha256": env.handshake["jar_sha256"], "config_sha256": sha256(config)})
                        sink.write(json.dumps(row, separators=(",", ":")) + "\n")
                        sink.flush()
                        log(f"{mode} {policy} {workload} trace {trace_id}: N={row['tasks']} reliability={row['reliability']:.3f} D={row['D']:.3f} ({row['wall_s']:.1f}s)")
    finally:
        env.close()
    return path


def load_rows(output_dir=OUTPUT_DIR):
    rows = []
    for mode in MODES:
        path = Path(output_dir) / f"rows-{mode}.jsonl"
        if path.exists():
            rows += [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    return rows


# ---- aggregation and gates ---------------------------------------------------------------------------------

POLICY_ORDER = ("always_local", "nearest_fog", "least_fog", "greedy_eft")
SCALAR_KEYS = ("failure_fraction", "reliability", "violation", "D", "energy_total_j", "energy_dynamic_j")
COST_KEYS = ("zL", "zE", "zD", "zB", "zQ")


def cell_means(rows):
    """Mean over the calibration traces of every (mode, policy, workload) cell. Each trace counts once."""
    grouped = {}
    for row in rows:
        grouped.setdefault((row["mode"], row["policy"], row["workload"]), []).append(row)
    cells = {}
    for key, group in grouped.items():
        mean = lambda getter: statistics.fmean(getter(r) for r in group)
        cell = {"traces": len(group), "tasks_mean": mean(lambda r: r["tasks"])}
        for name in SCALAR_KEYS:
            cell[name] = mean(lambda r, n=name: r[n])
        cell["costs"] = {name: mean(lambda r, n=name: r["costs"][n]) for name in COST_KEYS}
        cell["on_time"] = mean(lambda r: r["on_time"] / r["tasks"])
        cell["late_success"] = mean(lambda r: r["late_success"] / r["tasks"])
        cell["failed"] = mean(lambda r: r["failed"] / r["tasks"])
        cell["failure_reasons"] = {reason: mean(lambda r, k=reason: r["failure_reasons"].get(k, 0) / r["tasks"])
                                   for reason in ("CPU_QUEUE_FULL", "RAM_EXHAUSTED", "NETWORK_QUEUE_FULL", "SERVICE_TIMEOUT")}
        cell["pressure"] = {name: mean(lambda r, n=name: r["pressure"][n]) for name in group[0]["pressure"]}
        cell["action_share"] = [sum(r["action_counts"][i] for r in group) / sum(r["tasks"] for r in group) for i in range(7)]
        if "eft_estimator" in group[0]:
            cell["eft_estimator"] = {name: mean(lambda r, n=name: r["eft_estimator"][n]) for name in group[0]["eft_estimator"] if name != "compared"}
        cells[key] = cell
    return cells


def distribution_gate(config, generator=None):
    """Gate 1: the 80 calibration traces pass the predeclared P01 distribution checks (counts, attributes, four dynamic phases)."""
    from .trace_report import calibration_report
    generator = generator or TraceGenerator(config)
    low, high = config["seeds"]["calibration_trace_ids"]
    traces = [generator.generate(TraceKey(config["seeds"]["master"], "calibration", None, None, i, w), role="calibrator")
              for w in WORKLOADS for i in range(low, high + 1)]
    report = calibration_report(traces, config)
    return {"status": report["status"], "traces": len(traces)}


def evaluate_gates(rows, feasibility, config, distribution):
    """Pre-registered gates (specification 24.2). Thresholds come from config['pilot']; nothing here is tuned to a result.

    1. distribution: the P01 predeclared checks pass on all 80 calibration traces.
    2. solo_feasibility: in each configuration, pooled over its calibration tasks, at least `solo_feasible_fraction` of tasks
       have a destination that meets the soft deadline when alone in an idle system.
    3. heavy_pressure: for at least one (configuration, reference policy), the heavy workload shows a mean failure fraction
       above `heavy_failure_fraction_gt` while mean reliability stays above `heavy_reliability_gt`. A failure fraction
       above 1% is the measured symptom of resource pressure; the descriptive indicators are reported alongside.
    4. complete: every planned episode is present, so a gate cannot pass on a partial run.
    """
    pilot = config["pilot"]
    cells = cell_means(rows)
    expected = len(MODES) * len(POLICY_ORDER) * len(WORKLOADS) * (config["seeds"]["calibration_trace_ids"][1] - config["seeds"]["calibration_trace_ids"][0] + 1)
    gates = {"complete": {"pass": len(rows) == expected, "episodes": len(rows), "expected": expected}}
    gates["distribution"] = {"pass": distribution["status"] == "pass", **distribution}
    gates["solo_feasibility"] = {
        "threshold": pilot["solo_feasible_fraction"],
        "by_mode": {mode: {"fraction": feasibility[mode]["fraction"], "tasks": feasibility[mode]["tasks"], "pass": feasibility[mode]["fraction"] >= pilot["solo_feasible_fraction"]} for mode in MODES},
        "pass": all(feasibility[mode]["fraction"] >= pilot["solo_feasible_fraction"] for mode in MODES)}
    heavy = {f"{m}/{p}": {"failure_fraction": c["failure_fraction"], "reliability": c["reliability"],
                          "pass": c["failure_fraction"] > pilot["heavy_failure_fraction_gt"] and c["reliability"] > pilot["heavy_reliability_gt"]}
             for (m, p, w), c in sorted(cells.items()) if w == "heavy"}
    gates["heavy_pressure"] = {"failure_fraction_gt": pilot["heavy_failure_fraction_gt"], "reliability_gt": pilot["heavy_reliability_gt"],
                               "conditions": heavy, "passing_conditions": sorted(k for k, v in heavy.items() if v["pass"]),
                               "pass": any(v["pass"] for v in heavy.values())}
    gates["all_pass"] = all(g["pass"] for g in gates.values() if isinstance(g, dict))
    # Informational diagnostics (never gates): is the problem trivial, infeasible or under-identified?
    reliabilities = [c["reliability"] for c in cells.values()]
    spread = {}
    for mode in MODES:
        for w in WORKLOADS:
            ds = [cells[(mode, p, w)]["D"] for p in POLICY_ORDER if (mode, p, w) in cells]
            if ds:
                spread[f"{mode}/{w}"] = {"D_min": min(ds), "D_max": max(ds), "range": max(ds) - min(ds)}
    gates["diagnostics"] = {"reliability_min": min(reliabilities), "reliability_max": max(reliabilities),
                            "every_cell_reliability_above_0_99": all(r > 0.99 for r in reliabilities),
                            "every_cell_reliability_below_0_01": all(r < 0.01 for r in reliabilities),
                            "D_spread_across_policies": spread}
    return gates


def parse_ids(text):
    low, _, high = text.partition("-")
    return list(range(int(low), int(high or low) + 1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run reference policies on calibration traces")
    run.add_argument("--mode", choices=list(MODES), required=True)
    run.add_argument("--policies", nargs="+", default=list(POLICIES), choices=list(POLICIES))
    run.add_argument("--workloads", nargs="+", default=list(WORKLOADS), choices=list(WORKLOADS))
    run.add_argument("--trace-ids", default="0-19")
    run.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    run.add_argument("--jdk-home", type=Path)
    args = parser.parse_args()
    if args.jdk_home:
        os.environ["JAVA_HOME"] = str(args.jdk_home.resolve())
    run_calibration(args.output_dir, args.mode, args.policies, args.workloads, parse_ids(args.trace_ids), jdk_home=args.jdk_home)


if __name__ == "__main__":
    main()
