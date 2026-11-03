"""Immutable external traces: six independent SHA-256/PCG64 streams.

P01 performs no scheduling, policy inference, offloading or outcome simulation.
"""

from dataclasses import dataclass
import json
import math

import numpy as np

from . import SCHEMA_VERSION
from .config import canonical_bytes, require, sha256, validate_config
from .contracts import trace_payload_sha256, validate_contract
from .schema_definitions import COMPONENTS
from .trace_access import TraceKey, authorize, key_from_dict

GENERATOR_VERSION = "research-v2.trace-1"


def access_fog(source_iot):
    require(type(source_iot) is int and 0 <= source_iot < 100, "source_iot must be integer 0..99")
    return source_iot // 20 + 1


def arrival_times(segments, rng):
    """Invert cumulative hazard of a unit-rate Poisson process.

    A hazard increment crossing a rate boundary keeps its residual; no extra
    arrival or fresh exponential draw is inserted at the boundary. Arrival
    intervals are [start,end), including an exact boundary at the next segment.
    """
    masses = [(s["end_s"] - s["start_s"]) * s["rate_per_s"] for s in segments]
    boundaries = [math.fsum(masses[:i + 1]) for i in range(len(masses))]
    total_hazard = boundaries[-1]
    hazard, left_hazard, index = 0.0, 0.0, 0
    while True:
        increment = float(rng.exponential())
        require(math.isfinite(increment) and increment > 0, "Nonpositive/nonfinite Poisson hazard; stop without resampling")
        following = hazard + increment
        require(following > hazard, "Poisson hazard lost numerical progress")
        hazard = following
        if hazard >= total_hazard:
            return
        while True:
            segment = segments[index]
            right_hazard = boundaries[index]
            if hazard < right_hazard:
                break
            index += 1
            left_hazard = right_hazard
        at = segment["start_s"] + (hazard - left_hazard) / segment["rate_per_s"]
        require(segment["start_s"] <= at < segment["end_s"], "Arrival inversion exceeded numeric segment bounds")
        yield float(at)


@dataclass(frozen=True, slots=True)
class Trace:
    """Canonical bytes are immutable; to_dict returns an independent copy."""
    _data: bytes

    @classmethod
    def from_dict(cls, value, config):
        validate_contract("trace", value, config)
        key_from_dict(value["seed_namespace"], config)
        return cls(canonical_bytes(value))

    def to_dict(self):
        return json.loads(self._data)

    @property
    def canonical_json(self):
        return self._data

    @property
    def payload_sha256(self):
        return self.to_dict()["payload_sha256"]

    @property
    def task_count(self):
        return self.to_dict()["task_count"]


class TraceGenerator:
    def __init__(self, config):
        validate_config(config)
        # Caller changes after construction cannot mutate generator parameters.
        self._config = canonical_bytes(config)

    @property
    def config(self):
        return json.loads(self._config)

    def generate(self, key: TraceKey, *, role: str):
        config = self.config
        key.validate(config)
        authorize(role, key.split, "generate")
        rng = {name: np.random.Generator(np.random.PCG64(key.seed(name))) for name in COMPONENTS}
        classes = config["tasks"]["classes"]
        probabilities = [c["probability"] for c in classes]
        tasks = []
        for task_id, at in enumerate(arrival_times(config["workloads"][key.workload], rng["arrival"])):
            profile = classes[int(rng["class"].choice(len(classes), p=probabilities))]
            source = int(rng["source"].integers(0, config["topology"]["iot_count"]))
            cpu = int(rng["cpu_mi"].integers(profile["cpu_mi"][0], profile["cpu_mi"][1] + 1))
            size = math.ceil(float(rng["input_bytes"].uniform(*profile["input_mib"])) * 2**20)
            deadline = float(rng["deadline"].uniform(*profile["deadline_s"]))
            tasks.append({"task_id": task_id, "source_iot": source, "access_fog": access_fog(source),
                          "class_id": profile["id"], "arrival_s": at, "cpu_mi": cpu,
                          "input_bytes": size, "output_bytes": math.ceil(config["tasks"]["output_fraction"] * size),
                          "deadline_relative_s": deadline, "timeout_relative_s": config["timing"]["timeout_factor"] * deadline,
                          "working_set_bytes": config["tasks"]["working_set_bytes"]})
        require(bool(tasks), "N=0 trace rejected; no resampling or forced task")
        trace = {"schema_version": SCHEMA_VERSION, "config_sha256": sha256(config), "payload_sha256": "0" * 64,
                 "seed_namespace": key.to_dict(), "arrival_window_s": config["timing"]["arrival_window_s"],
                 "horizon_s": config["timing"]["horizon_s"], "task_count": len(tasks), "tasks": tasks}
        trace["payload_sha256"] = trace_payload_sha256(trace)
        return Trace.from_dict(trace, config)
