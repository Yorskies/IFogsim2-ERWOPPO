import unittest

import numpy as np

from research_v2 import p14, p14_search as S, p14_traces as T
from research_v2.config import ContractError, load_config
from research_v2.learning import aggregate_costs

CONFIG = load_config()


def fake(w):
    return [w[0] ** 2 + 0.1 * w[2], w[1] + 0.2 * w[3], 1 - w[2], w[3] * w[4], (w[4] - 0.2) ** 2]


def drive(search):
    while not search.done:
        batch = search.next_batch()
        if batch is None:
            break
        search.tell([fake(w) for w in batch])
    return search


class DevSplitTests(unittest.TestCase):
    def test_range_ids_and_independence(self):
        ids = [k.trace_id for k in T.keys(CONFIG, T.TRACE_IDS)]
        self.assertEqual(len(ids), 100)
        self.assertEqual(T.SEARCH_IDS[1] + 1, T.HOLDOUT_IDS[0])
        with self.assertRaisesRegex(ContractError, 'range'):
            T.generate(CONFIG, T.DevKey(CONFIG['seeds']['master'], 30000, 'light'))
        a = T.generate(CONFIG, T.DevKey(CONFIG['seeds']['master'], 40000, 'light'))
        self.assertEqual(a['seed_namespace']['split'], 'dev_validation')
        self.assertEqual(a, T.generate(CONFIG, T.DevKey(CONFIG['seeds']['master'], 40000, 'light')))


class SearchTests(unittest.TestCase):
    def test_every_algorithm_spends_exactly_the_slots_and_is_deterministic(self):
        for name in S.ALGORITHMS:
            a, b = drive(S.Search(name, 100, 90)), drive(S.Search(name, 100, 90))
            self.assertEqual(len(a.records), 90, name)
            self.assertEqual([r['weights'] for r in a.records], [r['weights'] for r in b.records], name)
            W = np.array([r['weights'] for r in a.records])
            self.assertTrue(np.allclose(W.sum(axis=1), 1) and W.min() >= 0.02 - 1e-12, name)
            np.testing.assert_allclose(W[:15], S.initial_population(100))           # shared initial population
            self.assertIn('selected_plain', a.summary())

    def test_no_state_leaks_between_searches(self):
        # regression: pymoo shares SPEA2's default survival object between instances
        for name in S.ALGORITHMS:
            first = [r['weights'] for r in drive(S.Search(name, 100, 60)).records]
            drive(S.Search(name, 101, 60))
            self.assertEqual([r['weights'] for r in drive(S.Search(name, 100, 60)).records], first, name)

    def test_initial_population_contains_equal_weights(self):
        np.testing.assert_allclose(S.initial_population(101)[0], [0.2] * 5)


class StatisticsTests(unittest.TestCase):
    def test_icc_extremes(self):
        self.assertAlmostEqual(p14.icc1([[1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3]]), 1.0)
        rng = np.random.default_rng(0)
        self.assertLess(abs(p14.icc1(rng.normal(size=(200, 4)))), 0.1)

    def test_spearman_brown(self):
        self.assertEqual(p14.spearman_brown(0.8, 0.8), 2)
        self.assertEqual(p14.spearman_brown(0.5, 0.8), 8)
        self.assertIsNone(p14.spearman_brown(0.0, 0.8))

    def test_cv_gain_uses_held_out_seeds(self):
        D = np.array([[0.30, 0.30, 0.30, 0.30], [0.20, 0.20, 0.20, 0.20]])
        self.assertAlmostEqual(p14.cv_gain(D, ['equal', 'good'])[0], 0.10)
        # a weight that is only lucky on some seeds earns no gain on the seeds it was not chosen on
        lucky = np.array([[0.30, 0.30, 0.30, 0.30], [0.10, 0.10, 0.50, 0.50]])
        gain, picks = p14.cv_gain(lucky, ['equal', 'lucky'])
        self.assertLess(gain, 0.0 + 1e-12 + 0.05)
        self.assertIn('lucky', picks)

    def test_d_matches_aggregate_costs(self):
        rng = np.random.default_rng(1)
        arr = rng.uniform(0, 1, (4, 3, 5))
        rows = [{'namespace': {'workload': w}, 'metrics': {'costs': dict(zip(p14.COSTS, arr[i, t]))}}
                for i, w in enumerate(CONFIG['training']['workload_order']) for t in range(3)]
        self.assertAlmostEqual(p14.d_of(arr), aggregate_costs(rows, CONFIG['training']['workload_order'])['D_macro'])

    def test_q1_weights_registered(self):
        names = [n for n, _ in p14.q1_weights()]
        self.assertEqual(len(names), 24)
        self.assertEqual(names[:2], ['equal', 'manual'])
        self.assertTrue(set(p14.Q1_LONG) <= set(names))


if __name__ == '__main__':
    unittest.main()
