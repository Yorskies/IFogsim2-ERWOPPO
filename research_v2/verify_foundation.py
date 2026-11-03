"""Re-run P00 checks and retain a machine-readable report; no training runs."""

import argparse
import io
import json
import os
from pathlib import Path
import platform
import sys
import unittest
import zipfile

from .__main__ import export_documents, file_hash
from .config import ROOT, load_config, read_json, require, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jdk-home", type=Path)
    parser.add_argument("--baseline", type=Path, help="Optional original local legacy snapshot; requires those results present")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/research_v2/milestones/P00_verification.json")
    args = parser.parse_args()
    if args.jdk_home:
        os.environ["JAVA_HOME"] = str(args.jdk_home.resolve())
    config = load_config()
    for path, expected in export_documents().items():
        require(read_json(path) == expected, f"Stale schema/contract export: {path}")
    receipt = read_json(ROOT / "ifogsim/build/research_v2/build_receipt.json")
    artifact = ROOT / receipt["artifact"]
    require(file_hash(artifact) == receipt["artifact_sha256"], "JAR hash does not match build receipt")
    for name, expected in receipt["inputs"].items():
        require(file_hash(ROOT / name) == expected, f"Build input changed; rebuild before verification: {name}")
    with zipfile.ZipFile(artifact) as archive:
        require(json.loads(archive.read("research_v2/default.json")) == config, "JAR config differs from validated config")
        require(json.loads(archive.read("research_v2/wire_contract.json")) == read_json(ROOT / "configs/research_v2/wire_contract.json"), "JAR wire contract is stale")
    baseline_check = {"status": "not_requested"}
    if args.baseline:
        baseline = read_json(args.baseline)
        for name, expected in {**baseline["legacy_source_hashes"], **baseline["legacy_suite_files"]}.items():
            require(file_hash(ROOT / name) == expected, f"Legacy file changed: {name}")
        # Detect added/deleted files as well as modified bytes in the original suite.
        suite = ROOT / "results/suite_20261102T151556_158373Z"
        actual = {p.relative_to(ROOT).as_posix() for p in suite.rglob("*") if p.is_file()}
        require(actual == set(baseline["legacy_suite_files"]), "Legacy suite file inventory changed")
        baseline_check = {"status": "pass", "git_head": baseline["git_head"],
                          "legacy_source_files": len(baseline["legacy_source_hashes"]),
                          "legacy_result_files": len(baseline["legacy_suite_files"]),
                          "legacy_suite_inventory_sha256": baseline["legacy_suite_inventory_sha256"]}
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().discover(str(ROOT / "tests/research_v2"), pattern="test_foundation.py"))
    suite.addTests(unittest.TestLoader().discover(str(ROOT / "tests"), pattern="test_experiment_suite.py"))
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    # A completed P00 audit must exercise Java, not silently pass with skips.
    passed = result.wasSuccessful() and not result.skipped
    report = {"phase": "P00", "status": "pass" if passed else "failed",
              "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "skipped": len(result.skipped), "test_log": log.getvalue(),
              "config_sha256": sha256(config), "build_receipt": receipt,
              "legacy_integrity": baseline_check,
              "verification_environment": {"python": sys.version, "platform": platform.platform()},
              "limitations": ["No task offloading engine or socket implemented in P00",
                              "Java release 21 bytecode is not proof of an Ubuntu/JDK21 runtime test",
                              "Local package inventory is not a validated Python3.12/Linux dependency lock"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("phase", "status", "tests_run", "failures", "errors", "skipped")}))
    print(f"Report: {args.output}")
    if not passed:
        print(log.getvalue(), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
