from dataclasses import FrozenInstanceError, replace
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from jsonschema import Draft202012Validator

from research_v2.config import ContractError, ROOT, canonical_bytes, load_config, read_json
from research_v2.trace_access import TraceKey, authorize
from research_v2.trace_fixtures import boundary_fixture, fixture_expectations
from research_v2.trace_report import calibration_report, describe_trace
from research_v2.trace_store import read_bundle, write_bundle
from research_v2.traces import Trace, TraceGenerator, access_fog, arrival_times
from research_v2.schema_definitions import COMPONENTS, trace_bundle_schema


def key(split="calibration", workload="light", trace_id=0, outer_run=None, model_repeat=None):
    return TraceKey(20261103, split, outer_run, model_repeat, trace_id, workload)


class SeedAndAccessTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_seed_known_vector_and_component_namespaces(self):
        example = key()
        self.assertEqual(example.seed_text("arrival"), "20261103|calibration|-|-|0|light|arrival")
        self.assertEqual(example.seed("arrival"), 10715774301338505746)
        self.assertEqual(example.seed("arrival"), int.from_bytes(hashlib.sha256(b"20261103|calibration|-|-|0|light|arrival").digest()[:8], "little"))
        self.assertEqual(len({example.seed(c) for c in COMPONENTS}), 6)
        self.assertNotEqual(example.seed("arrival"), replace(example, workload="dynamic").seed("arrival"))

    def test_distinct_pilot_validation_candidate_and_final_streams(self):
        examples = [key("pilot_validation", trace_id=10000), key("validation", trace_id=10000),
                    key("pilot_train", outer_run=100, model_repeat=0),
                    key("train_candidate", outer_run=0, model_repeat=0),
                    key("train_candidate", outer_run=0, model_repeat=1),
                    key("train_final", outer_run=0, model_repeat=0)]
        for example in examples:
            example.validate(self.config)
        self.assertEqual(len({k.seed("arrival") for k in examples}), len(examples))

    def test_invalid_ids_and_namespace_fields(self):
        invalid = [replace(key(), master=1), replace(key(), trace_id=True), replace(key(), trace_id=20),
                   replace(key(), outer_run=0), key("validation", trace_id=0), key("test", trace_id=2000),
                   key("pilot_train", outer_run=0, model_repeat=0), key("train_candidate", outer_run=100, model_repeat=0),
                   key("train_candidate", outer_run=0, model_repeat=2), key("train_final", outer_run=0, model_repeat=1),
                   key("train_final", outer_run=0, model_repeat=None)]
        for example in invalid:
            with self.subTest(key=example), self.assertRaises(ContractError):
                example.validate(self.config)

    def test_role_cannot_cross_split_and_holdout_has_no_reader(self):
        pairs = [("calibrator", "validation"), ("candidate_trainer", "test"), ("final_trainer", "validation"),
                 ("search_validator", "test"), ("pilot_validator", "validation")]
        for role, split in pairs:
            with self.subTest(role=role, split=split), self.assertRaises(ContractError):
                authorize(role, split, "generate")
        authorize("holdout_preparer", "test", "generate")
        for operation in ("read", "describe"):
            with self.assertRaisesRegex(ContractError, "sealed"):
                authorize("holdout_preparer", "test", operation)


class ArrivalTests(unittest.TestCase):
    def test_homogeneous_inversion_and_no_forced_time_zero(self):
        class FixedHazards:
            def __init__(self):
                self.draws = iter([.5, .5, 1.])
            def exponential(self):
                return next(self.draws)
        actual = list(arrival_times([{"start_s": 0, "end_s": 1, "rate_per_s": 2}], FixedHazards()))
        self.assertEqual(actual, [.25, .5])  # Last hazard falls exactly at T: excluded.

    def test_hazard_residual_survives_rate_boundary(self):
        class FixedHazards:
            def __init__(self):
                self.draws = iter([.5, 2.5, 2, 1])
            def exponential(self):
                return next(self.draws)
        actual = list(arrival_times([{"start_s": 0, "end_s": 1, "rate_per_s": 2},
                                    {"start_s": 1, "end_s": 2, "rate_per_s": 4}], FixedHazards()))
        self.assertEqual(actual, [.25, 1.25, 1.75])
        self.assertNotIn(1., actual)

    def test_exact_boundary_is_natural_arrival_not_extra_task(self):
        class FixedHazards:
            def __init__(self):
                self.draws = iter([2., 4.])
            def exponential(self):
                return next(self.draws)
        actual = list(arrival_times([{"start_s": 0, "end_s": 1, "rate_per_s": 2},
                                    {"start_s": 1, "end_s": 2, "rate_per_s": 4}], FixedHazards()))
        self.assertEqual(actual, [1.])

    def test_multiple_crossings_preserve_one_hazard_draw(self):
        class FixedHazards:
            def __init__(self):
                self.draws = iter([4.5, 10.])
            def exponential(self):
                return next(self.draws)
        segments = [{"start_s": 0, "end_s": 1, "rate_per_s": 1},
                    {"start_s": 1, "end_s": 2, "rate_per_s": 2},
                    {"start_s": 2, "end_s": 3, "rate_per_s": 3}]
        self.assertEqual(list(arrival_times(segments, FixedHazards())), [2.5])


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.generator = TraceGenerator(self.config)

    def test_golden_trace_across_process_restart(self):
        expected = "837b180f9a354ef413c68efba3de4de1657d25142e50d0931c6b266e8d34babd"
        trace = self.generator.generate(key(), role="calibrator")
        self.assertEqual(trace.task_count, 328)
        self.assertEqual(trace.payload_sha256, expected)
        code = ("from research_v2.config import load_config; from research_v2.traces import TraceGenerator; "
                "from research_v2.trace_access import TraceKey; "
                "print(TraceGenerator(load_config()).generate(TraceKey(20261103,'calibration',None,None,0,'light'),role='calibrator').payload_sha256)")
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.strip(), expected)

    def test_policy_rng_method_order_and_rewards_do_not_change_trace(self):
        original = self.generator.generate(key(), role="calibrator")
        for method in ("PPO-Equal", "NSGA-II", "RandomSearch", "LeastFog"):
            np.random.default_rng(len(method)).integers(0, 7, size=1000)
            self.assertEqual(self.generator.generate(key(), role="calibrator").canonical_json, original.canonical_json)

    def test_reward_configuration_cannot_change_external_task_stream(self):
        original = self.generator.generate(key(), role="calibrator").to_dict()
        self.config["reward"]["scale"] = 200.
        self.config["search"]["manual_weights"] = [.2] * 5
        modified = TraceGenerator(self.config).generate(key(), role="calibrator").to_dict()
        self.assertEqual(modified["tasks"], original["tasks"])
        self.assertEqual(modified["seed_namespace"], original["seed_namespace"])
        # Full-protocol identity still changes for audit even though tasks do not.
        self.assertNotEqual(modified["config_sha256"], original["config_sha256"])

    def test_generator_leaves_numpy_global_rng_untouched(self):
        state = np.random.get_state()
        self.generator.generate(key(), role="calibrator")
        following = np.random.get_state()
        self.assertEqual(state[0], following[0])
        self.assertTrue(np.array_equal(state[1], following[1]))
        self.assertEqual(state[2:], following[2:])

    def test_component_streams_isolate_cpu_parameter_changes(self):
        original = self.generator.generate(key(), role="calibrator").to_dict()["tasks"]
        self.config["tasks"]["classes"][0]["cpu_mi"] = [110, 310]
        modified = TraceGenerator(self.config).generate(key(), role="calibrator").to_dict()["tasks"]
        for before, after in zip(original, modified):
            self.assertEqual({k: v for k, v in before.items() if k != "cpu_mi"},
                             {k: v for k, v in after.items() if k != "cpu_mi"})
        self.assertTrue(any(a["cpu_mi"] != b["cpu_mi"] for a, b in zip(original, modified)))

    def test_frozen_trace_and_generator_config_snapshot(self):
        trace = self.generator.generate(key(), role="calibrator")
        copy = trace.to_dict()
        copy["tasks"][0]["cpu_mi"] = -1
        self.config["tasks"]["classes"][0]["cpu_mi"] = [1, 1]
        self.assertEqual(self.generator.generate(key(), role="calibrator").canonical_json, trace.canonical_json)
        self.assertGreater(trace.to_dict()["tasks"][0]["cpu_mi"], 0)
        with self.assertRaises(FrozenInstanceError):
            trace._data = b"modified"

    def test_source_mapping_and_each_attribute_in_bounds(self):
        self.assertEqual([access_fog(i) for i in (0, 19, 20, 99)], [1, 1, 2, 5])
        for bad in (-1, 100, True, 2.5):
            with self.assertRaises(ContractError):
                access_fog(bad)
        for workload in ("light", "moderate", "heavy", "dynamic"):
            tasks = self.generator.generate(key(workload=workload), role="calibrator").to_dict()["tasks"]
            self.assertEqual([t["task_id"] for t in tasks], list(range(len(tasks))))
            self.assertEqual(sorted(t["arrival_s"] for t in tasks), [t["arrival_s"] for t in tasks])
            for task in tasks:
                self.assertTrue(0 <= task["arrival_s"] < 60)
                self.assertEqual(task["output_bytes"], math.ceil(.05 * task["input_bytes"]))
                self.assertEqual(task["working_set_bytes"], 67108864)
                self.assertEqual(task["timeout_relative_s"], 3 * task["deadline_relative_s"])

    def test_zero_task_trace_is_error_without_resampling(self):
        self.config["workloads"]["light"][0]["rate_per_s"] = 1e-9
        with self.assertRaisesRegex(ContractError, "N=0"):
            TraceGenerator(self.config).generate(key(), role="calibrator")

    def test_dynamic_is_not_moderate_or_phase_boundary_injection(self):
        dynamic = self.generator.generate(key(workload="dynamic"), role="calibrator")
        moderate = self.generator.generate(key(workload="moderate"), role="calibrator")
        self.assertNotEqual(dynamic.to_dict()["tasks"], moderate.to_dict()["tasks"])
        times = [t["arrival_s"] for t in dynamic.to_dict()["tasks"]]
        self.assertFalse(any(t in (0, 15, 30, 45, 60) for t in times))
        report = describe_trace(dynamic, self.config, role="calibrator")
        self.assertEqual(sum(i["count"] for i in report["arrival_intervals"]), dynamic.task_count)
        with self.assertRaises(ContractError):
            describe_trace(dynamic, self.config, role="search_validator")

    def test_calibration_requires_all_predeclared_ids(self):
        with self.assertRaisesRegex(ContractError, "incomplete"):
            calibration_report([self.generator.generate(key(), role="calibrator")], self.config)

    def test_calibration_report_rejects_held_out_split(self):
        held_out = self.generator.generate(key("test", trace_id=20000), role="holdout_preparer")
        with self.assertRaisesRegex(ContractError, "cannot access"):
            calibration_report([held_out], self.config)


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.generator = TraceGenerator(self.config)

    def test_atomic_idempotent_write_and_canonical_roundtrip(self):
        trace = self.generator.generate(key(), role="calibrator")
        with tempfile.TemporaryDirectory(prefix="P01 space ") as temporary:
            path = write_bundle(temporary, trace, self.config, role="calibrator")
            original = {p.name: p.read_bytes() for p in path.iterdir()}
            self.assertEqual(write_bundle(temporary, trace, self.config, role="calibrator"), path)
            self.assertEqual(original, {p.name: p.read_bytes() for p in path.iterdir()})
            replay = read_bundle(path, role="calibrator", config=self.config)
            self.assertEqual(replay.canonical_json, trace.canonical_json)
            self.assertEqual(json.loads((path / "config.json").read_bytes())["units"]["time"], "s")
            Draft202012Validator.check_schema(trace_bundle_schema())

    def test_tampered_bundle_is_never_overwritten_or_returned(self):
        trace = self.generator.generate(key(), role="calibrator")
        with tempfile.TemporaryDirectory() as temporary:
            path = write_bundle(temporary, trace, self.config, role="calibrator")
            (path / "trace.json").write_bytes(b"tampered")
            for action in (lambda: read_bundle(path, role="calibrator"),
                           lambda: write_bundle(temporary, trace, self.config, role="calibrator")):
                with self.assertRaises(ContractError):
                    action()
            self.assertEqual((path / "trace.json").read_bytes(), b"tampered")

    def test_concurrent_identical_writers_publish_one_complete_bundle(self):
        trace = self.generator.generate(key(), role="calibrator")
        with tempfile.TemporaryDirectory() as temporary:
            with ThreadPoolExecutor(max_workers=2) as workers:
                futures = [workers.submit(write_bundle, temporary, trace, self.config, role="calibrator") for _ in range(2)]
                paths = [f.result() for f in futures]
            self.assertEqual(paths[0], paths[1])
            self.assertEqual(read_bundle(paths[0], role="calibrator").canonical_json, trace.canonical_json)
            self.assertFalse(list(Path(temporary).rglob(".pending-*")))

    def test_test_bundle_is_sealed_and_read_and_characterization_are_blocked(self):
        trace = self.generator.generate(key("test", trace_id=20000), role="holdout_preparer")
        with tempfile.TemporaryDirectory() as temporary:
            path = write_bundle(temporary, trace, self.config, role="holdout_preparer")
            self.assertEqual(read_json(path / "manifest.json")["status"], "sealed")
            for role in ("candidate_trainer", "search_validator", "holdout_preparer"):
                with self.assertRaises(ContractError):
                    read_bundle(path, role=role)
            with self.assertRaises(ContractError):
                describe_trace(trace, self.config, role="holdout_preparer")

    def test_cli_generates_all_workloads_and_checks_access(self):
        with tempfile.TemporaryDirectory() as temporary:
            command = [sys.executable, "-m", "research_v2", "generate-traces", "--split", "calibration", "--role", "calibrator",
                       "--trace-id", "0", "--output", temporary]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
            rows = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(len(rows), 4)
            for row in rows:
                read_bundle(row["path"], role="calibrator")
            command[command.index("calibrator")] = "search_validator"
            invalid = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("cannot access", invalid.stderr)

    def test_fixture_ties_and_timestamp_boundaries(self):
        trace = boundary_fixture(self.config).to_dict()
        self.assertEqual([t["source_iot"] for t in trace["tasks"]], [0, 19, 20, 99])
        self.assertEqual([t["arrival_s"] for t in trace["tasks"]], [0., 0., 15., 59.999999])
        self.assertEqual(fixture_expectations()["task_0_boundary_cases"][2]["expected_terminal"], "LATE_SUCCESS")
        expected = ROOT / "tests/research_v2/fixtures/boundary.trace.json"
        self.assertEqual(read_json(expected), trace)


def java_path():
    from test_foundation import java_executable
    return java_executable()


@unittest.skipUnless(os.environ.get("JAVA_HOME"), "Set JAVA_HOME for P01 Java timestamp replay")
class JavaTimestampTests(unittest.TestCase):
    def test_java_replays_every_timestamp_bit_and_derived_boundaries(self):
        config = load_config()
        traces = [boundary_fixture(config), TraceGenerator(config).generate(key(), role="calibrator")]
        with tempfile.TemporaryDirectory(prefix="P01 timestamp ") as temporary:
            path = Path(temporary) / "trace.json"
            for trace in traces:
                path.write_bytes(trace.canonical_json)
                command = [java_path(), "-cp", str(ROOT / "ifogsim/dist/research-v2-foundation.jar"),
                           "org.fog.erwo.v2.TraceTimestampProbe", str(path)]
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                replay = json.loads(result.stdout)
                self.assertEqual(replay["payload_sha256"], trace.payload_sha256)
                self.assertEqual(replay["task_count"], trace.task_count)
                for source, row in zip(trace.to_dict()["tasks"], replay["timestamp_bits"]):
                    expected = {name: source[name] for name in ("arrival_s", "deadline_relative_s", "timeout_relative_s")}
                    expected["absolute_deadline_s"] = source["arrival_s"] + source["deadline_relative_s"]
                    expected["absolute_timeout_s"] = source["arrival_s"] + source["timeout_relative_s"]
                    self.assertEqual(row, {"task_id": source["task_id"], **{k: struct.pack(">d", v).hex() for k, v in expected.items()}})


if __name__ == "__main__":
    unittest.main()
