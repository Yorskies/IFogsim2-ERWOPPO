"""Run the complete workload/budget/seed matrix with isolated, resumable outputs."""

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import socket
import statistics
import subprocess
import sys
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parent
METHODS = (
    "Nearest Fog", "Least Fog", "Q-Learning-Equal", "DQN-Equal",
    "DDPG-Equal", "PPO-Equal", "ERWO-PPO",
)
METRICS = (
    "latency", "energy", "deadline", "violation_rate", "load_imbalance",
    "qos", "decision_time_ms", "reward",
)
OVERHEAD = ("avg_cand_train", "avg_cand_eval", "total_search_time", "final_ppo_train_time")
WEIGHTS = ("alpha_latency", "beta_energy", "lambda_deadline", "gamma_qos")


def write_json(path, value):
    """Replace checkpoints atomically so interrupted writes can be retried."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_config(config):
    allowed = {
        "workloads", "final_timesteps", "seeds", "candidate_timesteps",
        "pop_size", "generations", "eval_episodes", "device",
    }
    if set(config) != allowed:
        raise ValueError(f"Konfigurasi harus memuat tepat: {sorted(allowed)}")
    for name in ("workloads", "final_timesteps", "seeds"):
        values = config[name]
        if not isinstance(values, list) or not values or len(set(values)) != len(values):
            raise ValueError(f"{name} harus berupa daftar unik yang tidak kosong")
    if any(w not in ("light", "moderate", "heavy", "dynamic") for w in config["workloads"]):
        raise ValueError("Workload tidak dikenal")
    numbers = config["final_timesteps"] + [config[k] for k in
        ("candidate_timesteps", "pop_size", "generations", "eval_episodes")]
    if any(type(n) is not int or n <= 0 for n in numbers):
        raise ValueError("Anggaran, populasi, generasi, dan jumlah episode harus integer positif")
    if any(type(s) is not int or not 0 <= s < 2**32 for s in config["seeds"]):
        raise ValueError("Seed harus integer dalam rentang 0..4294967295")
    if config["device"] not in ("cpu", "auto"):
        raise ValueError("device harus cpu atau auto")
    return config


def plan_runs(config):
    # Each budget starts fresh; it is not a continuation of the previous model.
    return [dict(workload=w, final_timesteps=t, seed=s,
                 run_id=f"{w}_t{t}_seed{s}")
            for t, w, s in itertools.product(
                config["final_timesteps"], config["workloads"], config["seeds"])]


def code_fingerprint():
    files = ("run_experiments.py", "main.py", "optimizer_nsga2.py", "agent_ppo.py",
             "agent_baselines.py", "env_ifogsim2.py", "logger.py", "requirements.txt",
             "ifogsim/src/org/fog/placement/IFogSimSocketServer.java")
    digest = hashlib.sha256()
    for name in files:
        digest.update(name.encode())
        digest.update((ROOT / name).read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def check_server():
    with socket.create_connection(("127.0.0.1", 5555), timeout=5) as connection:
        connection.settimeout(5)
        connection.sendall(b"PING\n")
        with connection.makefile("rb") as response:
            if response.readline(64).strip() != b"PONG":
                raise RuntimeError("Port 5555 tidak memberikan respons PONG dari server iFogSim")
        connection.sendall(b"CLOSE\n")


def command_for(config, run):
    return [sys.executable, "-u", str(ROOT / "main.py"),
            "--workload", run["workload"], "--seed", str(run["seed"]),
            "--candidate-timesteps", str(config["candidate_timesteps"]),
            "--final-timesteps", str(run["final_timesteps"]),
            "--eval-episodes", str(config["eval_episodes"]),
            "--pop-size", str(config["pop_size"]),
            "--generations", str(config["generations"]),
            "--tag", run["run_id"], "--require-java"]


def execute_run(config, run, folder):
    folder.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.update(IFOGSIM_DISABLE_DASHBOARD="1", PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    if config["device"] == "cpu":
        environment["CUDA_VISIBLE_DEVICES"] = ""
    # cwd isolates all existing main.py outputs, including models, Data.md and logs.
    with (folder / "runner.log").open("a", encoding="utf-8") as log:
        process = subprocess.Popen(command_for(config, run), cwd=folder, env=environment,
                                   stdout=log, stderr=subprocess.STDOUT)
        try:
            returncode = process.wait()
        except BaseException:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            raise
    if returncode:
        raise RuntimeError(f"Training gagal (exit {returncode}). Lihat {folder / 'runner.log'}")


def collect_result(config, run, folder):
    experiments = sorted((folder / "logs/experiments").glob("*/config.json"),
                         key=lambda p: p.stat().st_mtime_ns)
    if not experiments:
        raise RuntimeError(f"Log eksperimen tidak ditemukan di {folder}")
    log_dir = experiments[-1].parent
    actual = read_json(log_dir / "config.json")
    expected = {k: config[k] for k in ("candidate_timesteps", "eval_episodes", "pop_size", "generations")}
    expected.update({k: run[k] for k in ("workload", "seed", "final_timesteps")})
    if any(actual.get(k) != value for k, value in expected.items()) or not actual.get("require_java"):
        raise RuntimeError("Konfigurasi hasil training tidak sesuai matriks eksperimen")
    benchmarks = read_json(log_dir / "benchmark_summary.json")
    overhead = read_json(log_dir / "computational_overhead.json")
    if set(benchmarks) != set(METHODS):
        raise RuntimeError("Metode benchmark tidak lengkap")
    values = [benchmarks[m][k] for m in METHODS for k in METRICS] + [overhead[k] for k in OVERHEAD]
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
        raise RuntimeError("Hasil benchmark mengandung nilai tidak valid")
    with (log_dir / "pareto_front.csv").open(encoding="utf-8", newline="") as stream:
        selected = [r for r in csv.DictReader(stream) if r["is_best_selected"].lower() == "true"]
    if len(selected) != 1:
        raise RuntimeError("Bobot Pareto terpilih tidak ditemukan")
    weights = {k: float(selected[0][k]) for k in WEIGHTS}
    if not all(math.isfinite(v) for v in weights.values()):
        raise RuntimeError("Bobot Pareto tidak valid")
    models = ("ppo_ifogsim2_erwo.zip", "ppo_equal.zip", "dqn_equal.zip", "ddpg_equal.zip", "qlearning_equal.pkl")
    if not (folder / "Data.md").is_file() or not all((folder / "models" / name).is_file() for name in models):
        raise RuntimeError("Laporan atau model training belum lengkap")
    return {**run, "benchmarks": benchmarks, "overhead": overhead, "weights": weights,
            "log_dir": str(log_dir.relative_to(folder)), "config": actual}


def mean_std(values):
    return {"mean": statistics.mean(values),
            "std": statistics.stdev(values) if len(values) > 1 else None}


def summarize(records):
    groups = {}
    for record in records:
        groups.setdefault((record["workload"], record["final_timesteps"]), []).append(record)
    result = []
    for (workload, budget), runs in groups.items():
        result.append({
            "workload": workload, "final_timesteps": budget,
            "seeds": [r["seed"] for r in runs], "n_seeds": len(runs),
            "benchmarks": {m: {k: mean_std([r["benchmarks"][m][k] for r in runs])
                                for k in METRICS} for m in METHODS},
            "overhead": {k: mean_std([r["overhead"][k] for r in runs]) for k in OVERHEAD},
            "weights": {k: mean_std([r["weights"][k] for r in runs]) for k in WEIGHTS},
        })
    return result


def cell(value, digits=2):
    spread = "N/A" if value["std"] is None else f"{value['std']:.{digits}f}"
    return f"{value['mean']:.{digits}f} ± {spread}"


def write_report(folder, manifest):
    records = []
    for run in manifest["runs"]:
        path = folder / "runs" / run["run_id"] / "result.json"
        if run["status"] == "complete":
            records.append(read_json(path))
    summary = summarize(records)
    write_json(folder / "summary.json", {"config": manifest["config"], "groups": summary,
                                         "completed_runs": len(records), "total_runs": len(manifest["runs"])})
    flat = [{"workload": r["workload"], "final_timesteps": r["final_timesteps"],
             "seed": r["seed"], "method": m, **r["benchmarks"][m]} for r in records for m in METHODS]
    with (folder / "runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["workload", "final_timesteps", "seed", "method", *METRICS])
        writer.writeheader()
        writer.writerows(flat)
    config = manifest["config"]
    lines = ["# Data akhir eksperimen ERWO-PPO", "",
             f"Status: {manifest['status']}; selesai {len(records)}/{len(manifest['runs'])} percobaan.", "",
             f"Konfigurasi: kandidat {config['candidate_timesteps']} timestep; populasi {config['pop_size']}; "
             f"generasi {config['generations']}; evaluasi {config['eval_episodes']} episode; device {config['device']}.",
             f"Seed training: {config['seeds']}. Workload: {config['workloads']}.", "",
             "Setiap kombinasi dilatih ulang dari awal, termasuk pencarian bobot NSGA-II. "
             "Anggaran timestep adalah nilai yang diminta; PPO dapat membulatkan ke ukuran rollout.", "",
             "Nilai tabel adalah rata-rata ± standar deviasi sampel antar-seed training, "
             "setelah setiap run dirata-ratakan atas episode evaluasi. N/A berarti baru ada satu seed. "
             "Hasil parsial tidak mewakili seluruh matriks.", "",
             "Latensi, energi, deadline, dan QoS adalah jumlah sub-reward per episode, "
             "bukan ms, Joule, atau persentase. Jangan membandingkan jumlah skor lintas workload "
             "dengan panjang episode berbeda. Violation menggunakan persen; decision time menggunakan ms.", "",
             "Seed validasi kandidat: 42..44; seed benchmark: "
             f"1000..{1000 + config['eval_episodes'] - 1}, sama untuk semua metode. "
             "Socket Java wajib; fallback Python dinonaktifkan. "
             "P-value per-run tersedia di log; tidak dirata-ratakan atau digabung menjadi klaim signifikansi antar-seed.", ""]
    for group in summary:
        lines += [f"## {group['workload']} — {group['final_timesteps']:,} timestep", "",
                  f"Seed selesai: {group['seeds']} ({group['n_seeds']}/{len(config['seeds'])}).", "",
                  "| Metode | Skor latensi ↑ | Efisiensi energi ↑ | Violation (%) ↓ | Load imbalance ↓ | QoS ↑ | Decision (ms) ↓ |",
                  "|---|---:|---:|---:|---:|---:|---:|"]
        for method in METHODS:
            metrics = group["benchmarks"][method]
            cells = [cell(metrics[k], 4 if k in ("load_imbalance", "decision_time_ms") else 2)
                     for k in ("latency", "energy", "violation_rate", "load_imbalance", "qos", "decision_time_ms")]
            lines.append("| " + " | ".join([method, *cells]) + " |")
        lines += ["", "Bobot ERWO-PPO (rata-rata ± SD; bukan bobot model gabungan): " +
                  "; ".join(f"{k}: {cell(v, 4)}" for k, v in group["weights"].items()) + ".", "",
                  "| Biaya per run | Detik, rata-rata ± SD |", "|---|---:|"]
        lines += [f"| {k} | {cell(v)} |" for k, v in group["overhead"].items()]
        lines += [""]
    lines += ["## Artefak", "", "- `runs.csv`: hasil tiap metode dan seed.",
              "- `summary.json`: agregasi seluruh metrik, bobot, dan overhead.",
              "- `manifest.json`: konfigurasi, fingerprint source, command, dan status tiap percobaan.",
              "- `runs/<workload>_t<budget>_seed<seed>/`: model, Data.md, log, statistik, dan CSV episode tiap run.", ""]
    report = folder / "Data_final.md"
    temporary = report.with_suffix(".md.tmp")
    temporary.write_text("\n".join(lines), encoding="utf-8")
    temporary.replace(report)


def run_suite(folder, manifest):
    environment_device = os.environ.get("CUDA_VISIBLE_DEVICES", "unset")
    print(f"Suite: {folder}\nDevice: {manifest['config']['device']} (inherited CUDA_VISIBLE_DEVICES={environment_device})", flush=True)
    for index, run in enumerate(manifest["runs"], 1):
        if run["status"] == "complete":
            continue
        run_folder = folder / "runs" / run["run_id"]
        run.update(status="running", command=command_for(manifest["config"], run))
        manifest["status"] = "running"
        write_json(folder / "manifest.json", manifest)
        print(f"[{index}/{len(manifest['runs'])}] {run['run_id']} — log: {run_folder / 'runner.log'}", flush=True)
        try:
            check_server()
            execute_run(manifest["config"], run, run_folder)
            result = collect_result(manifest["config"], run, run_folder)
            write_json(run_folder / "result.json", result)
            run.update(status="complete")
            run.pop("error", None)
        except (Exception, KeyboardInterrupt) as error:
            run.update(status="interrupted" if isinstance(error, KeyboardInterrupt) else "failed",
                       error=str(error) or "KeyboardInterrupt")
            manifest["status"] = run["status"]
            write_json(folder / "manifest.json", manifest)
            write_report(folder, manifest)
            print(f"Lanjutkan dengan: python run_experiments.py --resume \"{folder}\"", flush=True)
            raise
        write_json(folder / "manifest.json", manifest)
        write_report(folder, manifest)
    manifest["status"] = "complete"
    write_json(folder / "manifest.json", manifest)
    write_report(folder, manifest)
    print(f"SELESAI: {folder / 'Data_final.md'}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "experiment_suite.json")
    parser.add_argument("--resume", type=Path, help="Direktori suite yang terputus")
    parser.add_argument("--dry-run", action="store_true", help="Tampilkan matriks tanpa training atau koneksi Java")
    args = parser.parse_args()
    if args.resume:
        folder = args.resume.resolve()
        manifest = read_json(folder / "manifest.json")
        validate_config(manifest["config"])
        if manifest["code_fingerprint"] != code_fingerprint():
            parser.error("Source berubah sejak suite dibuat. Gunakan source semula untuk resume atau mulai suite baru.")
        expected = plan_runs(manifest["config"])
        actual = [{k: r[k] for k in ("workload", "final_timesteps", "seed", "run_id")} for r in manifest["runs"]]
        if actual != expected:
            parser.error("Matriks pada manifest tidak sesuai konfigurasi")
    else:
        config = validate_config(read_json(args.config))
        folder = ROOT / "results" / ("suite_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ"))
        manifest = {"config": config, "code_fingerprint": code_fingerprint(), "status": "pending",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "python": sys.version, "runs": [dict(r, status="pending") for r in plan_runs(config)]}
    if args.dry_run:
        print(json.dumps({"config": manifest["config"], "total_runs": len(manifest["runs"]),
                          "runs": [{k: r[k] for k in ("run_id", "status")} for r in manifest["runs"]]}, indent=2))
        return
    if any(run["status"] != "complete" for run in manifest["runs"]):
        check_server()
    folder.mkdir(parents=True, exist_ok=True)
    write_json(folder / "manifest.json", manifest)
    run_suite(folder, manifest)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
