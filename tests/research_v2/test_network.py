"""P03 acceptance tests N01–N06 and failure paths for the store-and-forward transport.

Expected times are computed here from the specification (serialization = 8 * bytes / bit_per_s, then propagation;
a server is held only while serializing), never copied from engine output.
"""

import json
import math
import unittest

from research_v2.config import load_config
from research_v2.engine_runner import EngineError, JAR, find_java, run_engine, scenario_from_trace
from research_v2.trace_access import TraceKey
from research_v2.traces import TraceGenerator

GIB = 1 << 30
MIB = 1 << 20
ACCESS = (20_000_000.0, 0.002)
LAN = (1_000_000_000.0, 0.0005)
WAN = (50_000_000.0, 0.02)
TIMING = {"arrival_window_s": 60.0, "horizon_s": 69.0}


def ser(num_bytes, link):
    return 8.0 * num_bytes / link[0]


def path_time(num_bytes, links):
    """Store-and-forward time over idle links: serialization plus propagation per hop."""
    return sum(ser(num_bytes, link) + link[1] for link in links)


def node(node_id, pes=2, mips=1000, ram=GIB, queue=16):
    return {"id": node_id, "pes": pes, "mips_per_pe": mips, "ram_bytes": ram, "queue_waiting": queue, "idle_w": 1.0, "busy_w": 2.0}


def nodes():
    return [node(f"F{k}") for k in range(1, 6)] + [node("cloud", pes=8, queue=64), node("IoT-0", pes=1, mips=500, queue=2)]


def task(task_id, source=0, input_bytes=MIB, output_bytes=None, mi=100, arrival=0.0, deadline=3.0, timeout=9.0):
    return {"task_id": task_id, "source_iot": source, "access_fog": source // 20 + 1, "class_id": "light", "arrival_s": arrival,
            "cpu_mi": mi, "input_bytes": input_bytes, "output_bytes": output_bytes or math.ceil(0.05 * input_bytes),
            "working_set_bytes": 0, "deadline_relative_s": deadline, "timeout_relative_s": timeout}


def run(tasks, action="F1", overrides=None, node_list=None, log=True, **extra):
    value = {"label": "net", "tasks": tasks, "nodes": node_list or nodes(), "actions": action, "timing": dict(TIMING),
             "network": {"log_transfers": log, **({"overrides": overrides} if overrides else {})}, **extra}
    return run_engine(value)["episodes"][0]


def by_id(episode):
    return {t["task_id"]: t for t in episode["tasks"]}


def link(episode, link_id):
    return next(item for item in episode["links"] if item["id"] == link_id)


def hops(episode, task_id, phase):
    return [h for h in episode["transfers"] if h["task_id"] == task_id and h["phase"] == phase]


@unittest.skipUnless(find_java(), "Set JAVA_HOME to a JDK >= 21 for P03 network tests")
class NetworkAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(JAR.exists(), "Build the v2 JAR first: python ifogsim/build_v2.py --self-test")

    def test_n01_n04_fog_access_round_trip_uses_only_the_wireless_channel(self):
        episode = run([task(0, output_bytes=52429)])
        t = by_id(episode)[0]
        self.assertAlmostEqual(ser(MIB, ACCESS), 0.4194304, places=12)
        self.assertAlmostEqual(t["input_arrived_s"], 0.4194304 + 0.002, places=9)  # N01: 0.4214304
        self.assertAlmostEqual(t["cpu_finish_s"], 0.4214304 + 0.1, places=9)
        back = ser(52429, ACCESS) + ACCESS[1]
        self.assertAlmostEqual(back, 0.0229716, places=9)  # N04
        self.assertAlmostEqual(t["delivered_s"], 0.4214304 + 0.1 + back, places=9)
        self.assertEqual(t["terminal"], "ON_TIME")  # about 0.544 s against the 3 s deadline
        # The access channel is used both ways; LAN/WAN are untouched and the node ran the CPU once (no transfer time added).
        access = link(episode, "access-F1")
        self.assertEqual((access["up_bytes_sent"], access["down_bytes_sent"]), (float(MIB), 52429.0))
        self.assertAlmostEqual(access["up_busy_s"], ser(MIB, ACCESS), places=9)
        self.assertAlmostEqual(access["down_busy_s"], ser(52429, ACCESS), places=9)
        for item in episode["links"]:
            if item["link_type"] != "access":
                self.assertEqual(item["busy_s_total"], 0.0, item["id"])

    def test_n02_second_transfer_starts_when_serialization_ends_not_after_propagation(self):
        episode = run([task(0, source=0), task(1, source=1)])
        by = by_id(episode)
        first, second = ser(MIB, ACCESS) + ACCESS[1], 2 * ser(MIB, ACCESS) + ACCESS[1]
        self.assertAlmostEqual(by[0]["input_arrived_s"], first, places=9)       # 0.4214304
        self.assertAlmostEqual(by[1]["input_arrived_s"], second, places=9)      # 0.8408608
        second_hop = hops(episode, 1, "INPUT")[0]
        self.assertAlmostEqual(second_hop["serialization_start_s"], ser(MIB, ACCESS), places=9)  # server freed at 0.4194304
        self.assertAlmostEqual(second_hop["queue_enter_s"], 0.0, places=12)
        self.assertEqual(link(episode, "access-F1")["max_waiting"], 1)

    def test_n03_half_duplex_channel_is_shared_but_other_channels_and_directions_are_not(self):
        # X: tiny input, result ready at 0.1024 s. Y: 1 MiB upload that occupies the channel from 0.05 s.
        x = task(0, source=0, input_bytes=1000, output_bytes=50)
        same = run([x, task(1, source=1, arrival=0.05)])
        busy_until = 0.05 + ser(MIB, ACCESS)
        self.assertAlmostEqual(by_id(same)[0]["delivered_s"], busy_until + ser(50, ACCESS) + ACCESS[1], places=9)
        # Y from another fog's channel (source 20 -> F1) leaves X's channel free.
        other = run([x, task(1, source=20, arrival=0.05)])
        ready = ser(1000, ACCESS) + ACCESS[1] + 0.1
        self.assertAlmostEqual(by_id(other)[0]["delivered_s"], ready + ser(50, ACCESS) + ACCESS[1], places=9)
        self.assertEqual(link(other, "access-F2")["up_started"], 1)

    def test_n03_full_duplex_lan_directions_have_independent_servers(self):
        # P: F1 -> F2 uses lan-F1-up then lan-F2-down. R: F2-access -> F1 uses lan-F2-up then lan-F1-down.
        # P is delayed so that R's lan-F1-down and P's lan-F1-up overlap in time.
        d = ser(MIB, LAN)
        p = task(0, source=0, arrival=LAN[1] + d / 2)
        r = task(1, source=20, arrival=0.0)
        episode = run([p, r], action={"default": "F1", "0": "F2"})
        p_up = [h for h in hops(episode, 0, "INPUT") if h["server"] == "lan-F1-up"][0]
        r_down = [h for h in hops(episode, 1, "INPUT") if h["server"] == "lan-F1-down"][0]
        self.assertLess(r_down["serialization_start_s"], p_up["serialization_end_s"])
        self.assertLess(p_up["serialization_start_s"], r_down["serialization_end_s"])
        # Neither waited: each started the moment it reached the hop.
        self.assertAlmostEqual(r_down["queue_enter_s"], r_down["serialization_start_s"], places=12)
        self.assertAlmostEqual(p_up["queue_enter_s"], p_up["serialization_start_s"], places=12)
        ids = {item["id"] for item in episode["links"]}
        self.assertTrue({"lan-F1-up", "lan-F1-down", "wan-up", "wan-down", "access-F1"} <= ids)
        self.assertNotIn("access-F1-up", ids, "access channels are half duplex: one shared server")

    def test_n05_multihop_store_and_forward_and_reverse_result_path(self):
        cpu = 0.1
        for target, forward, backward in (
                ("F1", [ACCESS], [ACCESS]),
                ("F3", [ACCESS, LAN, LAN], [LAN, LAN, ACCESS]),
                ("cloud", [ACCESS, LAN, WAN], [WAN, LAN, ACCESS])):
            with self.subTest(target=target):
                episode = run([task(0, output_bytes=52429, timeout=20.0, deadline=10.0)], action=target)
                t = by_id(episode)[0]
                arrive = path_time(MIB, forward)
                self.assertAlmostEqual(t["input_arrived_s"], arrive, places=9)
                self.assertAlmostEqual(t["delivered_s"], arrive + cpu + path_time(52429, backward), places=9)
                # Each hop of the input is serialized exactly once, in order, after the previous hop arrived.
                chain = hops(episode, 0, "INPUT")
                self.assertEqual(len(chain), len(forward))
                for before, after in zip(chain, chain[1:]):
                    self.assertGreaterEqual(after["serialization_start_s"], before["arrival_s"] - 1e-12)
                # Bit-hops on wired links: every wired hop counted once per message and direction.
                wired = [h for h in chain + hops(episode, 0, "RESULT") if not h["server"].startswith("access")]
                lan_wan_bits = sum(8 * item["up_bytes_sent"] + 8 * item["down_bytes_sent"] for item in episode["links"] if item["link_type"] != "access")
                self.assertEqual(lan_wan_bits, sum(8 * h["bytes_sent"] for h in wired))

    def test_n06_timeout_mid_serialization_counts_partial_bytes_and_releases_the_server(self):
        doomed = task(0, source=0, deadline=0.05, timeout=0.1)
        follower = task(1, source=1, arrival=0.01)
        episode = run([doomed, follower])
        by = by_id(episode)
        self.assertEqual((by[0]["terminal"], by[0]["failure_reason"], by[0]["terminal_s"]), ("FAILED", "SERVICE_TIMEOUT", 0.1))
        partial = hops(episode, 0, "INPUT")[0]
        self.assertEqual(partial["status"], "cancelled_in_service")
        self.assertAlmostEqual(partial["bytes_sent"], 0.1 * ACCESS[0] / 8.0, places=3)  # 2,000,000 bits = 250,000 bytes
        # Only the serialized interval is busy time; the follower starts the instant the timeout frees the server.
        access = link(episode, "access-F1")
        self.assertAlmostEqual(access["up_busy_s"], 0.1 + ser(MIB, ACCESS), places=9)
        self.assertAlmostEqual(access["up_bytes_sent"], 250_000.0 + MIB, places=3)
        self.assertAlmostEqual(hops(episode, 1, "INPUT")[0]["serialization_start_s"], 0.1, places=12)
        # The cancelled message's old completion is stale, and the node never saw the task.
        self.assertEqual(episode["stale_by_kind"].get("SERIALIZATION_DONE"), 1)
        self.assertEqual(next(n for n in episode["nodes"] if n["id"] == "F1")["admitted"], 1)

    # ---- queues, cancellation phases and result path --------------------------------------------------

    def test_full_link_queue_fails_with_network_queue_full_and_holds_nothing(self):
        episode = run([task(0, source=0), task(1, source=1), task(2, source=2)], overrides={"access": {"queue_waiting": 1}})
        by = by_id(episode)
        self.assertEqual((by[2]["terminal"], by[2]["failure_reason"], by[2]["terminal_s"]), ("FAILED", "NETWORK_QUEUE_FULL", 0.0))
        self.assertIsNone(by[2]["input_arrived_s"])
        self.assertEqual((by[0]["terminal"], by[1]["terminal"]), ("ON_TIME", "ON_TIME"))
        access = link(episode, "access-F1")
        self.assertEqual((access["up_rejected_queue_full"], access["max_waiting"], access["up_started"]), (1, 1, 2))
        self.assertEqual(next(n for n in episode["nodes"] if n["id"] == "F1")["admitted"], 2)

    def test_result_queue_full_after_cpu_still_counts_the_work(self):
        # Task 0 occupies the access channel downlink with a 1 MiB result from 0.1024 s; task 1's result finds it busy.
        t0 = task(0, source=0, input_bytes=1000, output_bytes=MIB)
        t1 = task(1, source=1, input_bytes=1000, output_bytes=50, arrival=0.1)
        episode = run([t0, t1], overrides={"access": {"queue_waiting": 0}})
        by = by_id(episode)
        self.assertEqual(by[0]["terminal"], "ON_TIME")
        self.assertEqual((by[1]["terminal"], by[1]["failure_reason"]), ("FAILED", "NETWORK_QUEUE_FULL"))
        self.assertIsNotNone(by[1]["cpu_finish_s"], "CPU finished before the result could not be sent")
        self.assertEqual(link(episode, "access-F1")["down_rejected_queue_full"], 1)
        self.assertEqual(next(n for n in episode["nodes"] if n["id"] == "F1")["ram_used_end_bytes"], 0)

    def test_timeout_while_waiting_in_a_link_queue_sends_nothing(self):
        # Task 1 waits behind task 0's upload and times out before the server is free.
        episode = run([task(0, source=0), task(1, source=1, deadline=0.1, timeout=0.2)])
        waiting = hops(episode, 1, "INPUT")[0]
        self.assertEqual((waiting["status"], waiting["bytes_sent"]), ("cancelled_waiting", 0.0))
        self.assertEqual(link(episode, "access-F1")["up_cancelled"], 1)
        self.assertEqual(by_id(episode)[1]["failure_reason"], "SERVICE_TIMEOUT")

    def test_timeout_during_propagation_keeps_full_bytes_and_ignores_the_arrival(self):
        done = ser(MIB, ACCESS)
        episode = run([task(0, deadline=0.1, timeout=done + 0.001)])  # after serialization, before the 2 ms propagation ends
        t = by_id(episode)[0]
        self.assertEqual(t["failure_reason"], "SERVICE_TIMEOUT")
        access = link(episode, "access-F1")
        self.assertEqual((access["up_bytes_sent"], access["up_completed"], access["up_cancelled"]), (float(MIB), 1, 0))
        self.assertEqual(episode["stale_by_kind"].get("HOP_ARRIVED"), 1)
        self.assertEqual(next(n for n in episode["nodes"] if n["id"] == "F1")["admitted"], 0)

    def test_timeout_during_result_return_counts_partial_result_bytes(self):
        big = MIB  # result serialization 0.4194304 s starting at cpu_finish
        start = ser(1000, ACCESS) + ACCESS[1] + 0.1
        episode = run([task(0, input_bytes=1000, output_bytes=big, deadline=0.2, timeout=start + 0.2)])
        t = by_id(episode)[0]
        self.assertEqual((t["terminal"], t["failure_reason"]), ("FAILED", "SERVICE_TIMEOUT"))
        result = hops(episode, 0, "RESULT")[0]
        self.assertEqual(result["status"], "cancelled_in_service")
        self.assertAlmostEqual(result["bytes_sent"], 0.2 * ACCESS[0] / 8.0, delta=1.0)
        self.assertIsNotNone(t["cpu_finish_s"])

    def test_local_task_crosses_no_link(self):
        episode = run([task(0, source=0, mi=100)], action="source_iot")
        self.assertEqual(by_id(episode)[0]["terminal"], "ON_TIME")
        self.assertTrue(all(item["busy_s_total"] == 0.0 for item in episode["links"]))
        self.assertEqual(episode["transfers"], [])

    # ---- invalid network scenarios --------------------------------------------------------------------

    def test_invalid_network_scenarios_are_rejected(self):
        base = {"label": "bad", "tasks": [task(0)], "nodes": nodes(), "actions": "F1", "timing": dict(TIMING), "network": {}}
        cases = {
            "network and fixture together": {**base, "fixture_transport": {"input_delay_s": 0.0}},
            "unknown override type": {**base, "network": {"overrides": {"satellite": {"queue_waiting": 1}}}},
            "unknown override field": {**base, "network": {"overrides": {"access": {"nonsense": 1}}}},
            "node not routable": {**base, "nodes": [node("N")], "actions": "N"},
            "access fog contradicts source": {**base, "tasks": [{**task(0), "access_fog": 3}]},
            "full duplex access override": {**base, "network": {"overrides": {"access": {"duplex": "full"}}}},
        }
        for name, scenario in cases.items():
            with self.subTest(name), self.assertRaises(EngineError):
                run_engine(scenario)


@unittest.skipUnless(find_java(), "Set JAVA_HOME to a JDK >= 21 for P03 network tests")
class NetworkOnRealTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()
        cls.generator = TraceGenerator(cls.config)

    def trace(self, workload, trace_id=0):
        key = TraceKey(self.config["seeds"]["master"], "calibration", None, None, trace_id, workload)
        return self.generator.generate(key, role="calibrator").to_dict()

    def episode(self, workload, action, **kwargs):
        trace = self.trace(workload)
        value = scenario_from_trace(trace, action, topology={"homogeneous_fog": False}, label=workload, **kwargs)
        value["network"] = {"log_transfers": True}
        return trace, run_engine(value)["episodes"][0]

    def check_links(self, episode):
        by_server = {}
        for h in episode["transfers"]:
            by_server.setdefault(h["server"], []).append(h)
        for server, items in by_server.items():
            served = sorted((h for h in items if h["serialization_start_s"] is not None), key=lambda h: (h["serialization_start_s"], h["task_id"]))
            # One message at a time per server (half-duplex access shares across directions).
            for before, after in zip(served, served[1:]):
                self.assertLessEqual(before["serialization_end_s"], after["serialization_start_s"] + 1e-9, server)
            # FCFS: service order follows queue-entry order.
            entered = [h["queue_enter_s"] for h in served]
            self.assertEqual(entered, sorted(entered), f"{server} served out of order")
        for item in episode["links"]:
            self.assertLessEqual(item["busy_s_total"], episode["horizon_s"] + 1e-9, item["id"])
            self.assertLessEqual(item["max_waiting"], item["queue_waiting_limit"])
            self.assertEqual((item["active_end"], item["waiting_end"]), (False, 0))
            logged = sum(h["bytes_sent"] for h in by_server.get(item["id"], []))
            self.assertAlmostEqual(logged, item["up_bytes_sent"] + item["down_bytes_sent"], delta=1e-3 * max(1.0, logged), msg=item["id"])

    def test_every_workload_conserves_tasks_and_respects_link_rules(self):
        for workload in ("light", "moderate", "heavy", "dynamic"):
            with self.subTest(workload=workload):
                trace, episode = self.episode(workload, "nearest_fog")
                self.assertEqual(episode["on_time"] + episode["late_success"] + episode["failed"], trace["task_count"])
                self.assertEqual(episode["finished_at_s"], 69.0)
                self.assertTrue(set(episode["failure_reasons"]) <= {"CPU_QUEUE_FULL", "RAM_EXHAUSTED", "NETWORK_QUEUE_FULL", "SERVICE_TIMEOUT"})
                self.check_links(episode)

    def test_multihop_routes_never_forward_before_the_previous_hop_arrived(self):
        trace, episode = self.episode("light", "F3")
        self.assertGreater(len([t for t in episode["tasks"] if t["input_arrived_s"] is not None]), 0)
        for task_id in {h["task_id"] for h in episode["transfers"]}:
            for phase in ("INPUT", "RESULT"):
                chain = [h for h in hops(episode, task_id, phase) if h["status"] == "serialized"]
                for before, after in zip(chain, chain[1:]):
                    self.assertGreaterEqual(after["queue_enter_s"], before["arrival_s"] - 1e-9)
        self.check_links(episode)

    def test_heavy_offered_load_on_access_channels_matches_the_specified_1_22_ratio(self):
        trace = self.trace("heavy")
        bits = sum(8 * (t["input_bytes"] + t["output_bytes"]) for t in trace["tasks"])
        ratio = bits / 5 / (ACCESS[0] * 60.0)
        self.assertTrue(1.10 < ratio < 1.35, ratio)  # section 12.2: about 1.22x if everything is offloaded
        _, episode = self.episode("heavy", "nearest_fog")
        access_busy = [link(episode, f"access-F{k}")["busy_s_total"] for k in range(1, 6)]
        self.assertTrue(all(b <= 69.0 + 1e-9 for b in access_busy))
        # Offered load above capacity must show up as link-level failures or saturation, not vanish.
        self.assertTrue(episode["failure_reasons"].get("NETWORK_QUEUE_FULL", 0) > 0 or max(access_busy) > 60.0, (episode["failure_reasons"], access_busy))

    def test_network_runs_repeat_identically_in_one_jvm_and_across_jvms(self):
        trace = self.trace("dynamic")
        value = scenario_from_trace(trace, "nearest_fog", topology={"homogeneous_fog": False}, repeat=2)
        value["network"] = {"log_transfers": False}
        strip = lambda e: json.dumps({k: v for k, v in e.items() if k != "episode_id"}, sort_keys=True)
        first = run_engine(value)["episodes"]
        self.assertEqual(strip(first[0]), strip(first[1]))
        self.assertEqual(strip(first[0]), strip(run_engine(value)["episodes"][0]))


if __name__ == "__main__":
    unittest.main()
