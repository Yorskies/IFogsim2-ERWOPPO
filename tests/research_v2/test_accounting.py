"""P04 acceptance tests E01–E04, M01–M03 and an independent re-evaluation of the Java ledger.

Expectations are arithmetic from the specification (section 15.2, 16), not engine output. The evaluator in
research_v2.evaluator re-derives every figure from raw records and must agree with the engine on real traces.
"""

import math
import unittest

from research_v2.config import load_config
from research_v2.engine_runner import EngineError, JAR, find_java, run_engine, scenario_from_trace
from research_v2.evaluator import compare, evaluate
from research_v2.trace_access import TraceKey
from research_v2.traces import TraceGenerator

GIB = 1 << 30
MIB = 1 << 20
H = 69.0
TIMING = {"arrival_window_s": 60.0, "horizon_s": H}
CPU_IDLE_W = 100 * 0.5 + (50 + 65 + 83.4333 + 100 + 120) + 100      # 568.4333 (IoT, F1..F5, cloud)
COMM_IDLE_W = 100 * 0.1 + 5 * 3 + 20 + 10                           # 55 (radios, APs, switch, WAN gateway)
IDLE_J = (CPU_IDLE_W + COMM_IDLE_W) * H                             # 43,016.8977 J


def node(node_id, pes=1, mips=500, ram=GIB, queue=2, idle=0.5, busy=2.5):
    return {"id": node_id, "pes": pes, "mips_per_pe": mips, "ram_bytes": ram, "queue_waiting": queue, "idle_w": idle, "busy_w": busy}


def task(task_id, source=0, input_bytes=MIB, output_bytes=None, mi=100, arrival=0.0, deadline=3.0, timeout=9.0, working_set=0):
    return {"task_id": task_id, "source_iot": source, "access_fog": source // 20 + 1, "class_id": "light", "arrival_s": arrival,
            "cpu_mi": mi, "input_bytes": input_bytes, "output_bytes": output_bytes or math.ceil(0.05 * input_bytes),
            "working_set_bytes": working_set, "deadline_relative_s": deadline, "timeout_relative_s": timeout}


def fixture(tasks, nodes, actions="source_iot", **extra):
    return {"label": "acct", "tasks": tasks, "nodes": nodes, "actions": actions, "timing": dict(TIMING), **extra}


def default_topology(tasks, actions, network=True):
    value = {"label": "acct", "tasks": tasks, "topology": {"homogeneous_fog": False}, "actions": actions, "timing": dict(TIMING)}
    if network:
        value["network"] = {"log_transfers": True}
    return value


def run(scenario):
    return run_engine(scenario)["episodes"][0]


def by_id(episode):
    return {t["task_id"]: t for t in episode["tasks"]}


@unittest.skipUnless(find_java(), "Set JAVA_HOME to a JDK >= 21 for P04 accounting tests")
class AccountingAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(JAR.exists(), "Build the v2 JAR first: python ifogsim/build_v2.py --self-test")
        self.config = load_config()

    def assertAgrees(self, episode):
        self.assertEqual(compare(episode, evaluate(episode, self.config)), [])

    # ---- E01–E04 -------------------------------------------------------------------------------------

    def test_e01_idle_system_pays_idle_power_for_the_whole_horizon_and_nothing_dynamic(self):
        self.assertAlmostEqual(CPU_IDLE_W, 568.4333, places=9)
        self.assertAlmostEqual(IDLE_J, 43016.8977, places=4)
        # Rejected on arrival (working set larger than the IoT RAM): nothing runs, no byte moves.
        episode = run(default_topology([task(0, working_set=1 << 40)], "source_iot"))
        energy, metrics = episode["energy"], episode["metrics"]
        self.assertEqual(by_id(episode)[0]["failure_reason"], "RAM_EXHAUSTED")
        self.assertAlmostEqual(energy["idle_power_w"], CPU_IDLE_W + COMM_IDLE_W, places=9)
        self.assertAlmostEqual(energy["idle_j"], IDLE_J, places=6)
        self.assertEqual(energy["dynamic_j"], 0.0)
        self.assertAlmostEqual(energy["total_j"], energy["idle_j"] + energy["dynamic_j"], places=9)
        self.assertEqual(metrics["costs"]["zE"], 0.0)
        self.assertAgrees(episode)

    def test_e02_local_cpu_adds_only_the_dynamic_increment(self):
        episode = run(default_topology([task(0, mi=100)], "source_iot"))
        energy = episode["energy"]
        self.assertAlmostEqual(energy["dynamic_j"], (2.5 - 0.5) * 0.2, places=9)  # 0.4 J
        self.assertAlmostEqual(energy["idle_j"], IDLE_J, places=6, msg="idle is counted once, never again for busy time")
        self.assertAlmostEqual(energy["by_group"]["cpu_iot"]["dynamic_j"], 0.4, places=9)
        self.assertAlmostEqual(episode["metrics"]["costs"]["zE"], 0.4 / 50.0, places=12)
        self.assertAlmostEqual(by_id(episode)[0]["cpu_dynamic_j"], 0.4, places=9)
        self.assertAgrees(episode)

    def test_e03_wireless_upload_adds_tx_plus_rx_during_serialization_only(self):
        episode = run(default_topology([task(0, source=0)], "F1"))
        upload = next(h for h in episode["transfers"] if h["phase"] == "INPUT")
        serialization = 8.0 * MIB / 20_000_000.0
        self.assertAlmostEqual(upload["dynamic_j"], (1.3 + 1.5) * serialization, places=9)
        self.assertAlmostEqual(upload["dynamic_j"], 1.17440512, places=8)
        download = next(h for h in episode["transfers"] if h["phase"] == "RESULT")
        self.assertAlmostEqual(download["dynamic_j"], (2.0 + 0.9) * 8.0 * 52429 / 20_000_000.0, places=9)
        groups = episode["energy"]["by_group"]
        up_s, down_s = serialization, 8.0 * 52429 / 20_000_000.0
        self.assertAlmostEqual(groups["radio"]["dynamic_j"], 1.3 * up_s + 0.9 * down_s, places=9)
        self.assertAlmostEqual(groups["ap"]["dynamic_j"], 1.5 * up_s + 2.0 * down_s, places=9)
        self.assertEqual((groups["lan"]["dynamic_j"], groups["wan"]["dynamic_j"]), (0.0, 0.0))
        self.assertAlmostEqual(groups["radio"]["idle_j"], 0.1 * 100 * H, places=9)
        self.assertAlmostEqual(groups["ap"]["idle_j"], 3.0 * 5 * H, places=9)
        self.assertAlmostEqual(episode["energy"]["idle_j"], IDLE_J, places=6)
        self.assertAgrees(episode)

    def test_e03b_wired_hops_cost_joules_per_bit_hop(self):
        episode = run(default_topology([task(0, source=0)], "cloud"))
        groups = episode["energy"]["by_group"]
        bits = 8.0 * (MIB + 52429)
        self.assertAlmostEqual(groups["lan"]["dynamic_j"], bits * 5e-9, places=12)    # one LAN hop each way
        self.assertAlmostEqual(groups["wan"]["dynamic_j"], bits * 20e-9, places=12)   # one WAN hop each way
        self.assertAgrees(episode)

    def test_e04_fog_imbalance_is_integrated_over_time(self):
        fogs = [node(f"F{k}", pes=2, mips=1000, queue=16, idle=1.0, busy=2.0) for k in range(1, 6)]
        # Two never-finishing tasks fill both PEs of F1 and F2 until their timeout at the horizon: u = [1,1,0,0,0].
        hog = lambda i: task(i, mi=10**9, deadline=30.0, timeout=69.0)
        episode = run(fixture([hog(0), hog(1), hog(2), hog(3)], fogs, actions={"default": "F1", "2": "F2", "3": "F2"}))
        metrics = episode["metrics"]
        self.assertAlmostEqual(math.sqrt(0.24), 0.4898979485566356, places=15)
        self.assertAlmostEqual(metrics["fog_utilization_std_integral_s"], 69 * math.sqrt(0.24), places=9)
        self.assertAlmostEqual(metrics["costs"]["zB"], 1.0, places=9)
        self.assertEqual(episode["failed"], 4)
        self.assertAlmostEqual(episode["energy"]["dynamic_j"], 2 * (2.0 - 1.0) * 69.0, places=9)  # two fully busy fogs
        self.assertAgrees(episode)

    # ---- M01–M03 -------------------------------------------------------------------------------------

    def test_m01_counts_and_ratios_share_one_denominator(self):
        tasks = ([task(i, mi=100) for i in range(6)]
                 + [task(i, mi=100, deadline=0.05) for i in (6, 7)]
                 + [task(i, working_set=1 << 40) for i in (8, 9)])
        episode = run(fixture(tasks, [node("F1", pes=10, mips=1000, queue=16)], actions="F1"))
        metrics = episode["metrics"]
        self.assertEqual((metrics["on_time"], metrics["late_success"], metrics["failed"], metrics["task_count"]), (6, 2, 2, 10))
        self.assertAlmostEqual(metrics["violation"], 0.4, places=12)
        self.assertAlmostEqual(metrics["reliability"], 0.8, places=12)
        self.assertAlmostEqual(metrics["costs"]["zD"], 0.4, places=12)
        self.assertAlmostEqual(metrics["costs"]["zQ"], 0.2, places=12)
        self.assertEqual(metrics["on_time"] + metrics["late_success"] + metrics["failed"], metrics["task_count"])
        self.assertAgrees(episode)

    def test_m02_failed_task_is_penalized_in_zL_but_absent_from_physical_latency(self):
        slow_iot = node("IoT-0", pes=1, mips=500, idle=0.5, busy=5.5)  # (5.5 - 0.5) W * 0.2 s = 1 J
        episode = run(fixture([task(0, mi=100), task(1, working_set=1 << 40)], [slow_iot]))
        metrics = episode["metrics"]
        self.assertAlmostEqual(episode["energy"]["dynamic_j"], 1.0, places=12)
        self.assertAlmostEqual(metrics["costs"]["zL"], (0.2 + 9.0) / (2 * 9.0), places=12)   # 0.5111111111
        self.assertAlmostEqual(metrics["costs"]["zE"], 1.0 / (50 * 2), places=12)             # 0.01
        self.assertAlmostEqual(metrics["latency"]["mean_s"], 0.2, places=12)
        self.assertEqual(metrics["latency"]["completed_tasks"], 1)
        self.assertEqual(metrics["latency"]["failed_tasks_excluded"], 1)
        self.assertTrue(metrics["latency_penalty_is_evaluation_convention_not_measured_latency"])
        self.assertAgrees(episode)

    def test_m03_no_completed_task_gives_null_statistics_not_zero(self):
        episode = run(fixture([task(0, working_set=1 << 40), task(1, working_set=1 << 40)], [node("IoT-0")], actions="IoT-0"))
        metrics = episode["metrics"]
        self.assertEqual((metrics["failed"], metrics["success_count"], metrics["reliability"], metrics["violation"]), (2, 0, 0.0, 1.0))
        self.assertEqual([metrics["latency"][k] for k in ("mean_s", "median_s", "p95_s")], [None, None, None])
        self.assertIsNone(episode["energy"]["joules_per_successful_task"])
        self.assertAlmostEqual(episode["energy"]["joules_per_arrived_task"], episode["energy"]["total_j"] / 2)
        self.assertAlmostEqual(metrics["costs"]["zL"], 1.0, places=12)  # every task carries the 9 s penalty
        self.assertAgrees(episode)
        with self.assertRaises(EngineError):  # N=0 is rejected before any division
            run_engine(fixture([], [node("IoT-0")]))

    # ---- further accounting rules --------------------------------------------------------------------

    def test_latency_percentiles_use_the_stated_nearest_rank_rule(self):
        tasks = [task(k, mi=100 * (k + 1), deadline=10.0, timeout=60.0) for k in range(20)]  # latencies 0.1 .. 2.0 s
        episode = run(fixture(tasks, [node("F1", pes=20, mips=1000, queue=16)], actions="F1"))
        latency = episode["metrics"]["latency"]
        self.assertAlmostEqual(latency["p95_s"], 1.9, places=9)       # element ceil(0.95 * 20) = 19
        self.assertAlmostEqual(latency["median_s"], 1.05, places=9)   # mean of the 10th and 11th values
        self.assertAlmostEqual(latency["mean_s"], 1.05, places=9)
        self.assertAgrees(episode)

    def test_throughput_separates_the_arrival_window_from_the_drain(self):
        episode = run(fixture([task(0, arrival=1.0), task(1, arrival=59.95)], [node("F1", pes=2, mips=1000)], actions="F1"))
        throughput = episode["metrics"]["throughput"]
        self.assertEqual((throughput["results_during_arrival_window"], throughput["results_after_arrival_window"]), (1, 1))
        self.assertAlmostEqual(throughput["results_per_s"], 2 / 69.0, places=12)

    def test_cancelled_task_still_pays_the_energy_it_used_but_has_no_physical_latency(self):
        episode = run(fixture([task(0, mi=1000, deadline=0.2, timeout=0.6)], [node("IoT-0")]))
        t = by_id(episode)[0]
        self.assertEqual(t["failure_reason"], "SERVICE_TIMEOUT")
        self.assertAlmostEqual(t["cpu_dynamic_j"], (2.5 - 0.5) * 0.6, places=9)  # ran 0.6 s before the timeout
        self.assertAlmostEqual(episode["energy"]["dynamic_j"], 1.2, places=9)
        self.assertIsNone(episode["metrics"]["latency"]["mean_s"])
        self.assertAgrees(episode)

    def test_out_of_reference_costs_are_flagged_and_never_clipped(self):
        hot = node("IoT-0", pes=1, mips=500, idle=0.5, busy=1000.0)
        episode = run(fixture([task(0, mi=100)], [hot]))
        metrics = episode["metrics"]
        self.assertAlmostEqual(metrics["costs"]["zE"], (1000.0 - 0.5) * 0.2 / 50.0, places=9)  # about 4.0
        self.assertGreater(metrics["costs"]["zE"], 1.0)
        self.assertEqual(metrics["out_of_reference"], ["zE"])
        self.assertTrue(metrics["diagnosis_required"])

    def test_total_energy_is_the_sum_of_components_and_attribution_closes(self):
        episode = run(default_topology([task(i, source=i, mi=300 + 50 * i) for i in range(6)], {"default": "F1", "1": "cloud", "2": "F3", "3": "source_iot"}))
        energy = episode["energy"]
        self.assertAlmostEqual(energy["total_j"], sum(c["idle_j"] + c["dynamic_j"] for c in energy["components"]), places=6)
        self.assertAlmostEqual(energy["total_j"], sum(g["total_j"] for g in energy["by_group"].values()), places=6)
        self.assertAlmostEqual(energy["attribution_gap_j"], 0.0, places=9)
        self.assertAgrees(episode)

    def test_fixture_transport_models_no_communication_energy(self):
        episode = run(fixture([task(0)], [node("F1", pes=2, mips=1000)], actions="F1"))
        self.assertFalse(episode["energy"]["communication_modeled"])
        self.assertEqual(set(episode["energy"]["by_group"]), {"cpu_fog"})
        self.assertAgrees(episode)


@unittest.skipUnless(find_java(), "Set JAVA_HOME to a JDK >= 21 for P04 accounting tests")
class IndependentEvaluatorOnRealTraces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()
        cls.generator = TraceGenerator(cls.config)

    def trace(self, workload):
        key = TraceKey(self.config["seeds"]["master"], "calibration", None, None, 0, workload)
        return self.generator.generate(key, role="calibrator").to_dict()

    def test_engine_ledger_equals_independent_recomputation_for_every_workload_and_mode(self):
        for workload in ("light", "moderate", "heavy", "dynamic"):
            for mode, action in (("network", "nearest_fog"), ("network", "cloud"), ("fixture", "nearest_fog")):
                with self.subTest(workload=workload, mode=mode, action=action):
                    value = scenario_from_trace(self.trace(workload), action, topology={"homogeneous_fog": False})
                    if mode == "network":
                        value["network"] = {"log_transfers": True}
                    episode = run_engine(value)["episodes"][0]
                    self.assertEqual(compare(episode, evaluate(episode, self.config)), [])
                    self.assertAlmostEqual(episode["energy"]["attribution_gap_j"], 0.0, places=6)
                    # Fixed policies on calibration traces stay inside the frozen reference scales; a flag here means diagnose.
                    self.assertEqual(episode["metrics"]["out_of_reference"], [], episode["metrics"]["costs"])

    def test_link_aggregates_agree_with_the_hop_log_when_the_log_is_off(self):
        value = scenario_from_trace(self.trace("dynamic"), "nearest_fog", topology={"homogeneous_fog": False})
        value["network"] = {"log_transfers": False}
        episode = run_engine(value)["episodes"][0]
        recomputed = evaluate(episode, self.config)
        self.assertEqual(recomputed["energy"]["communication_source"], "link_aggregates")
        self.assertEqual(compare(episode, recomputed), [])


if __name__ == "__main__":
    unittest.main()
