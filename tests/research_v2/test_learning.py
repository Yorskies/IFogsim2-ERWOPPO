"""P07 preparation checks. NO learn(), optimizer step, rollout collection or Java server."""
import json
from pathlib import Path
import random
import tempfile
import unittest

import gymnasium as gym
import numpy as np
import torch

from research_v2.config import ContractError, load_config
from research_v2.learning import (AuditedPPO, EpisodeAudit, PilotStream, equal_nested,
                                  pilot_plan, ppo_kwargs, rng_state, aggregate_costs)


class FakeEnv(gym.Env):
    observation_space = gym.spaces.Box(-1, 2, (108,), dtype=np.float32)
    action_space = gym.spaces.Discrete(7)
    weights = np.array([0.2] * 5)
    last_cost_cumulative = np.zeros(5)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.index = 0
        return np.zeros(108, dtype=np.float32), {}

    def step(self, action):
        self.index += 1
        terminal = self.index == 2
        costs = {k: 0.1 for k in ('zL', 'zE', 'zD', 'zB', 'zQ')}
        return np.zeros(108, dtype=np.float32), -10.0 if terminal else 0.0, terminal, False, {
            'summary': {'metrics': {'costs': costs}} if terminal else None}


class LearningPreparationTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_macro_score_is_rms_after_equal_workload_aggregation(self):
        rows = [{'namespace': {'workload': w}, 'metrics': {'costs': dict(zip(
                    ('zL', 'zE', 'zD', 'zB', 'zQ'), z))}} for w, z in
                [('a', [1,0,0,0,0]), ('a', [1,0,0,0,0]), ('b', [0,0,0,0,0])]]
        result = aggregate_costs(rows, ['a','b'])
        self.assertEqual(result['macro_costs'], [0.5,0,0,0,0])
        self.assertAlmostEqual(result['D_macro'], np.sqrt(0.05))
        self.assertNotAlmostEqual(result['D_macro'], np.mean(result['macro_costs']))

    def validation_fixture(self, directory):
        from research_v2.learning import write_json
        data = []
        for w in self.config['training']['workload_order']:
            for trace_id in range(10000,10005):
                data.append({'namespace': {'split':'pilot_validation','workload':w,'trace_id':trace_id},
                             'decisions':1, 'reward':-10.0, 'action_counts':[1,0,0,0,0,0,0],
                             'metrics': {'task_count':1,'diagnosis_required':False,'reliability':1.0,
                             'violation':0.0,'latency':{'mean_s':0.2},
                             'costs':{k:0.1 for k in ('zL','zE','zD','zB','zQ')}}})
        write_json(Path(directory)/'summary.json', {'D_macro':0.1,'macro_costs':[0.1]*5})
        return data

    def test_evidence_audit_rejects_missing_or_duplicate_validation(self):
        from research_v2.learning_report import audit_validation
        with tempfile.TemporaryDirectory() as tmp:
            data=self.validation_fixture(tmp)
            for invalid in (data[:-1], data[:-1]+[data[0]]):
                (Path(tmp)/'episodes.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in invalid))
                with self.assertRaises(ContractError):
                    audit_validation(Path(tmp))

    def test_evidence_audit_rejects_reward_corruption(self):
        from research_v2.learning_report import audit_validation
        with tempfile.TemporaryDirectory() as tmp:
            data=self.validation_fixture(tmp)
            data[0]['reward']=-9.0
            (Path(tmp)/'episodes.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in data))
            with self.assertRaises(ContractError):
                audit_validation(Path(tmp))

    def test_evidence_audit_accepts_complete_physical_validation(self):
        from research_v2.learning_report import audit_validation
        with tempfile.TemporaryDirectory() as tmp:
            data=self.validation_fixture(tmp)
            (Path(tmp)/'episodes.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in data))
            result=audit_validation(Path(tmp))
            self.assertEqual(result['episodes'],20)
            self.assertAlmostEqual(result['D_macro'],0.1)

    def test_budget_rollout_alignment(self):
        for budget in (0, 500, 5000, -512):
            with self.assertRaises(ContractError):
                pilot_plan(self.config, 100, 0, budget, [0.2] * 5)
        self.assertEqual(pilot_plan(self.config, 100, 0, 10240, [0.2] * 5)['rollouts'], 20)

    def test_namespace_and_weights_guards(self):
        for outer, repeat, weights in ((0, 0, [0.2]*5), (100, 2, [0.2]*5),
                                      (100, 0, [0, 0.25, 0.25, 0.25, 0.25])):
            with self.assertRaises(ContractError):
                pilot_plan(self.config, outer, repeat, 512, weights)

    def test_seed_and_offset(self):
        for outer in (100, 101, 102):
            for repeat in (0, 1):
                plan = pilot_plan(self.config, outer, repeat, 512, [0.2]*5)
                self.assertEqual(plan['model_seed'], 200000 + 2*outer + repeat)
                self.assertEqual(plan['offset'], (outer + repeat) % 4)

    def test_round_robin_trace_counters(self):
        stream = PilotStream(self.config, 101, 0)
        names = []
        for i in range(8):
            trace = stream(None, i)
            names.append(trace['seed_namespace']['workload'])
            self.assertEqual(trace['seed_namespace']['trace_id'], i//4)
            self.assertEqual(trace['seed_namespace']['split'], 'pilot_train')
        self.assertEqual(names, ['moderate', 'heavy', 'dynamic', 'light']*2)
        with self.assertRaises(ContractError):
            stream(None, 0)

    def test_stream_does_not_touch_policy_rng(self):
        before = rng_state()
        a = PilotStream(self.config, 100, 0)(7, 0)
        self.assertTrue(equal_nested(before, rng_state()))
        random.random()
        np.random.random(10)
        torch.rand(10)
        b = PilotStream(self.config, 100, 0)(999, 0)
        self.assertEqual(a, b)

    def test_config_policy_parameters(self):
        kwargs = ppo_kwargs(self.config)
        self.assertEqual(kwargs['gamma'], 1.0)
        self.assertEqual(kwargs['n_steps'], 512)
        self.assertEqual(kwargs['policy_kwargs']['net_arch'], {'pi': [128,128], 'vf': [128,128]})
        self.assertEqual(kwargs['learning_rate'], 0.0003)
        self.assertEqual(kwargs['device'], 'cpu')

    def test_policy_creation_and_save_without_training(self):
        # Construct/save only: this test never invokes PPO.learn or PPO.train.
        model = AuditedPPO('MlpPolicy', FakeEnv(), seed=200200, **ppo_kwargs(self.config))
        model.audit_env = object()
        model.audit_directory = Path('/unused')
        self.assertIn('audit_env', model._excluded_save_params())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'model.zip'
            model.save(path)
            loaded = AuditedPPO.load(path, device='cpu')
            self.assertTrue(equal_nested(model.policy.state_dict(), loaded.policy.state_dict()))
            self.assertTrue(equal_nested(model.policy.optimizer.state_dict(), loaded.policy.optimizer.state_dict()))
            self.assertEqual(loaded.num_timesteps, 0)
            self.assertFalse(hasattr(loaded, 'audit_env'))

    def test_delayed_reward_audit_and_budget_partial(self):
        class Stream:
            current = {'tasks': 2, 'namespace': {'workload': 'light'}}
            def state(self):
                return {'current': self.current}
        with tempfile.TemporaryDirectory() as tmp:
            env = EpisodeAudit(FakeEnv(), Stream(), tmp)
            env.reset()
            env.step(0)
            self.assertTrue(env.state()['active_episode']['pending_outcomes_not_evaluated'])
            self.assertFalse((Path(tmp)/'episodes.jsonl').exists())
            env.step(6)
            row = json.loads((Path(tmp)/'episodes.jsonl').read_text())
            self.assertAlmostEqual(row['reward'], -10)
            self.assertEqual(row['action_counts'], [1,0,0,0,0,0,1])
            self.assertFalse(env.state()['active_episode']['pending_outcomes_not_evaluated'])

    def test_reward_mismatch_rejected(self):
        class Stream:
            current = {'tasks': 2, 'namespace': {'workload': 'light'}}
            def state(self):
                return {'current': self.current}
        with tempfile.TemporaryDirectory() as tmp:
            env = EpisodeAudit(FakeEnv(), Stream(), tmp)
            env.reset()
            env.step(0)
            env.total_reward += 1
            with self.assertRaises(ContractError):
                env.step(0)

    def test_comparison_detects_optimizer_or_rng_difference(self):
        self.assertFalse(equal_nested({'step': torch.tensor(1)}, {'step': torch.tensor(2)}))
        self.assertFalse(equal_nested((np.array([1,2]),), (np.array([1,3]),)))
        self.assertTrue(equal_nested(rng_state(), rng_state()))


if __name__ == '__main__':
    unittest.main()
