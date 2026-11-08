"""Hand-calculated GAE, passive gradients, and single-factor experiment guards."""
import copy
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch

from research_v2.config import ContractError, load_config, sha256
from research_v2.learning import effective_learner, write_json, rng_state, equal_nested
from research_v2.learning_instrumentation import recompute_gae, gradient_clip_recorder


class InstrumentationTests(unittest.TestCase):
    def test_terminal_drain_is_included_without_bootstrapping_next_episode(self):
        rewards=np.array([[1.],[2.]],dtype=np.float32);values=np.array([[.5],[.25]],dtype=np.float32)
        starts=np.array([[1.],[0.]],dtype=np.float32)
        for lam,expected in ((1.,3.),(.95,2.9125)):
            a,r=recompute_gae(rewards,values,starts,np.array([99.]),np.array([True]),1.,lam)
            self.assertAlmostEqual(float(r[0,0]),expected,places=5)
            self.assertAlmostEqual(float(r[1,0]),2.,places=5)

    def test_episode_boundary_stops_credit_and_partial_rollout_bootstraps(self):
        a,r=recompute_gae(np.array([[1.],[2.]],dtype=np.float32),np.array([[.5],[.25]],dtype=np.float32),
                         np.array([[1.],[1.]],dtype=np.float32),np.array([10.]),np.array([False]),1.,1.)
        np.testing.assert_allclose(r,[[1.],[12.]])

    def test_gradient_recorder_is_passive(self):
        first=torch.nn.Parameter(torch.zeros(2));second=torch.nn.Parameter(torch.zeros(2))
        first.grad=torch.tensor([3.,4.]);second.grad=first.grad.clone();records=[]
        before=rng_state()
        original=torch.nn.utils.clip_grad_norm_
        expected=original([first],.5)
        actual=gradient_clip_recorder(original,records)(iter([second]),.5)
        self.assertEqual(float(expected),float(actual))
        self.assertTrue(torch.equal(first.grad,second.grad))
        self.assertTrue(equal_nested(before,rng_state()))
        self.assertEqual(records[0]['pre_clip_norm'],5.)
        self.assertLessEqual(records[0]['post_clip_norm'],.5)
        self.assertTrue(records[0]['was_clipped'])

    def spec(self,config,lam):
        effective=copy.deepcopy(config);effective['ppo']['gae_lambda']=lam
        return {'protocol':'P07-lambda-ablation-1','simulation_config_sha256':sha256(config),
                'ppo':effective['ppo'],'effective_config_sha256':sha256(effective)}

    def test_learner_differs_only_in_lambda_while_base_is_immutable(self):
        config=load_config();original=copy.deepcopy(config)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'spec.json';write_json(path,self.spec(config,1.))
            effective,spec=effective_learner(config,path)
            self.assertEqual(effective['ppo']['gae_lambda'],1.)
            self.assertEqual(config,original)
            effective['ppo']['gae_lambda']=.95
            self.assertEqual(effective,config)

    def test_learner_rejects_other_changes_or_wrong_hash(self):
        config=load_config()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'spec.json'
            for kind in ('other','hash'):
                spec=self.spec(config,1.)
                if kind=='other':
                    spec['ppo']['ent_coef']=.1
                    clone=copy.deepcopy(config);clone['ppo']=spec['ppo'];spec['effective_config_sha256']=sha256(clone)
                else:spec['simulation_config_sha256']='0'*64
                write_json(path,spec)
                with self.assertRaises(ContractError):effective_learner(config,path)


if __name__=='__main__':unittest.main()
