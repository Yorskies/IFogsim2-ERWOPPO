"""P04 milestone audit: energy ledger, metrics and independent re-evaluation, with acceptance E01–E04 and M01–M03."""

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

# Acceptance IDs (docs/research_v2/ACCEPTANCE_TESTS.md) -> the test methods that must all pass for the case.
ACCEPTANCE = {
    "E01": ["test_e01_idle_system_pays_idle_power_for_the_whole_horizon_and_nothing_dynamic"],
    "E02": ["test_e02_local_cpu_adds_only_the_dynamic_increment"],
    "E03": ["test_e03_wireless_upload_adds_tx_plus_rx_during_serialization_only",
            "test_e03b_wired_hops_cost_joules_per_bit_hop"],
    "E04": ["test_e04_fog_imbalance_is_integrated_over_time"],
    "M01": ["test_m01_counts_and_ratios_share_one_denominator"],
    "M02": ["test_m02_failed_task_is_penalized_in_zL_but_absent_from_physical_latency"],
    "M03": ["test_m03_no_completed_task_gives_null_statistics_not_zero"],
    "independent_evaluator": ["test_engine_ledger_equals_independent_recomputation_for_every_workload_and_mode",
                              "test_link_aggregates_agree_with_the_hop_log_when_the_log_is_off"],
}
ENGINE_SOURCES = ("BoundedFcfsScheduler", "ComputeNode", "EngineCoordinator", "EngineMain", "Json", "MetricsLedger", "NetworkModel", "NodeSpec", "TaskSpec")


def engine_source_sha256():
    """Engine Java fingerprint with line endings normalized, so CRLF and LF checkouts agree."""
    folder = ROOT / "ifogsim/src/org/fog/erwo/v2"
    digest = {name: hashlib.sha256((folder / f"{name}.java").read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name in ENGINE_SOURCES}
    return hashlib.sha256(json.dumps(digest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jdk-home", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/research_v2/milestones/P04_verification.json")
    args = parser.parse_args()
    if args.jdk_home:
        os.environ["JAVA_HOME"] = str(args.jdk_home.resolve())
    for path, expected in export_documents().items():
        require(read_json(path) == expected, f"Stale schema export: {path}")
    receipt = read_json(ROOT / "ifogsim/build/research_v2/build_receipt.json")
    require(file_hash(ROOT / receipt["artifact"]) == receipt["artifact_sha256"], "Build artifact hash mismatch")
    for name, expected in receipt["inputs"].items():
        require(file_hash(ROOT / name) == expected, f"Build input changed: {name}; rebuild before verification")
    suite = unittest.TestLoader().discover(str(ROOT / "tests/research_v2"), pattern="test_accounting.py")
    log = io.StringIO()
    tests = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    bad = {t.id().split(".")[-1] for t, _ in tests.failures + tests.errors + tests.skipped}
    acceptance = {case: ("fail" if any(m in bad for m in methods) else "pass") for case, methods in ACCEPTANCE.items()}
    passed = tests.wasSuccessful() and not tests.skipped and all(v == "pass" for v in acceptance.values())
    packages = {}
    for name in ("numpy", "jsonschema"):
        dist = importlib.metadata.distribution(name)
        packages[name] = {"version": dist.version, "installed_record_sha256": hashlib.sha256((dist.read_text("RECORD") or "").encode()).hexdigest()}
    output = {"phase": "P04", "status": "pass" if passed else "failed", "tests_run": tests.testsRun,
              "failures": len(tests.failures), "errors": len(tests.errors), "skipped": len(tests.skipped),
              "acceptance": acceptance, "engine_source_sha256": engine_source_sha256(), "test_log": log.getvalue(),
              "environment": {"python": sys.version, "platform": platform.platform(), "packages": packages},
              "build_receipt": receipt,
              "limitations": ["Parameters are synthetic assumptions (section 11); energy is IT-modeled system energy, not facility electricity",
                              "No dynamic power during queue waiting or propagation; no retransmission or DVFS (section 15)",
                              "The evaluator shares the config with the engine; it is independent code and independent raw inputs, not an independent specification",
                              "Reward, normalization-by-validation and aggregation across traces/workloads (Dglobal) are P05/P10 work; only per-trace costs and D exist here",
                              "Fixture transport models no communication energy; communication is accounted only in network mode",
                              "Fixed-policy checks on calibration traces are not a method benchmark; no production test split was used"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: output[k] for k in ("phase", "status", "tests_run", "failures", "errors", "skipped", "acceptance")}))
    if not passed:
        print(log.getvalue(), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
