"""Schema and cross-field checks for exported records, not a simulator."""

import math
from functools import lru_cache

from jsonschema import Draft202012Validator

from .config import close, require, sha256, validate_json
from .schema_definitions import EVENT_PRIORITIES, contract_schema


def trace_payload_sha256(trace):
    """Hash the complete envelope excluding its own payload_sha256 field."""
    return sha256({k: v for k, v in trace.items() if k != "payload_sha256"})


@lru_cache(maxsize=None)
def _validator(kind):
    root = contract_schema()
    if kind not in root["$defs"]:
        raise ValueError(f"Unknown contract kind: {kind}")
    return Draft202012Validator({**root, "$ref": f"#/$defs/{kind}"})


def _task_semantics(value, config):
    require(value["access_fog"] == value["source_iot"] // 20 + 1, "task source/access fog mismatch")
    require(value["timeout_relative_s"] > value["deadline_relative_s"], "timeout must exceed soft deadline")
    if config:
        require(value["arrival_s"] < config["timing"]["arrival_window_s"], "arrival must be in [0,T)")
        require(close(value["timeout_relative_s"], config["timing"]["timeout_factor"] * value["deadline_relative_s"]), "task timeout factor mismatch")
        require(value["output_bytes"] == math.ceil(config["tasks"]["output_fraction"] * value["input_bytes"]), "task output byte count mismatch")
        require(value["working_set_bytes"] == config["tasks"]["working_set_bytes"], "task working set mismatch")
        profile = next(c for c in config["tasks"]["classes"] if c["id"] == value["class_id"])
        require(profile["cpu_mi"][0] <= value["cpu_mi"] <= profile["cpu_mi"][1], "task MI outside class bounds")
        require(math.ceil(profile["input_mib"][0] * 2**20) <= value["input_bytes"] <=
                math.ceil(profile["input_mib"][1] * 2**20), "task input outside class bounds")
        require(profile["deadline_s"][0] <= value["deadline_relative_s"] <= profile["deadline_s"][1], "task deadline outside class bounds")


def validate_contract(kind, value, config=None):
    validate_json(value, _validator(kind))
    if kind == "task":
        _task_semantics(value, config)
    elif kind == "event":
        require(value["priority"] == EVENT_PRIORITIES[value["kind"]], "event priority does not match kind")
        require((value["task_id"] is None) == (value["kind"] == "HORIZON"), "only HORIZON has no task ID")
    elif kind == "outcome":
        success = value["terminal"] != "FAILED"
        require((value["failure_reason"] is None) == success, "failure reason inconsistent with terminal state")
        require((value["result_received_s"] is not None) == success, "success must have result receipt; failure must not")
        require(value["deadline_violated"] == (value["terminal"] != "ON_TIME"), "deadline flag inconsistent with outcome")
        if success:
            require(close(value["at_s"], value["result_received_s"]), "terminal success time must be receipt time")
    elif kind == "resource":
        require(value["busy_w"] >= value["idle_w"], "resource busy power below idle power")
    elif kind == "cost_vector":
        require(value["out_of_reference"] == any(v > 1 for v in value["values"]), "cost out_of_reference flag mismatch")
    elif kind == "route":
        require((not value["input_hops"] and not value["result_hops"]) == (value["action"] == 0), "only local action has an empty route")
        incoming, outgoing = value["input_hops"], value["result_hops"]
        require(len(incoming) == len(outgoing), "input/result path hop counts differ")
        for hops in (incoming, outgoing):
            require(all(a["to_id"] == b["from_id"] for a, b in zip(hops, hops[1:])), "disconnected route")
        require([(h["to_id"], h["from_id"]) for h in reversed(incoming)] ==
                [(h["from_id"], h["to_id"]) for h in outgoing], "result path must reverse input path")
    elif kind == "trace":
        require(value["task_count"] == len(value["tasks"]), "trace task_count mismatch")
        require(value["horizon_s"] > value["arrival_window_s"], "trace horizon must exceed arrival window")
        require(value["payload_sha256"] == trace_payload_sha256(value), "trace payload hash mismatch")
        if config:
            require(value["config_sha256"] == sha256(config), "trace config hash mismatch")
            require(close(value["arrival_window_s"], config["timing"]["arrival_window_s"]) and close(value["horizon_s"], config["timing"]["horizon_s"]), "trace/config time mismatch")
        keys = []
        for task in value["tasks"]:
            # The root trace schema already validated each task. Reuse semantic
            # checks without repeating JSON Schema for every task in large traces.
            _task_semantics(task, config)
            require(task["arrival_s"] < value["arrival_window_s"], "arrival outside trace window")
            require(task["arrival_s"] + task["timeout_relative_s"] <= value["horizon_s"], "task may outlive horizon")
            keys.append((task["arrival_s"], task["task_id"]))
        require(keys == sorted(keys), "trace tasks must be ordered by arrival and ID")
        require(len({t["task_id"] for t in value["tasks"]}) == len(keys), "duplicate task IDs")
        namespace = value["seed_namespace"]
        training = namespace["split"] in ("pilot_train", "train_candidate", "train_final")
        require((namespace["outer_run"] is not None) == training and
                (namespace["model_repeat"] is not None) == training, "outer/model namespace fields belong only to training splits")
    elif kind == "manifest" and value["status"] == "complete":
        require(value["invariants_valid"] and bool(value["artifacts"]), "complete manifest requires validated artifacts")
    elif kind == "rpc_request":
        require((value["action"] is not None) == (value["operation"] == "step"), "only step requests carry an action")
    return value
