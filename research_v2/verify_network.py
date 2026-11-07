"""P03 milestone audit: transport tests, build provenance and acceptance N01–N06 status."""

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
    "N01": ["test_n01_n04_fog_access_round_trip_uses_only_the_wireless_channel"],
    "N02": ["test_n02_second_transfer_starts_when_serialization_ends_not_after_propagation"],
    "N03": ["test_n03_half_duplex_channel_is_shared_but_other_channels_and_directions_are_not",
            "test_n03_full_duplex_lan_directions_have_independent_servers"],
    "N04": ["test_n01_n04_fog_access_round_trip_uses_only_the_wireless_channel"],
    "N05": ["test_n05_multihop_store_and_forward_and_reverse_result_path"],
    "N06": ["test_n06_timeout_mid_serialization_counts_partial_bytes_and_releases_the_server"],
}
ENGINE_SOURCES = ("BoundedFcfsScheduler", "ComputeNode", "EngineCoordinator", "EngineMain", "Json", "NetworkModel", "NodeSpec", "TaskSpec")


def engine_source_sha256():
    """Engine Java fingerprint with line endings normalized, so CRLF and LF checkouts agree."""
    folder = ROOT / "ifogsim/src/org/fog/erwo/v2"
    digest = {name: hashlib.sha256((folder / f"{name}.java").read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name in ENGINE_SOURCES}
    return hashlib.sha256(json.dumps(digest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jdk-home", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/research_v2/milestones/P03_verification.json")
    args = parser.parse_args()
    if args.jdk_home:
        os.environ["JAVA_HOME"] = str(args.jdk_home.resolve())
    for path, expected in export_documents().items():
        require(read_json(path) == expected, f"Stale schema export: {path}")
    receipt = read_json(ROOT / "ifogsim/build/research_v2/build_receipt.json")
    require(file_hash(ROOT / receipt["artifact"]) == receipt["artifact_sha256"], "Build artifact hash mismatch")
    for name, expected in receipt["inputs"].items():
        require(file_hash(ROOT / name) == expected, f"Build input changed: {name}; rebuild before verification")
    suite = unittest.TestLoader().discover(str(ROOT / "tests/research_v2"), pattern="test_network.py")
    log = io.StringIO()
    tests = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    bad = {t.id().split(".")[-1] for t, _ in tests.failures + tests.errors + tests.skipped}
    acceptance = {case: ("fail" if any(m in bad for m in methods) else "pass") for case, methods in ACCEPTANCE.items()}
    passed = tests.wasSuccessful() and not tests.skipped and all(v == "pass" for v in acceptance.values())
    packages = {}
    for name in ("numpy", "jsonschema"):
        dist = importlib.metadata.distribution(name)
        packages[name] = {"version": dist.version, "installed_record_sha256": hashlib.sha256((dist.read_text("RECORD") or "").encode()).hexdigest()}
    output = {"phase": "P03", "status": "pass" if passed else "failed", "tests_run": tests.testsRun,
              "failures": len(tests.failures), "errors": len(tests.errors), "skipped": len(tests.skipped),
              "acceptance": acceptance, "engine_source_sha256": engine_source_sha256(), "test_log": log.getvalue(),
              "environment": {"python": sys.version, "platform": platform.platform(), "packages": packages},
              "build_receipt": receipt,
              "limitations": ["No energy ledger: serialization seconds and bytes per link and direction are recorded as inputs for P04",
                              "No retransmission, packet/PHY model, contention backoff or control traffic (specification section 15)",
                              "Links are engine-internal servers on the same ordered event queue as P02, not CloudSim NetworkTopology entities",
                              "Network mode needs nodes named F1..F5 and cloud as targets; custom fixture node names are rejected there",
                              "Trace-based runs are structural checks on calibration traces; outcomes are not a method benchmark",
                              "FogDevice/TimeKeeper/NetworkUsageMonitor static state is still not exercised"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: output[k] for k in ("phase", "status", "tests_run", "failures", "errors", "skipped", "acceptance")}))
    if not passed:
        print(log.getvalue(), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
