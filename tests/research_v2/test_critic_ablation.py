import copy
from pathlib import Path
import tempfile
import unittest
from research_v2.config import load_config,sha256,ContractError
from research_v2.learning import write_json,effective_learner


class CriticAblationTests(unittest.TestCase):
    def spec(self,config,**changes):
        clone=copy.deepcopy(config);clone['ppo'].update(changes)
        return {'protocol':'P07-critic-scale-ablation-1','simulation_config_sha256':sha256(config),
                'ppo':clone['ppo'],'effective_config_sha256':sha256(clone)}

    def test_only_critic_coefficient_changes(self):
        config=load_config()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'spec.json';write_json(p,self.spec(config,vf_coef=.05))
            actual,_=effective_learner(config,p)
            self.assertEqual(actual['ppo']['vf_coef'],.05)
            self.assertEqual(actual['ppo']['gae_lambda'],.95)
            self.assertEqual(actual['ppo']['max_grad_norm'],.5)
            actual['ppo']['vf_coef']=.5
            self.assertEqual(actual,config)

    def test_cannot_change_lambda_and_critic_together(self):
        config=load_config()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'spec.json';write_json(p,self.spec(config,vf_coef=.05,gae_lambda=1.))
            with self.assertRaises(ContractError):effective_learner(config,p)

    def test_cannot_change_clipping_rule(self):
        config=load_config()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'spec.json';write_json(p,self.spec(config,vf_coef=.05,max_grad_norm=5.))
            with self.assertRaises(ContractError):effective_learner(config,p)

    def test_unplanned_coefficient_rejected(self):
        config=load_config()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'spec.json';write_json(p,self.spec(config,vf_coef=.005))
            with self.assertRaises(ContractError):effective_learner(config,p)


if __name__=='__main__':unittest.main()
