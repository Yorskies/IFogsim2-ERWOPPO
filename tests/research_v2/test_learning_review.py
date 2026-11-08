"""Unit/scale checks for the read-only observation review; no training or Java."""
import unittest
import numpy as np
from research_v2.config import ROOT, load_config, read_json
from research_v2.learning_review import transform


class ReviewTransformTests(unittest.TestCase):
    def setUp(self):
        self.config=load_config()
        self.names=read_json(ROOT/'configs/research_v2/wire_contract.json')['observation_features']
        self.raw={name:0.0 for name in self.names}

    def vector(self):
        return dict(zip(self.names,transform(self.raw,self.config)))

    def test_deadline_sentinel_and_negative_value_are_distinct(self):
        self.raw['node.F1.minimum_remaining_deadline_s']=None
        self.raw['node.F2.minimum_remaining_deadline_s']=-3.0
        v=self.vector()
        self.assertEqual(v['node.F1.minimum_remaining_deadline_s'],1.0)
        self.assertEqual(v['node.F2.minimum_remaining_deadline_s'],-0.5)

    def test_time_squash_preserves_scale_and_does_not_clip(self):
        self.raw['route.cloud.estimated_input_delay_s']=4.5
        self.raw['node.F1.queued_mi_over_mips_s']=18.0
        v=self.vector()
        self.assertAlmostEqual(v['route.cloud.estimated_input_delay_s'],1/3,places=6)
        self.assertAlmostEqual(v['node.F1.queued_mi_over_mips_s'],2/3,places=6)

    def test_units_one_hot_and_wire_order(self):
        self.raw['task.input_bytes']=2.2*2**20
        self.raw['node.cloud.mips_per_pe']=5600
        self.raw['task.class.heavy']=1
        vector=transform(self.raw,self.config)
        self.assertEqual(vector.shape,(108,))
        self.assertEqual(vector.dtype,np.float32)
        v=dict(zip(self.names,vector))
        self.assertEqual(v['task.input_bytes'],1)
        self.assertEqual(v['node.cloud.mips_per_pe'],1)
        self.assertEqual(v['task.class.heavy'],1)


if __name__=='__main__':unittest.main()
