"""Thin Python access to the P02 headless Java engine (fixed actions, fixture transport).

This module only builds scenario JSON and parses the engine output. Task outcomes, times and
resource accounting are produced by Java; nothing here recomputes them and there is no Python fallback.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
JAR = ROOT / "ifogsim/dist/research-v2-foundation.jar"
MAIN_CLASS = "org.fog.erwo.v2.EngineMain"


class EngineError(RuntimeError):
    """The Java engine rejected the scenario or an invariant failed; the run is stopped, not repaired."""


def find_java(jdk_home=None):
    home = jdk_home or os.environ.get("JAVA_HOME")
    if home:
        path = Path(home) / "bin" / ("java.exe" if os.name == "nt" else "java")
        return str(path) if path.is_file() else None
    return shutil.which("java")


def run_engine(scenario, *, jdk_home=None, timeout_s=600):
    """Run one scenario in a fresh JVM and return the parsed result. Raises EngineError on any engine failure."""
    java = find_java(jdk_home)
    if java is None:
        raise EngineError("No Java found; set JAVA_HOME to a JDK >= 21")
    if not JAR.is_file():
        raise EngineError(f"Build the v2 JAR first: {JAR}")
    with tempfile.TemporaryDirectory(prefix="engine-scenario-") as folder:
        path = Path(folder) / "scenario.json"
        path.write_text(json.dumps(scenario, allow_nan=False), encoding="utf-8")
        completed = subprocess.run([java, "-cp", str(JAR), MAIN_CLASS, "--run", str(path)], capture_output=True,
                                   text=True, encoding="utf-8", timeout=timeout_s, cwd=folder)
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise EngineError(f"Engine produced no JSON (exit {completed.returncode}): {completed.stderr[-500:]}") from error
    if completed.returncode != 0 or result.get("status") != "pass":
        raise EngineError(f"{result.get('error')}: {result.get('message')}")
    return result


def scenario_from_trace(trace, actions, *, nodes=None, topology=None, fixture_transport=None, label="trace", repeat=1):
    """Scenario from a P01 trace envelope. Exactly one of `nodes` (explicit fixture nodes) or `topology` is required."""
    if (nodes is None) == (topology is None):
        raise ValueError("Pass exactly one of nodes or topology")
    scenario = {"label": label, "tasks": trace["tasks"], "actions": actions, "repeat": repeat,
                "timing": {"arrival_window_s": trace["arrival_window_s"], "horizon_s": trace["horizon_s"]}}
    if nodes is not None:
        scenario["nodes"] = nodes
    else:
        scenario["topology"] = topology
    if fixture_transport is not None:
        scenario["fixture_transport"] = fixture_transport
    return scenario
