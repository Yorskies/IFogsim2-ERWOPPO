import json
import unittest

import numpy as np

from research_v2 import p13, p13_learners as L, p13_traces as T
from research_v2.config import ContractError, canonical_bytes, load_config
from research_v2.trace_access import TraceKey
from research_v2.traces import TraceGenerator

CONFIG = load_config()


class BenchmarkTraceTests(unittest.TestCase):
    def test_generator_is_byte_identical_to_the_locked_generator(self):
        for split, trace_id in (('validation', 10000), ('pilot_validation', 10003)):
            for workload in ('light', 'dynamic'):
                key = TraceKey(CONFIG['seeds']['master'], split, None, None, trace_id, workload)
                locked = TraceGenerator(CONFIG).generate(key, role='search_validator' if split == 'validation' else 'pilot_validator')
                self.assertEqual(canonical_bytes(T.build(CONFIG, key)), locked.canonical_json)

    def test_new_split_has_new_streams_and_a_valid_envelope(self):
        key = T.BenchmarkKey(CONFIG['seeds']['master'], 30000, 'heavy')
        trace = T.generate(CONFIG, key, purpose='prepare')
        self.assertEqual(trace['seed_namespace']['split'], 'benchmark_test')
        self.assertIn('benchmark_test', key.seed_text('arrival'))
        test_key = TraceKey(CONFIG['seeds']['master'], 'test', None, None, 20000, 'heavy')
        self.assertNotEqual(key.seed('arrival'), test_key.seed('arrival'))
        self.assertEqual(T.build(CONFIG, key), trace)                       # deterministic
        broken = json.loads(json.dumps(trace))
        broken['tasks'][0]['cpu_mi'] += 1
        with self.assertRaises(ContractError):
            T.check_envelope(broken, CONFIG)

    def test_sealed_until_opened_and_range_enforced(self):
        key = T.BenchmarkKey(CONFIG['seeds']['master'], 30099, 'light')
        with self.assertRaisesRegex(ContractError, 'sealed'):
            T.generate(CONFIG, key, purpose='evaluate')
        with self.assertRaisesRegex(ContractError, 'range'):
            T.generate(CONFIG, T.BenchmarkKey(CONFIG['seeds']['master'], 20000, 'light'), purpose='prepare')
        self.assertEqual(len(list(T.keys(CONFIG))), 400)


class LearnerTests(unittest.TestCase):
    def test_registered_grids(self):
        self.assertEqual({a: len(g) for a, g in L.GRIDS.items()}, {'dqn': 8, 'tabq': 8, 'ddpg': 8})
        self.assertEqual(L.GRIDS['dqn'][0], {'learning_rate': 1e-4, 'target_update_interval': 1000, 'exploration_fraction': 0.1})
        self.assertTrue(all(L.FIXED[a]['gamma'] == 0.97 for a in L.ALGORITHMS))

    def test_decision_log_window(self):
        self.assertTrue(all(L.logged(i, 204_800) for i in (0, 204_799)))
        B = 19_637_248
        self.assertEqual([L.logged(i, B) for i in (0, 102_399, 102_400, B - 102_401, B - 102_400, B - 1)],
                         [True, True, False, False, True, True])

    def test_tabular_state_bins(self):
        snap = {'task.deadline_relative_s': 1.0, 'task.cpu_mi': 100.0, 'task.class.light': 0.0, 'task.class.medium': 1.0,
                'task.class.heavy': 0.0}
        for i, name in enumerate(('source_iot', 'F1', 'F2', 'F3', 'F4', 'F5', 'cloud')):
            node = name
            snap[f'route.{name}.estimated_input_delay_s'] = 0.0
            snap[f'route.{name}.estimated_result_delay_s'] = 0.0
            snap[f'node.{node}.earliest_pe_free_delay_s'] = [0.1, 0.7, 2.0, 0.1, 0.1, 0.1, 0.1][i]
            snap[f'node.{node}.queued_mi_over_mips_s'] = 0.0
            snap[f'node.{node}.mips_per_pe'] = 1000.0
        bins = [0, 1, 2, 0, 0, 0, 0]
        expected = 0
        for b in bins:
            expected = expected * 3 + b
        self.assertEqual(L.tabular_state(snap), expected * 3 + 1)
        self.assertLess(L.tabular_state(snap), L.N_STATES)

    def test_tabular_update_and_epsilon(self):
        agent = L.TabularQ(1, 100, alpha=0.5, eps_end=0.05, eps_fraction=0.1)
        self.assertEqual(agent.epsilon(0), 1.0)
        self.assertAlmostEqual(agent.epsilon(10), 0.05)
        self.assertAlmostEqual(agent.epsilon(99), 0.05)
        agent.q[2, 3] = 4.0
        agent.update(1, 0, -1.0, 2, False)
        self.assertAlmostEqual(agent.q[1, 0], 0.5 * (-1.0 + 0.97 * 4.0))
        agent.update(1, 0, -1.0, None, True)
        self.assertEqual(agent.visits[1, 0], 2)

    def test_score_relaxation_argmax(self):
        self.assertEqual(L.ScoreActions.action(None, np.array([0.1, 0.9, 0.9, -1, 0, 0, 0])), 1)


class LockTests(unittest.TestCase):
    def test_seal_detects_any_change(self):
        lock = p13.seal({'a': 1, 'selected': {'dqn': {'index': 3}}})
        self.assertEqual(p13.seal(lock)['lock_sha256'], lock['lock_sha256'])
        tampered = {**lock, 'selected': {'dqn': {'index': 4}}}
        self.assertNotEqual(p13.seal(tampered)['lock_sha256'], lock['lock_sha256'])

    def test_hypothesis_families(self):
        self.assertEqual([h[0] for h in p13.PRIMARY], ['B1', 'B2', 'B3'])
        self.assertTrue(all(t == 'equal_B' for _, _, t in p13.PRIMARY))
        self.assertEqual(len(p13.SECONDARY), 6)


if __name__ == '__main__':
    unittest.main()
