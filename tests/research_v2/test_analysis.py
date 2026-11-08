import itertools
import math
import unittest

import numpy as np
from scipy import stats as scipy_stats

from research_v2.analysis import stats as S
from research_v2.analysis.loader import rows_to_table
from research_v2.analysis.report import build_report, render
from research_v2.config import ContractError, load_config

CONFIG = load_config()
WORKLOADS = tuple(CONFIG['training']['workload_order'])


def make_table(methods=('equal_F', 'random', 'equal_B', 'nsga2'), outers=20, traces=6, seed=1, effects=None):
    """Synthetic costs in [0,1.2]. effects[m] is an additive shift of every cost for method m."""
    rng = np.random.default_rng(seed)
    z = {}
    base = {w: rng.uniform(0.1, 0.9, size=(1, outers, traces, 5)) for w in WORKLOADS}
    for w in WORKLOADS:
        z[w] = np.concatenate([np.clip(base[w] + (effects or {}).get(m, 0.0) + rng.normal(0, 0.01, size=base[w].shape), 0, None)
                               for m in methods])
    return S.Table(methods=tuple(methods), outers=tuple(range(outers)), workloads=WORKLOADS,
                   trace_ids={w: list(range(traces)) for w in WORKLOADS}, z=z)


class AggregationTests(unittest.TestCase):
    def test_trace_to_workload_to_global_by_hand(self):
        # one method, one outer, two traces per workload; worked by hand.
        z = {}
        for k, w in enumerate(WORKLOADS):
            a = np.full(5, 0.1 * (k + 1))
            b = np.full(5, 0.3 * (k + 1))
            z[w] = np.stack([a, b])[None, None]          # (1,1,2,5)
        table = S.Table(('m',), (0,), WORKLOADS, {w: [0, 1] for w in WORKLOADS}, z)
        agg = S.aggregate(table)
        workload_mean = np.array([0.2, 0.4, 0.6, 0.8])   # mean of 0.1k and 0.3k
        F = workload_mean.mean()                          # equal workload weights: 0.5
        self.assertAlmostEqual(agg['D'][0, 0], math.sqrt(5 * F ** 2 / 5))
        for k in range(4):
            self.assertAlmostEqual(agg['Dw'][0, 0, k], workload_mean[k])
        self.assertEqual(int(agg['worst_workload'][0, 0]), 3)

    def test_heavy_task_count_does_not_dominate(self):
        # Trace-level costs are averaged within a workload; a workload with more traces gets no extra weight.
        small = make_table(methods=('a',), outers=2, traces=2)
        big = make_table(methods=('a',), outers=2, traces=2)
        big.z['heavy'] = np.concatenate([big.z['heavy']] * 5, axis=2)
        big.trace_ids['heavy'] = list(range(10))
        np.testing.assert_allclose(S.aggregate(small)['D'], S.aggregate(big)['D'])


class SignFlipTests(unittest.TestCase):
    def brute(self, diffs):
        diffs = np.asarray(diffs, float)
        obs = abs(diffs.sum())
        hits = sum(abs(np.dot(signs, diffs)) >= obs - 1e-12 for signs in itertools.product((1, -1), repeat=len(diffs)))
        return hits / 2 ** len(diffs)

    def test_matches_brute_force_including_ties(self):
        for diffs in ([0.3, -0.1, 0.2, 0.2, -0.2], [1, 1, 1, -1, 0.5, 0.5, 2], [0.0, 0.0, 0.4], [-0.5, 0.25, 0.125, 0.0625]):
            self.assertAlmostEqual(S.exact_signflip_p(diffs), self.brute(diffs), places=12)

    def test_matches_scipy_permutation_test(self):
        diffs = np.array([0.31, -0.12, 0.2, 0.27, -0.05, 0.4, 0.11, 0.09])
        result = scipy_stats.permutation_test((diffs,), lambda x, axis: np.sum(x, axis=axis), permutation_type='samples',
                                              n_resamples=np.inf, alternative='two-sided')
        self.assertAlmostEqual(S.exact_signflip_p(diffs), float(result.pvalue), places=12)

    def test_all_differences_zero(self):
        table = make_table(methods=('equal_F', 'random', 'equal_B', 'nsga2'), outers=20)
        for m in ('equal_F', 'random', 'equal_B'):
            for w in WORKLOADS:
                table.z[w][table.methods.index(m)] = table.z[w][table.methods.index('nsga2')]
        report = S.analyse(table, CONFIG, bootstrap_draws=200, signflip_draws=2000)
        for row in report['primary']:
            self.assertEqual(row['raw_p_exact_signflip'], 1.0)
            self.assertEqual(row['holm_adjusted_p'], 1.0)
            self.assertEqual(row['mean_difference'], 0.0)
            self.assertEqual(row['ci95_difference'], [0.0, 0.0])
            self.assertIsNone(row['effect_size_dz']['dz'])
        self.assertTrue(all(c['holm_adjusted_p'] == 1.0 for c in report['secondary']))

    def test_all_same_sign_gives_two_over_two_to_the_n(self):
        diffs = np.linspace(0.01, 0.2, 20)
        self.assertEqual(S.exact_signflip_p(diffs), 2 / 2 ** 20)
        self.assertEqual(S.exact_signflip_p(-diffs), 2 / 2 ** 20)

    def test_swapping_the_pair_mirrors_everything(self):
        rng = np.random.default_rng(3)
        diffs = rng.normal(0.05, 0.1, 20)
        self.assertEqual(S.exact_signflip_p(diffs), S.exact_signflip_p(-diffs))
        self.assertAlmostEqual(S.paired_dz(diffs)['dz'], -S.paired_dz(-diffs)['dz'])
        table = make_table(effects={'nsga2': -0.05, 'equal_F': 0.0, 'random': 0.01, 'equal_B': 0.02}, outers=8)
        pairs = [('equal_F', 'nsga2'), ('nsga2', 'equal_F')]
        boot = S.bootstrap(table, pairs, draws=300, seed=7)
        np.testing.assert_allclose(boot['diff_ci'][:, 0], -boot['diff_ci'][::-1, 1])

    def test_sd_zero_with_nonzero_mean_is_undefined_not_zero(self):
        out = S.paired_dz(np.full(20, 0.1))
        self.assertIsNone(out['dz'])
        self.assertEqual(out['status'], 'undefined_zero_sd_nonzero_mean')
        self.assertEqual(S.exact_signflip_p(np.full(20, 0.1)), 2 / 2 ** 20)
        self.assertEqual(S.paired_dz([0.5])['status'], 'undefined_n_lt_2')

    def test_montecarlo_close_to_exact_and_never_zero(self):
        diffs = np.array([0.3, -0.1, 0.25, 0.4, 0.05, -0.02, 0.33, 0.1, 0.2, 0.15])
        signs = S.make_signs(100000, diffs.size, CONFIG['seeds']['secondary_signflip'])
        mc = S.montecarlo_signflip_p(diffs[None], signs)[0]
        self.assertLess(abs(mc - S.exact_signflip_p(diffs)), 0.01)
        strong = np.full(20, 1.0)
        floor = S.montecarlo_signflip_p(strong[None], S.make_signs(1000, 20, 1))[0]
        self.assertGreaterEqual(floor, 1 / 1001)
        self.assertEqual(S.make_signs(50, 20, 5).tolist(), S.make_signs(50, 20, 5).tolist())

    def test_exact_enumeration_limits(self):
        with self.assertRaises(ContractError):
            S.exact_signflip_p(np.ones(25))
        with self.assertRaises(ContractError):
            S.exact_signflip_p([0.1, np.nan])


class HolmTests(unittest.TestCase):
    def test_hand_computed_example(self):
        # sorted p: .005 .01 .03 .04 with m=4 -> 4*.005=.02, 3*.01=.03, 2*.03=.06, max(.06, 1*.04)=.06
        adjusted = S.holm([0.01, 0.04, 0.03, 0.005])
        np.testing.assert_allclose(adjusted, [0.03, 0.06, 0.06, 0.02])

    def test_caps_at_one_and_keeps_order(self):
        np.testing.assert_allclose(S.holm([0.5, 0.9, 0.2]), [1.0, 1.0, 0.6])
        np.testing.assert_allclose(S.holm([0.2]), [0.2])

    def test_matches_independent_closed_testing_reference(self):
        rng = np.random.default_rng(11)
        for _ in range(200):
            m = int(rng.integers(1, 9))
            p = np.round(rng.uniform(0, 1, m) ** 2, 4)
            if rng.random() < 0.3:
                p[rng.integers(0, m)] = p[rng.integers(0, m)]   # ties
            np.testing.assert_allclose(S.holm(p), S.holm_by_closed_testing(p), atol=1e-12)

    def test_rejects_invalid_pvalues(self):
        for bad in ([], [1.2], [-0.1], [np.nan]):
            with self.assertRaises(ContractError):
                S.holm(bad)


class BootstrapAndPairingTests(unittest.TestCase):
    def test_trace_indices_are_shared_by_all_models(self):
        table = make_table(outers=6, traces=8)
        i, j = table.methods.index('equal_F'), table.methods.index('nsga2')
        for w in WORKLOADS:
            table.z[w][i] = table.z[w][j]
        boot = S.bootstrap(table, [('equal_F', 'nsga2')], draws=200, seed=2)
        self.assertEqual(boot['diff_ci'].tolist(), [[0.0], [0.0]])     # identical models: zero in every draw
        self.assertTrue((boot['cell_ci'] == 0).all())

    def test_seed_reproducible_and_seed_sensitive(self):
        table = make_table(outers=6, traces=8, effects={'nsga2': -0.05})
        a = S.bootstrap(table, [('equal_F', 'nsga2')], draws=200, seed=20261105)
        b = S.bootstrap(table, [('equal_F', 'nsga2')], draws=200, seed=20261105)
        c = S.bootstrap(table, [('equal_F', 'nsga2')], draws=200, seed=1)
        np.testing.assert_array_equal(a['diff_ci'], b['diff_ci'])
        self.assertFalse(np.array_equal(a['diff_ci'], c['diff_ci']))

    def test_ci_brackets_true_effect_and_resamples_aggregation_not_means(self):
        table = make_table(outers=20, traces=10, effects={'nsga2': -0.1})
        point = float((S.aggregate(table)['D'][0] - S.aggregate(table)['D'][-1]).mean())
        boot = S.bootstrap(table, [('equal_F', 'nsga2')], draws=500, seed=4)
        self.assertLess(boot['diff_ci'][0, 0], point)
        self.assertGreater(boot['diff_ci'][1, 0], point)
        self.assertGreater(boot['diff_ci'][0, 0], 0)

    def test_unknown_pair_rejected(self):
        with self.assertRaises(ContractError):
            S.bootstrap(make_table(outers=3), [('nope', 'nsga2')], draws=2, seed=1)


class MissingDataTests(unittest.TestCase):
    def test_missing_or_nonfinite_data_is_an_error(self):
        table = make_table(outers=20)
        table.z['heavy'][0, 3, 2, 1] = np.nan
        with self.assertRaisesRegex(ContractError, 'non-finite'):
            S.analyse(table, CONFIG, bootstrap_draws=10, signflip_draws=100)

    def test_all_twenty_outer_runs_are_required(self):
        with self.assertRaisesRegex(ContractError, 'Missing or extra outer'):
            S.analyse(make_table(outers=19), CONFIG, bootstrap_draws=10, signflip_draws=100)

    def test_missing_method_and_shape_mismatch(self):
        table = make_table(methods=('equal_F', 'nsga2'), outers=20)
        with self.assertRaisesRegex(ContractError, 'Primary comparison needs'):
            S.analyse(table, CONFIG, bootstrap_draws=10, signflip_draws=100)
        table = make_table(outers=20)
        table.z['light'] = table.z['light'][:, :, :-1]
        with self.assertRaisesRegex(ContractError, 'shape'):
            S.validate_table(table)

    def test_loader_rejects_missing_cell_and_unpaired_traces(self):
        def row(trace, sha='a', split='validation'):
            return {'namespace': {'split': split, 'workload': 'light', 'trace_id': trace}, 'trace_sha256': sha,
                    'metrics': {'costs': dict(zip(S.COSTS, [0.1] * 5)), 'task_count': 10, 'violation': 0.1, 'reliability': 0.9}}
        cfg = {**CONFIG, 'training': {**CONFIG['training'], 'workload_order': ['light']}}
        ok = {('a', 0): [row(0), row(1)], ('b', 0): [row(0), row(1)]}
        self.assertEqual(rows_to_table(ok, cfg).methods, ('a', 'b'))
        with self.assertRaisesRegex(ContractError, 'Missing'):
            rows_to_table({('a', 0): [row(0)], ('a', 1): [row(0)], ('b', 0): [row(0)]}, cfg)
        with self.assertRaisesRegex(ContractError, 'pairing'):
            rows_to_table({('a', 0): [row(0)], ('b', 0): [row(0, sha='other')]}, cfg)
        with self.assertRaisesRegex(ContractError, 'not readable'):
            rows_to_table({('a', 0): [row(0, split='test')]}, cfg)


class FamilyAndReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = make_table(outers=20, traces=5, effects={'nsga2': -0.04, 'random': -0.01, 'equal_B': -0.06})
        cls.report = S.analyse(cls.table, CONFIG, bootstrap_draws=300, signflip_draws=3000)

    def test_registered_families(self):
        r = self.report
        self.assertEqual([x['id'] for x in r['primary']], ['RQ1', 'RQ2', 'RQ3'])
        self.assertTrue(all(x['label'] == 'confirmatory_primary' for x in r['primary']))
        self.assertEqual(len(r['secondary']), 60)
        self.assertEqual(len({x['id'] for x in r['secondary']}), 60)
        self.assertTrue(all(x['label'] == 'secondary_prespecified' for x in r['secondary']))
        np.testing.assert_allclose([x['holm_adjusted_p'] for x in r['primary']],
                                   S.holm([x['raw_p_exact_signflip'] for x in r['primary']]))
        np.testing.assert_allclose([x['holm_adjusted_p'] for x in r['secondary']],
                                   S.holm([x['raw_p_montecarlo_signflip'] for x in r['secondary']]))

    def test_unit_is_the_outer_run_and_p_values_are_not_pooled(self):
        r = self.report
        self.assertEqual(r['protocol']['n_units'], 20)
        self.assertEqual(r['protocol']['traces_per_workload'], {w: 5 for w in WORKLOADS})
        self.assertFalse(r['protocol']['pools_tasks_or_episodes_as_replicates'])
        self.assertFalse(r['protocol']['p_values_averaged'])
        self.assertTrue(all(len(x['differences_by_outer']) == 20 for x in r['primary']))

        def keys(value):
            if isinstance(value, dict):
                for k, v in value.items():
                    yield k
                    yield from keys(v)
            elif isinstance(value, list):
                for v in value:
                    yield from keys(v)
        self.assertFalse([k for k in keys(r) if 'mean_p' in k or 'pooled' in k.replace('pools_', '')])

    def test_sign_convention_positive_means_nsga_better(self):
        by_id = {x['id']: x for x in self.report['primary']}
        self.assertGreater(by_id['RQ1']['mean_difference'], 0)           # equal_F is worse than the better nsga2
        self.assertLess(by_id['RQ3']['mean_difference'], 0)              # equal_B was given the lower cost here
        self.assertTrue(by_id['RQ1']['meets_1pct_reporting_screen'])

    def test_deterministic_for_fixed_seeds(self):
        again = S.analyse(self.table, CONFIG, bootstrap_draws=300, signflip_draws=3000)
        self.assertEqual(self.report['primary'], again['primary'])
        self.assertEqual(self.report['secondary'], again['secondary'])

    def test_family_size_must_match_registration(self):
        bad = {**CONFIG, 'statistics': {**CONFIG['statistics'], 'secondary_family_size': 59}}
        with self.assertRaises(ContractError):
            S.analyse(self.table, bad, bootstrap_draws=10, signflip_draws=100)

    def test_rendered_report_labels_and_assumption(self):
        report = build_report(self.table, CONFIG, bootstrap_draws=100, signflip_draws=1000, expected_outers=range(20),
                              exploratory_pairs=[('equal_F', 'equal_B')])
        text = render(report)
        for needle in ('outer training run', 'positive = NSGA-II better', 'symmetric about zero', 'confirmatory (3 tests',
                       'secondary, pre-specified (60 tests', 'exploratory (unregistered family', 'not evidence of practical benefit'):
            self.assertIn(needle, text)
        self.assertEqual(len([l for l in text.splitlines() if l.startswith('| RQ') and ':' not in l.split('|')[1]]), 3)
        self.assertEqual(report['exploratory'][0]['label'], 'exploratory_unadjusted')


if __name__ == '__main__':
    unittest.main()
