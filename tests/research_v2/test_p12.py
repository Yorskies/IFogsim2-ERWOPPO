import copy
import json
import shutil
import unittest
import zipfile

from research_v2 import p12
from research_v2.config import ContractError, ROOT, load_config, sha256, validate_config
from research_v2.engine_runner import JAR
from research_v2.trace_access import TraceKey
from research_v2.traces import TraceGenerator

CONFIG = load_config()


def mutated(name):
    config = copy.deepcopy(CONFIG)
    p12.variant_specs(CONFIG)[name][1](config)
    return config


class VariantTests(unittest.TestCase):
    def test_levels_come_from_the_registered_sensitivity_block(self):
        specs = p12.variant_specs(CONFIG)
        s = CONFIG['sensitivity']
        expected = (['identity'] + [f'timeout_k{k:g}' for k in s['timeout_factors']] + [f'fog_queue_{q}' for q in s['fog_queue_waiting']]
                    + [f'wan_prop_{p:g}' for p in s['wan_propagation_s']] + [f'dyn_power_x{m:g}' for m in s['dynamic_power_multipliers']]
                    + ['homogeneous_fog'])
        self.assertEqual(list(specs), expected)
        self.assertEqual(specs['homogeneous_fog'][2], {'homogeneous_fog': True})

    def test_each_variant_changes_one_factor_and_never_the_normalization(self):
        for name, (_, mutate, _) in p12.variant_specs(CONFIG).items():
            if mutate is None:
                continue
            config = mutated(name)
            changed = p12.validate_variant(config, CONFIG)
            self.assertEqual(config['evaluation'], CONFIG['evaluation'])
            self.assertEqual(config['observation'], CONFIG['observation'])
            self.assertEqual(len(changed) > 0, name != 'identity', name)
        self.assertEqual(mutated('identity'), CONFIG)
        k4 = mutated('timeout_k4')
        self.assertEqual(k4['timing']['horizon_s'], 60 + 4 * 3)
        with self.assertRaisesRegex(ContractError, 'latency reference'):
            validate_config(k4)       # k = 4 breaks the main contract by design; validate_variant documents and allows it
        power = mutated('dyn_power_x0.75')
        f1, g1 = power['topology']['fogs'][0], CONFIG['topology']['fogs'][0]
        self.assertAlmostEqual(f1['busy_w'] - f1['idle_w'], 0.75 * (g1['busy_w'] - g1['idle_w']))
        self.assertEqual(f1['idle_w'], g1['idle_w'])
        self.assertAlmostEqual(power['network']['wan_j_per_bit_hop'], 0.75 * CONFIG['network']['wan_j_per_bit_hop'])
        self.assertEqual(power['network']['wan_idle_w'], CONFIG['network']['wan_idle_w'])

    def test_unregistered_changes_are_refused(self):
        config = mutated('fog_queue_8')
        config['evaluation']['latency_reference_s'] = 12.0
        config['evaluation']['failure_latency_penalty_s'] = 12.0
        with self.assertRaisesRegex(ContractError, 'unregistered blocks|normalization'):
            p12.validate_variant(config, CONFIG)

    def test_variant_trace_keeps_arrivals_and_scales_timeouts(self):
        key = TraceKey(CONFIG['seeds']['master'], 'validation', None, None, 10000, 'light')
        trace = TraceGenerator(CONFIG).generate(key, role='search_validator').to_dict()
        self.assertEqual(p12.variant_trace(trace, CONFIG), trace)
        k2 = mutated('timeout_k2')
        out = p12.variant_trace(trace, k2)
        self.assertEqual(out['config_sha256'], sha256(k2))
        self.assertEqual(out['horizon_s'], 66.0)
        self.assertEqual([t['arrival_s'] for t in out['tasks']], [t['arrival_s'] for t in trace['tasks']])
        self.assertTrue(all(t['timeout_relative_s'] == 2.0 * t['deadline_relative_s'] for t in out['tasks']))

    def test_variant_jar_differs_only_in_the_config_resource(self):
        target = ROOT / 'ifogsim/dist_p12/_unittest/variant.jar'
        try:
            data = (json.dumps(mutated('wan_prop_0.04'), indent=2) + '\n').encode()
            record = p12.build_variant_jar(JAR, target, data)
            self.assertTrue(record['config_entry_changed'])
            with zipfile.ZipFile(target) as z:
                self.assertEqual(z.read(p12.CONFIG_ENTRY), data)
            a, b = p12.jar_entries(JAR), p12.jar_entries(target)
            self.assertEqual([n for n in a if a[n] != b[n]], [p12.CONFIG_ENTRY])
        finally:
            shutil.rmtree(target.parent, ignore_errors=True)


def row(zL_mean=0.5, failed=2, n=10):
    ev = CONFIG['evaluation']
    completed = n - failed
    zL = (zL_mean * completed + failed * ev['failure_latency_penalty_s']) / (n * ev['latency_reference_s'])
    return {'metrics': {'task_count': n, 'failed': failed, 'latency': {'completed_tasks': completed, 'mean_s': zL_mean},
                        'costs': {'zL': zL, 'zE': 0.3, 'zD': 0.2, 'zB': 0.4, 'zQ': failed / n}}}


class NormalizationTests(unittest.TestCase):
    def test_identity_multipliers_return_the_same_costs(self):
        r = row()
        self.assertEqual(p12.renormalize(r, CONFIG, 1, 1, 1, 1)['metrics']['costs'], r['metrics']['costs'])

    def test_scaled_references(self):
        r = row()
        c = p12.renormalize(r, CONFIG, 2, 1, 0.5, 4)['metrics']['costs']
        # Reference and penalty scale together (main rule penalty = reference): only measured latency is divided by 2.
        self.assertAlmostEqual(c['zL'], (0.5 * 8 / 2 + 2 * 9) / 90)
        self.assertAlmostEqual(c['zE'], 0.6)
        self.assertAlmostEqual(c['zB'], 0.1)
        self.assertEqual((c['zD'], c['zQ']), (0.2, 0.2))
        pen = p12.renormalize(r, CONFIG, 1, 1.2, 1, 1)['metrics']['costs']['zL']
        self.assertAlmostEqual(pen, (0.5 * 8 + 2 * 9 * 1.2) / 90)

    def test_inconsistent_row_is_refused(self):
        r = row()
        r['metrics']['costs']['zL'] += 0.01
        with self.assertRaisesRegex(ContractError, 'reconstructed'):
            p12.renormalize(r, CONFIG, 1, 1, 1, 1)

    def test_registered_normalization_variants(self):
        names = list(p12.normalization_variants(CONFIG))
        self.assertEqual(len(names), 4 * len(CONFIG['sensitivity']['normalization_multipliers']))


if __name__ == '__main__':
    unittest.main()
