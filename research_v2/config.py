"""Validated configuration and canonical hashing. Never imports legacy code."""

import hashlib
import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator

from .schema_definitions import config_schema

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs/research_v2/default.json"


class ContractError(ValueError):
    """Invalid or inconsistent input: callers must stop the run."""


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def sha256(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    def invalid_constant(value):
        raise ContractError(f"Non-finite JSON constant: {value}")
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=_unique_object, parse_constant=invalid_constant)


def validate_json(value, schema):
    # JSON Schema alone does not reject Python NaN or overflow such as 1e999.
    def finite(item, path="$"):
        if isinstance(item, float) and not math.isfinite(item):
            raise ContractError(f"{path}: non-finite number")
        if isinstance(item, dict):
            for key, child in item.items():
                finite(child, f"{path}.{key}")
        elif isinstance(item, list):
            for i, child in enumerate(item):
                finite(child, f"{path}[{i}]")
    finite(value)
    validator = schema if isinstance(schema, Draft202012Validator) else Draft202012Validator(schema)
    error = next(validator.iter_errors(value), None)
    if error:
        path = ".".join(str(p) for p in error.absolute_path) or "$"
        raise ContractError(f"{path}: {error.message}")


def require(condition, message):
    if not condition:
        raise ContractError(message)


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)


def validate_config(config):
    validate_json(config, config_schema())
    timing, tasks, topology = (config[k] for k in ("timing", "tasks", "topology"))
    require(close(timing["horizon_s"], timing["arrival_window_s"] + timing["timeout_factor"] * timing["deadline_max_s"]),
            "timing.horizon_s must equal T + k * Dmax")
    require(timing["comparison_epsilon_s"] < timing["min_event_spacing_s"], "time epsilon must be below minimum event spacing")
    require(timing["min_event_spacing_s"] < min(c["deadline_s"][0] for c in tasks["classes"]),
            "minimum event spacing must be below the smallest deadline")
    require(close(sum(c["probability"] for c in tasks["classes"]), 1), "task probabilities must sum to one")
    require([c["id"] for c in tasks["classes"]] == ["light", "medium", "heavy"], "task class order must be light, medium, heavy")
    for task_class in tasks["classes"]:
        for key in ("cpu_mi", "input_mib", "deadline_s"):
            require(task_class[key][0] <= task_class[key][1], f"{task_class['id']}.{key}: reversed bounds")
    require(close(max(c["deadline_s"][1] for c in tasks["classes"]), timing["deadline_max_s"]), "Dmax does not match task classes")
    require(topology["iot_count"] == topology["iot_per_access_fog"] * len(topology["fogs"]), "IoT access mapping is inconsistent")
    require([n["id"] for n in topology["fogs"]] == [f"F{i}" for i in range(1, 6)], "fog IDs/order must be F1..F5")
    require(topology["iot"]["id"] == "IoT" and topology["cloud"]["id"] == "cloud", "invalid IoT/cloud IDs")
    for node in [topology["iot"], *topology["fogs"], topology["cloud"]]:
        require(node["busy_w"] >= node["idle_w"], f"{node['id']}: busy power is below idle power")
        max_input = math.ceil(max(c["input_mib"][1] for c in tasks["classes"]) * 2**20)
        ram = tasks["working_set_bytes"] + max_input + math.ceil(tasks["output_fraction"] * max_input)
        require(node["ram_bytes"] >= ram, f"{node['id']}: RAM cannot admit even one maximum-size task")
    if topology["fog_mode"] == "homogeneous":
        profiles = [{k: v for k, v in n.items() if k != "id"} for n in topology["fogs"]]
        require(all(p == profiles[2] for p in profiles), "homogeneous mode requires all fog profiles equal to F3")
    for name, segments in config["workloads"].items():
        boundary = 0.0
        for segment in segments:
            require(close(segment["start_s"], boundary), f"workloads.{name}: gap or overlap")
            require(segment["end_s"] > segment["start_s"], f"workloads.{name}: empty interval")
            boundary = segment["end_s"]
        require(close(boundary, timing["arrival_window_s"]), f"workloads.{name}: must cover [0,T)")
    for name, duplex in (("access", "half"), ("lan", "full"), ("wan", "full")):
        require(config["network"][name]["duplex"] == duplex, f"network.{name}: wrong duplex")
    evaluation, observation = config["evaluation"], config["observation"]
    require(close(evaluation["imbalance_reference"], math.sqrt(.24)), "imbalance reference must be sqrt(0.24)")
    require(evaluation["latency_reference_s"] >= timing["timeout_factor"] * timing["deadline_max_s"], "main latency reference below maximum successful service time")
    require(evaluation["failure_latency_penalty_s"] == evaluation["latency_reference_s"], "main failure penalty must equal latency reference")
    # Scales are part of the observation contract, not guessed from each run.
    nodes = [topology["iot"], *topology["fogs"], topology["cloud"]]
    require(max(n["mips_per_pe"] for n in nodes) <= observation["mips_reference"], "node MIPS exceeds observation reference")
    require(max(n["pes"] for n in nodes) <= observation["pes_reference"], "node PE count exceeds observation reference")
    ppo, search, training = (config[k] for k in ("ppo", "search", "training"))
    rollout = ppo["n_steps"] * ppo["environments"]
    require(rollout % ppo["batch_size"] == 0, "PPO rollout must be divisible by batch size")
    for key, budget in training.items():
        if key.endswith("_decisions"):
            require(budget % rollout == 0, f"training.{key} must be a multiple of rollout")
    require(training["checkpoint_decisions"] <= training["final_decisions"], "checkpoint exceeds final budget")
    require(search["population"] >= 2, "search population must accommodate equal and manual anchors")
    require(search["candidate_slots"] == search["population"] * search["generations_including_initial"], "candidate slot accounting mismatch")
    for key in ("equal_weights", "manual_weights"):
        weights = search[key]
        require(close(sum(weights), 1) and min(weights) >= search["weight_floor"], f"search.{key}: invalid bounded simplex")
    require(close(search["mutation_probability_per_variable"], 1 / 5), "mutation variable probability must be 1/5")
    seeds = config["seeds"]
    for key in ("calibration_trace_ids", "validation_trace_ids", "test_trace_ids"):
        require(seeds[key][0] <= seeds[key][1], f"seeds.{key}: reversed inclusive range")
    require(seeds["validation_trace_ids"][1] - seeds["validation_trace_ids"][0] + 1 == search["validation_traces_per_workload"], "validation trace count mismatch")
    require(min(seeds["pilot_outer_ids"]) >= seeds["outer_runs"], "pilot outer IDs overlap confirmatory outer runs")
    ladder = config["pilot"]["candidate_budget_ladder"]
    require(ladder == sorted(set(ladder)) and all(k % rollout == 0 for k in ladder), "candidate ladder must be increasing unique rollout multiples")
    require(training["candidate_decisions"] in ladder, "candidate budget is absent from fidelity ladder")
    require(config["execution"]["heartbeat_wall_s"] < config["execution"]["rpc_timeout_wall_s"], "heartbeat must precede RPC timeout")
    return config


def load_config(path=DEFAULT_CONFIG):
    return validate_config(read_json(path))
