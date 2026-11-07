"""P06 tests: reference policies, solo-task analysis, estimator exactness and gate logic.

Policy expectations are hand computed from specification 20.3; solo times are checked against the engine, never the
reverse; gate logic is exercised on synthetic rows including exact-boundary cases. No PPO and no learned component.
"""

import copy
import math
import unittest

from research_v2.baselines import (ACTIONS, FEATURES, POLICIES, AuditedSnapshot, always_local, eft_scores, greedy_eft, least_fog, nearest_fog)
from research_v2.calibration import (MODES, POLICY_ORDER, calibration_trace, cell_means, evaluate_gates, solo_feasibility, solo_time)
from research_v2.config import load_config
from research_v2.engine_runner import find_java, run_engine
from research_v2.schema_definitions import WORKLOADS
from research_v2.traces import TraceGenerator

CONFIG = load_config()
GENERATOR = TraceGenerator(CONFIG)
NAMES = ["source_iot", "F1", "F2", "F3", "F4", "F5", "cloud"]


def snapshot(**overrides):
    """A full public snapshot (exactly the contract's 108 keys), all zero, with sensible constants, then overrides."""
    data = {name: 0.0 for name in FEATURES}
    for node, mips in zip(NAMES, (500, 700, 1050, 1400, 1750, 2100, 5600)):
        data[f"node.{node}.mips_per_pe"] = float(mips)
        data[f"node.{node}.pes"] = 1.0
        data[f"node.{node}.minimum_remaining_deadline_s"] = None
    data["task.cpu_mi"] = 1000.0
    data["source.access_fog.F2"] = 1.0
    data.update(overrides)
    assert set(data) == set(FEATURES)
    return data


class ReferencePolicyTests(unittest.TestCase):
    def test_always_local_and_nearest_fog(self):
        self.assertEqual(always_local(snapshot()), 0)
        for k in range(1, 6):
            one_hot = {f"source.access_fog.F{j}": float(j == k) for j in range(1, 6)}
            self.assertEqual(nearest_fog(snapshot(**one_hot)), k)

    def test_least_fog_picks_the_smallest_backlog_among_fogs_only(self):
        backlog = {"F1": 3.0, "F2": 2.0, "F3": 0.5, "F4": 1.0, "F5": 4.0}
        data = snapshot(**{f"node.{n}.remaining_mi_over_mips_s": v for n, v in backlog.items()})
        # IoT and cloud are idle (0) yet must be ignored: Least Fog only considers the five fogs.
        self.assertEqual(least_fog(data), 3)

    def test_least_fog_ties_use_the_shorter_path_then_the_smaller_id(self):
        same = {f"node.F{k}.remaining_mi_over_mips_s": 1.0 for k in range(1, 6)}
        paths = {"route.F1.estimated_input_delay_s": 0.5, "route.F2.estimated_input_delay_s": 0.2, "route.F3.estimated_input_delay_s": 0.2,
                 "route.F4.estimated_input_delay_s": 0.9, "route.F5.estimated_input_delay_s": 0.9,
                 "route.F2.estimated_result_delay_s": 0.01, "route.F3.estimated_result_delay_s": 0.01}
        self.assertEqual(least_fog(snapshot(**same, **paths)), 2, "F2 and F3 tie on path too: the smaller id wins")
        self.assertEqual(least_fog(snapshot(**same, **{**paths, "route.F3.estimated_result_delay_s": 0.0})), 3, "shorter transfer path wins the tie")
        near = {f"node.F{k}.remaining_mi_over_mips_s": v for k, v in zip(range(1, 6), (1.0, 1.0 + 5e-10, 1.0, 1.0, 1.0))}
        self.assertEqual(least_fog(snapshot(**near)), 1, "a difference below 1e-9 s is a tie")
        far = {f"node.F{k}.remaining_mi_over_mips_s": v for k, v in zip(range(1, 6), (1.0, 1.0 - 1e-6, 1.0, 1.0, 1.0))}
        self.assertEqual(least_fog(snapshot(**far)), 2, "a difference above 1e-9 s is not a tie")

    def test_greedy_eft_scores_follow_the_specified_formula(self):
        far = {f"route.{n}.estimated_input_delay_s": 5.0 for n in ("F1", "F3", "F4", "F5")}   # keep every other fog out of the race
        data = snapshot(**{
            **far, "task.cpu_mi": 1000.0,
            "route.F2.estimated_input_delay_s": 0.1, "route.F2.estimated_result_delay_s": 0.05,
            "route.cloud.estimated_input_delay_s": 0.5, "route.cloud.estimated_result_delay_s": 0.2,
            "node.cloud.mips_per_pe": 5000.0,
        })
        scores = eft_scores(data)
        self.assertAlmostEqual(scores[0], 1000 / 500, places=12)                      # local: no network, no wait
        self.assertAlmostEqual(scores[2], 0.1 + 0.0 + 1000 / 1050 + 0.05, places=12)  # Tin + W + MI/MIPS + Tout
        self.assertAlmostEqual(scores[6], 0.5 + 0.0 + 1000 / 5000 + 0.2, places=12)
        self.assertEqual(greedy_eft(data), 6)
        # Queue statistics enter through W = max(0, earliest_free + queued - Tin).
        loaded = snapshot(**{**{**far, "task.cpu_mi": 1000.0, "route.F2.estimated_input_delay_s": 0.1, "route.F2.estimated_result_delay_s": 0.05,
                                "route.cloud.estimated_input_delay_s": 0.5, "route.cloud.estimated_result_delay_s": 0.2,
                                "node.cloud.mips_per_pe": 5000.0}, "node.cloud.queued_mi_over_mips_s": 1.0, "node.cloud.earliest_pe_free_delay_s": 0.25})
        self.assertAlmostEqual(eft_scores(loaded)[6], 0.5 + (0.25 + 1.0 - 0.5) + 0.2 + 0.2, places=12)
        self.assertEqual(greedy_eft(loaded), 2, "the loaded cloud (1.65 s) loses to F2 (1.152 s)")
        # W is clamped at zero: a queue shorter than the transfer time is hidden by the transfer.
        clamped = snapshot(**{"route.F1.estimated_input_delay_s": 2.0, "node.F1.queued_mi_over_mips_s": 1.0})
        self.assertAlmostEqual(eft_scores(clamped)[1], 2.0 + 0.0 + 1000 / 700, places=12)

    def test_greedy_eft_ties_go_to_the_smaller_destination_and_ignore_admission_state(self):
        data = snapshot(**{f"node.{n}.mips_per_pe": 1000.0 for n in NAMES})
        self.assertEqual(greedy_eft(data), 0, "all scores equal: the smallest id")
        data = snapshot(**{**{f"node.{n}.mips_per_pe": 1000.0 for n in NAMES}, "node.F3.mips_per_pe": 1000.0 * (1 + 1e-12)})
        self.assertEqual(greedy_eft(data), 0)
        # A full queue gives no hint to the policy: no admission mask.
        full = snapshot(**{"node.F5.queue_fraction": 1.0, "node.F5.mips_per_pe": 1e6, "node.F5.busy_pe_fraction": 1.0})
        self.assertEqual(greedy_eft(full), 5)

    def test_policies_read_only_public_features_and_are_pure(self):
        for name, policy in POLICIES.items():
            with self.subTest(policy=name):
                data = AuditedSnapshot(snapshot(**{"node.F2.remaining_mi_over_mips_s": 0.3, "source.access_fog.F3": 1.0, "source.access_fog.F2": 0.0}))
                before = dict(data)
                first = policy(data)                 # raises KeyError if it touched anything outside the 108 contract keys
                self.assertLessEqual(data.accessed, FEATURES)
                self.assertTrue(data.accessed or name == "always_local")
                self.assertEqual(dict(data), before, "a policy must not modify the snapshot")
                self.assertEqual(policy(AuditedSnapshot(dict(data))), first)
                self.assertIn(first, range(7))

    def test_policy_registry_matches_the_calibration_set(self):
        self.assertEqual(set(POLICIES), set(POLICY_ORDER))
        self.assertEqual(ACTIONS, NAMES)


class SoloAnalysisTests(unittest.TestCase):
    def sample_tasks(self):
        tasks = []
        for workload in WORKLOADS:
            tasks += calibration_trace(GENERATOR, CONFIG, workload, 0)["tasks"][::53][:5]
        return tasks[:18]

    def test_solo_time_formula_by_hand(self):
        task = {"cpu_mi": 400, "input_bytes": 1 << 20, "output_bytes": 52429, "access_fog": 2, "deadline_relative_s": 1.0}
        access, lan, wan = (20e6, 0.002), (1e9, 0.0005), (50e6, 0.02)
        leg = lambda n, hops: sum(8.0 * n / b + p for b, p in hops)
        self.assertAlmostEqual(solo_time(task, 0, CONFIG, False), 400 / 500.0, places=12)
        self.assertAlmostEqual(solo_time(task, 2, CONFIG, False), leg(1 << 20, [access]) + 400 / 1050.0 + leg(52429, [access]), places=12)
        self.assertAlmostEqual(solo_time(task, 4, CONFIG, False), leg(1 << 20, [access, lan, lan]) + 400 / 1750.0 + leg(52429, [lan, lan, access]), places=12)
        self.assertAlmostEqual(solo_time(task, 6, CONFIG, False), leg(1 << 20, [access, lan, wan]) + 400 / 5600.0 + leg(52429, [wan, lan, access]), places=12)
        self.assertAlmostEqual(solo_time(task, 4, CONFIG, True), leg(1 << 20, [access, lan, lan]) + 400 / 1400.0 + leg(52429, [lan, lan, access]), places=12,
                               msg="homogeneous mode gives every fog the F3 speed")

    def test_feasibility_counts_a_task_once_and_respects_the_deadline(self):
        impossible = {"task_id": 0, "class_id": "heavy", "cpu_mi": 3000, "input_bytes": 2306867, "output_bytes": 115344, "access_fog": 1,
                      "deadline_relative_s": 0.05, "arrival_s": 0.0}
        easy = {**impossible, "task_id": 1, "class_id": "light", "cpu_mi": 100, "input_bytes": 50_000, "output_bytes": 2500, "deadline_relative_s": 3.0}
        trace = {"seed_namespace": {"workload": "light"}, "tasks": [impossible, easy]}
        result = solo_feasibility([trace], CONFIG, False)
        self.assertEqual((result["tasks"], result["feasible"]), (2, 1))
        self.assertEqual(result["by_class"]["heavy"]["fraction"], 0.0)
        self.assertEqual(result["by_class"]["light"]["fraction"], 1.0)

    @unittest.skipUnless(find_java(), "Set JAVA_HOME to a JDK >= 21 for engine agreement tests")
    def test_analytic_solo_time_equals_the_engine_for_every_destination_and_mode(self):
        tasks = self.sample_tasks()
        for mode, homogeneous in MODES.items():
            for action in range(7):
                for start in range(0, len(tasks), 6):
                    chunk = []
                    for slot, task in enumerate(tasks[start:start + 6]):
                        chunk.append({**copy.deepcopy(task), "task_id": slot, "arrival_s": 5.0 + 10.0 * slot})   # 10 s apart: strictly alone
                    scenario = {"label": "solo", "tasks": chunk, "topology": {"homogeneous_fog": homogeneous}, "network": {},
                                "actions": NAMES[action], "timing": {"arrival_window_s": 60.0, "horizon_s": 69.0}}
                    episode = run_engine(scenario)["episodes"][0]
                    for outcome, task in zip(episode["tasks"], chunk):
                        expected = solo_time(task, action, CONFIG, homogeneous)
                        with self.subTest(mode=mode, action=action, task=task["task_id"], start=start):
                            if outcome["terminal"] == "FAILED":
                                self.assertEqual(outcome["failure_reason"], "SERVICE_TIMEOUT")
                                self.assertGreater(expected, task["timeout_relative_s"] - 1e-9)
                            else:
                                self.assertAlmostEqual(outcome["delivered_s"] - outcome["arrival_s"], expected, places=9)
                                self.assertEqual(outcome["terminal"] == "ON_TIME", expected <= task["deadline_relative_s"] + 1e-9)

    @unittest.skipUnless(find_java(), "Set JAVA_HOME to a JDK >= 21 for engine agreement tests")
    def test_eft_estimate_is_exact_for_a_lone_task_and_only_an_estimate_otherwise(self):
        from research_v2.gym_env import OffloadingEnv
        from research_v2.config import sha256
        from research_v2.contracts import trace_payload_sha256
        tasks = self.sample_tasks()[:6]
        for task in tasks:
            single = {**copy.deepcopy(task), "task_id": 0, "arrival_s": 1.0}
            trace = {"schema_version": "research-v2.1", "config_sha256": sha256(CONFIG), "payload_sha256": "0" * 64,
                     "seed_namespace": {"master": CONFIG["seeds"]["master"], "split": "calibration", "outer_run": None, "model_repeat": None,
                                        "trace_id": 0, "workload": "light"},
                     "arrival_window_s": 60.0, "horizon_s": 69.0, "task_count": 1, "tasks": [single]}
            trace["payload_sha256"] = trace_payload_sha256(trace)
            env = OffloadingEnv([trace], [0.2] * 5, config=CONFIG, any_port=True, detail=True)
            try:
                _, info = env.reset(seed=0)
                scores = eft_scores(info["raw_snapshot"])
                action = greedy_eft(info["raw_snapshot"])
                _, _, terminated, _, info = env.step(action)
            finally:
                env.close()
            self.assertTrue(terminated)
            outcome = info["result"]["tasks"][0]
            with self.subTest(task=task["class_id"], source=task["source_iot"], action=action):
                self.assertNotEqual(outcome["terminal"], "FAILED")
                self.assertAlmostEqual(outcome["delivered_s"] - outcome["arrival_s"], scores[action], places=9)
                self.assertAlmostEqual(scores[action], min(solo_time(single, a, CONFIG, False) for a in range(7)), places=9,
                                       msg="on an idle system the best EFT score is the best solo time")


def fake_row(mode, policy, workload, trace_id, *, failure=0.0, reliability=1.0):
    n = 100
    failed = round(failure * n)
    return {"mode": mode, "policy": policy, "workload": workload, "trace_id": trace_id, "tasks": n, "on_time": n - failed, "late_success": 0, "failed": failed,
            "failure_fraction": failure, "reliability": reliability, "violation": failure, "failure_reasons": {"SERVICE_TIMEOUT": failed},
            "costs": {"zL": 0.1, "zE": 0.1, "zD": failure, "zB": 0.1, "zQ": failure}, "D": 0.2, "latency": {}, "energy_total_j": 50000.0, "energy_dynamic_j": 100.0,
            "pressure": {"access_utilization_max": 0.5, "access_queue_max": 2, "fog_cpu_utilization_mean": 0.3, "iot_queue_max": 0, "cpu_queue_rejections": 0,
                         "network_queue_rejections": 0, "fog_cpu_utilization_max": 0.4, "fog_queue_max": 0, "iot_cpu_utilization_max": 0.1, "cloud_cpu_utilization": 0.1,
                         "ram_rejections": 0, "access_utilization_mean": 0.4, "wan_utilization_max": 0.1},
            "action_counts": [n, 0, 0, 0, 0, 0, 0], "steps": n, "wall_s": 0.1}


def full_rows(heavy_failure=0.2, heavy_reliability=0.8):
    rows = []
    for mode in MODES:
        for policy in POLICY_ORDER:
            for workload in WORKLOADS:
                for trace_id in range(20):
                    heavy = workload == "heavy"
                    rows.append(fake_row(mode, policy, workload, trace_id, failure=heavy_failure if heavy else 0.0, reliability=heavy_reliability if heavy else 1.0))
    return rows


def fake_feasibility(fraction):
    return {mode: {"fraction": fraction, "tasks": 1000} for mode in MODES}


class GateLogicTests(unittest.TestCase):
    def gates(self, rows=None, feasibility=0.97, distribution="pass"):
        return evaluate_gates(rows if rows is not None else full_rows(), fake_feasibility(feasibility), CONFIG, {"status": distribution, "traces": 80})

    def test_all_gates_pass_when_every_condition_holds(self):
        gates = self.gates()
        self.assertTrue(gates["all_pass"])
        self.assertEqual(len(gates["heavy_pressure"]["passing_conditions"]), 8)

    def test_a_partial_run_cannot_pass(self):
        gates = self.gates(full_rows()[:-1])
        self.assertFalse(gates["complete"]["pass"])
        self.assertFalse(gates["all_pass"])

    def test_solo_feasibility_boundary_is_inclusive_at_95_percent(self):
        self.assertTrue(self.gates(feasibility=0.95)["solo_feasibility"]["pass"])
        self.assertFalse(self.gates(feasibility=0.9499999)["solo_feasibility"]["pass"])
        both = fake_feasibility(1.0)
        both["homogeneous"]["fraction"] = 0.94        # the average (0.97) clears 95%, but one configuration does not
        gates = evaluate_gates(full_rows(), both, CONFIG, {"status": "pass", "traces": 80})
        self.assertFalse(gates["solo_feasibility"]["pass"], "every configuration must clear the threshold, not their average")
        self.assertEqual({m: v["pass"] for m, v in gates["solo_feasibility"]["by_mode"].items()}, {"heterogeneous": True, "homogeneous": False})

    def test_heavy_gate_needs_failure_above_1_percent_and_reliability_above_50_percent(self):
        cases = {"no pressure": (0.0, 1.0, False), "failure exactly 1%": (0.01, 0.9, False), "failure just above 1%": (0.02, 0.9, True),
                 "services collapsed": (0.6, 0.4, False), "reliability exactly 50%": (0.3, 0.5, False), "reliability just above 50%": (0.3, 0.51, True)}
        for name, (failure, reliability, expected) in cases.items():
            with self.subTest(name):
                self.assertEqual(self.gates(full_rows(failure, reliability))["heavy_pressure"]["pass"], expected)

    def test_a_single_passing_condition_is_enough_for_the_heavy_gate(self):
        rows = full_rows(heavy_failure=0.0, heavy_reliability=1.0)
        for row in rows:
            if row["workload"] == "heavy" and row["mode"] == "heterogeneous" and row["policy"] == "greedy_eft":
                row.update(failure_fraction=0.2, reliability=0.8)
        gates = self.gates(rows)
        self.assertEqual(gates["heavy_pressure"]["passing_conditions"], ["heterogeneous/greedy_eft"])
        self.assertTrue(gates["heavy_pressure"]["pass"])

    def test_a_failed_distribution_check_fails_the_calibration(self):
        self.assertFalse(self.gates(distribution="fail")["all_pass"])

    def test_cell_means_weigh_every_trace_equally(self):
        rows = [fake_row("heterogeneous", "greedy_eft", "light", i, failure=f) for i, f in enumerate((0.0, 0.5))]
        rows[1]["tasks"] = 900                                  # a longer trace must not outweigh a shorter one
        cell = cell_means(rows)[("heterogeneous", "greedy_eft", "light")]
        self.assertAlmostEqual(cell["failure_fraction"], 0.25)
        self.assertEqual(cell["traces"], 2)

    def test_diagnostics_flag_a_trivial_or_collapsed_problem_without_failing_it(self):
        gates = self.gates(full_rows(0.0, 1.0))
        self.assertTrue(gates["diagnostics"]["every_cell_reliability_above_0_99"])
        self.assertFalse(gates["heavy_pressure"]["pass"])


if __name__ == "__main__":
    unittest.main()
