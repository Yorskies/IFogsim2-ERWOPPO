import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from research_v2 import fidelity_v03 as F
from research_v2 import learner as L
from research_v2.config import ContractError, ROOT, load_config, sha256

CONFIG = load_config()
WORKLOADS = CONFIG['training']['workload_order']


class LearnerProtocolTests(unittest.TestCase):
    def test_v02_is_the_config_itself_and_v03_changes_only_gamma(self):
        v2, m2 = L.effective_learner(CONFIG, '0.2')
        v3, m3 = L.effective_learner(CONFIG, '0.3')
        self.assertEqual(v2, CONFIG)
        self.assertEqual(m2['learner_config_sha256'], sha256(CONFIG))
        self.assertEqual(v3['ppo']['gamma'], 0.97)
        self.assertEqual({k: v for k, v in v3['ppo'].items() if k != 'gamma'},
                         {k: v for k, v in CONFIG['ppo'].items() if k != 'gamma'})
        self.assertEqual({k: v for k, v in v3.items() if k != 'ppo'}, {k: v for k, v in CONFIG.items() if k != 'ppo'})
        self.assertEqual(m3['ppo_overrides'], {'gamma': 0.97})
        self.assertNotEqual(m3['learner_config_sha256'], m2['learner_config_sha256'])

    def test_unknown_version_and_tampered_files_are_refused(self):
        with self.assertRaises(ContractError):
            L.effective_learner(CONFIG, '0.4')
        spec = json.loads((ROOT / 'configs/research_v2/learner_v0.3.json').read_text())
        for mutate, needle in ((lambda s: s.update(simulation_config_sha256='0' * 64), 'another simulation config'),
                               (lambda s: s['ppo_overrides'].update(ent_coef=0.05), 'outside the registered keys'),
                               (lambda s: s['ppo_overrides'].update(gamma=0.5), 'out of bounds'),
                               (lambda s: s.update(protocol='research-v2-learner-9'), 'mismatch')):
            with tempfile.TemporaryDirectory() as tmp:
                data = json.loads(json.dumps(spec))
                mutate(data)
                path = Path(tmp) / 'learner.json'
                path.write_text(json.dumps(data))
                with patch.dict(L.FILES, {'0.3': path}):
                    with self.assertRaisesRegex(ContractError, needle):
                        L.effective_learner(CONFIG, '0.3')


def fake_gate(root, d_by_budget):
    """d_by_budget[n][outer] -> list of 8 per-weight cost scalars (same scalar on all 5 costs, both repeats)."""
    ids = list(F.weights())
    for n, per_outer in d_by_budget.items():
        for outer, values in per_outer.items():
            for weight, value in zip(ids, values):
                for repeat in F.REPEATS:
                    directory = F.model_dir(root, weight, outer, repeat) / f'eval_{n:08d}'
                    directory.mkdir(parents=True, exist_ok=True)
                    vector = [value] * 5
                    (directory / 'summary.json').write_text(json.dumps({'macro_costs': vector}))
                    rows = [{'namespace': {'workload': w}, 'metrics': {'costs': dict(zip(F.COSTS, vector))}}
                            for w in WORKLOADS for _ in range(5)]
                    (directory / 'episodes.jsonl').write_text('\n'.join(map(json.dumps, rows)) + '\n')
                    (directory.parent / 'done.json').write_text('{}')


def budgets(per_k):
    return {n: {o: per_k(n, o) for o in F.OUTERS} for n in (*F.LADDER, F.REFERENCE)}


REF = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80]


class FidelityGateTests(unittest.TestCase):
    def test_perfect_agreement_selects_the_smallest_K(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_gate(tmp, budgets(lambda n, o: REF))
            r = F.analyse(tmp)
        self.assertEqual((r['status'], r['selected_K']), ('fidelity_passed', 10240))
        self.assertEqual(r['ladder'][0]['median'], 1.0)

    def test_short_rankings_reversed_until_30720(self):
        reverse = REF[::-1]
        with tempfile.TemporaryDirectory() as tmp:
            fake_gate(tmp, budgets(lambda n, o: reverse if n < 30720 else REF))
            r = F.analyse(tmp)
        self.assertEqual(r['selected_K'], 30720)
        self.assertEqual([x['pass'] for x in r['ladder']], [False, False, True, True])

    def test_one_negative_outer_fails_even_with_high_median(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_gate(tmp, budgets(lambda n, o: REF[::-1] if (o == 102 and n < F.REFERENCE) else REF))
            r = F.analyse(tmp)
        self.assertEqual((r['status'], r['selected_K']), ('fidelity_failed_stop', None))
        self.assertEqual(r['ladder'][0]['median'], 1.0)
        self.assertEqual(r['ladder'][0]['minimum'], -1.0)

    def test_constant_reference_stops_and_constant_short_ranking_is_undefined(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_gate(tmp, budgets(lambda n, o: [0.3] * 8 if n == F.REFERENCE else REF))
            r = F.analyse(tmp)
        self.assertEqual(r['status'], 'fidelity_stopped_uninformative')
        with tempfile.TemporaryDirectory() as tmp:
            fake_gate(tmp, budgets(lambda n, o: [0.3] * 8 if n == 10240 else REF))
            r = F.analyse(tmp)
        self.assertEqual(r['ladder'][0]['median'], None)
        self.assertFalse(r['ladder'][0]['pass'])
        self.assertEqual(r['selected_K'], 20480)

    def test_ties_use_average_ranks(self):
        tied = [0.10, 0.10, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
        with tempfile.TemporaryDirectory() as tmp:
            fake_gate(tmp, budgets(lambda n, o: tied if n == 10240 else REF))
            r = F.analyse(tmp)
        expected = float(np.corrcoef([1.5, 1.5, 3, 4, 5, 6, 7, 8], range(1, 9))[0, 1])
        self.assertAlmostEqual(r['ladder'][0]['median'], expected)

    def test_audit_recomputes_from_raw_rows_and_detects_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_gate(tmp, budgets(lambda n, o: REF))
            for o in F.OUTERS:
                path = Path(tmp) / 'prefix' / f'equal_o{o}r0.json'
                path.parent.mkdir(exist_ok=True)
                path.write_text(json.dumps({'pass': True}))
            result = F.analyse(tmp)
            (Path(tmp) / 'result.json').write_text(json.dumps(result))
            self.assertEqual(F.audit(tmp)['status'], 'pass')
            # A summary that disagrees with its own episode rows must be caught.
            target = F.model_dir(tmp, 'equal', 100, 0) / 'eval_00010240' / 'summary.json'
            target.write_text(json.dumps({'macro_costs': [0.95] * 5}))
            tampered = F.analyse(tmp)
            (Path(tmp) / 'result.json').write_text(json.dumps(tampered))
            self.assertEqual(F.audit(tmp)['status'], 'fail')

    def test_v04_design_gives_K_equal_F_with_learner_v03(self):
        design = ROOT / 'configs/research_v2/design_v0.4.json'
        self.assertEqual(F.require_fidelity_gate(design), (CONFIG['training']['final_decisions'], '0.3'))
        data = json.loads(design.read_text())
        for mutate, needle in ((lambda d: d.update(candidate_decisions_K=30720), 'K = F'),
                               (lambda d: d.update(simulation_config_sha256='0' * 64), 'Config changed'),
                               (lambda d: d['predecessors']['v0.3'].update(fidelity_result_sha256='0' * 64), 'Predecessor v0.3')):
            with tempfile.TemporaryDirectory() as tmp:
                copy = json.loads(json.dumps(data))
                mutate(copy)
                path = Path(tmp) / 'design.json'
                path.write_text(json.dumps(copy))
                with self.assertRaisesRegex(ContractError, needle):
                    F.require_fidelity_gate(path)

    def test_superseded_v02_evidence_is_refused_on_v03_code(self):
        evidence = ROOT / 'results/research_v2/P08_fidelity_extension_1'
        with self.assertRaisesRegex(ContractError, 'Source changed after fidelity'):
            F.require_fidelity_gate(evidence)


if __name__ == '__main__':
    unittest.main()
