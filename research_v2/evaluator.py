"""Independent re-computation of the P04 energy ledger and evaluation metrics from raw engine records.

Inputs are only what the engine publishes as raw facts: per-task timestamps and terminal state, node specifications,
the optional per-hop transfer log and the validated config. Nothing here reads the Java energy or cost fields, so a
mismatch in `compare` points at the Java accounting (or at this module), never at shared code.
"""

import math

IOT_PREFIX = "IoT-"


def _is_fog(node_id):
    return len(node_id) >= 2 and node_id[0] == "F" and node_id[1:].isdigit()


def _group(node_id):
    if node_id.startswith(IOT_PREFIX):
        return "cpu_iot"
    if _is_fog(node_id):
        return "cpu_fog"
    return "cpu_cloud" if node_id == "cloud" else "cpu_other"


def nearest_rank(sorted_values, p):
    return sorted_values[max(1, math.ceil(p * len(sorted_values))) - 1]


def median(sorted_values):
    n = len(sorted_values)
    return sorted_values[n // 2] if n % 2 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2


def _cpu_intervals(episode):
    """CPU busy interval of every task that ever held a PE: [cpu_start, cpu_finish or the timeout that cancelled it]."""
    intervals = {}
    for t in episode["tasks"]:
        if t["cpu_start_s"] is None:
            continue
        end = t["cpu_finish_s"] if t["cpu_finish_s"] is not None else t["terminal_s"]
        intervals.setdefault(t["node"], []).append((t["task_id"], t["cpu_start_s"], end))
    return intervals


def fog_imbalance_integral(episode, fog_nodes, intervals):
    """Exact integral of the population std of fog utilizations by sweeping the busy-PE change points."""
    if not fog_nodes:
        return 0.0
    pes = {n["id"]: n["pes"] for n in fog_nodes}
    changes = []
    for node_id in pes:
        for _, start, end in intervals.get(node_id, []):
            changes.append((start, node_id, +1))
            changes.append((end, node_id, -1))
    changes.sort(key=lambda c: c[0])
    busy = {node_id: 0 for node_id in pes}
    total, last = 0.0, 0.0
    for time, node_id, delta in changes:
        if time > last:
            util = [busy[n] / pes[n] for n in pes]
            mean = sum(util) / len(util)
            total += math.sqrt(sum((u - mean) ** 2 for u in util) / len(util)) * (time - last)
            last = time
        busy[node_id] += delta
    horizon = episode["horizon_s"]
    if horizon > last:
        util = [busy[n] / pes[n] for n in pes]
        mean = sum(util) / len(util)
        total += math.sqrt(sum((u - mean) ** 2 for u in util) / len(util)) * (horizon - last)
    return total


def evaluate(episode, config):
    """Recompute energy, physical metrics, five costs and D. Returns a plain dict (see `compare` for the checked keys)."""
    horizon, window = episode["horizon_s"], episode["arrival_window_s"]
    nodes = {n["id"]: n for n in episode["nodes"]}
    tasks = episode["tasks"]
    n_tasks = len(tasks)
    if n_tasks == 0:
        raise ValueError("N=0 trace rejected")
    intervals = _cpu_intervals(episode)

    # ---- CPU-IT energy: idle for the whole horizon plus dynamic from independently summed busy intervals.
    groups, task_cpu_j = {}, {}
    for node_id, node in nodes.items():
        busy_s = sum(end - start for _, start, end in intervals.get(node_id, []))
        dyn = (node["busy_w"] - node["idle_w"]) / node["pes"] * busy_s
        g = groups.setdefault(_group(node_id), {"idle_j": 0.0, "dynamic_j": 0.0})
        g["idle_j"] += node["idle_w"] * horizon
        g["dynamic_j"] += dyn
        for task_id, start, end in intervals.get(node_id, []):
            task_cpu_j[task_id] = (node["busy_w"] - node["idle_w"]) / node["pes"] * (end - start)

    # ---- communication energy (network mode only), from the per-hop log when available.
    net = config["network"]
    network_mode = episode["transport"].startswith("NETWORK_P03")
    task_comm_j = {}
    comm_source = "not_modeled"
    if network_mode:
        iot = sum(1 for n in nodes if n.startswith(IOT_PREFIX))
        fogs = len(config["topology"]["fogs"])
        comm = {"radio": [net["radio_idle_w"] * iot * horizon, 0.0], "ap": [net["ap_idle_w"] * fogs * horizon, 0.0],
                "lan": [net["lan_idle_w"] * horizon, 0.0], "wan": [net["wan_idle_w"] * horizon, 0.0]}
        if "transfers" in episode:
            comm_source = "transfer_log"
            for h in episode["transfers"]:
                if h["serialization_start_s"] is None:
                    continue
                seconds = h["serialization_end_s"] - h["serialization_start_s"]
                server = h["server"]
                if server.startswith("access"):
                    up = h["direction"] == "up"
                    radio = (net["radio_tx_increment_w"] if up else net["radio_rx_increment_w"]) * seconds
                    ap = (net["ap_rx_increment_w"] if up else net["ap_tx_increment_w"]) * seconds
                    comm["radio"][1] += radio
                    comm["ap"][1] += ap
                    joules = radio + ap
                else:
                    kind = "lan" if server.startswith("lan") else "wan"
                    joules = h["bytes_sent"] * 8.0 * net[f"{kind}_j_per_bit_hop"]
                    comm[kind][1] += joules
                task_comm_j[h["task_id"]] = task_comm_j.get(h["task_id"], 0.0) + joules
        else:
            comm_source = "link_aggregates"
            for item in episode["links"]:
                if item["link_type"] == "access":
                    comm["radio"][1] += net["radio_tx_increment_w"] * item["up_busy_s"] + net["radio_rx_increment_w"] * item["down_busy_s"]
                    comm["ap"][1] += net["ap_rx_increment_w"] * item["up_busy_s"] + net["ap_tx_increment_w"] * item["down_busy_s"]
                else:
                    bits = 8.0 * (item["up_bytes_sent"] + item["down_bytes_sent"])
                    comm[item["link_type"]][1] += bits * net[f"{item['link_type']}_j_per_bit_hop"]
        for name, (idle, dyn) in comm.items():
            groups[name] = {"idle_j": idle, "dynamic_j": dyn}

    idle_j = sum(g["idle_j"] for g in groups.values())
    dynamic_j = sum(g["dynamic_j"] for g in groups.values())

    # ---- physical metrics
    success = [t for t in tasks if t["terminal"] != "FAILED"]
    failed = len(tasks) - len(success)
    latencies = sorted(t["delivered_s"] - t["arrival_s"] for t in success)
    late = sum(1 for t in tasks if t["terminal"] == "LATE_SUCCESS")
    metrics = {
        "task_count": n_tasks, "on_time": len(success) - late, "late_success": late, "failed": failed,
        "violation": (late + failed) / n_tasks, "reliability": len(success) / n_tasks,
        "latency": ({"mean_s": sum(latencies) / len(latencies), "median_s": median(latencies), "p95_s": nearest_rank(latencies, 0.95)}
                    if latencies else {"mean_s": None, "median_s": None, "p95_s": None}),
        "throughput": {"results_received": len(success), "results_per_s": len(success) / horizon,
                       "results_during_arrival_window": sum(1 for t in success if t["delivered_s"] < window),
                       "results_after_arrival_window": sum(1 for t in success if t["delivered_s"] >= window)},
    }

    # ---- five costs
    ev = config["evaluation"]
    fog_nodes = [n for n in episode["nodes"] if _is_fog(n["id"])]
    integral = fog_imbalance_integral(episode, fog_nodes, intervals)
    z = {
        "zL": (sum(latencies) + failed * ev["failure_latency_penalty_s"]) / (n_tasks * ev["latency_reference_s"]),
        "zE": dynamic_j / (ev["energy_reference_j_per_arrival"] * n_tasks),
        "zD": (late + failed) / n_tasks,
        "zB": integral / (horizon * ev["imbalance_reference"]) if fog_nodes else None,
        "zQ": failed / n_tasks,
    }
    metrics["costs"] = z
    metrics["D"] = math.sqrt(sum(v * v for v in z.values() if v is not None) / 5.0) if fog_nodes else None
    return {"energy": {"idle_j": idle_j, "dynamic_j": dynamic_j, "total_j": idle_j + dynamic_j, "by_group": groups,
                       "communication_source": comm_source},
            "metrics": metrics, "fog_utilization_std_integral_s": integral,
            "task_cpu_dynamic_j": task_cpu_j, "task_comm_dynamic_j": task_comm_j}


def _close(a, b, rel, abs_):
    if a is None or b is None:
        return a is b
    return math.isclose(a, b, rel_tol=rel, abs_tol=abs_)


def compare(episode, recomputed, rel=1e-9, abs_=1e-9):
    """Mismatches between the engine's published accounting and `evaluate`. An empty list means they agree."""
    bad = []

    def check(name, java, python):
        if not _close(java, python, rel, abs_):
            bad.append(f"{name}: engine={java!r} evaluator={python!r}")

    e, r = episode["energy"], recomputed["energy"]
    for key in ("idle_j", "dynamic_j", "total_j"):
        check(f"energy.{key}", e[key], r[key])
    for group, values in r["by_group"].items():
        for key in ("idle_j", "dynamic_j"):
            check(f"energy.{group}.{key}", e["by_group"][group][key], values[key])
    if set(e["by_group"]) != set(r["by_group"]):
        bad.append(f"energy groups differ: {sorted(e['by_group'])} vs {sorted(r['by_group'])}")
    m, rm = episode["metrics"], recomputed["metrics"]
    for key in ("task_count", "on_time", "late_success", "failed", "success_count"):
        if key in rm and m[key] != rm[key]:
            bad.append(f"metrics.{key}: engine={m[key]!r} evaluator={rm[key]!r}")
    for key in ("violation", "reliability"):
        check(f"metrics.{key}", m[key], rm[key])
    for key in ("mean_s", "median_s", "p95_s"):
        check(f"latency.{key}", m["latency"][key], rm["latency"][key])
    for key, value in rm["throughput"].items():
        check(f"throughput.{key}", m["throughput"][key], value)
    for key, value in rm["costs"].items():
        check(f"costs.{key}", m["costs"][key], value)
    check("D", m["D"], rm["D"])
    check("fog_utilization_std_integral_s", m["fog_utilization_std_integral_s"], recomputed["fog_utilization_std_integral_s"])
    for t in episode["tasks"]:
        check(f"task {t['task_id']} cpu_dynamic_j", t["cpu_dynamic_j"], recomputed["task_cpu_dynamic_j"].get(t["task_id"], 0.0))
        if recomputed["energy"]["communication_source"] == "transfer_log":
            check(f"task {t['task_id']} comm_dynamic_j", t["comm_dynamic_j"], recomputed["task_comm_dynamic_j"].get(t["task_id"], 0.0))
    return bad
