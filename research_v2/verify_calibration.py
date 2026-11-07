"""P06 milestone audit: reference-policy and gate tests, plus verification of the stored calibration evidence.

The evidence check recomputes the gates and every reported figure from the stored per-episode rows and the regenerated
traces, and requires them to equal the stored summary. It also requires every row to carry this build's JAR hash and the
canonical config hash, so the calibration cannot be silently mixed with another build or configuration.
"""

import argparse
import hashlib
import importlib.metadata
import io
import json
import math
import os
from pathlib import Path
import platform
import sys
import unittest

from .__main__ import export_documents, file_hash
from .calibration import MODES, OUTPUT_DIR, POLICY_ORDER, calibration_trace, load_rows
from .calibration_report import compute_summary
from .config import ROOT, read_json, require, sha256, load_config
from .schema_definitions import WORKLOADS
from .traces import TraceGenerator

ACCEPTANCE = {
    "reference_policy_logic": ["test_always_local_and_nearest_fog", "test_least_fog_picks_the_smallest_backlog_among_fogs_only",
                               "test_least_fog_ties_use_the_shorter_path_then_the_smaller_id",
                               "test_greedy_eft_scores_follow_the_specified_formula",
                               "test_greedy_eft_ties_go_to_the_smaller_destination_and_ignore_admission_state"],
    "public_snapshot_only": ["test_policies_read_only_public_features_and_are_pure", "test_policy_registry_matches_the_calibration_set"],
    "estimator_as_estimator": ["test_eft_estimate_is_exact_for_a_lone_task_and_only_an_estimate_otherwise"],
    "solo_task_analysis": ["test_solo_time_formula_by_hand", "test_feasibility_counts_a_task_once_and_respects_the_deadline",
                           "test_analytic_solo_time_equals_the_engine_for_every_destination_and_mode"],
    "gate_logic": ["test_all_gates_pass_when_every_condition_holds", "test_a_partial_run_cannot_pass",
                   "test_solo_feasibility_boundary_is_inclusive_at_95_percent",
                   "test_heavy_gate_needs_failure_above_1_percent_and_reliability_above_50_percent",
                   "test_a_single_passing_condition_is_enough_for_the_heavy_gate", "test_a_failed_distribution_check_fails_the_calibration",
                   "test_cell_means_weigh_every_trace_equally", "test_diagnostics_flag_a_trivial_or_collapsed_problem_without_failing_it"],
}
SOURCES = ("research_v2/baselines.py", "research_v2/calibration.py", "research_v2/calibration_report.py", "research_v2/gym_env.py", "research_v2/rpc_client.py")


def flatten(tests):
    for item in tests:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def close(a, b, rel=1e-9, abs_=1e-12):
    """Structural equality with a float tolerance, for comparing recomputed and stored summaries."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k], rel, abs_) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(close(x, y, rel, abs_) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        return a is not None and b is not None and math.isclose(a, b, rel_tol=rel, abs_tol=abs_)
    return a == b


def source_fingerprint():
    digest = {name: hashlib.sha256((ROOT / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name in SOURCES}
    return hashlib.sha256(json.dumps(digest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# Fields that describe how a row was produced rather than what it measured; they legitimately differ between two code
# versions (wall-clock time varies, and provenance/trace hash were added after the first calibration pass).
NON_RESULT_FIELDS = ("wall_s", "provenance", "trace_payload_sha256")


def comparable(row):
    """The measured content of a row: what must be identical between two replications of the same calibration."""
    return {k: v for k, v in row.items() if k not in NON_RESULT_FIELDS}


def check_evidence(output_dir, receipt, replicate_from=None):
    config = load_config()
    rows = load_rows(output_dir)
    problems = []
    keys = {(r["mode"], r["policy"], r["workload"], r["trace_id"]) for r in rows}
    if len(keys) != len(rows):
        problems.append("duplicate episodes in the stored rows")
    for row in rows:
        provenance = row.get("provenance") or {}
        if provenance.get("jar_sha256") != receipt["artifact_sha256"]:
            problems.append("a row was produced by a different JAR than the one in the build receipt")
            break
    if any((r.get("provenance") or {}).get("config_sha256") != sha256(config) for r in rows):
        problems.append("a row was produced under a different canonical config")
    generator = TraceGenerator(config)
    low, high = config["seeds"]["calibration_trace_ids"]
    hashes = {(w, i): calibration_trace(generator, config, w, i)["payload_sha256"] for w in WORKLOADS for i in range(low, high + 1)}
    if any(hashes[(r["workload"], r["trace_id"])] != r["trace_payload_sha256"] for r in rows):
        problems.append("a row was run on a trace that differs from the regenerated calibration trace")
    summary, *_ = compute_summary(output_dir)
    stored = read_json(output_dir / "calibration_summary.json")
    if not close(summary, stored):
        problems.append("calibration_summary.json differs from a recomputation from the stored rows")
    replication = None
    if replicate_from is not None:
        other = load_rows(Path(replicate_from))
        index = {(r["mode"], r["policy"], r["workload"], r["trace_id"]): comparable(r) for r in other}
        mine = {(r["mode"], r["policy"], r["workload"], r["trace_id"]): comparable(r) for r in rows}
        identical = index.keys() == mine.keys() and all(json.dumps(index[k], sort_keys=True) == json.dumps(mine[k], sort_keys=True) for k in mine)
        replication = {"rows_compared": len(mine), "identical_apart_from_wall_clock": identical}
        if not identical:
            problems.append("the replication run differs from the stored rows")
    return summary, replication, problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jdk-home", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/research_v2/milestones/P06_verification.json")
    parser.add_argument("--evidence-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--replicate-from", type=Path, help="rows of an earlier run to compare against (must be identical)")
    args = parser.parse_args()
    if args.jdk_home:
        os.environ["JAVA_HOME"] = str(args.jdk_home.resolve())
    for path, expected in export_documents().items():
        require(read_json(path) == expected, f"Stale schema export: {path}")
    receipt = read_json(ROOT / "ifogsim/build/research_v2/build_receipt.json")
    require(file_hash(ROOT / receipt["artifact"]) == receipt["artifact_sha256"], "Build artifact hash mismatch")
    for name, expected in receipt["inputs"].items():
        require(file_hash(ROOT / name) == expected, f"Build input changed: {name}; rebuild before verification")
    suite = unittest.TestLoader().discover(str(ROOT / "tests/research_v2"), pattern="test_calibration.py")
    ran = {t.id().split(".")[-1] for t in flatten(suite)}
    log = io.StringIO()
    tests = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    bad = {t.id().split(".")[-1] for t, _ in tests.failures + tests.errors + tests.skipped}
    acceptance = {case: ("fail" if any(m in bad for m in methods) else "pass") for case, methods in ACCEPTANCE.items()}
    unmapped = sorted(ran - {m for methods in ACCEPTANCE.values() for m in methods})
    summary, replication, problems = check_evidence(args.evidence_dir, receipt, args.replicate_from)
    gates = summary["gates"]
    passed = tests.wasSuccessful() and not tests.skipped and all(v == "pass" for v in acceptance.values()) and not problems
    packages = {name: {"version": importlib.metadata.distribution(name).version} for name in ("numpy", "jsonschema", "gymnasium", "matplotlib")}
    output = {"phase": "P06", "status": "pass" if passed else "failed", "tests_run": tests.testsRun, "failures": len(tests.failures),
              "errors": len(tests.errors), "skipped": len(tests.skipped), "acceptance": acceptance, "tests_not_mapped_to_a_criterion": unmapped,
              "evidence_problems": problems, "replication": replication, "source_sha256": source_fingerprint(),
              "calibration_gates": {k: (v["pass"] if isinstance(v, dict) and "pass" in v else v) for k, v in gates.items() if k != "diagnostics"},
              "calibration_decision": "all gates pass" if gates["all_pass"] else "GATE FAILED: stop and diagnose; do not tune parameters",
              "episodes": gates["complete"]["episodes"], "test_log": log.getvalue(), "build_receipt": receipt,
              "environment": {"python": sys.version, "platform": platform.platform(), "packages": packages},
              "limitations": ["Only four deterministic reference policies were run; no learning claim and no PPO/ERWO result enters calibration",
                              "Gate interpretations are fixed in `evaluate_gates` and in the P06 note; thresholds come from config['pilot']",
                              "Solo-task feasibility is analytic (idle system, soft deadline D), verified against the engine on a sample of tasks, not on every task",
                              "The heavy-pressure gate passes if any one (configuration, reference policy) condition does; other conditions may fail it",
                              "Calibration is one pass over the predeclared 20 traces per workload: no seed was selected or replaced",
                              "Windows, Python 3.12.6 and OpenJDK 21.0.13 only"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: output[k] for k in ("phase", "status", "tests_run", "failures", "errors", "skipped", "acceptance", "tests_not_mapped_to_a_criterion",
                                             "evidence_problems", "replication", "calibration_gates", "calibration_decision")}))
    if not passed:
        print(log.getvalue(), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
