"""Handwritten deterministic inputs; never substitute these for random workloads."""

import math

from . import SCHEMA_VERSION
from .config import require, sha256
from .contracts import trace_payload_sha256
from .traces import Trace, access_fog


def boundary_fixture(config):
    require(config["timing"]["arrival_window_s"] == 60 and config["timing"]["timeout_factor"] == 3,
            "Boundary fixture is defined for the default T60/k3 protocol")
    tasks = []
    # Simultaneous arrivals, source/access boundaries, exact phase boundary,
    # and a maximum deadline immediately before the end of the arrival window.
    for task_id, (source, at, class_id) in enumerate([(0, 0., "light"), (19, 0., "light"),
                                                     (20, 15., "light"), (99, 59.999999, "heavy")]):
        profile = next(c for c in config["tasks"]["classes"] if c["id"] == class_id)
        size = math.ceil(profile["input_mib"][0] * 2**20)
        deadline = .5 if class_id == "light" else 3.
        tasks.append({"task_id": task_id, "source_iot": source, "access_fog": access_fog(source),
                      "class_id": class_id, "arrival_s": at, "cpu_mi": profile["cpu_mi"][0],
                      "input_bytes": size, "output_bytes": math.ceil(config["tasks"]["output_fraction"] * size),
                      "deadline_relative_s": deadline, "timeout_relative_s": deadline * config["timing"]["timeout_factor"],
                      "working_set_bytes": config["tasks"]["working_set_bytes"]})
    trace = {"schema_version": SCHEMA_VERSION, "config_sha256": sha256(config), "payload_sha256": "0" * 64,
             "seed_namespace": {"master": config["seeds"]["master"], "split": "calibration", "outer_run": None,
                                "model_repeat": None, "trace_id": 0, "workload": "dynamic"},
             "arrival_window_s": config["timing"]["arrival_window_s"], "horizon_s": config["timing"]["horizon_s"],
             "task_count": len(tasks), "tasks": tasks}
    trace["payload_sha256"] = trace_payload_sha256(trace)
    return Trace.from_dict(trace, config)


def fixture_expectations():
    return {"kind": "handwritten_fixture_not_workload_sample", "arrival_order": [0, 1, 2, 3],
            "source_access_fogs": [1, 1, 2, 5], "simultaneous_arrival_ids": [0, 1],
            "task_0_boundary_cases": [
                {"hypothetical_receipt_s": .5, "expected_terminal": "ON_TIME"},
                {"hypothetical_receipt_s": .500001, "expected_terminal": "LATE_SUCCESS"},
                {"hypothetical_receipt_s": 1.5, "expected_terminal": "LATE_SUCCESS"},
                {"hypothetical_receipt_s": 1.500001, "expected_terminal": "FAILED", "reason": "SERVICE_TIMEOUT"}],
            "scope": "Expected outcomes for P02; P01 does not execute tasks or claim these outcomes observed"}
