"""P08 bounded-simplex search. Pure optimizers use an injected cost evaluator; no training on import."""
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.core.repair import Repair
from pymoo.indicators.hv import HV
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
from scipy.stats import spearmanr

from .config import load_config, require

FLOOR=.02


def feasible(weights):
    a=np.asarray(weights,dtype=float)
    require(a.shape==(5,) and np.isfinite(a).all() and a.min()>=FLOOR-1e-12 and abs(a.sum()-1)<1e-10,'Infeasible weight vector')
    return a


def project(weights):
    """Euclidean projection onto sum=1 and each coordinate>=.02 (not clip-and-renormalize)."""
    v=np.asarray(weights,dtype=float)
    require(v.shape==(5,) and np.isfinite(v).all(),'Invalid projection input')
    if v.min()>=FLOOR and abs(v.sum()-1)<1e-12:
        return v.copy()
    x=v-FLOOR;u=np.sort(x)[::-1];css=np.cumsum(u)-.9
    rho=np.nonzero(u-css/np.arange(1,6)>0)[0][-1]
    p=np.maximum(x-css[rho]/(rho+1),0)+FLOOR
    p[np.argmax(p)]+=1-p.sum()
    return feasible(p)


def sample_simplex(rng,count):
    return FLOOR+.9*rng.dirichlet(np.ones(5),size=count)


def initial_population(config,outer):
    rng=np.random.Generator(np.random.PCG64(config['search']['initial_rng_base']+outer))
    return np.vstack([config['search']['equal_weights'],config['search']['manual_weights'],sample_simplex(rng,18)])


def pilot_weights(config):
    result=[('equal',config['search']['equal_weights']),('manual',config['search']['manual_weights'])]
    for j in range(5):
        w=np.full(5,FLOOR);w[j]=.92;result.append((f'vertex{j}',w.tolist()))
    rng=np.random.Generator(np.random.PCG64(config['seeds']['pilot_simplex']))
    result.append(('simplex',sample_simplex(rng,1)[0].tolist()))
    return [{'id':name,'weights':feasible(w).tolist()} for name,w in result]


def rms(costs):
    a=np.asarray(costs,dtype=float)
    require(a.shape==(5,) and np.isfinite(a).all() and a.min()>=-1e-10,'Invalid objective vector')
    return float(np.sqrt(np.mean(a*a)))


def repeated_objectives(vectors):
    a=np.asarray(vectors,dtype=float)
    require(a.shape==(2,5) and np.isfinite(a).all(),'Exactly two model cost vectors required')
    costs=a.mean(axis=0)
    return {'costs':costs.tolist(),'D':rms(costs)}


def fidelity_gate(short,reference):
    """Rows are three outer runs x eight candidates; Spearman uses average ranks for ties."""
    x=np.asarray(short,dtype=float);y=np.asarray(reference,dtype=float)
    require(x.shape==y.shape==(3,8) and np.isfinite(x).all() and np.isfinite(y).all(),'Incomplete fidelity pairs')
    correlations=[]
    for a,b in zip(x,y):
        if np.ptp(a)==0 or np.ptp(b)==0:correlations.append(None)
        else:correlations.append(float(spearmanr(a,b).statistic))
    defined=all(c is not None and np.isfinite(c) for c in correlations)
    median=float(np.median(correlations)) if defined else None
    return {'correlations':correlations,'median_spearman':median,
            'pass':bool(defined and median>=.60 and min(correlations)>=0),
            'undefined':not defined}


class SimplexRepair(Repair):
    def _do(self,problem,X,**kwargs):
        return np.array([project(x) for x in X])


def archive(records):
    f=np.asarray([r['costs'] for r in records])
    indices=NonDominatedSorting().do(f,only_non_dominated_front=True)
    return [records[int(i)] for i in indices]


def select(records):
    front=archive(records);minimum=min(r['D'] for r in front)
    tied=[r for r in front if r['D']<=minimum+1e-9]
    return min(tied,key=lambda r:(r['costs'][4],r['costs'][2],tuple(r['weights'])))


def optimize(method,outer,evaluate,config=None):
    """80 charged slots even for duplicates. evaluate(weights,slot)->five macro costs."""
    config=config or load_config();require(method in ('nsga2','random'),'Unknown search method')
    common=initial_population(config,outer);records=[];generations=[]
    def evaluate_batch(batch):
        costs=[]
        for w in batch:
            w=feasible(w);slot=len(records);f=np.asarray(evaluate(w.tolist(),slot),dtype=float)
            score=rms(f);require(np.all(f<=1.1),'Objective outside frozen hypervolume reference')
            records.append({'slot':slot,'weights':w.tolist(),'costs':f.tolist(),'D':score});costs.append(f)
        front=archive(records)
        generations.append({'slots_completed':len(records),'hypervolume':float(HV(ref_point=np.full(5,1.1))(np.array([r['costs'] for r in front])))})
        return np.array(costs)
    if method=='random':
        rng=np.random.Generator(np.random.PCG64(config['search']['random_rng_base']+outer))
        evaluate_batch(common)
        for _ in range(3):evaluate_batch(sample_simplex(rng,20))
    else:
        algorithm=NSGA2(pop_size=20,sampling=common,eliminate_duplicates=False,repair=SimplexRepair(),
                        crossover=SBX(prob=.9,eta=15),mutation=PM(prob=1.,prob_var=.2,eta=20))
        algorithm.setup(Problem(n_var=5,n_obj=5,xl=FLOOR,xu=.92),termination=('n_gen',4),
                        seed=config['search']['nsga_rng_base']+outer,verbose=False)
        while algorithm.has_next():
            pop=algorithm.ask();pop.set('F',evaluate_batch(pop.get('X')));algorithm.tell(infills=pop)
    require(len(records)==80,'Search budget must be exactly 80 slots')
    return {'method':method,'outer':outer,'records':records,'archive':archive(records),
            'selected':select(records),'generations':generations,'candidate_slots':len(records)}
