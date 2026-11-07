"""P05 tests: socket protocol, Gymnasium environment, 108-feature observation and delayed reward.

Expectations are derived from the specification (sections 15, 16, 17.1, 18) with independent arithmetic. Fixed or random
actions are used throughout (no PPO), so a simulator fault cannot hide behind learning.
"""

import copy
import json
import math
import time
import unittest
import warnings

import numpy as np
from gymnasium.utils.env_checker import check_env

from research_v2.config import ContractError, load_config, read_json, sha256, ROOT
from research_v2.contracts import trace_payload_sha256
from research_v2.engine_runner import find_java, run_engine, scenario_from_trace
from research_v2.evaluator import compare, evaluate
from research_v2.gym_env import LegacyIncompatibleError, OffloadingEnv, check_policy_interface, validate_weights
from research_v2.rpc_client import (ConnectionLostError, HandshakeError, RpcError, ServerProcess, V2Client, file_sha256, verify_handshake)
from research_v2.trace_access import TraceKey
from research_v2.traces import TraceGenerator

CONFIG = load_config()
CONFIG_SHA = sha256(CONFIG)
WIRE = read_json(ROOT / "configs/research_v2/wire_contract.json")
FEATURES = WIRE["observation_features"]
ACTIONS = WIRE["actions"]
EQUAL = [0.2] * 5
MANUAL = CONFIG["search"]["manual_weights"]
MIB = 1 << 20
ACCESS_BPS, ACCESS_PROP = 20e6, 0.002
LAN_BPS, LAN_PROP = 1e9, 0.0005
WAN_BPS, WAN_PROP = 50e6, 0.02
GENERATOR = TraceGenerator(CONFIG)


def calibration_trace(workload, trace_id=0):
    key = TraceKey(CONFIG["seeds"]["master"], "calibration", None, None, trace_id, workload)
    return GENERATOR.generate(key, role="calibrator").to_dict()


def custom_task(task_id, arrival, source=0, cpu_mi=100, input_bytes=100_000, deadline=3.0, class_id="light", working_set=None):
    return {"task_id": task_id, "source_iot": source, "access_fog": source // 20 + 1, "class_id": class_id, "arrival_s": arrival,
            "cpu_mi": cpu_mi, "input_bytes": input_bytes, "output_bytes": math.ceil(0.05 * input_bytes),
            "working_set_bytes": CONFIG["tasks"]["working_set_bytes"] if working_set is None else working_set,
            "deadline_relative_s": deadline, "timeout_relative_s": CONFIG["timing"]["timeout_factor"] * deadline}


def custom_trace(tasks, trace_id=0):
    """A trace envelope with a correct declared payload hash (the server compares it with the request's trace hash)."""
    trace = {"schema_version": "research-v2.1", "config_sha256": CONFIG_SHA, "payload_sha256": "0" * 64,
             "seed_namespace": {"master": CONFIG["seeds"]["master"], "split": "calibration", "outer_run": None, "model_repeat": None,
                                "trace_id": trace_id, "workload": "light"},
             "arrival_window_s": 60.0, "horizon_s": 69.0, "task_count": len(tasks), "tasks": tasks}
    trace["payload_sha256"] = trace_payload_sha256(trace)
    return trace


def ser(num_bytes, bps):
    return 8.0 * num_bytes / bps


def squash(x, ref):
    return x / (x + ref)


def play(env, chooser, seed=0):
    """Run one episode. chooser(step_index, obs, info) -> action. Returns the full transcript."""
    obs, info = env.reset(seed=seed)
    steps = [{"obs": obs, "info": info, "reward": None, "action": None}]
    index = 0
    while True:
        action = int(chooser(index, obs, info))
        obs, reward, terminated, truncated, info = env.step(action)
        steps.append({"obs": obs, "info": info, "reward": reward, "action": action})
        index += 1
        if terminated or truncated:
            return steps


def random_chooser(seed):
    rng = np.random.default_rng(seed)
    return lambda i, o, info: rng.integers(0, 7)


@unittest.skipUnless(find_java(), "Set JAVA_HOME to a JDK >= 21 for P05 socket/Gym tests")
class SocketGymTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ServerProcess(CONFIG, any_port=True)
        cls.light = calibration_trace("light")

    @classmethod
    def tearDownClass(cls):
        cls.server.close()

    def env(self, traces=None, weights=EQUAL, **kwargs):
        return OffloadingEnv(traces or [self.light], weights, config=CONFIG, host=self.server.host, port=self.server.port, **kwargs)

    # ---- environment contract ------------------------------------------------------------------------

    def test_gymnasium_environment_checker_passes(self):
        env = self.env([calibration_trace("light", 0), calibration_trace("light", 1)])
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                check_env(env, skip_render_check=True)
        finally:
            env.close()

    def test_one_step_per_arrival_and_termination_at_the_horizon(self):
        env = self.env()
        try:
            steps = play(env, random_chooser(1))
        finally:
            env.close()
        decisions = steps[:-1]            # the reset observation plus every step that is not the terminal one
        self.assertEqual(len(steps) - 1, self.light["task_count"], "exactly one step per arrival")
        self.assertEqual([s["info"]["task_id"] for s in decisions], [t["task_id"] for t in self.light["tasks"]])
        self.assertEqual(steps[0]["info"]["sim_time_s"], self.light["tasks"][0]["arrival_s"])
        last = steps[-1]
        self.assertFalse(last["info"]["observation_valid"])
        self.assertEqual(float(np.abs(last["obs"]).sum()), 0.0)
        self.assertEqual(last["info"]["sim_time_s"], 69.0)
        self.assertTrue(all(s["info"]["observation_valid"] for s in decisions))

    def test_step_after_termination_requires_reset(self):
        env = self.env([custom_trace([custom_task(0, 0.0)])])
        try:
            play(env, lambda *a: 1)
            with self.assertRaises(RuntimeError):
                env.step(1)
            obs, _ = env.reset(seed=0)   # and a fresh episode works
            self.assertEqual(obs.shape, (108,))
        finally:
            env.close()

    def test_observation_vector_follows_the_wire_contract_order(self):
        env = self.env()
        try:
            obs, info = env.reset(seed=0)
        finally:
            env.close()
        self.assertEqual(len(FEATURES), 108)
        self.assertEqual(list(info["raw_snapshot"]), FEATURES, "raw snapshot keys are in contract order")
        self.assertEqual(env.feature_names, FEATURES)
        self.assertTrue(env.observation_space.contains(obs))

    # ---- all 108 features, recomputed from the specification -----------------------------------------

    def expected_idle_features(self, task):
        """Spec 17.1 values for the first decision on an idle system (nothing queued, nothing in flight)."""
        topo = CONFIG["topology"]
        specs = {"source_iot": topo["iot"], **{f["id"]: f for f in topo["fogs"]}, "cloud": topo["cloud"]}
        obs_cfg = CONFIG["observation"]
        out = {}
        for block, spec in specs.items():
            p = f"node.{block}."
            increment = (spec["busy_w"] - spec["idle_w"]) / spec["pes"] / spec["mips_per_pe"]
            out[p + "busy_pe_fraction"] = out[p + "queue_fraction"] = 0.0
            out[p + "earliest_pe_free_delay_s"] = out[p + "queued_mi_over_mips_s"] = out[p + "remaining_mi_over_mips_s"] = 0.0
            out[p + "mips_per_pe"] = spec["mips_per_pe"] / obs_cfg["mips_reference"]
            out[p + "pes"] = spec["pes"] / obs_cfg["pes_reference"]
            out[p + "cpu_increment_j_per_mi"] = increment / obs_cfg["cpu_increment_reference_j_per_mi"]
            out[p + "minimum_remaining_deadline_s"] = 1.0   # empty node sentinel
        a, b_in, b_out = task["access_fog"], task["input_bytes"], task["output_bytes"]
        access = (ACCESS_BPS, ACCESS_PROP)
        lan, wan = (LAN_BPS, LAN_PROP), (WAN_BPS, WAN_PROP)
        for name in ACTIONS:
            p = f"route.{name}."
            if name == "source_iot":
                hops_in = hops_out = []
            elif name == f"F{a}":
                hops_in = hops_out = [access]
            elif name == "cloud":
                hops_in, hops_out = [access, lan, wan], [wan, lan, access]
            else:
                hops_in = hops_out = [access, lan, lan]
            delay = lambda n, hops: sum(ser(n, h[0]) + h[1] for h in hops)
            wireless = lambda n: (CONFIG["network"]["radio_tx_increment_w"] + CONFIG["network"]["ap_rx_increment_w"]) * ser(n, ACCESS_BPS)
            wireless_down = lambda n: (CONFIG["network"]["ap_tx_increment_w"] + CONFIG["network"]["radio_rx_increment_w"]) * ser(n, ACCESS_BPS)
            lan_hops = sum(1 for h in hops_in if h == lan)
            wan_hops = sum(1 for h in hops_in if h == wan)
            energy = 0.0
            if hops_in:
                energy = wireless(b_in) + wireless_down(b_out)
                energy += lan_hops * (b_in + b_out) * 8 * CONFIG["network"]["lan_j_per_bit_hop"]
                energy += wan_hops * (b_in + b_out) * 8 * CONFIG["network"]["wan_j_per_bit_hop"]
            out[p + "estimated_input_delay_s"] = squash(delay(b_in, hops_in), obs_cfg["time_squash_reference_s"]) if hops_in else 0.0
            out[p + "estimated_result_delay_s"] = squash(delay(b_out, hops_out), obs_cfg["time_squash_reference_s"]) if hops_out else 0.0
            out[p + "bottleneck_bit_per_s"] = min(h[0] for h in hops_in) / obs_cfg["bandwidth_reference_bit_per_s"] if hops_in else 0.0
            out[p + "estimated_dynamic_energy_j"] = squash(energy, obs_cfg["communication_squash_reference_j"]) if hops_in else 0.0
        out["task.cpu_mi"] = task["cpu_mi"] / obs_cfg["cpu_mi_reference"]
        out["task.input_bytes"] = b_in / (obs_cfg["input_reference_mib"] * MIB)
        out["task.output_bytes"] = b_out / (obs_cfg["output_reference_mib"] * MIB)
        out["task.deadline_relative_s"] = task["deadline_relative_s"] / obs_cfg["deadline_reference_s"]
        out["task.timeout_relative_s"] = task["timeout_relative_s"] / obs_cfg["timeout_reference_s"]
        for c in ("light", "medium", "heavy"):
            out[f"task.class.{c}"] = 1.0 if task["class_id"] == c else 0.0
        for f in range(1, 6):
            out[f"source.access_fog.F{f}"] = 1.0 if a == f else 0.0
        t = task["arrival_s"]
        out["global.time_fraction"] = t / CONFIG["timing"]["arrival_window_s"]
        out["global.arrival_ema_per_s"] = squash(1.0 / obs_cfg["ema_time_constant_s"], obs_cfg["arrival_squash_reference_per_s"])
        out["global.mean_iot_utilization"] = 0.0
        out["global.interarrival_s"] = squash(t, obs_cfg["time_squash_reference_s"])   # time since t=0 for the first decision
        return out

    def test_all_108_features_match_independent_computation_on_an_idle_system(self):
        for source_task in (self.light["tasks"][0], custom_task(0, 0.25, source=45, input_bytes=1_500_000, cpu_mi=2000, class_id="heavy", deadline=2.0)):
            trace = custom_trace([source_task])
            env = self.env([trace])
            try:
                obs, info = env.reset(seed=0)
            finally:
                env.close()
            expected = self.expected_idle_features(source_task)
            self.assertEqual(set(expected), set(FEATURES))
            for index, name in enumerate(FEATURES):
                self.assertAlmostEqual(float(obs[index]), expected[name], places=6, msg=name)
            self.assertIsNone(info["raw_snapshot"]["node.cloud.minimum_remaining_deadline_s"], "raw value of the empty-node sentinel is null")

    def test_second_decision_sees_the_current_backlog_and_partial_energy_but_nothing_future(self):
        first = custom_task(0, 0.0, source=0, input_bytes=MIB, cpu_mi=100)
        second = custom_task(1, 0.1, source=1, input_bytes=100_000, cpu_mi=100)
        env = self.env([custom_trace([first, second])])
        try:
            env.reset(seed=0)
            _, _, _, _, info = env.step(1)                      # task 0 -> F1 (its own access fog): 1 MiB upload from t = 0
        finally:
            env.close()
        raw = info["raw_snapshot"]
        residual = MIB - 0.1 * ACCESS_BPS / 8.0                 # still uploading at t = 0.1
        self.assertAlmostEqual(raw["route.F1.estimated_input_delay_s"], (residual + second["input_bytes"]) * 8 / ACCESS_BPS + ACCESS_PROP, places=9)
        self.assertAlmostEqual(raw["route.F1.estimated_result_delay_s"], (residual + second["output_bytes"]) * 8 / ACCESS_BPS + ACCESS_PROP, places=9)
        self.assertEqual(raw["node.F1.busy_pe_fraction"], 0.0, "task 0 is still in transit, not on the node")
        # The energy of the half-sent upload is charged to the interval in which it was spent (stateless partial accrual).
        partial = 0.1 * (CONFIG["network"]["radio_tx_increment_w"] + CONFIG["network"]["ap_rx_increment_w"])
        self.assertAlmostEqual(info["cost_delta"][1], partial / (50.0 * 2), places=12)
        self.assertEqual(raw["global.interarrival_s"], 0.1)
        self.assertAlmostEqual(raw["global.arrival_ema_per_s"], 0.2 * math.exp(-0.1 / 5.0) + 0.2, places=12)

    def test_loaded_node_features_match_hand_computation(self):
        # F1 has 2 PEs at 700 MIPS. Tasks 0 and 1 run (10 s and 20 s of CPU), task 2 waits; the 4th decision is at t = 0.03.
        tiny = dict(input_bytes=1000, deadline=3.0)
        tasks = [custom_task(0, 0.00, cpu_mi=7000, **tiny), custom_task(1, 0.01, cpu_mi=14000, **tiny),
                 custom_task(2, 0.02, cpu_mi=700, **tiny), custom_task(3, 0.03, cpu_mi=100, **tiny)]
        env = self.env([custom_trace(tasks)])
        try:
            env.reset(seed=0)
            for _ in range(2):
                env.step(1)
            obs, _, _, _, info = env.step(1)       # the answer to task 2's placement, observed at task 3's arrival
        finally:
            env.close()
        arrive = ser(1000, ACCESS_BPS) + ACCESS_PROP          # 0.0024 s from arrival to the node
        now = 0.03
        started0, started1 = 0.00 + arrive, 0.01 + arrive
        remaining0 = 7000 - (now - started0) * 700
        remaining1 = 14000 - (now - started1) * 700
        capacity = 2 * 700.0
        free_in = min(started0 + 7000 / 700 - now, started1 + 14000 / 700 - now)
        raw = info["raw_snapshot"]
        self.assertEqual(raw["node.F1.busy_pe_fraction"], 1.0)
        self.assertAlmostEqual(raw["node.F1.queue_fraction"], 1 / 16, places=12)
        self.assertAlmostEqual(raw["node.F1.earliest_pe_free_delay_s"], free_in, places=9)
        self.assertAlmostEqual(raw["node.F1.queued_mi_over_mips_s"], 700 / capacity, places=12)
        self.assertAlmostEqual(raw["node.F1.remaining_mi_over_mips_s"], (remaining0 + remaining1 + 700) / capacity, places=9)
        self.assertAlmostEqual(raw["node.F1.minimum_remaining_deadline_s"], min(3.0 - now, 3.01 - now, 3.02 - now), places=9)
        index = FEATURES.index
        nine = CONFIG["observation"]["time_squash_reference_s"]
        self.assertAlmostEqual(float(obs[index("node.F1.busy_pe_fraction")]), 1.0, places=6)
        self.assertAlmostEqual(float(obs[index("node.F1.earliest_pe_free_delay_s")]), squash(free_in, nine), places=6)
        self.assertAlmostEqual(float(obs[index("node.F1.remaining_mi_over_mips_s")]), squash((remaining0 + remaining1 + 700) / capacity, nine), places=6)
        remaining_deadline = 3.0 - now
        self.assertAlmostEqual(float(obs[index("node.F1.minimum_remaining_deadline_s")]), remaining_deadline / (abs(remaining_deadline) + 3.0), places=6)
        self.assertEqual(raw["node.F2.busy_pe_fraction"], 0.0, "other fogs stay idle")

    def test_observation_does_not_depend_on_future_arrivals(self):
        base = calibration_trace("moderate")
        cut = 60
        altered = copy.deepcopy(base)
        for task in altered["tasks"][cut:]:
            task["cpu_mi"] = task["cpu_mi"] * 2 if task["cpu_mi"] < 1500 else 100
            task["input_bytes"] = task["input_bytes"] // 2 + 1
            task["output_bytes"] = math.ceil(0.05 * task["input_bytes"])
        altered["payload_sha256"] = trace_payload_sha256(altered)
        self.assertNotEqual(base["payload_sha256"], altered["payload_sha256"])
        runs = []
        for trace in (base, altered):
            env = self.env([trace])
            try:
                obs, info = env.reset(seed=0)
                rows = [(obs.copy(), info["cost_cumulative"].copy())]
                rng = np.random.default_rng(3)
                for _ in range(cut - 1):
                    obs, _, _, _, info = env.step(int(rng.integers(0, 7)))
                    rows.append((obs.copy(), info["cost_cumulative"].copy()))
            finally:
                env.close()
            runs.append(rows)
        for step, ((o1, c1), (o2, c2)) in enumerate(zip(*runs)):
            np.testing.assert_array_equal(o1, o2, err_msg=f"observation changed at step {step} when only later tasks differ")
            np.testing.assert_array_equal(c1, c2, err_msg=f"cost changed at step {step}")

    # ---- reward ---------------------------------------------------------------------------------------

    def test_return_equals_minus_100_times_weighted_costs_for_every_workload_and_weighting(self):
        for workload in ("light", "moderate", "heavy", "dynamic"):
            for weights in (EQUAL, MANUAL, [0.6, 0.1, 0.1, 0.1, 0.1], [0.02, 0.02, 0.02, 0.02, 0.92]):
                with self.subTest(workload=workload, weights=weights):
                    detailed = weights is EQUAL      # one full-record run per workload, for the independent evaluator
                    env = self.env([calibration_trace(workload)], weights=weights, detail=detailed, log_transfers=detailed)
                    try:
                        steps = play(env, random_chooser(7))
                    finally:
                        env.close()
                    final = steps[-1]["info"]
                    costs = final["summary"]["metrics"]["costs"]
                    z = np.array([costs[k] for k in ("zL", "zE", "zD", "zB", "zQ")])
                    total = sum(s["reward"] for s in steps[1:])
                    self.assertAlmostEqual(total, -100.0 * float(np.dot(weights, z)), places=9)
                    np.testing.assert_allclose(final["cost_cumulative"], z, rtol=1e-9, atol=1e-12)
                    if detailed:
                        # z is also what an independent evaluator derives from the raw records of this very episode.
                        episode = final["result"]
                        self.assertEqual(compare(episode, evaluate(episode, CONFIG)), [])

    def test_completion_reward_arrives_at_the_decision_after_it_happens(self):
        # Task 0 (arrival 0) is delivered about 0.54 s later; tasks 1 and 2 arrive at 1 s and 2 s.
        tasks = [custom_task(0, 0.0, input_bytes=MIB, cpu_mi=100), custom_task(1, 1.0, source=1, input_bytes=200_000, cpu_mi=100),
                 custom_task(2, 2.0, source=2, input_bytes=200_000, cpu_mi=100)]
        env = self.env([custom_trace(tasks)])
        try:
            env.reset(seed=0)
            _, r0, _, _, i0 = env.step(1)       # decision for task 0 -> F1; answered at t = 1.0
            env.step(1)
            _, _, done, _, last = env.step(1)
        finally:
            env.close()
        self.assertTrue(done)
        latency0 = (ser(MIB, ACCESS_BPS) + ACCESS_PROP) + 100 / 700.0 + (ser(math.ceil(0.05 * MIB), ACCESS_BPS) + ACCESS_PROP)  # F1 is 700 MIPS/PE
        self.assertAlmostEqual(i0["cost_delta"][0], latency0 / (9.0 * 3), places=9, msg="latency cost lands when the result is received")
        self.assertEqual(i0["cost_delta"][2], 0.0, "on time: no deadline cost")
        self.assertLess(r0, 0.0)
        self.assertGreater(last["cost_delta"][1], 0.0, "the drain after the last arrival is part of the last transition")

    def test_each_outcome_kind_charges_deadline_and_failure_cost_exactly_once(self):
        # (a) refused on arrival, before its deadline; (b) on time; (c) late success; (d) times out after its deadline passed.
        tasks = [custom_task(0, 0.0, source=0, working_set=2 << 30),
                 custom_task(1, 0.1, source=1, cpu_mi=100),
                 custom_task(2, 0.2, source=2, cpu_mi=1000, deadline=1.0),
                 custom_task(3, 0.3, source=3, cpu_mi=10_000, deadline=1.0)]
        env = self.env([custom_trace(tasks)], detail=True)
        try:
            steps = play(env, lambda *a: 0)              # everything stays on its own IoT
        finally:
            env.close()
        final = steps[-1]["info"]
        outcomes = {t["task_id"]: (t["terminal"], t["failure_reason"]) for t in final["result"]["tasks"]}
        self.assertEqual(outcomes, {0: ("FAILED", "RAM_EXHAUSTED"), 1: ("ON_TIME", None), 2: ("LATE_SUCCESS", None), 3: ("FAILED", "SERVICE_TIMEOUT")})
        cumulative = final["cost_cumulative"]
        self.assertAlmostEqual(cumulative[2], 3 / 4, places=12, msg="CD: tasks 0, 2 and 3 each once")
        self.assertAlmostEqual(cumulative[4], 2 / 4, places=12, msg="CQ: only the two failures, not the late success")
        self.assertAlmostEqual(final["summary"]["metrics"]["costs"]["zD"], 3 / 4, places=12)
        self.assertAlmostEqual(final["summary"]["metrics"]["costs"]["zQ"], 2 / 4, places=12)
        # Task 0 was refused at t = 0, so its deadline and failure costs are in the very first interval.
        self.assertAlmostEqual(steps[1]["info"]["cost_delta"][2], 1 / 4, places=12)
        self.assertAlmostEqual(steps[1]["info"]["cost_delta"][4], 1 / 4, places=12)

    def test_costs_are_nondecreasing_and_terminal_cost_includes_the_drain(self):
        env = self.env([calibration_trace("heavy")])
        try:
            steps = play(env, random_chooser(11))
        finally:
            env.close()
        cumulative = np.array([s["info"]["cost_cumulative"] for s in steps])
        self.assertTrue((np.diff(cumulative, axis=0) >= -1e-12).all(), "cumulative costs never decrease")
        self.assertGreater(float(np.abs(steps[-1]["info"]["cost_delta"]).sum()), 0.0)

    # ---- equivalence, determinism, isolation ---------------------------------------------------------

    def test_socket_episode_equals_the_headless_run_with_the_same_actions(self):
        trace = calibration_trace("dynamic")
        env = self.env([trace], detail=True, log_transfers=True)
        try:
            steps = play(env, random_chooser(5))
        finally:
            env.close()
        chosen = {}
        for before, after in zip(steps, steps[1:]):
            chosen[str(before["info"]["task_id"])] = ACTIONS[after["action"]]
        scenario = scenario_from_trace(trace, chosen, topology={"homogeneous_fog": False})
        scenario["network"] = {"log_transfers": True}
        headless = run_engine(scenario)["episodes"][0]
        served = steps[-1]["info"]["result"]
        for key in ("tasks", "nodes", "links", "transfers", "energy", "metrics", "on_time", "late_success", "failed", "failure_reasons"):
            self.assertEqual(json.dumps(served[key], sort_keys=True), json.dumps(headless[key], sort_keys=True), key)

    def test_same_seed_gives_identical_transcripts_in_separate_servers(self):
        transcripts = []
        for _ in range(2):
            server = ServerProcess(CONFIG, any_port=True)
            env = OffloadingEnv([self.light], EQUAL, config=CONFIG, host=server.host, port=server.port)
            try:
                steps = play(env, random_chooser(2))
                transcripts.append([(s["obs"].tobytes(), s["reward"]) for s in steps])
            finally:
                env.close()
                server.close()
        self.assertEqual(transcripts[0], transcripts[1])

    def test_consecutive_and_interrupted_episodes_do_not_contaminate_each_other(self):
        env = self.env([calibration_trace("moderate")])
        try:
            clean = play(env, random_chooser(4))
            again = play(env, random_chooser(4))
            self.assertEqual([(s["obs"].tobytes(), s["reward"]) for s in clean], [(s["obs"].tobytes(), s["reward"]) for s in again])
            env.reset(seed=0)                                   # abandon an episode part-way and start over
            for _ in range(25):
                env.step(2)
            third = play(env, random_chooser(4))
            self.assertEqual([(s["obs"].tobytes(), s["reward"]) for s in clean], [(s["obs"].tobytes(), s["reward"]) for s in third])
        finally:
            env.close()

    # ---- protocol: identity, idempotency, errors -----------------------------------------------------

    def client(self):
        return V2Client(self.server.host, self.server.port, timeout_s=30.0)

    def reset_request(self, client, trace=None, **overrides):
        trace = trace or self.light
        fields = {"episode_id": "t1", "config_sha256": CONFIG_SHA, "trace_sha256": trace["payload_sha256"], "trace": trace}
        fields.update(overrides)
        return client.request("reset", **fields)

    def test_handshake_identifies_the_exact_jar_config_and_contract(self):
        client = self.client()
        try:
            handshake = client.request("hello")["handshake"]
        finally:
            client.close()
        self.assertEqual(verify_handshake(handshake, CONFIG), handshake)
        self.assertEqual(handshake["observation_dimension"], 108)
        self.assertEqual(handshake["actions"], ACTIONS)
        self.assertEqual(handshake["config_file_sha256"], file_sha256(ROOT / "configs/research_v2/default.json"))
        receipt = read_json(ROOT / "ifogsim/build/research_v2/build_receipt.json")
        self.assertEqual(handshake["jar_sha256"], receipt["artifact_sha256"])
        for key, value in (("jar_sha256", "0" * 64), ("config_file_sha256", "1" * 64), ("wire_contract_file_sha256", "2" * 64),
                           ("observation_dimension", 46)):
            with self.subTest(tampered=key), self.assertRaises(HandshakeError):
                verify_handshake({**handshake, key: value}, CONFIG)

    def test_identical_retry_gets_the_cached_answer_and_is_not_applied_twice(self):
        client = self.client()
        try:
            self.reset_request(client)
            fields = {"episode_id": "t1", "config_sha256": CONFIG_SHA, "trace_sha256": self.light["payload_sha256"]}
            first = client.request("step", action=1, **fields)
            retry = client.resend_last()
            self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(retry, sort_keys=True))
            second = client.request("step", action=1, **fields)
            self.assertEqual(second["step_index"], first["step_index"] + 1, "the retried step must not advance the episode")
            self.assertEqual(second["task_id"], self.light["tasks"][2]["task_id"])
        finally:
            client.close()

    def test_malformed_legacy_and_mismatched_requests_get_errors_not_crashes(self):
        client = self.client()
        try:
            self.assertEqual(client.send_raw_line("{not json")["error"]["code"], "BAD_JSON")
            legacy = client.send_raw_line(json.dumps({"schema_version": "legacy-46", "request_id": "x", "operation": "step"}))
            self.assertEqual(legacy["error"]["code"], "UNSUPPORTED_SCHEMA")
            with self.assertRaises(RpcError) as ctx:
                client.request("step", episode_id="none", action=1)
            self.assertEqual(ctx.exception.code, "NO_EPISODE")
            for name, overrides in (("trace hash", {"trace_sha256": "f" * 64}), ("config hash", {"config_sha256": "e" * 64})):
                with self.subTest(name), self.assertRaises(RpcError) as ctx:
                    self.reset_request(client, **overrides)
                self.assertEqual(ctx.exception.code, "HASH_MISMATCH")
            self.reset_request(client)
            fields = {"episode_id": "t1", "config_sha256": CONFIG_SHA, "trace_sha256": self.light["payload_sha256"]}
            for bad in (7, -1, "x", 1.5, None):
                # Sent raw: the client would reject these before the wire, but the server must refuse them too.
                reply = client.send_raw_line(json.dumps({"schema_version": "research-v2.1", "request_id": f"bad-{bad}", "operation": "step",
                                                         "action": bad, **fields}))
                self.assertEqual((reply["status"], reply["error"]["code"]), ("error", "BAD_STEP"), bad)
            with self.assertRaises(RpcError) as ctx:
                client.request("step", action=1, **{**fields, "episode_id": "other"})
            self.assertEqual(ctx.exception.code, "BAD_STEP")
            # The episode survived every rejected frame: a valid step still works from the first decision.
            self.assertEqual(client.request("step", action=1, **fields)["step_index"], 1)
        finally:
            client.close()

    def test_engine_invariant_violation_is_reported_and_the_server_keeps_serving(self):
        broken = copy.deepcopy(self.light)
        broken["tasks"][-1]["timeout_relative_s"] = 30.0           # would outlive the horizon
        broken["tasks"][-1]["deadline_relative_s"] = 3.0
        broken["payload_sha256"] = trace_payload_sha256(broken)
        client = self.client()
        try:
            with self.assertRaises(RpcError) as ctx:
                self.reset_request(client, broken, trace_sha256=broken["payload_sha256"])
            self.assertEqual(ctx.exception.code, "ENGINE_ERROR")
            self.assertEqual(self.reset_request(client)["step_index"], 0)
        finally:
            client.close()

    def test_abrupt_client_loss_aborts_the_episode_without_a_result_and_the_server_recovers(self):
        client = self.client()
        self.reset_request(client)
        client.close()                                             # vanish mid-episode, no close frame
        time.sleep(0.3)
        env = self.env()
        try:
            obs, info = env.reset(seed=0)
            self.assertEqual(info["step_index"], 0)
        finally:
            env.close()

    def test_a_mid_episode_reset_over_the_wire_starts_a_fresh_episode(self):
        client = self.client()
        try:
            self.reset_request(client)
            fields = {"episode_id": "t1", "config_sha256": CONFIG_SHA, "trace_sha256": self.light["payload_sha256"]}
            for _ in range(5):
                client.request("step", action=1, **fields)
            fresh = self.reset_request(client, episode_id="t2")
            self.assertEqual((fresh["step_index"], fresh["task_id"], fresh["episode_id"]), (0, self.light["tasks"][0]["task_id"], "t2"))
        finally:
            client.close()

    # ---- legacy refusal ------------------------------------------------------------------------------

    def test_legacy_four_weights_and_46_feature_policies_are_refused(self):
        with self.assertRaises(LegacyIncompatibleError):
            validate_weights([0.25, 0.25, 0.25, 0.25])
        with self.assertRaises(LegacyIncompatibleError):
            check_policy_interface(46, 7)
        for bad in ([0.5, 0.5, 0.5, 0.5, 0.5], [-0.1, 0.3, 0.3, 0.3, 0.2], [0.2, 0.2, 0.2, 0.2], [float("nan")] + [0.25] * 4):
            with self.subTest(weights=bad), self.assertRaises(ContractError):
                validate_weights(bad)
        check_policy_interface(108, 7)
        with self.assertRaises(LegacyIncompatibleError):
            self.env(weights=[0.25] * 4)

    def test_feature_computation_uses_neither_workload_label_seed_weights_nor_task_count(self):
        env = self.env()
        try:
            _, info = env.reset(seed=0)
        finally:
            env.close()
        forbidden = ("workload", "seed", "weight", "task_count", "total", "horizon")
        self.assertFalse([name for name in FEATURES if any(word in name for word in forbidden)])
        self.assertFalse([name for name in FEATURES if name.startswith("source.") and "iot" in name], "no raw device id")


@unittest.skipUnless(find_java(), "Set JAVA_HOME to a JDK >= 21 for P05 socket/Gym tests")
class ConnectionFailureTests(unittest.TestCase):
    """Each test owns its server because it kills it or lets timers expire."""

    def trace(self):
        return calibration_trace("light")

    def test_killed_server_raises_and_never_reports_success(self):
        server = ServerProcess(CONFIG, any_port=True)
        env = OffloadingEnv([self.trace()], EQUAL, config=CONFIG, host=server.host, port=server.port, rpc_timeout_s=10.0)
        try:
            env.reset(seed=0)
            for _ in range(3):
                env.step(1)
            server.process.kill()
            server.process.wait()
            with self.assertRaises(ConnectionLostError):
                env.step(1)
            with self.assertRaises(ConnectionLostError):      # the environment stays unusable; it never fakes a terminal state
                env.reset(seed=0)
        finally:
            env.close()
            server.close()

    def test_idle_connection_hits_the_server_rpc_timeout_and_the_episode_is_lost(self):
        server = ServerProcess(CONFIG, any_port=True, rpc_timeout_s=1.0)
        env = OffloadingEnv([self.trace()], EQUAL, config=CONFIG, host=server.host, port=server.port, rpc_timeout_s=10.0)
        try:
            env.reset(seed=0)
            time.sleep(2.0)
            with self.assertRaises(ConnectionLostError):
                env.step(1)
        finally:
            env.close()
            server.close()

    def test_heartbeats_keep_a_slow_client_alive(self):
        server = ServerProcess(CONFIG, any_port=True, rpc_timeout_s=1.0)
        env = OffloadingEnv([self.trace()], EQUAL, config=CONFIG, host=server.host, port=server.port, rpc_timeout_s=10.0)
        try:
            env.reset(seed=0)
            for _ in range(5):
                time.sleep(0.4)
                env.heartbeat()
            _, _, terminated, _, info = env.step(1)         # 2 s of wall time passed, the episode is intact
            self.assertFalse(terminated)
            self.assertEqual(info["step_index"], 1)
        finally:
            env.close()
            server.close()

    def test_server_refuses_ports_outside_the_configured_allow_list(self):
        with self.assertRaises(RuntimeError):
            ServerProcess(CONFIG, port=39999)

    def test_wrong_config_hash_binding_is_refused_at_reset(self):
        server = ServerProcess(CONFIG, any_port=True)
        other_config = copy.deepcopy(CONFIG)
        other_config["execution"]["technical_retries"] = 3
        try:
            client = V2Client(server.host, server.port, timeout_s=30.0)
            trace = self.trace()
            with self.assertRaises(RpcError) as ctx:
                client.request("reset", episode_id="x", config_sha256=sha256(other_config), trace_sha256=trace["payload_sha256"], trace=trace)
            self.assertEqual(ctx.exception.code, "HASH_MISMATCH")
            client.close()
        finally:
            server.close()


if __name__ == "__main__":
    unittest.main()
