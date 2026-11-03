"""Atomic trace bundles. Existing bytes are verified and never overwritten."""

import hashlib
import os
from pathlib import Path
import platform
import tempfile

import numpy as np

from .config import ROOT, canonical_bytes, read_json, require, sha256, validate_config, validate_json
from .schema_definitions import COMPONENTS, trace_bundle_schema
from .trace_access import authorize, key_from_dict
from .traces import GENERATOR_VERSION, Trace


def bytes_sha256(value):
    return hashlib.sha256(value).hexdigest()


def generator_source_sha256():
    names = ["__init__.py", "config.py", "contracts.py", "schema_definitions.py", "trace_access.py", "traces.py", "trace_store.py"]
    return sha256({name: bytes_sha256((ROOT / "research_v2" / name).read_bytes()) for name in names})


def bundle_path(root, key, config):
    key.validate(config)
    return (Path(root) / sha256(config) / key.split /
            f"outer-{'-' if key.outer_run is None else key.outer_run}" /
            f"repeat-{'-' if key.model_repeat is None else key.model_repeat}" /
            key.workload / f"trace-{key.trace_id:06d}")


def _read_verified(path, expected_config=None):
    path = Path(path)
    manifest = read_json(path / "manifest.json")
    validate_json(manifest, trace_bundle_schema())
    config = read_json(path / "config.json")
    validate_config(config)
    require(sha256(config) == manifest["config_sha256"], "Bundle config hash mismatch")
    if expected_config is not None:
        require(canonical_bytes(config) == canonical_bytes(expected_config), "Bundle uses a different config")
    for name, expected in manifest["files"].items():
        require(bytes_sha256((path / name).read_bytes()) == expected, f"Bundle file hash mismatch: {name}")
    trace = Trace.from_dict(read_json(path / "trace.json"), config)
    require((path / "trace.json").read_bytes() == trace.canonical_json, "Bundle trace is not canonical JSON")
    data = trace.to_dict()
    key = key_from_dict(data["seed_namespace"], config)
    require(manifest["seed_namespace"] == data["seed_namespace"], "Bundle namespace mismatch")
    require(manifest["payload_sha256"] == trace.payload_sha256 and manifest["task_count"] == trace.task_count, "Bundle payload/count mismatch")
    require(manifest["units"] == config["units"], "Bundle unit mismatch")
    require(manifest["component_seeds"] == {name: key.seed(name) for name in COMPONENTS}, "Bundle RNG recipe mismatch")
    require(manifest["status"] == ("sealed" if key.split == "test" else "ready"), "Bundle seal status mismatch")
    return trace, config, manifest


def write_bundle(root, trace, config, *, role):
    data = trace.to_dict()
    key = key_from_dict(data["seed_namespace"], config)
    authorize(role, key.split, "generate")
    # Validate at the persistence boundary too, including callers constructing Trace directly.
    validated = Trace.from_dict(data, config)
    require(validated.canonical_json == trace.canonical_json, "Trace bytes must be canonical JSON")
    path = bundle_path(root, key, config)
    expected_files = {"trace.json": trace.canonical_json, "config.json": canonical_bytes(config)}
    if path.exists():
        existing, _, _ = _read_verified(path, config)
        require(existing.canonical_json == trace.canonical_json, "Refusing to overwrite different trace at the same namespace")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "bundle_version": "research-v2.trace-bundle-1", "generator_version": GENERATOR_VERSION,
        "status": "sealed" if key.split == "test" else "ready", "seed_namespace": key.to_dict(),
        "task_count": trace.task_count, "payload_sha256": trace.payload_sha256, "config_sha256": sha256(config),
        "files": {name: bytes_sha256(content) for name, content in expected_files.items()},
        "units": config["units"], "component_seeds": {name: key.seed(name) for name in COMPONENTS},
        "producer": {"python": platform.python_version(), "numpy": np.__version__, "source_sha256": generator_source_sha256()},
    }
    validate_json(manifest, trace_bundle_schema())
    # Publish the nonempty directory only after every file has been flushed.
    with tempfile.TemporaryDirectory(prefix=".pending-", dir=path.parent) as temporary:
        stage = Path(temporary)
        for name, content in {**expected_files, "manifest.json": canonical_bytes(manifest)}.items():
            with (stage / name).open("xb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        try:
            os.rename(stage, path)
        except OSError:
            if not path.exists():
                raise
            existing, _, _ = _read_verified(path, config)
            require(existing.canonical_json == trace.canonical_json, "Concurrent writer published a different trace")
    return path


def read_bundle(path, *, role, config=None):
    # Check access before loading any task content. A caller cannot use a train
    # role to read held-out data merely by pointing it at another directory.
    manifest = read_json(Path(path) / "manifest.json")
    validate_json(manifest, trace_bundle_schema())
    authorize(role, manifest["seed_namespace"]["split"], "read")
    trace, _, _ = _read_verified(path, config)
    return trace
