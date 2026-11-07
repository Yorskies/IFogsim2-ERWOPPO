"""P02 acceptance tests C01–C08 and failure paths for the headless Java event engine.

Every expectation below is derived from the specification (sections 13–14) or from arithmetic that can be
checked by hand, never from the engine's own output. Transport here is the labeled zero-network fixture.
"""

import json
import math
import unittest

from research_v2.config import load_config
from research_v2.engine_runner import EngineError, JAR, find_java, run_engine, scenario_from_trace
from research_v2.trace_access import TraceKey
from research_v2.traces import TraceGenerator

GIB = 1 << 30
TIMING = {"arrival_window_s": 60.0, "horizon_s": 69.0}


def node(node_id="IoT-0", pes=1, mips=500, ram=GIB, queue=2, idle=0.5, busy=2.5):
    return {"id": node_id, "pes": pes, "mips_per_pe": mips, "ram_bytes": ram, "queue_waiting": queue,
            "idle_w": idle, "busy_w": busy}


def task(task_id, mi=100, arrival=0.0, deadline=3.0, timeout=9.0, source=0, input_bytes=1000, output_bytes=50, working_set=0):
    return {"task_id": task_id, "source_iot": source, "access_fog": source // 20 + 1, "class_id": "light",
            "arrival_s": arrival, "cpu_mi": mi, "input_bytes": input_bytes, "output_bytes": output_bytes,
            "working_set_bytes": working_set, "deadline_relative_s": deadline, "timeout_relative_s": timeout}


def scenario(tasks, nodes, actions="source_iot", transport=None, repeat=1, label="fixture"):
    value = {"label": label, "tasks": tasks, "nodes": nodes, "actions": actions, "timing": dict(TIMING), "repeat": repeat}
    if transport is not None:
        value["fixture_transport"] = transport
    return value


def run(*args, **kwargs):
    return run_engine(scenario(*args, **kwargs))["episodes"][0]


def by_id(episode):
    return {t["task_id"]: t for t in episode["tasks"]}


@unittest.skipUnless(find_java(), "Set JAVA_HOME to a JDK >= 21 for P02 engine tests")
class EngineAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(JAR.exists(), "Build the v2 JAR first: python ifogsim/build_v2.py --self-test")

    # ---- C01–C08 -------------------------------------------------------------------------------------

    def test_c01_single_task_cpu_time_and_native_cloudlet_finishes(self):
        episode = run([task(0, mi=100, deadline=0.5, timeout=1.5)], [node()])
        t = by_id(episode)[0]
        self.assertEqual((t["cpu_start_s"], t["cpu_finish_s"], t["delivered_s"]), (0.0, 0.2, 0.2))
        self.assertEqual(t["terminal"], "ON_TIME")
        self.assertEqual(t["native_cloudlet_status"], "SUCCESS")
        report = episode["nodes"][0]
        self.assertEqual((report["native_finished_cloudlets"], report["native_used_pes_end"]), (1, 0))

    def test_c02_fcfs_one_pe_order_by_id_and_busy_never_above_one(self):
        # Listed out of order on purpose: simultaneous arrivals are served by task id.
        episode = run([task(2), task(0), task(1)], [node(queue=2)])
        tasks = by_id(episode)
        for i, (start, finish) in enumerate([(0.0, 0.2), (0.2, 0.4), (0.4, 0.6)]):
            self.assertAlmostEqual(tasks[i]["cpu_start_s"], start, places=9)
            self.assertAlmostEqual(tasks[i]["cpu_finish_s"], finish, places=9)
        report = episode["nodes"][0]
        self.assertEqual((report["max_busy_pes"], report["max_waiting"]), (1, 2))
        self.assertAlmostEqual(report["busy_pe_seconds"], 0.6, places=9)

    def test_c03_two_pes_pin_smallest_free_pe(self):
        episode = run([task(0), task(1), task(2)], [node("F1", pes=2, queue=2)], actions="F1")
        tasks = by_id(episode)
        self.assertEqual([tasks[i]["cpu_start_s"] for i in range(3)], [0.0, 0.0, 0.2])
        self.assertEqual([tasks[i]["pe"] for i in range(3)], [0, 1, 0])
        self.assertAlmostEqual(tasks[2]["cpu_finish_s"], 0.4, places=9)
        self.assertEqual(episode["nodes"][0]["max_busy_pes"], 2)

    def test_c03b_waiting_tasks_start_on_the_pe_that_frees_in_fcfs_order(self):
        # Each completion frees exactly one PE, so the adapter's promote-all loop is defensive; the stock
        # one-waiting-per-update hazard cannot arise in this event-driven design. This checks the visible
        # behavior: two PEs freeing at the same instant start the two waiting tasks, lowest PE id first.
        tasks = [task(0, mi=100), task(1, mi=100), task(2, mi=100), task(3, mi=100)]
        episode = run(tasks, [node("F1", pes=2, queue=2)], actions="F1")
        by = by_id(episode)
        self.assertEqual([by[i]["cpu_start_s"] for i in range(4)], [0.0, 0.0, 0.2, 0.2])
        self.assertEqual([by[i]["pe"] for i in range(4)], [0, 1, 0, 1])

    def test_c04_bounded_queue_rejects_third_task_without_reroute(self):
        episode = run([task(0), task(1), task(2)], [node(queue=1)])
        tasks = by_id(episode)
        self.assertEqual((tasks[0]["terminal"], tasks[1]["terminal"]), ("ON_TIME", "ON_TIME"))
        self.assertEqual((tasks[2]["terminal"], tasks[2]["failure_reason"]), ("FAILED", "CPU_QUEUE_FULL"))
        self.assertIsNone(tasks[2]["cpu_start_s"])
        self.assertEqual(episode["nodes"][0]["rejected_cpu_queue_full"], 1)
        self.assertEqual(episode["nodes"][0]["max_waiting"], 1)
        self.assertEqual(episode["on_time"] + episode["late_success"] + episode["failed"], 3)

    def test_c05_ram_rejection_holds_no_pe_or_queue_slot(self):
        rejected = task(0, input_bytes=51, output_bytes=50)  # 0 + 51 + 50 = 101 > 100
        episode = run([rejected], [node(ram=100)])
        t = by_id(episode)[0]
        self.assertEqual((t["terminal"], t["failure_reason"]), ("FAILED", "RAM_EXHAUSTED"))
        report = episode["nodes"][0]
        self.assertEqual((report["admitted"], report["max_busy_pes"], report["max_waiting"], report["ram_peak_bytes"]), (0, 0, 0, 0))
        # A task that fits is still admitted afterwards, and a second one cannot fit while it holds RAM.
        episode = run([task(0, input_bytes=40, output_bytes=20), task(1, input_bytes=40, output_bytes=20)], [node(ram=100, queue=2)])
        tasks = by_id(episode)
        self.assertEqual(tasks[0]["terminal"], "ON_TIME")
        self.assertEqual((tasks[1]["terminal"], tasks[1]["failure_reason"]), ("FAILED", "RAM_EXHAUSTED"))
        self.assertEqual(episode["nodes"][0]["ram_used_end_bytes"], 0)

    def test_c06_deadline_and_timeout_boundaries(self):
        fast = node(mips=10000)
        cases = {5000: ("ON_TIME", False), 5001: ("LATE_SUCCESS", True), 15000: ("LATE_SUCCESS", True)}
        for mi, (terminal, flag) in cases.items():
            with self.subTest(receipt_s=mi / 10000):
                episode = run([task(0, mi=mi, deadline=0.5, timeout=1.5)], [fast])
                t = by_id(episode)[0]
                self.assertEqual(t["terminal"], terminal)
                self.assertEqual(t["deadline_flag"], flag)
        # Receipt exactly at timeout is processed before the timeout, so the task succeeds (late), not fails.
        self.assertEqual(episode["stale_by_kind"].get("TIMEOUT"), 1)
        self.assertEqual(by_id(episode)[0]["delivered_s"], 1.5)

    def test_c07_timeout_cancels_cpu_frees_resources_and_voids_stale_completion(self):
        tasks = [task(0, mi=1000, deadline=0.2, timeout=0.6),
                 task(1, mi=100, arrival=0.1),
                 task(2, mi=100, arrival=1.0)]
        episode = run(tasks, [node(queue=2)])
        by = by_id(episode)
        self.assertEqual((by[0]["terminal"], by[0]["failure_reason"], by[0]["terminal_s"]), ("FAILED", "SERVICE_TIMEOUT", 0.6))
        self.assertTrue(by[0]["deadline_flag"], "deadline passed at 0.2 only flags; it must not cancel")
        self.assertEqual(by[0]["cpu_executed_mi"], 300.0)  # 0.6 s * 500 MIPS
        # The waiting task is promoted at the instant the timeout frees the PE.
        self.assertEqual(by[1]["cpu_start_s"], 0.6)
        self.assertEqual(by[1]["terminal"], "ON_TIME")
        self.assertEqual(by[2]["cpu_start_s"], 1.0)
        report = episode["nodes"][0]
        self.assertEqual((report["cancelled_running"], report["cancelled_executed_mi"], report["native_used_pes_end"]), (1, 300.0, 0))
        # The completion originally due at 2.0 s must not revive the task.
        self.assertEqual(episode["stale_by_kind"].get("CPU_COMPLETE"), 1)
        self.assertEqual(episode["failed"], 1)
        # Busy PE-seconds: task0 0–0.6, task1 0.6–0.8, task2 1.0–1.2.
        self.assertAlmostEqual(report["busy_pe_seconds"], 1.0, places=9)

    def test_c08_horizon_is_fixed_and_counts_conserve(self):
        tasks = [task(0, mi=100), task(1, mi=100), task(2, mi=100, arrival=1.0, deadline=0.1), task(3, mi=100, arrival=59.9)]
        episode = run(tasks, [node(queue=0)])
        self.assertEqual(episode["horizon_s"], 69.0)
        self.assertEqual(episode["finished_at_s"], 69.0)
        self.assertAlmostEqual(episode["native_clock_at_horizon_s"], 69.0, delta=1e-9)
        by = by_id(episode)
        self.assertEqual((by[0]["terminal"], by[2]["terminal"], by[1]["terminal"]), ("ON_TIME", "LATE_SUCCESS", "FAILED"))
        self.assertEqual(episode["on_time"] + episode["late_success"] + episode["failed"], episode["task_count"])
        self.assertTrue(episode["conservation_ok"])
        # The node is observed until H even though the last task finished near 60 s.
        self.assertGreater(episode["finished_at_s"], by[3]["terminal_s"] + 8)

    # ---- ordering, tolerance and stale handling ------------------------------------------------------

    # In real traces ids grow with arrival time, so the task-id tie-break alone would hide a missing priority
    # layer. These fixtures give the *arriving* task the smaller id, so only the domain priority
    # (completion/timeout before arrival) can produce the specified outcome.
    def test_equal_time_completion_precedes_arrival(self):
        episode = run([task(1, mi=100), task(0, mi=100, arrival=0.2)], [node(queue=0)])
        by = by_id(episode)
        self.assertEqual(by[0]["terminal"], "ON_TIME", "PE freed at 0.2 must be visible to the arrival at 0.2")
        self.assertEqual(by[0]["cpu_start_s"], 0.2)

    def test_equal_time_timeout_precedes_arrival(self):
        episode = run([task(1, mi=1000, deadline=0.2, timeout=0.6), task(0, mi=100, arrival=0.6)], [node(queue=0)])
        by = by_id(episode)
        self.assertEqual(by[1]["failure_reason"], "SERVICE_TIMEOUT")
        self.assertEqual((by[0]["terminal"], by[0]["cpu_start_s"]), ("ON_TIME", 0.6))

    def test_equal_time_simultaneous_arrivals_are_served_by_task_id(self):
        episode = run([task(7), task(3), task(5)], [node(queue=2)])
        by = by_id(episode)
        self.assertEqual([by[i]["cpu_start_s"] for i in (3, 5, 7)], [0.0, 0.2, 0.4])

    def test_boundary_within_tolerance_counts_as_on_the_boundary(self):
        fast = node("F1", mips=10000)
        # CPU 0.5 s, result delay makes the receipt land just after a boundary.
        def receipt(delay, deadline, timeout):
            return run([task(0, mi=5000, deadline=deadline, timeout=timeout)], [fast], actions="F1",
                       transport={"input_delay_s": 0.0, "result_delay_s": delay})
        on_time = receipt(0.5 + 5e-10, 1.0, 5.0)  # 5e-10 after the deadline, inside the 1e-9 tolerance
        self.assertEqual((by_id(on_time)[0]["terminal"], by_id(on_time)[0]["deadline_flag"]), ("ON_TIME", False))
        self.assertGreaterEqual(on_time["boundary_tolerance_drains"], 1)
        late = receipt(0.5 + 2e-9, 1.0, 5.0)  # outside tolerance
        self.assertEqual((by_id(late)[0]["terminal"], by_id(late)[0]["deadline_flag"]), ("LATE_SUCCESS", True))
        ok = receipt(1.0 + 5e-10, 0.5, 1.5)  # just after the timeout, inside tolerance: success
        self.assertEqual(by_id(ok)[0]["terminal"], "LATE_SUCCESS")
        failed = receipt(1.0 + 2e-9, 0.5, 1.5)  # outside tolerance: timeout wins
        self.assertEqual((by_id(failed)[0]["terminal"], by_id(failed)[0]["failure_reason"]), ("FAILED", "SERVICE_TIMEOUT"))

    def test_timeout_during_input_transfer_leaves_node_untouched(self):
        episode = run([task(0, deadline=0.1, timeout=0.2)], [node("F1")], actions="F1",
                      transport={"input_delay_s": 0.3, "result_delay_s": 0.0})
        t = by_id(episode)[0]
        self.assertEqual((t["terminal"], t["failure_reason"]), ("FAILED", "SERVICE_TIMEOUT"))
        self.assertEqual(episode["stale_by_kind"].get("TRANSFER_COMPLETE"), 1)
        report = episode["nodes"][0]
        self.assertEqual((report["admitted"], report["max_busy_pes"], report["ram_peak_bytes"]), (0, 0, 0))

    def test_timeout_during_result_return_cancels_pending_delivery(self):
        episode = run([task(0, mi=100, deadline=0.2, timeout=0.5)], [node("F1")], actions="F1",
                      transport={"input_delay_s": 0.0, "result_delay_s": 1.0})
        t = by_id(episode)[0]
        self.assertEqual((t["terminal"], t["failure_reason"]), ("FAILED", "SERVICE_TIMEOUT"))
        self.assertEqual(t["cpu_finish_s"], 0.2, "CPU work finished; only the result return timed out")
        self.assertEqual(episode["stale_by_kind"].get("RESULT_DELIVERED"), 1)
        self.assertEqual(episode["nodes"][0]["ram_used_end_bytes"], 0)

    # ---- invalid input stops the run -----------------------------------------------------------------

    def test_invalid_scenarios_are_rejected_not_repaired(self):
        cases = {
            "arrival at T": scenario([task(0, arrival=60.0)], [node()]),
            "timeout after horizon": scenario([task(0, arrival=59.9, deadline=3.0, timeout=9.2)], [node()]),
            "N=0": scenario([], [node()]),
            "duplicate task id": scenario([task(0), task(0)], [node()]),
            "unknown target": scenario([task(0)], [node()], actions="F9"),
            "IoT receives other IoT's task": scenario([task(0, source=0)], [node("IoT-1")], actions="IoT-1"),
            "duplicate node id": scenario([task(0)], [node(), node()]),
            "no queue limit field": scenario([task(0)], [{k: v for k, v in node().items() if k != "queue_waiting"}]),
            "fractional cpu_mi": scenario([{**task(0), "cpu_mi": 100.5}], [node()]),
        }
        for name, bad in cases.items():
            with self.subTest(name), self.assertRaises(EngineError):
                run_engine(bad)

    # ---- determinism and isolation -------------------------------------------------------------------

    def test_repeated_episodes_in_one_jvm_and_across_jvms_are_identical(self):
        tasks = [task(i, mi=100 + 37 * i, arrival=0.05 * i, deadline=0.4, timeout=1.2) for i in range(40)]
        value = scenario(tasks, [node(queue=3), node("F1", pes=2, queue=4)], actions={"default": "F1", "0": "source_iot", "5": "source_iot"}, repeat=3)
        first = run_engine(value)["episodes"]
        strip = lambda e: json.dumps({k: v for k, v in e.items() if k != "episode_id"}, sort_keys=True)
        self.assertEqual(len({strip(e) for e in first}), 1, "state leaked between episodes in one JVM")
        second = run_engine(value)["episodes"]
        self.assertEqual(strip(first[0]), strip(second[0]), "result differs across JVM processes")

    # ---- topology factory ----------------------------------------------------------------------------

    def test_topology_factory_builds_100_5_1_with_specified_capacity(self):
        trace = {"tasks": [task(0, source=45)], "arrival_window_s": 60.0, "horizon_s": 69.0}
        for homogeneous in (False, True):
            with self.subTest(homogeneous=homogeneous):
                episode = run_engine(scenario_from_trace(trace, "nearest_fog", topology={"homogeneous_fog": homogeneous}))["episodes"][0]
                nodes = {n["id"]: n for n in episode["nodes"]}
                self.assertEqual(len(nodes), 106)
                self.assertEqual([nid for nid in nodes if nid.startswith("IoT-")], [f"IoT-{i}" for i in range(100)])
                fog_mips = sum(nodes[f"F{i}"]["pes"] * nodes[f"F{i}"]["mips_per_pe"] for i in range(1, 6))
                self.assertEqual(fog_mips, 14000.0)
                self.assertEqual((nodes["cloud"]["pes"], nodes["cloud"]["mips_per_pe"], nodes["cloud"]["queue_waiting_limit"]), (8, 5600.0, 64))
                self.assertEqual(nodes["IoT-0"]["queue_waiting_limit"], 2)
                if homogeneous:
                    self.assertEqual({nodes[f"F{i}"]["mips_per_pe"] for i in range(1, 6)}, {1400.0})
                else:
                    self.assertEqual([nodes[f"F{i}"]["mips_per_pe"] for i in range(1, 6)], [700.0, 1050.0, 1400.0, 1750.0, 2100.0])
                # Source 45 maps to access fog F3 (45 // 20 + 1) and ran there.
                self.assertEqual(by_id(episode)[0]["node"], "F3")


@unittest.skipUnless(find_java(), "Set JAVA_HOME to a JDK >= 21 for P02 engine tests")
class EngineOnRealTraceTests(unittest.TestCase):
    """Calibration traces from P01 through the full 100+5+1 topology; checks structure and conservation only."""

    @classmethod
    def setUpClass(cls):
        cls.config = load_config()
        cls.generator = TraceGenerator(cls.config)

    def trace(self, workload, trace_id=0):
        key = TraceKey(self.config["seeds"]["master"], "calibration", None, None, trace_id, workload)
        return self.generator.generate(key, role="calibrator").to_dict()

    def check_episode(self, trace, episode):
        self.assertEqual(episode["task_count"], trace["task_count"])
        self.assertEqual(episode["on_time"] + episode["late_success"] + episode["failed"], trace["task_count"])
        self.assertEqual(len(episode["tasks"]), trace["task_count"])
        self.assertEqual(episode["finished_at_s"], 69.0)
        self.assertAlmostEqual(episode["native_clock_at_horizon_s"], 69.0, delta=1e-9)
        executed_s = {}
        tasks = by_id(episode)
        for t in tasks.values():
            self.assertIn(t["terminal"], ("ON_TIME", "LATE_SUCCESS", "FAILED"))
            if t["terminal"] == "FAILED":
                self.assertIn(t["failure_reason"], ("CPU_QUEUE_FULL", "RAM_EXHAUSTED", "SERVICE_TIMEOUT"))
        for report in episode["nodes"]:
            self.assertLessEqual(report["max_busy_pes"], report["pes"])
            self.assertLessEqual(report["max_waiting"], report["queue_waiting_limit"])
            self.assertLessEqual(report["ram_peak_bytes"], report["ram_bytes"])
            self.assertEqual((report["native_used_pes_end"], report["native_waiting_end"], report["ram_used_end_bytes"]), (0, 0, 0))
            executed_s[report["id"]] = 0.0
        for t in tasks.values():
            if t["node"] is not None and t["cpu_executed_mi"]:
                node_report = next(n for n in episode["nodes"] if n["id"] == t["node"])
                executed_s[t["node"]] += t["cpu_executed_mi"] / node_report["mips_per_pe"]
        # Independent recomputation: node busy PE-seconds equals the sum of per-task executed work / MIPS.
        for report in episode["nodes"]:
            self.assertAlmostEqual(report["busy_pe_seconds"], executed_s[report["id"]], places=6, msg=report["id"])
        return tasks

    def test_every_workload_runs_to_horizon_with_exact_conservation(self):
        for workload in ("light", "moderate", "heavy", "dynamic"):
            with self.subTest(workload=workload):
                trace = self.trace(workload)
                episode = run_engine(scenario_from_trace(trace, "nearest_fog", topology={"homogeneous_fog": False}, label=workload))["episodes"][0]
                self.check_episode(trace, episode)

    def test_overloading_one_fog_exposes_queue_and_timeout_failures(self):
        trace = self.trace("heavy")
        episode = run_engine(scenario_from_trace(trace, "F1", topology={"homogeneous_fog": False}, label="heavy-all-F1"))["episodes"][0]
        tasks = self.check_episode(trace, episode)
        reasons = episode["failure_reasons"]
        self.assertGreater(reasons.get("CPU_QUEUE_FULL", 0), 0)
        f1 = next(n for n in episode["nodes"] if n["id"] == "F1")
        self.assertEqual(f1["max_waiting"], 16)
        self.assertEqual(sum(1 for t in tasks.values() if t["node"] == "F1"), trace["task_count"])

    def test_same_trace_and_actions_give_identical_outcomes_in_new_jvm(self):
        trace = self.trace("dynamic")
        value = scenario_from_trace(trace, "nearest_fog", topology={"homogeneous_fog": False}, repeat=2)
        episodes = run_engine(value)["episodes"]
        strip = lambda e: json.dumps({k: v for k, v in e.items() if k != "episode_id"}, sort_keys=True)
        self.assertEqual(strip(episodes[0]), strip(episodes[1]))
        self.assertEqual(strip(episodes[0]), strip(run_engine(value)["episodes"][0]))


if __name__ == "__main__":
    unittest.main()
