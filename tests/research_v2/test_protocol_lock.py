import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research_v2 import trace_access
from research_v2.analysis import lock as L
from research_v2.config import ContractError, ROOT, load_config, sha256

FIDELITY = ROOT / 'results/research_v2/v0.3/fidelity'
V02_LOCK = ROOT / 'results/research_v2/P10_protocol_lock/protocol_lock.json'


class ProtocolLockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """The real v0.3 gate failed, so no real v0.3 lock exists. Mechanism tests use a SYNTHETIC lock: the gate result is
        patched to K=30,720 and the v0.2 live evidence/dry-run stand in for the (never produced) v0.3 ones."""
        cls.tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls.tmp.name)
        dry = json.loads((ROOT / L.ARTIFACTS['0.2']['dry_run']).read_text())
        dry['learner_version'] = '0.3'
        (tmp / 'dry_run.json').write_text(json.dumps(dry))
        artifacts = {**L.ARTIFACTS['0.3'], 'live_evidence': L.ARTIFACTS['0.2']['live_evidence'],
                     'dry_run': str((tmp / 'dry_run.json').relative_to(ROOT)) if str(tmp).startswith(str(ROOT)) else str(tmp / 'dry_run.json')}
        cls.patches = [patch.dict(L.ARTIFACTS, {'0.3': artifacts}),
                       patch('research_v2.fidelity_v03.require_fidelity_gate', return_value=(30720, '0.3'))]
        for item in cls.patches:
            item.start()
        cls.path = tmp / 'protocol_lock.json'
        cls.lock = L.build_lock(fidelity_evidence=FIDELITY, deviations=['synthetic unit-test lock'])
        cls.path.write_text(json.dumps(cls.lock, indent=2, sort_keys=True))

    @classmethod
    def tearDownClass(cls):
        for item in reversed(cls.patches):
            item.stop()
        cls.tmp.cleanup()

    def tearDown(self):
        trace_access._TEST_UNSEALED = None

    def test_contents_freeze_the_registered_design(self):
        lock = self.lock
        self.assertEqual(lock['version'], 'P10-lock-2')
        self.assertEqual(lock['frozen_design']['candidate_decisions_K'], 30720)
        self.assertEqual(lock['frozen_design']['baseline_budget_B'], 8168448)
        self.assertEqual(lock['frozen_design']['final_decisions_F'], 102400)
        self.assertEqual(lock['frozen_design']['ppo_effective']['gamma'], 0.97)
        self.assertEqual(lock['frozen_design']['ppo']['gamma'], 1.0)            # the simulation config itself is unchanged
        self.assertEqual(lock['learner']['ppo_overrides'], {'gamma': 0.97})
        self.assertEqual(lock['predecessor']['lock_sha256'], json.loads(V02_LOCK.read_text())['lock_sha256'])
        self.assertEqual(lock['predecessor']['git_tag'], 'protocol-v0.2')
        self.assertTrue(lock['diagnosis_evidence'])
        self.assertEqual(lock['frozen_design']['seeds'], load_config()['seeds'])
        self.assertEqual([h['id'] for h in lock['hypotheses']['primary']], ['RQ1', 'RQ2', 'RQ3'])
        self.assertEqual(len(lock['hypotheses']['secondary_ids']), 60)
        self.assertEqual(len(set(lock['hypotheses']['secondary_ids'])), 60)
        self.assertFalse(lock['test_opened'])
        self.assertTrue(lock['traces']['test']['prepared_only'])
        self.assertFalse(lock['traces']['test']['outcomes_observed'])
        self.assertEqual(lock['traces']['test']['traces'], 400)
        self.assertIn('caveat', lock['fidelity'])
        self.assertTrue(lock['sources'])
        self.assertEqual(sorted(lock['sensitivity']['registered_factors']), sorted(load_config()['sensitivity']))
        self.assertIn('adding seeds until significant', lock['hypotheses']['forbidden'])

    def test_untouched_lock_verifies(self):
        problems, _ = L.verify_lock(self.path)
        self.assertEqual(problems, [])
        self.assertEqual(L.require_valid_lock(self.path)['lock_sha256'], self.lock['lock_sha256'])

    def test_modified_missing_added_files(self):
        real = L.source_hashes()
        name = next(iter(self.lock['sources']))
        changed = {**real, name: '0' * 64}
        with patch.object(L, 'source_hashes', return_value=changed):
            problems, _ = L.verify_lock(self.path)
        self.assertIn(f'locked file modified: {name}', problems)
        missing = {k: v for k, v in real.items() if k != name}
        with patch.object(L, 'source_hashes', return_value=missing):
            problems, _ = L.verify_lock(self.path)
        self.assertIn(f'locked file missing: {name}', problems)
        added = {**real, 'research_v2/test_evaluator_new.py': 'f' * 64}
        with patch.object(L, 'source_hashes', return_value=added):
            problems, warnings = L.verify_lock(self.path)
        self.assertEqual(problems, [])
        self.assertTrue(any('added after the lock' in w for w in warnings))

    def test_tampered_lock_file_is_rejected(self):
        for mutate, needle in ((lambda d: d['frozen_design'].update(candidate_decisions_K=5120), 'own hash'),
                               (lambda d: d.update(test_opened=True), 'already opened'),
                               (lambda d: d['hypotheses']['primary'].pop(), 'own hash')):
            data = copy.deepcopy(self.lock)
            mutate(data)
            path = Path(self.tmp.name) / 'tampered.json'
            path.write_text(json.dumps(data))
            problems, _ = L.verify_lock(path)
            self.assertTrue(any(needle in p for p in problems), (needle, problems))

    def test_config_jar_seed_and_evidence_drift(self):
        config = load_config()
        with patch.object(L, 'load_config', return_value={**config, 'seeds': {**config['seeds'], 'bootstrap': 1}}):
            problems, _ = L.verify_lock(self.path)
        self.assertTrue(any('config differs' in p for p in problems) and any('seeds differ' in p for p in problems))
        real = L.file_sha256
        with patch.object(L, 'file_sha256', side_effect=lambda p: '0' * 64 if 'live_evidence' in str(p) else real(p)):
            problems, _ = L.verify_lock(self.path)
        self.assertTrue(any('evidence changed' in p for p in problems))

    def test_real_v03_lock_is_refused_because_the_gate_failed(self):
        for item in reversed(self.patches):
            item.stop()
        try:
            with self.assertRaisesRegex(ContractError, 'v0.3 fidelity gate did not pass'):
                L.build_lock(fidelity_evidence=FIDELITY)
        finally:
            for item in self.patches:
                item.start()

    def test_v02_lock_is_preserved_but_superseded_on_this_tree(self):
        v02 = json.loads(V02_LOCK.read_text())
        self.assertEqual(v02['version'], 'P10-lock-1')
        problems, _ = L.verify_lock(V02_LOCK)
        self.assertTrue(any(p.startswith('locked file modified') for p in problems))   # verifies only at tag protocol-v0.2
        self.assertFalse(any('own hash' in p for p in problems))                       # the archived file itself is intact

    def test_learner_protocol_drift_is_a_violation(self):
        from research_v2 import learner
        real = learner.effective_learner
        def changed(config, version):
            cfg, meta = real(config, version)
            return cfg, {**meta, 'ppo_overrides': {'gamma': 0.98}}
        with patch.object(learner, 'effective_learner', side_effect=changed):
            problems, _ = L.verify_lock(self.path)
        self.assertIn('learner protocol differs from lock', problems)

    def test_dependency_drift_is_a_violation(self):
        data = copy.deepcopy(self.lock)
        data['environment']['packages']['numpy'] = '0.0.1'
        data['lock_sha256'] = L.hashlib.sha256(json.dumps({k: v for k, v in data.items() if k != 'lock_sha256'},
                                                          sort_keys=True).encode()).hexdigest()
        path = Path(self.tmp.name) / 'dependency.json'
        path.write_text(json.dumps(data))
        problems, _ = L.verify_lock(path)
        self.assertTrue(any(p.startswith('package numpy') for p in problems))

    def test_test_split_is_sealed_until_a_valid_lock_is_verified(self):
        for operation in ('read', 'describe', 'generate'):
            with self.assertRaisesRegex(ContractError, 'sealed'):
                trace_access.authorize('test_evaluator', 'test', operation)
        trace_access.authorize('holdout_preparer', 'test', 'generate')       # preparation only
        with self.assertRaisesRegex(ContractError, 'sealed'):
            trace_access.authorize('holdout_preparer', 'test', 'read')
        for role in ('search_validator', 'final_trainer', 'calibrator', 'candidate_trainer'):
            with self.assertRaises(ContractError):
                trace_access.authorize(role, 'test', 'generate')
        bad = copy.deepcopy(self.lock)
        bad['test_opened'] = True
        bad_path = Path(self.tmp.name) / 'bad.json'
        bad_path.write_text(json.dumps(bad))
        with self.assertRaises(ContractError):
            trace_access.unseal_test(bad_path)
        with self.assertRaisesRegex(ContractError, 'sealed'):
            trace_access.authorize('test_evaluator', 'test', 'read')
        trace_access.unseal_test(self.path)
        for operation in ('read', 'describe', 'generate'):
            trace_access.authorize('test_evaluator', 'test', operation)
        with self.assertRaisesRegex(ContractError, 'sealed'):
            trace_access.authorize('holdout_preparer', 'test', 'read')       # unsealing does not widen other roles
        with self.assertRaises(ContractError):
            trace_access.authorize('test_evaluator', 'validation', 'read')   # evaluator is test-only


if __name__ == '__main__':
    unittest.main()
