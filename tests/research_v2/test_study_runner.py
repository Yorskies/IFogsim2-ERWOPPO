import json
from pathlib import Path
import tempfile
import unittest

from research_v2.config import ContractError, ROOT, load_config, read_json
from research_v2.learning import file_hash
from research_v2.study_budget import budget, build_plan, job_manifest
from research_v2.study_final import FinalStream
from research_v2.study_worker import compress_decision_logs
from research_v2.study_runner import (StudyLock, process_start, atomic_json, attempt_history, verify_complete,
                                      verify_plan)


class BudgetTests(unittest.TestCase):
    def test_B01_rounds_only_baseline_and_charges_validation(self):
        config = load_config()
        traces = [{'workload': w, 'trace_id': 10000 + i, 'tasks': 975,
                   'payload_sha256': '0' * 64} for w in config['training']['workload_order'] for i in range(5)]
        b = budget(config, K=5120, slots=80, F=102400, traces=traces)
        self.assertEqual((b['Ntrace'], b['S'], b['V'], b['C'], b['B'], b['rounding_overhead']),
                         (19500, 819200, 3120000, 4041600, 4041728, 128))
        self.assertEqual(b['physical_total_per_outer'], 2 * (b['C'] + b['B']))

    def test_actual_validation_trace_count_and_revised_K(self):
        p = build_plan(K=30720, outers=[0])
        b = p['budget']
        self.assertEqual((b['Ntrace'], b['S'], b['V'], b['C'], b['B']),
                         (19690, 4915200, 3150400, 8168000, 8168448))
        self.assertEqual(len(p['validation_traces']), 20)
        self.assertFalse(p['test_accessed'])

    def test_A_B_reuse_search_and_final_jobs(self):
        jobs = job_manifest(0)
        self.assertEqual(len(jobs), 6)
        self.assertEqual({x['id'] for x in jobs if x['role'] == 'search'},
                         {'r00_nsga2_search', 'r00_random_search'})
        self.assertEqual({x['depends_on'] for x in jobs if x['role'] == 'final'},
                         {'r00_nsga2_search', 'r00_random_search'})
        self.assertTrue(all(x['protocols'] == ['A', 'B'] for x in jobs))

    def test_final_stream_uses_fixed_method_independent_namespace(self):
        config = load_config()
        first = FinalStream(config, 0)
        second = FinalStream(config, 0)
        a = first(None, 0)
        b = second(None, 0)
        self.assertEqual(a['payload_sha256'], b['payload_sha256'])
        self.assertEqual(a['seed_namespace']['split'], 'train_final')
        self.assertEqual(a['seed_namespace']['model_repeat'], 0)


class OwnershipTests(unittest.TestCase):
    def test_active_owner_refuses_second_writer(self):
        with tempfile.TemporaryDirectory() as tmp:
            with StudyLock(Path(tmp)):
                with self.assertRaises(ContractError):
                    with StudyLock(Path(tmp)):
                        pass

    def test_dead_owner_is_archived_before_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock = StudyLock(root)
            dead = {**lock.owner, 'pid': 99999999, 'process_start': 'dead'}
            atomic_json(root / '.owner.lock', dead)
            with StudyLock(root):
                self.assertEqual(len(list(root.glob('.owner.stale.*.json'))), 1)
            self.assertFalse((root / '.owner.lock').exists())

    def test_completed_pointer_rejects_tampered_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            job = {'id': 'r00_equal', 'role': 'baseline', 'outer': 0}
            attempt = root / 'jobs/r00_equal/attempt_000'
            (attempt / 'data').mkdir(parents=True)
            (attempt / 'data/result.json').write_text('{}')
            atomic_json(root / 'jobs/r00_equal/complete.json', {
                'status': 'complete', 'job_id': job['id'],
                'attempt': 'jobs/r00_equal/attempt_000', 'result_sha256': '0' * 64,
                'artifact_sha256': {}})
            with self.assertRaises(ContractError):
                verify_complete(root, job, {'budget': {}, 'fixture_only': True})


class LivenessTests(unittest.TestCase):
    def test_zombie_is_not_a_live_owner(self):
        import os
        import subprocess
        import sys
        import time
        child = subprocess.Popen([sys.executable, '-c', 'pass'])
        try:
            self.assertIsNotNone(process_start(os.getpid()))
            for _ in range(100):  # exited but not reaped = zombie, as under a PID 1 that never reaps
                if Path(f'/proc/{child.pid}/stat').read_text().rsplit(')', 1)[1].split()[0] == 'Z':
                    break
                time.sleep(0.05)
            self.assertIsNone(process_start(child.pid))
        finally:
            child.wait()


class AttemptTests(unittest.TestCase):
    def _attempts(self, root, statuses):
        paths = []
        for i, status in enumerate(statuses):
            path = root / f'attempt_{i:03d}'
            path.mkdir()
            if status is not None:
                atomic_json(path / 'status.json', status)
            paths.append(path)
        return paths

    def test_interrupted_attempts_do_not_consume_technical_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._attempts(Path(tmp), [
                {'status': 'interrupted'}, {'status': 'interrupted'}, None,
                {'status': 'failed', 'kind': 'technical'}])
            self.assertEqual(attempt_history(paths), (1, 0))

    def test_algorithmic_failure_is_reported_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = self._attempts(Path(tmp), [
                {'status': 'failed', 'kind': 'technical'}, {'status': 'failed', 'kind': 'algorithmic'}])
            self.assertEqual(attempt_history(paths), (1, 1))


class LogCompressionTests(unittest.TestCase):
    def test_gzip_is_lossless_deterministic_and_removes_raw(self):
        import gzip
        with tempfile.TemporaryDirectory() as tmp:
            rows = ''.join(json.dumps({'task_id': i, 'x': [i] * 40}) + '\n' for i in range(500))
            outputs = []
            for name in ('a', 'b'):
                directory = Path(tmp) / name / 'training'
                directory.mkdir(parents=True)
                (directory / 'decisions.jsonl').write_text(rows)
                raw, packed = compress_decision_logs(Path(tmp) / name)
                self.assertGreater(raw, 5 * packed)
                self.assertFalse((directory / 'decisions.jsonl').exists())
                self.assertEqual(gzip.open(directory / 'decisions.jsonl.gz', 'rt').read(), rows)
                outputs.append((directory / 'decisions.jsonl.gz').read_bytes())
            self.assertEqual(outputs[0], outputs[1])


class DriftTests(unittest.TestCase):
    def _fixture_plan(self, root):
        plan = build_plan(K=512, outers=[0], mini=True)
        plan['jar_sha256'] = read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256']
        plan['source_hashes'] = {p.relative_to(ROOT).as_posix(): file_hash(p)
                                 for p in sorted((ROOT / 'research_v2').glob('*.py'))}
        atomic_json(root / 'protocol.json', plan)
        return plan

    def test_untouched_plan_verifies_and_each_drift_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self._fixture_plan(root)
            self.assertEqual(verify_plan(root)['config_sha256'], plan['config_sha256'])
            for key, value, message in (('config_sha256', '0' * 64, 'config'),
                                        ('jar_sha256', '0' * 64, 'JAR')):
                changed = {**plan, key: value}
                atomic_json(root / 'protocol.json', changed)
                with self.assertRaisesRegex(ContractError, message):
                    verify_plan(root)
            changed = {**plan, 'source_hashes': {**plan['source_hashes'], 'research_v2/search.py': '0' * 64}}
            atomic_json(root / 'protocol.json', changed)
            with self.assertRaisesRegex(ContractError, 'source drift'):
                verify_plan(root)
            changed = {**plan, 'validation_manifest_sha256': '0' * 64}
            atomic_json(root / 'protocol.json', changed)
            with self.assertRaisesRegex(ContractError, 'trace drift'):
                verify_plan(root)


if __name__ == '__main__':
    unittest.main()
