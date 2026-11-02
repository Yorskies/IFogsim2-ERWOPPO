import contextlib
import csv
import io
import math
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_experiments as suite


class SuiteTests(unittest.TestCase):
    def setUp(self):
        self.config = suite.read_json(suite.ROOT / "experiment_suite.json")

    def fixture_training(self, config, run, folder):
        """Write main.py's artifact schema without doing expensive RL training."""
        self.executed.append(run["run_id"])
        logs = folder / "logs/experiments/test"
        logs.mkdir(parents=True, exist_ok=True)
        suite.write_json(logs / "config.json", {
            **config, **run, "require_java": True,
        })
        value = run["seed"] + run["final_timesteps"]
        benchmarks = {m: {k: float(value) for k in suite.METRICS} for m in suite.METHODS}
        suite.write_json(logs / "benchmark_summary.json", benchmarks)
        suite.write_json(logs / "computational_overhead.json", {k: 2. for k in suite.OVERHEAD})
        with (logs / "pareto_front.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["is_best_selected", *suite.WEIGHTS])
            writer.writeheader()
            writer.writerow({"is_best_selected": True, **dict.fromkeys(suite.WEIGHTS, .25)})
        (folder / "models").mkdir(exist_ok=True)
        for name in ("ppo_ifogsim2_erwo.zip", "ppo_equal.zip", "dqn_equal.zip", "ddpg_equal.zip", "qlearning_equal.pkl"):
            (folder / "models" / name).write_bytes(b"fixture")
        (folder / "Data.md").write_text("isolated run", encoding="utf-8")

    def test_default_matrix_and_command(self):
        suite.validate_config(self.config)
        runs = suite.plan_runs(self.config)
        self.assertEqual(len(runs), 80)
        self.assertEqual(len({r["run_id"] for r in runs}), 80)
        self.assertEqual(runs[0]["final_timesteps"], 5000)
        self.assertEqual(runs[-1]["final_timesteps"], 100000)
        command = suite.command_for(self.config, runs[0])
        self.assertEqual(command[command.index("--candidate-timesteps") + 1], "5000")
        self.assertIn("--require-java", command)

    def test_invalid_configuration(self):
        for key, value in (("seeds", [1, 1]), ("seeds", [-1]),
                           ("candidate_timesteps", 0), ("workloads", ["unknown"])):
            with self.subTest(key=key, value=value):
                config = {**self.config, key: value}
                with self.assertRaises(ValueError):
                    suite.validate_config(config)

    def test_failed_run_is_excluded_and_resume_preserves_completed_runs(self):
        config = {**self.config, "workloads": ["light", "heavy"],
                  "final_timesteps": [5000, 25000], "seeds": [0, 2]}
        manifest = {"config": config, "status": "pending",
                    "runs": [dict(r, status="pending") for r in suite.plan_runs(config)]}
        self.executed = []
        def fail_second(config, run, folder):
            if len(self.executed) == 1:
                raise RuntimeError("simulated connection loss")
            self.fixture_training(config, run, folder)
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            folder = Path(temporary)
            with patch.object(suite, "check_server"), patch.object(suite, "execute_run", side_effect=fail_second):
                with self.assertRaisesRegex(RuntimeError, "connection loss"):
                    suite.run_suite(folder, manifest)
            self.assertEqual(suite.read_json(folder / "summary.json")["completed_runs"], 1)
            first_result = folder / "runs" / manifest["runs"][0]["run_id"] / "result.json"
            first_bytes = first_result.read_bytes()
            # Resume from disk, exactly as a new process would do.
            manifest = suite.read_json(folder / "manifest.json")
            with patch.object(suite, "check_server"), patch.object(suite, "execute_run", side_effect=self.fixture_training):
                suite.run_suite(folder, manifest)
            self.assertEqual(len(self.executed), 8)
            self.assertEqual(first_bytes, first_result.read_bytes())
            summary = suite.read_json(folder / "summary.json")
            self.assertEqual(summary["completed_runs"], 8)
            self.assertEqual(len(summary["groups"]), 4)
            group = summary["groups"][0]
            self.assertEqual(group["n_seeds"], 2)
            metric = group["benchmarks"]["ERWO-PPO"]["latency"]
            self.assertEqual(metric["mean"], 5001.)
            self.assertAlmostEqual(metric["std"], math.sqrt(2))
            self.assertIn("selesai 8/8", (folder / "Data_final.md").read_text(encoding="utf-8"))
            with (folder / "runs.csv").open(encoding="utf-8", newline="") as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), 8 * 7)
            result = suite.read_json(first_result)
            result["benchmarks"]["ERWO-PPO"]["latency"] = float("nan")
            with self.assertRaises(ValueError):
                suite.write_json(folder / "invalid.json", result)

    def test_child_working_directory_and_cpu_settings(self):
        run = suite.plan_runs(self.config)[0]
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / "isolated"
            with patch.object(suite.subprocess, "Popen") as process:
                process.return_value.wait.return_value = 0
                suite.execute_run(self.config, run, folder)
            kwargs = process.call_args.kwargs
            self.assertEqual(kwargs["cwd"], folder)
            self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], "")
            self.assertEqual(kwargs["env"]["IFOGSIM_DISABLE_DASHBOARD"], "1")


class JavaRequirementTests(unittest.TestCase):
    def test_java_required_disables_fallback_on_connect_and_empty_responses(self):
        from env_ifogsim2 import iFogSim2Env
        with patch.dict(os.environ, {"IFOGSIM_REQUIRE_JAVA": "1"}), patch("env_ifogsim2.socket.socket") as sock:
            sock.return_value.connect.side_effect = ConnectionRefusedError()
            with self.assertRaisesRegex(RuntimeError, "fallback Python"):
                iFogSim2Env()
        for operation in ("reset", "step"):
            with self.subTest(operation=operation), patch.dict(os.environ, {"IFOGSIM_REQUIRE_JAVA": "1"}), patch("env_ifogsim2.socket.socket") as sock:
                sock.return_value.makefile.return_value.readline.return_value = ""
                with iFogSim2Env() as env:
                    with self.assertRaisesRegex(RuntimeError, "fallback Python"):
                        env.reset(seed=0) if operation == "reset" else env.step(0)

    def test_legacy_python_fallback_is_still_available(self):
        from env_ifogsim2 import iFogSim2Env
        with patch.dict(os.environ, {"IFOGSIM_REQUIRE_JAVA": "0"}), patch("env_ifogsim2.socket.socket") as sock:
            sock.return_value.connect.side_effect = ConnectionRefusedError()
            with iFogSim2Env() as env:
                _, info = env.reset(seed=1)
                self.assertNotEqual(info["source"], "java_ifogsim2")


if __name__ == "__main__":
    unittest.main()
