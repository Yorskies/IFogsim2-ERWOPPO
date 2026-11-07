"""P01 milestone audit: all calibration traces, native numeric replay and tests."""

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

from .config import ROOT, load_config, read_json, require
from .__main__ import export_documents, file_hash
from .schema_definitions import WORKLOADS
from .trace_access import TraceKey
from .trace_report import calibration_report
from .trace_store import generator_source_sha256, read_bundle, write_bundle
from .traces import GENERATOR_VERSION, TraceGenerator


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jdk-home", type=Path)
    parser.add_argument("--trace-root", type=Path, default=ROOT / "results/research_v2/P01_calibration/traces")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/research_v2/milestones/P01_verification.json")
    parser.add_argument("--baseline", type=Path, help="Optional existing local P00 snapshot for legacy integrity")
    args = parser.parse_args()
    if args.jdk_home:
        os.environ["JAVA_HOME"] = str(args.jdk_home.resolve())
    config = load_config()
    for path, expected in export_documents().items():
        require(read_json(path) == expected, f"Stale schema export: {path}")
    receipt = read_json(ROOT / "ifogsim/build/research_v2/build_receipt.json")
    require(file_hash(ROOT / receipt["artifact"]) == receipt["artifact_sha256"], "Build artifact hash mismatch")
    for name, expected in receipt["inputs"].items():
        require(file_hash(ROOT / name) == expected, f"Build input changed: {name}; rebuild before verification")
    generator = TraceGenerator(config)
    traces, locations = [], []
    low, high = config["seeds"]["calibration_trace_ids"]
    for workload in WORKLOADS:
        for trace_id in range(low, high + 1):
            key = TraceKey(config["seeds"]["master"], "calibration", None, None, trace_id, workload)
            trace = generator.generate(key, role="calibrator")
            path = write_bundle(args.trace_root, trace, config, role="calibrator")
            replay = read_bundle(path, role="calibrator", config=config)
            require(replay.canonical_json == trace.canonical_json, "Persisted trace differs from generator")
            traces.append(replay)
            locations.append(str(path))
        print(f"Calibration: {workload} {high - low + 1} traces", flush=True)
    report = calibration_report(traces, config)
    suite = unittest.TestSuite()
    # Explicit modules keep the P01 count at 49 as later phases add their own test files.
    for pattern in ("test_foundation.py", "test_traces.py"):
        suite.addTests(unittest.TestLoader().discover(str(ROOT / "tests/research_v2"), pattern=pattern))
    suite.addTests(unittest.TestLoader().discover(str(ROOT / "tests"), pattern="test_experiment_suite.py"))
    log = io.StringIO()
    tests = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    passed = report["status"] == "pass" and tests.wasSuccessful() and not tests.skipped
    legacy = {"status": "not_requested"}
    if args.baseline:
        baseline = read_json(args.baseline)
        for name, expected in {**baseline["legacy_source_hashes"], **baseline["legacy_suite_files"]}.items():
            require(file_hash(ROOT / name) == expected, f"Legacy file changed: {name}")
        suite_path = ROOT / "results/suite_20261102T151556_158373Z"
        require({p.relative_to(ROOT).as_posix() for p in suite_path.rglob("*") if p.is_file()} == set(baseline["legacy_suite_files"]),
                "Legacy suite inventory changed")
        legacy = {"status": "pass", "source_files": len(baseline["legacy_source_hashes"]), "result_files": len(baseline["legacy_suite_files"])}
    packages = {}
    for name in ("numpy", "jsonschema", "attrs", "jsonschema-specifications", "referencing", "rpds-py", "typing-extensions"):
        dist = importlib.metadata.distribution(name)
        packages[name] = {"version": dist.version, "installed_record_sha256": hashlib.sha256((dist.read_text("RECORD") or "").encode()).hexdigest()}
    output = {"phase": "P01", "status": "pass" if passed else "failed", "generator_version": GENERATOR_VERSION,
              "source_sha256": generator_source_sha256(), "tests_run": tests.testsRun,
              "failures": len(tests.failures), "errors": len(tests.errors), "skipped": len(tests.skipped),
              "test_log": log.getvalue(), "calibration": report, "trace_locations": locations,
              "environment": {"python": sys.version, "platform": platform.platform(), "packages": packages},
              "build_receipt": receipt, "legacy_integrity": legacy,
              "limitations": ["Calibration distribution checks do not validate the offloading engine",
                              "No production test split used to select methods or parameters",
                              "Split guards are application-level checks, not encryption or OS access control",
                              "Windows/JDK27 release21 only; Ubuntu/Python3.12/JDK21 remains unverified"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: output[k] for k in ("phase", "status", "tests_run", "failures", "errors", "skipped")}))
    if not passed:
        print(log.getvalue(), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
