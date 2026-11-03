import copy
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

from jsonschema import Draft202012Validator

from research_v2.__main__ import export_documents
from research_v2.config import ContractError, ROOT, canonical_bytes, load_config, read_json, sha256, validate_config
from research_v2.contracts import trace_payload_sha256, validate_contract
from research_v2.schema_definitions import config_schema, contract_schema, wire_contract


def task(task_id=0, arrival=0):
    return {"task_id": task_id, "source_iot": 0, "access_fog": 1, "class_id": "light",
            "arrival_s": arrival, "cpu_mi": 100, "input_bytes": 100000, "output_bytes": 5000,
            "deadline_relative_s": .5, "timeout_relative_s": 1.5, "working_set_bytes": 67108864}


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_default_design_and_analytical_load(self):
        config = self.config
        self.assertEqual(sum(f["pes"] * f["mips_per_pe"] for f in config["topology"]["fogs"]), 14000)
        self.assertEqual(sum(c["probability"] * sum(c["cpu_mi"]) / 2 for c in config["tasks"]["classes"]), 700)
        counts = {w: sum((s["end_s"] - s["start_s"]) * s["rate_per_s"] for s in segments)
                  for w, segments in config["workloads"].items()}
        self.assertEqual(counts, {"light": 300, "moderate": 900, "heavy": 1800, "dynamic": 900})
        self.assertNotEqual(config["workloads"]["moderate"], config["workloads"]["dynamic"])

    def test_invalid_configuration_stops_before_run(self):
        cases = [
            (("units", "time"), "ms"), (("units", "data"), "MiB"),
            (("timing", "horizon_s"), 60), (("timing", "timeout_factor"), 1),
            (("timing", "comparison_epsilon_s"), .1), (("timing", "arrival_window_s"), float("nan")),
            (("topology", "iot_count"), 99), (("topology", "overbooking"), True),
            (("topology", "iot", "pes"), True), (("topology", "iot", "busy_w"), .1),
            (("topology", "iot", "ram_bytes"), 1024), (("topology", "fog_mode"), "homogeneous"),
            (("network", "access", "duplex"), "full"), (("network", "wan", "bandwidth_bit_per_s"), 0),
            (("evaluation", "weights"), [.4, .2, .2, .1, .1]), (("evaluation", "latency_reference_s"), 3),
            (("evaluation", "clip_costs"), True), (("observation", "dimension"), 46),
            (("ppo", "gamma"), .99), (("ppo", "batch_size"), 127),
            (("training", "candidate_decisions"), 5000), (("training", "checkpoint_decisions"), 204800),
            (("search", "candidate_slots"), 79), (("search", "manual_weights"), [.01, .2, .2, .2, .39]),
            (("search", "manual_weights"), [.2] * 4), (("seeds", "pilot_outer_ids"), [0, 1, 2]),
            (("seeds", "validation_trace_ids"), [10000, 10005]), (("seeds", "test_trace_ids"), [10, 0]),
            (("pilot", "candidate_budget_ladder"), [5120, 5120]), (("execution", "python_fallback"), True),
            (("execution", "rpc_timeout_wall_s"), 5), (("execution", "output_namespace"), "results/legacy"),
        ]
        for path, value in cases:
            with self.subTest(path=path, value=value):
                config = copy.deepcopy(self.config)
                parent = config
                for key in path[:-1]:
                    parent = parent[key]
                parent[path[-1]] = value
                with self.assertRaises(ContractError):
                    validate_config(config)

    def test_gaps_ranges_probabilities_and_unknown_fields(self):
        changes = [lambda c: c["tasks"]["classes"][0].update(probability=.6),
                   lambda c: c["tasks"]["classes"][0].update(cpu_mi=[300, 100]),
                   lambda c: c["workloads"]["dynamic"][1].update(start_s=16),
                   lambda c: c["workloads"]["heavy"][0].update(end_s=59),
                   lambda c: c["topology"]["fogs"][0].update(id="F2"),
                   lambda c: c.update(unrecognized=True)]
        for change in changes:
            config = copy.deepcopy(self.config)
            change(config)
            with self.assertRaises(ContractError):
                validate_config(config)

    def test_homogeneous_control_uses_equal_profiles(self):
        config = copy.deepcopy(self.config)
        config["topology"]["fog_mode"] = "homogeneous"
        anchor = config["topology"]["fogs"][2]
        config["topology"]["fogs"] = [{**anchor, "id": f"F{i}"} for i in range(1, 6)]
        validate_config(config)

    def test_reject_ambiguous_json_and_nonfinite_overflow(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            for text in ('{"a":1,"a":2}', '{"a":NaN}'):
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(ContractError):
                    read_json(path)
            config = copy.deepcopy(self.config)
            config["timing"]["horizon_s"] = math.inf
            with self.assertRaises(ContractError):
                validate_config(config)

    def test_hash_is_order_independent_and_time_roundtrips(self):
        self.assertEqual(sha256({"a": 1, "b": 2}), sha256({"b": 2, "a": 1}))
        value = .4194304
        self.assertEqual(json.loads(canonical_bytes({"at_s": value}))["at_s"], value)
        self.assertNotEqual(sha256(self.config), sha256({**self.config, "parameter_origin": "changed"}))

    def test_schema_exports_and_vocabulary_are_valid(self):
        Draft202012Validator.check_schema(config_schema())
        Draft202012Validator.check_schema(contract_schema())
        for path, expected in export_documents().items():
            self.assertEqual(read_json(path), expected, str(path))
        wire = wire_contract()
        self.assertEqual(len(wire["observation_features"]), 108)
        self.assertEqual(len(set(wire["observation_features"])), 108)
        self.assertEqual(wire["actions"], ["source_iot", "F1", "F2", "F3", "F4", "F5", "cloud"])
        self.assertEqual(wire["objective_order"], self.config["evaluation"]["objective_order"])
        self.assertEqual(wire["observation_features"][91:99], ["task.cpu_mi", "task.input_bytes", "task.output_bytes",
            "task.deadline_relative_s", "task.timeout_relative_s", "task.class.light", "task.class.medium", "task.class.heavy"])


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_task_units_mapping_and_deadline(self):
        validate_contract("task", task(), self.config)
        for updates in ({"source_iot": 20}, {"cpu_mi": 1.5}, {"input_bytes": -1},
                        {"timeout_relative_s": .4}, {"arrival_s": 60}, {"output_bytes": 5001}):
            with self.subTest(updates=updates), self.assertRaises(ContractError):
                validate_contract("task", {**task(), **updates}, self.config)

    def test_event_priority_and_horizon(self):
        event = {"episode_id": "fixture", "task_id": 0, "at_s": .5, "kind": "RESULT_DELIVERED",
                 "priority": 0, "sequence": 1, "generation": 0, "resource_id": "iot:0"}
        validate_contract("event", event)
        with self.assertRaises(ContractError):
            validate_contract("event", {**event, "priority": 2})
        with self.assertRaises(ContractError):
            validate_contract("event", {**event, "task_id": None})
        validate_contract("event", {**event, "kind": "HORIZON", "task_id": None, "priority": 3})

    def test_late_success_is_success_and_failure_is_always_violation(self):
        outcome = {"episode_id": "fixture", "task_id": 0, "terminal": "LATE_SUCCESS", "failure_reason": None,
                   "at_s": 1., "result_received_s": 1., "dynamic_energy_j": .4, "deadline_violated": True}
        validate_contract("outcome", outcome)
        validate_contract("outcome", {**outcome, "terminal": "FAILED", "failure_reason": "SERVICE_TIMEOUT", "result_received_s": None})
        for updates in ({"deadline_violated": False}, {"terminal": "FAILED"}, {"at_s": 2.}):
            with self.subTest(updates=updates), self.assertRaises(ContractError):
                validate_contract("outcome", {**outcome, **updates})

    def trace(self):
        trace = {"schema_version": "research-v2.1", "config_sha256": sha256(self.config), "payload_sha256": "0" * 64,
                 "seed_namespace": {"master": 20261103, "split": "calibration", "outer_run": None,
                                    "model_repeat": None, "trace_id": 0, "workload": "light"},
                 "arrival_window_s": 60., "horizon_s": 69., "task_count": 2,
                 "tasks": [task(0, 0), task(1, .1)]}
        trace["payload_sha256"] = trace_payload_sha256(trace)
        return trace

    def test_trace_tampering_empty_unordered_and_duplicate_tasks_rejected(self):
        validate_contract("trace", self.trace(), self.config)
        trace = self.trace()
        trace["tasks"][0]["cpu_mi"] += 1
        with self.assertRaisesRegex(ContractError, "hash mismatch"):
            validate_contract("trace", trace, self.config)
        for tasks in ([], [task(), task()], [task(1, 1), task(0, 0)]):
            trace = self.trace()
            trace.update(tasks=tasks, task_count=len(tasks))
            trace["payload_sha256"] = trace_payload_sha256(trace)
            with self.assertRaises(ContractError):
                validate_contract("trace", trace, self.config)

    def test_route_must_be_connected_reversed_and_nonempty_for_offload(self):
        hop = {"link_id": "wireless:F1", "from_id": "iot:0", "to_id": "F1",
               "bandwidth_bit_per_s": 20000000, "propagation_s": .002,
               "server_id": "wireless:F1:shared", "queue_waiting": 64}
        route = {"source_iot": 0, "action": 1, "input_hops": [hop],
                 "result_hops": [{**hop, "from_id": "F1", "to_id": "iot:0"}]}
        validate_contract("route", route)
        with self.assertRaises(ContractError):
            validate_contract("route", {**route, "result_hops": [hop]})
        validate_contract("route", {**route, "action": 0, "input_hops": [], "result_hops": []})
        with self.assertRaises(ContractError):
            validate_contract("route", {**route, "input_hops": [], "result_hops": []})

    def test_costs_keep_out_of_reference_visible(self):
        costs = {"objective_order": self.config["evaluation"]["objective_order"], "values": [1.1, 0, 0, 0, 0], "out_of_reference": True}
        validate_contract("cost_vector", costs)
        with self.assertRaises(ContractError):
            validate_contract("cost_vector", {**costs, "out_of_reference": False})

    def test_complete_manifest_cannot_hide_missing_validation(self):
        manifest = {"schema_version": "research-v2.1", "study_id": "fixture", "run_id": "r0", "status": "complete",
                    "attempt": 1, "source_sha256": "0" * 64, "config_sha256": "0" * 64,
                    "build_sha256": "0" * 64, "trace_sha256": ["0" * 64],
                    "artifacts": {"outcomes.jsonl": "1" * 64}, "invariants_valid": True}
        validate_contract("manifest", manifest)
        for update in ({"invariants_valid": False}, {"artifacts": {}}):
            with self.assertRaises(ContractError):
                validate_contract("manifest", {**manifest, **update})

    def test_rpc_step_only_carries_action(self):
        rpc = {"schema_version": "research-v2.1", "request_id": "r0", "episode_id": "e0", "config_sha256": "0" * 64,
               "trace_sha256": "0" * 64, "operation": "reset", "action": None}
        validate_contract("rpc_request", rpc)
        validate_contract("rpc_request", {**rpc, "operation": "step", "action": 6})
        for update in ({"action": 0}, {"operation": "step"}, {"operation": "step", "action": 7}):
            with self.assertRaises(ContractError):
                validate_contract("rpc_request", {**rpc, **update})


def java_executable():
    if os.environ.get("JAVA_HOME"):
        path = Path(os.environ["JAVA_HOME"]) / "bin" / ("java.exe" if os.name == "nt" else "java")
        return str(path) if path.exists() else None
    return shutil.which("java")


@unittest.skipUnless(java_executable(), "Set JAVA_HOME for P00 Java integration checks")
class JavaFoundationTests(unittest.TestCase):
    def setUp(self):
        self.jar = ROOT / "ifogsim/dist/research-v2-foundation.jar"
        self.assertTrue(self.jar.exists(), "Build the v2 foundation JAR first")

    def test_java_contract_equals_python_from_unrelated_directory(self):
        with tempfile.TemporaryDirectory(prefix="p00 space ") as temporary:
            result = subprocess.run([java_executable(), "-jar", str(self.jar), "--describe"], cwd=temporary,
                                    capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout), wire_contract())
        with zipfile.ZipFile(self.jar) as archive:
            self.assertEqual(int.from_bytes(archive.read("org/fog/erwo/v2/FoundationMain.class")[6:8], "big"), 65)

    def test_native_event_probe_and_unimplemented_server_exit(self):
        result = subprocess.run([java_executable(), "-jar", str(self.jar), "--self-test"], capture_output=True, text=True, check=True)
        probe = json.loads(result.stdout)
        self.assertEqual(probe["status"], "pass")
        self.assertEqual(probe["sequential_episodes"], 2)
        self.assertEqual(probe["idle_probe_energy_j"], 34.5)
        self.assertFalse(probe["native_cancel_releases_used_pes"])
        missing = subprocess.run([java_executable(), "-jar", str(self.jar), "5555"], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)
        self.assertIn("not implemented", missing.stderr)


if __name__ == "__main__":
    unittest.main()
