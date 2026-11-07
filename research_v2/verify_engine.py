"""P02 milestone audit: headless event-engine tests, build provenance and acceptance C01–C08 status."""

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

# Acceptance IDs (docs/research_v2/ACCEPTANCE_TESTS.md) -> test method that exercises them.
ACCEPTANCE = {
    "C01": "test_c01_single_task_cpu_time_and_native_cloudlet_finishes",
    "C02": "test_c02_fcfs_one_pe_order_by_id_and_busy_never_above_one",
    "C03": "test_c03_two_pes_pin_smallest_free_pe",
    "C04": "test_c04_bounded_queue_rejects_third_task_without_reroute",
    "C05": "test_c05_ram_rejection_holds_no_pe_or_queue_slot",
    "C06": "test_c06_deadline_and_timeout_boundaries",
    "C07": "test_c07_timeout_cancels_cpu_frees_resources_and_voids_stale_completion",
    "C08": "test_c08_horizon_is_fixed_and_counts_conserve",
}
ENGINE_SOURCES = ("BoundedFcfsScheduler", "ComputeNode", "EngineCoordinator", "EngineMain", "Json", "NodeSpec", "TaskSpec")


def engine_source_sha256():
    """Fingerprint of the engine Java sources with line endings normalized, so CRLF checkouts match LF ones."""
    folder = ROOT / "ifogsim/src/org/fog/erwo/v2"
    digest = {name: hashlib.sha256((folder / f"{name}.java").read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name in ENGINE_SOURCES}
    return hashlib.sha256(json.dumps(digest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jdk-home", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/research_v2/milestones/P02_verification.json")
    args = parser.parse_args()
    if args.jdk_home:
        os.environ["JAVA_HOME"] = str(args.jdk_home.resolve())
    for path, expected in export_documents().items():
        require(read_json(path) == expected, f"Stale schema export: {path}")
    receipt = read_json(ROOT / "ifogsim/build/research_v2/build_receipt.json")
    require(file_hash(ROOT / receipt["artifact"]) == receipt["artifact_sha256"], "Build artifact hash mismatch")
    for name, expected in receipt["inputs"].items():
        require(file_hash(ROOT / name) == expected, f"Build input changed: {name}; rebuild before verification")
    suite = unittest.TestLoader().discover(str(ROOT / "tests/research_v2"), pattern="test_engine.py")
    log = io.StringIO()
    tests = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    bad = {t.id().split(".")[-1] for t, _ in tests.failures + tests.errors + tests.skipped}
    acceptance = {case: ("fail" if method in bad else "pass") for case, method in ACCEPTANCE.items()}
    passed = tests.wasSuccessful() and not tests.skipped and all(v == "pass" for v in acceptance.values())
    packages = {}
    for name in ("numpy", "jsonschema"):
        dist = importlib.metadata.distribution(name)
        packages[name] = {"version": dist.version, "installed_record_sha256": hashlib.sha256((dist.read_text("RECORD") or "").encode()).hexdigest()}
    output = {"phase": "P02", "status": "pass" if passed else "failed", "tests_run": tests.testsRun,
              "failures": len(tests.failures), "errors": len(tests.errors), "skipped": len(tests.skipped),
              "acceptance": acceptance, "engine_source_sha256": engine_source_sha256(), "test_log": log.getvalue(),
              "environment": {"python": sys.version, "platform": platform.platform(), "packages": packages},
              "build_receipt": receipt,
              "limitations": ["Fixture zero-network transport only: no link queues, serialization, propagation or routing (P03)",
                              "No energy ledger or physical latency/QoS metrics (P04); busy PE-seconds are recorded as a prerequisite",
                              "No socket, Gymnasium environment, observation or reward (P05)",
                              "Engine uses CloudSim for clock/event queue, Host/Vm/Pe/Cloudlet objects and the adapted space-shared scheduler; "
                              "completion times are exact (MI/MIPS) rather than native floor-MI progress",
                              "Static-state isolation shown for CloudSim clock/queue and engine objects across episodes; "
                              "FogDevice/TimeKeeper/NetworkUsageMonitor are not instantiated yet and remain to be re-audited"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: output[k] for k in ("phase", "status", "tests_run", "failures", "errors", "skipped", "acceptance")}))
    if not passed:
        print(log.getvalue(), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
