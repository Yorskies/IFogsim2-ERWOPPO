import unittest
from unittest import mock

import numpy as np

from research_v2 import p15 as P, p16_traces as T
from research_v2.config import ContractError, load_config

CONFIG = load_config()


def fake_costs(w):
    w = np.asarray(w)
    return np.array([w[0] ** 2 + 0.1 * w[2], w[1] + 0.2 * w[3], 1 - w[2], w[3] * w[4], (w[4] - 0.2) ** 2])


class FakePool:
    def __init__(self):
        self.specs = []

    def submit(self, s):
        self.specs.append(s)


def drive(method):
    from research_v2.search import rms
    pool = FakePool()
    with mock.patch.object(P, 'score', lambda w, o, n: (fake_costs(w), rms(fake_costs(w)))), \
         mock.patch.object(P.Driver, 'specs_ready', lambda self, w, n: True):
        d = P.Driver(method, 3)
        while not d.search.done:
            d.advance(pool)
        return d, pool


class EvaluatorTests(unittest.TestCase):
    def test_four_models_per_candidate_and_three_elites_per_generation(self):
        for method in P.SEARCH_METHODS:
            d, pool = drive(method)
            self.assertEqual(len(d.search.records), P.SLOTS, method)
            self.assertEqual(len(d.elites), P.SLOTS // P.GENERATION * P.ELITE_PER_GENERATION, method)
            self.assertEqual(len({tuple(e) for e in d.elites}), len(d.elites), method)           # no candidate twice
            extra = [s for s in pool.specs if s['seed'] - P.P15_SEED_BASE - 100 * 3 >= P.BASE_MODELS]
            self.assertEqual(len(extra), len(d.elites) * P.ELITE_EXTRA, method)

    def test_common_random_numbers(self):
        a = P.candidate_spec([0.2] * 5, 7, 2)
        b = P.candidate_spec([0.1, 0.1, 0.6, 0.1, 0.1], 7, 2)
        self.assertEqual((a['seed'], a['stream']), (b['seed'], b['stream']))
        self.assertEqual(a['stream'], {'split': 'train_candidate', 'outer': 7, 'repeat': 0})
        self.assertEqual(a['eval']['ids'], list(P.SEARCH_IDS))

    def test_lock_seal(self):
        lock = P.seal({'a': 1, 'final': {'lean_zD': P.LEAN_ZD}})
        self.assertEqual(P.seal(lock)['lock_sha256'], lock['lock_sha256'])
        self.assertNotEqual(P.seal({**lock, 'a': 2})['lock_sha256'], lock['lock_sha256'])


class TestSplitTests(unittest.TestCase):
    def test_sealed_and_ranged(self):
        key = T.TestKey(CONFIG['seeds']['master'], 50000, 'heavy')
        with self.assertRaisesRegex(ContractError, 'sealed'):
            T.generate(CONFIG, key, purpose='evaluate')
        trace = T.generate(CONFIG, key, purpose='prepare')
        self.assertEqual(trace['seed_namespace']['split'], 'p16_test')
        with self.assertRaisesRegex(ContractError, 'range'):
            T.generate(CONFIG, T.TestKey(CONFIG['seeds']['master'], 40000, 'heavy'), purpose='prepare')
        self.assertEqual(len(list(T.keys(CONFIG))), 400)


if __name__ == '__main__':
    unittest.main()
