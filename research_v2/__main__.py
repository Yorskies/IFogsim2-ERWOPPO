"""Research v2 config and trace tools. Training remains unavailable."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from pathlib import Path

from .config import ROOT, DEFAULT_CONFIG, canonical_bytes, load_config, read_json, sha256
from .schema_definitions import config_schema, contract_schema, trace_bundle_schema, wire_contract


def export_documents():
    return {
        ROOT / "schemas/research_v2/config.schema.json": config_schema(),
        ROOT / "schemas/research_v2/contracts.schema.json": contract_schema(),
        ROOT / "configs/research_v2/wire_contract.json": wire_contract(),
        ROOT / "schemas/research_v2/trace_bundle.schema.json": trace_bundle_schema(),
    }


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def foundation_snapshot():
    git = ["git", "-c", f"safe.directory={ROOT.as_posix()}"]
    revision = subprocess.check_output([*git, "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    suite = ROOT / "results/suite_20261102T151556_158373Z"
    files = [p for p in suite.rglob("*") if p.is_file()]
    legacy = {p.relative_to(ROOT).as_posix(): file_hash(p) for p in sorted(files)}
    code = [p for p in (ROOT / "ifogsim/src").rglob("*.java") if "erwo/v2" not in p.as_posix()]
    code += [ROOT / p for p in ("main.py", "env_ifogsim2.py", "run_experiments.py", "experiment_suite.json", "requirements.txt")]
    packages = {}
    for name in ("jsonschema", "attrs", "jsonschema-specifications", "referencing", "rpds-py", "typing-extensions"):
        dist = importlib.metadata.distribution(name)
        record = dist.read_text("RECORD")
        packages[name] = {"version": dist.version,
                          "installed_record_sha256": hashlib.sha256((record or "").encode()).hexdigest()}
    return {"git_head": revision, "legacy_source_hashes": {p.relative_to(ROOT).as_posix(): file_hash(p) for p in sorted(code)},
            "legacy_suite_present": suite.exists(), "legacy_suite_file_count": len(legacy),
            "legacy_suite_files": legacy, "legacy_suite_inventory_sha256": sha256(legacy),
            "environment": {"python": sys.version, "executable": sys.executable, "os": platform.platform(),
                            "machine": platform.machine(), "processor": platform.processor(), "packages": packages},
            "hash_note": "Installed RECORD hashes identify this environment; they are not downloadable wheel hashes or a Linux lock."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    export = commands.add_parser("export-schemas")
    export.add_argument("--check", action="store_true")
    snapshot = commands.add_parser("snapshot")
    snapshot.add_argument("--output", type=Path, required=True)
    generate = commands.add_parser("generate-traces", help="Create immutable trace bundles; no simulator or training")
    generate.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    generate.add_argument("--split", required=True)
    generate.add_argument("--role", required=True)
    generate.add_argument("--workload", choices=["light", "moderate", "heavy", "dynamic", "all"], default="all")
    generate.add_argument("--trace-id", type=int, required=True)
    generate.add_argument("--outer-run", type=int)
    generate.add_argument("--model-repeat", type=int)
    generate.add_argument("--output", type=Path, default=ROOT / "results/research_v2/traces")
    describe = commands.add_parser("describe-trace", help="Characterize an authorized non-test bundle")
    describe.add_argument("path", type=Path)
    describe.add_argument("--role", required=True)
    args = parser.parse_args()
    if args.command == "validate":
        config = load_config(args.config)
        print(json.dumps({"valid": True, "config_sha256": sha256(config), "implemented_phase": "P01"}))
    elif args.command == "export-schemas":
        for path, data in export_documents().items():
            content = json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
            if args.check:
                if not path.exists() or path.read_text(encoding="utf-8") != content:
                    raise SystemExit(f"Schema export is stale: {path}")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
        print("Schema exports OK")
    elif args.command == "snapshot":
        if args.output.exists():
            raise SystemExit(f"Refusing to overwrite foundation evidence: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(foundation_snapshot(), indent=2) + "\n", encoding="utf-8")
        print(f"Snapshot: {args.output}")
    elif args.command == "generate-traces":
        from .schema_definitions import WORKLOADS
        from .trace_access import TraceKey
        from .trace_store import write_bundle
        from .traces import TraceGenerator
        config = load_config(args.config)
        generator = TraceGenerator(config)
        workloads = WORKLOADS if args.workload == "all" else [args.workload]
        for workload in workloads:
            key = TraceKey(config["seeds"]["master"], args.split, args.outer_run, args.model_repeat, args.trace_id, workload)
            trace = generator.generate(key, role=args.role)
            path = write_bundle(args.output, trace, config, role=args.role)
            print(json.dumps({"path": str(path), "payload_sha256": trace.payload_sha256,
                              "status": "sealed" if args.split == "test" else "ready"}))
    else:
        from .trace_report import describe_trace
        from .trace_store import read_bundle
        config = read_json(args.path / "config.json")
        trace = read_bundle(args.path, role=args.role, config=config)
        print(json.dumps(describe_trace(trace, config, role=args.role), indent=2))


if __name__ == "__main__":
    main()
