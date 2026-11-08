from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from research_v2.config import load_config,ContractError,read_json
from research_v2.learning import candidate_plan,PilotStream
from research_v2.fidelity import prepare


class FidelityTests(unittest.TestCase):
    def test_candidate_namespaces_and_seeds(self):
        c=load_config();p=candidate_plan(c,3,1,5120,[.2]*5)
        self.assertEqual(p['model_seed'],200007);self.assertEqual(p['split'],'train_candidate')
        self.assertEqual(p['evaluation_split'],'validation')
        t=PilotStream(c,3,1,split='train_candidate')(None,0)
        self.assertEqual(t['seed_namespace']['split'],'train_candidate')
        self.assertEqual(t['seed_namespace']['workload'],'light')
        with self.assertRaises(ContractError):candidate_plan(c,100,0,5120,[.2]*5)
        with self.assertRaises(ContractError):PilotStream(c,3,0,split='train_final')

    def test_frozen_protocol_has_48_unique_paired_jobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'pilot'
            with patch('research_v2.fidelity.socket.socket'):
                prepare(root)
            p=read_json(root/'protocol.json')
            self.assertEqual(len(p['jobs']),48);self.assertEqual(len({j['id'] for j in p['jobs']}),48)
            self.assertEqual(len(p['weights']),8)
            for seed in (100,101,102):
                for w in p['weights']:
                    jobs=[j for j in p['jobs'] if j['outer']==seed and j['weight_id']==w['id']]
                    self.assertEqual([j['repeat'] for j in jobs],[0,1])
                    self.assertTrue(all(j['weights']==w['weights'] for j in jobs))
            self.assertEqual(p['budget_train_maximum'],48*(51200+5120+10240+20480))
            self.assertFalse(p['test_accessed'])


if __name__=='__main__':unittest.main()
