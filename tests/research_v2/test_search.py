import unittest
import numpy as np
from research_v2.config import load_config,ContractError
from research_v2.search import (project,feasible,pilot_weights,fidelity_gate,repeated_objectives,optimize,select)


class SearchTests(unittest.TestCase):
    def test_projection_known_solution(self):
        np.testing.assert_allclose(project([2,0,0,0,0]),[.92,.02,.02,.02,.02])
        np.testing.assert_allclose(project([0,0,0,0,0]),[.2]*5)
        np.testing.assert_allclose(project([.3,.15,.25,.1,.2]),[.3,.15,.25,.1,.2])
        with self.assertRaises(ContractError):project([float('nan')]*5)

    def test_pilot_weights_frozen_and_feasible(self):
        a=pilot_weights(load_config());self.assertEqual(len(a),8)
        self.assertEqual(a,pilot_weights(load_config()))
        for w in a:feasible(w['weights'])
        self.assertEqual(a[2]['weights'],[.92,.02,.02,.02,.02])

    def test_aggregate_before_rms_not_mean_D(self):
        r=repeated_objectives([[1,0,0,0,0],[0,0,0,0,0]])
        self.assertAlmostEqual(r['D'],np.sqrt(.05));self.assertEqual(r['costs'],[.5,0,0,0,0])

    def test_fidelity_ties_negative_and_undefined(self):
        a=np.array([[1,1,2,3,4,5,6,7]]*3)
        self.assertTrue(fidelity_gate(a,a)['pass'])
        self.assertFalse(fidelity_gate(a,-a)['pass'])
        self.assertTrue(fidelity_gate(np.ones((3,8)),a)['undefined'])
        with self.assertRaises(ContractError):fidelity_gate(a[:2],a[:2])

    def test_fidelity_threshold_and_no_negative_outer(self):
        ordered=np.array([[1,2,3,4,5,6,7,8]]*3)
        above=np.array([[1,2,7,4,5,6,3,8]]*3)
        below=np.array([[2,1,7,4,5,6,3,8]]*3)
        self.assertTrue(fidelity_gate(ordered,above)['pass'])
        self.assertFalse(fidelity_gate(ordered,below)['pass'])
        above[0]=ordered[0,::-1]
        self.assertGreater(fidelity_gate(ordered,above)['median_spearman'],.60)
        self.assertFalse(fidelity_gate(ordered,above)['pass'])

    def test_hypervolume_reference_is_not_adapted(self):
        with self.assertRaises(ContractError):
            optimize('random',100,lambda w,slot:[1.2]*5)

    def test_search_exact_budget_common_initial_and_reproducibility(self):
        def f(w,slot):return np.asarray(w)*.5+.1
        a=optimize('nsga2',100,f);b=optimize('random',100,f)
        self.assertEqual(a['candidate_slots'],80);self.assertEqual(b['candidate_slots'],80)
        self.assertEqual([r['weights'] for r in a['records'][:20]],[r['weights'] for r in b['records'][:20]])
        self.assertEqual(a,optimize('nsga2',100,f))
        self.assertEqual(len(a['archive']),80)
        for r in a['records']:feasible(r['weights'])

    def test_policy_global_rng_resets_do_not_change_search_proposals(self):
        import random
        numpy_state=np.random.get_state();python_state=random.getstate()
        try:
            def clean(w,slot):return np.array(w)*.5+.1
            def policy_like(w,slot):
                np.random.seed(slot);random.seed(slot);np.random.random(31)
                return clean(w,slot)
            self.assertEqual(optimize('nsga2',100,clean),optimize('nsga2',100,policy_like))
            self.assertEqual(optimize('random',100,clean),optimize('random',100,policy_like))
        finally:
            np.random.set_state(numpy_state);random.setstate(python_state)

    def test_duplicates_are_charged_and_tie_uses_failure(self):
        calls=[]
        def f(w,slot):calls.append(slot);return [.2]*5
        config=load_config();config['search']['manual_weights']=list(config['search']['equal_weights'])
        r=optimize('nsga2',101,f,config);self.assertEqual(calls,list(range(80)))
        self.assertEqual(r['records'][0]['weights'],r['records'][1]['weights'])
        self.assertAlmostEqual(r['generations'][-1]['hypervolume'],.9**5)
        candidates=[{'weights':[.2]*5,'costs':[.3,.2,.2,.2,.1],'D':.22},
                    {'weights':[.3,.15,.25,.1,.2],'costs':[.1,.2,.2,.2,.3],'D':.22}]
        self.assertEqual(select(candidates),candidates[0])


if __name__=='__main__':unittest.main()
