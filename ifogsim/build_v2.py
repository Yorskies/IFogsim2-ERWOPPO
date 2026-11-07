"""Portable P00 build: Python + JDK >=21, emitting Java 21 bytecode.

No shell expansion, no changes to legacy classes/JARs. Run from any directory.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
from urllib.parse import quote
import zipfile

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parent
ARTIFACT = PROJECT / "dist/research-v2-foundation.jar"
MAIN_CLASS = "org.fog.erwo.v2.FoundationMain"


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tools(jdk_home=None):
    suffix = ".exe" if os.name == "nt" else ""
    home = jdk_home or os.environ.get("JAVA_HOME")
    paths = {name: str(Path(home) / "bin" / (name + suffix)) if home else shutil.which(name)
             for name in ("javac", "jar", "java")}
    if not all(value and Path(value).is_file() for value in paths.values()):
        raise SystemExit("JDK tools not found. Set JAVA_HOME or pass --jdk-home; JDK >=21 required.")
    return paths


def run(command, **kwargs):
    return subprocess.run(command, check=True, text=True, encoding="utf-8", **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jdk-home", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    jdk = tools(args.jdk_home)
    build = PROJECT / "build/research_v2"
    build.mkdir(parents=True, exist_ok=True)
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    sources = sorted((PROJECT / "src").rglob("*.java"))
    jars = sorted((PROJECT / "jars").rglob("*.jar"))
    resources = [ROOT / name for name in ("configs/research_v2/default.json", "configs/research_v2/wire_contract.json",
                                         "schemas/research_v2/config.schema.json", "schemas/research_v2/contracts.schema.json")]
    # Keep each isolated build for inspection. Windows scanners can hold .class
    # directories briefly; cleanup must not turn a successful compile into failure.
    # No stale classes are reused, and no legacy/generated directory is deleted.
    stage = Path(tempfile.mkdtemp(prefix="p00-", dir=build))
    classes = stage / "classes"
    classes.mkdir()
    source_list = stage / "sources.txt"
    source_list.write_text("\n".join('"' + p.as_posix() + '"' for p in sources), encoding="utf-8")
    run([jdk["javac"], "--release", "21", "-encoding", "UTF-8", "-cp", os.pathsep.join(map(str, jars)),
         "-d", str(classes), "@" + str(source_list)], cwd=ROOT)
    for path in resources:
        target = classes / "research_v2" / path.name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(path, target)
    manifest = stage / "MANIFEST.MF"
    entries = "Class-Path: " + " ".join(quote("../" + p.relative_to(PROJECT).as_posix()) for p in jars)
    lines = ["Manifest-Version: 1.0", f"Main-Class: {MAIN_CLASS}"]
    while len(entries) > 70:
        lines.append(entries[:70])
        entries = " " + entries[70:]
    lines.append(entries)
    manifest.write_bytes(("\r\n".join(lines) + "\r\n\r\n").encode("ascii"))
    staged_jar = stage / ARTIFACT.name
    run([jdk["jar"], "--create", "--file", str(staged_jar), "--manifest", str(manifest), "-C", str(classes), "."], cwd=ROOT)
    with zipfile.ZipFile(staged_jar) as archive:
        header = archive.read(MAIN_CLASS.replace(".", "/") + ".class")[:8]
        if header[:4] != b"\xca\xfe\xba\xbe" or int.from_bytes(header[6:8], "big") != 65:
            raise RuntimeError("Foundation bytecode is not Java 21 (major 65)")
    os.replace(staged_jar, ARTIFACT)
    probe = None
    if args.self_test:
        probe = json.loads(run([jdk["java"], "-jar", str(ARTIFACT), "--self-test"], cwd=ROOT, capture_output=True).stdout)
        if probe.get("status") != "pass":
            raise RuntimeError(f"Foundation smoke test failed: {probe}")
    receipt = {
        "phase": "P00", "artifact": ARTIFACT.relative_to(ROOT).as_posix(), "artifact_sha256": file_hash(ARTIFACT),
        "main_class": MAIN_CLASS, "java_release": 21, "class_major_version": 65,
        "build_directory": stage.relative_to(ROOT).as_posix(),
        "javac_version": run([jdk["javac"], "-version"], capture_output=True).stdout.strip(),
        "java_version": run([jdk["java"], "-version"], capture_output=True).stderr.strip(),
        "platform": platform.platform(), "python": platform.python_version(),
        "inputs": {p.relative_to(ROOT).as_posix(): file_hash(p) for p in sources + jars + resources + [Path(__file__).resolve()]},
        "self_test": probe,
        "scope": "foundation probe (FoundationMain) plus P02 headless task engine (EngineMain, fixture transport); not a socket server"
    }
    (build / "build_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"artifact": str(ARTIFACT), "sha256": receipt["artifact_sha256"], "self_test": probe}))


if __name__ == "__main__":
    main()
