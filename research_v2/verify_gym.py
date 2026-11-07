"""P05 milestone audit: socket protocol, Gymnasium environment, 108-feature observation and delayed reward."""

import argparse
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import sys
import unittest

from .__main__ import export_documents, file_hash
from .config import ROOT, read_json, require

# Acceptance IDs (docs/research_v2/ACCEPTANCE_TESTS.md) and the P05 pass criteria -> tests that must all pass.
ACCEPTANCE = {
    "G01": ["test_one_step_per_arrival_and_termination_at_the_horizon",
            "test_step_after_termination_requires_reset",
            "test_completion_reward_arrives_at_the_decision_after_it_happens",
            "test_costs_are_nondecreasing_and_terminal_cost_includes_the_drain"],
    "G02": ["test_return_equals_minus_100_times_weighted_costs_for_every_workload_and_weighting",
            "test_each_outcome_kind_charges_deadline_and_failure_cost_exactly_once"],
    "G03": ["test_killed_server_raises_and_never_reports_success",
            "test_idle_connection_hits_the_server_rpc_timeout_and_the_episode_is_lost",
            "test_engine_invariant_violation_is_reported_and_the_server_keeps_serving",
            "test_malformed_legacy_and_mismatched_requests_get_errors_not_crashes"],
    "gymnasium_environment_checker": ["test_gymnasium_environment_checker_passes"],
    "observation_108_features": ["test_observation_vector_follows_the_wire_contract_order",
                                 "test_all_108_features_match_independent_computation_on_an_idle_system",
                                 "test_loaded_node_features_match_hand_computation",
                                 "test_second_decision_sees_the_current_backlog_and_partial_energy_but_nothing_future"],
    "no_future_information": ["test_observation_does_not_depend_on_future_arrivals",
                              "test_feature_computation_uses_neither_workload_label_seed_weights_nor_task_count"],
    "episode_isolation": ["test_consecutive_and_interrupted_episodes_do_not_contaminate_each_other",
                          "test_same_seed_gives_identical_transcripts_in_separate_servers",
                          "test_a_mid_episode_reset_over_the_wire_starts_a_fresh_episode"],
    "engine_equivalence": ["test_socket_episode_equals_the_headless_run_with_the_same_actions"],
    "handshake_and_idempotency": ["test_handshake_identifies_the_exact_jar_config_and_contract",
                                  "test_identical_retry_gets_the_cached_answer_and_is_not_applied_twice",
                                  "test_wrong_config_hash_binding_is_refused_at_reset"],
    "heartbeat_and_timeouts": ["test_heartbeats_keep_a_slow_client_alive",
                               "test_abrupt_client_loss_aborts_the_episode_without_a_result_and_the_server_recovers"],
    "legacy_refusal": ["test_legacy_four_weights_and_46_feature_policies_are_refused",
                       "test_server_refuses_ports_outside_the_configured_allow_list"],
}
ENGINE_SOURCES = ("BoundedFcfsScheduler", "ComputeNode", "EngineCoordinator", "EngineMain", "Json", "MetricsLedger", "NetworkModel",
                  "NodeSpec", "ObservationBuilder", "TaskSpec", "V2SocketServer")
PYTHON_SOURCES = ("rpc_client.py", "gym_env.py")


def flatten(tests):
    for item in tests:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def source_fingerprint():
    """Engine Java and client Python sources, line endings normalized so CRLF and LF checkouts agree."""
    folder = ROOT / "ifogsim/src/org/fog/erwo/v2"
    digest = {f"java/{name}": hashlib.sha256((folder / f"{name}.java").read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name in ENGINE_SOURCES}
    digest.update({f"python/{name}": hashlib.sha256((ROOT / "research_v2" / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name in PYTHON_SOURCES})
    return hashlib.sha256(json.dumps(digest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jdk-home", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/research_v2/milestones/P05_verification.json")
    args = parser.parse_args()
    if args.jdk_home:
        os.environ["JAVA_HOME"] = str(args.jdk_home.resolve())
    for path, expected in export_documents().items():
        require(read_json(path) == expected, f"Stale schema export: {path}")
    receipt = read_json(ROOT / "ifogsim/build/research_v2/build_receipt.json")
    require(file_hash(ROOT / receipt["artifact"]) == receipt["artifact_sha256"], "Build artifact hash mismatch")
    for name, expected in receipt["inputs"].items():
        require(file_hash(ROOT / name) == expected, f"Build input changed: {name}; rebuild before verification")
    suite = unittest.TestLoader().discover(str(ROOT / "tests/research_v2"), pattern="test_gym.py")
    ran = {t.id().split(".")[-1] for t in flatten(suite)}     # before running: a TestSuite empties itself as it executes
    log = io.StringIO()
    tests = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    bad = {t.id().split(".")[-1] for t, _ in tests.failures + tests.errors + tests.skipped}
    acceptance = {case: ("fail" if any(m in bad for m in methods) else "pass") for case, methods in ACCEPTANCE.items()}
    covered = {m for methods in ACCEPTANCE.values() for m in methods}
    unmapped = sorted(ran - covered)
    passed = tests.wasSuccessful() and not tests.skipped and all(v == "pass" for v in acceptance.values())
    packages = {}
    for name in ("numpy", "jsonschema", "gymnasium"):
        dist = importlib.metadata.distribution(name)
        packages[name] = {"version": dist.version, "installed_record_sha256": hashlib.sha256((dist.read_text("RECORD") or "").encode()).hexdigest()}
    output = {"phase": "P05", "status": "pass" if passed else "failed", "tests_run": tests.testsRun,
              "failures": len(tests.failures), "errors": len(tests.errors), "skipped": len(tests.skipped),
              "acceptance": acceptance, "tests_not_mapped_to_a_criterion": unmapped,
              "source_sha256": source_fingerprint(), "test_log": log.getvalue(),
              "environment": {"python": sys.version, "platform": platform.platform(), "packages": packages},
              "build_receipt": receipt,
              "limitations": ["Loopback TCP only, one client and one simulation per server JVM (CloudSim static state)",
                              "Java does not recompute the canonical config/trace hashes: it binds the server to --config-sha256, checks the request's trace hash "
                              "against the trace's declared payload_sha256, and the client verifies the JAR hash against the build receipt",
                              "The observation is an aggregate snapshot, not a Markov state: pending transfers, queued deadlines and the task list are only summarized",
                              "The route features are estimates from current queues; outcomes always come from the engine",
                              "Fixed and random actions only; no PPO, no learning claim",
                              "A dropped connection loses the episode (raises); there is no partial-episode resume",
                              "Rewards are computed in Python from Java's cumulative cost deltas; Java does not know the reward weights"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: output[k] for k in ("phase", "status", "tests_run", "failures", "errors", "skipped", "acceptance", "tests_not_mapped_to_a_criterion")}))
    if not passed:
        print(log.getvalue(), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
