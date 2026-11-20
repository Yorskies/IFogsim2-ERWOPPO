"""P14 search wrappers: NSGA-II, NSGA-III, MOEA/D, SPEA2 and random search over the 5-weight simplex, ask/tell, equal slots.

All algorithms share: population 15 (= 15 Das-Dennis reference directions for 5 objectives, partitions 2), the same initial
population per outer run (equal weights + 14 Dirichlet points), the simplex repair and variation operators of P11
(SBX p 0.9 eta 15, PM eta 20 per-variable 0.2), and a hard budget of exactly `slots` evaluated candidates. MOEA/D is the
standard per-offspring variant (pymoo gives 15 initial points, then one offspring per ask). Deterministic for a given seed.
The evaluator is external: next_batch() returns weight vectors, tell() receives their five macro costs.
"""
import numpy as np
from pymoo.algorithms.moo.moead import MOEAD
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.algorithms.moo.spea2 import SPEA2, SPEA2Survival, spea_binary_tournament
from pymoo.core.population import Population
from pymoo.core.problem import Problem
from pymoo.decomposition.pbi import PBI
from pymoo.indicators.hv import HV
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.selection.tournament import TournamentSelection
from pymoo.util.ref_dirs import get_reference_directions

from .config import require
from .search import FLOOR, SimplexRepair, archive, feasible, rms, sample_simplex, select

ALGORITHMS = ('nsga2', 'nsga3', 'moead', 'spea2', 'random')
POPULATION = 15
SLOTS = 90
INIT_BASE, ALGO_BASE, RANDOM_BASE = 640_000, 650_000, 660_000
HV_REFERENCE = 1.1


def initial_population(outer):
    rng = np.random.Generator(np.random.PCG64(INIT_BASE + outer))
    return np.vstack([np.full(5, 0.2), sample_simplex(rng, POPULATION - 1)])


def make_algorithm(name, init):
    common = dict(sampling=init, repair=SimplexRepair(), crossover=SBX(prob=.9, eta=15), mutation=PM(prob=1., prob_var=.2, eta=20))
    ref = get_reference_directions('das-dennis', 5, n_partitions=2)
    require(len(ref) == POPULATION, 'reference directions must equal the population size')
    if name == 'nsga2':
        return NSGA2(pop_size=POPULATION, eliminate_duplicates=False, **common)
    if name == 'nsga3':
        return NSGA3(ref_dirs=ref, pop_size=POPULATION, eliminate_duplicates=False, **common)
    if name == 'spea2':
        # pymoo builds SPEA2's survival (with normalization state) and selection once as default arguments, so they are shared
        # by every SPEA2 instance in a process and leak state between searches; fresh objects make each search independent.
        return SPEA2(pop_size=POPULATION, eliminate_duplicates=False, survival=SPEA2Survival(normalize=True),
                     selection=TournamentSelection(spea_binary_tournament), **common)
    if name == 'moead':
        return MOEAD(ref_dirs=ref, n_neighbors=5, prob_neighbor_mating=0.9, decomposition=PBI(), **common)
    raise ValueError(name)


class Search:
    def __init__(self, name, outer, slots=SLOTS):
        require(name in ALGORITHMS, f'unknown algorithm {name}')
        self.name, self.outer, self.slots = name, outer, slots
        self.init = initial_population(outer)
        self.records, self.pending, self.history = [], None, []
        if name == 'random':
            self.rng = np.random.Generator(np.random.PCG64(RANDOM_BASE + outer))
            self.algorithm = None
        else:
            self.algorithm = make_algorithm(name, self.init)
            self.algorithm.setup(Problem(n_var=5, n_obj=5, xl=FLOOR, xu=.92), termination=('n_gen', 10 ** 6),
                                 seed=ALGO_BASE + outer, verbose=False)

    @property
    def done(self):
        return len(self.records) >= self.slots and self.pending is None

    def next_batch(self):
        """Weight vectors to evaluate next (never more than the remaining slots); None when the budget is spent."""
        require(self.pending is None, 'previous batch not told yet')
        remaining = self.slots - len(self.records)
        if remaining <= 0:
            return None
        if self.algorithm is None:
            X = self.init if not self.records else sample_simplex(self.rng, POPULATION)
            self.pending = ('random', X[:remaining])
        else:
            # Some pymoo paths (SPEA2 tournament ties) draw from the global numpy RNG; pin it so a replay is identical.
            np.random.seed((ALGO_BASE + self.outer) * 1000 + len(self.records))
            o = self.algorithm.ask()
            X = np.atleast_2d(o.get('X') if isinstance(o, Population) else o.X)
            require(len(X) <= remaining, f'{self.name} asked {len(X)} candidates with {remaining} slots left')
            self.pending = (o, X)
        return [feasible(x).tolist() for x in self.pending[1]]

    def tell(self, costs):
        o, X = self.pending
        F = np.asarray(costs, dtype=float)
        require(F.shape == (len(X), 5) and np.isfinite(F).all(), 'costs do not match the asked batch')
        for x, f in zip(X, F):
            self.records.append({'slot': len(self.records), 'weights': feasible(x).tolist(), 'costs': f.tolist(), 'D': rms(f)})
        if not isinstance(o, str):
            if isinstance(o, Population):
                o.set('F', F)
            else:
                o.set('F', F[0])
            self.algorithm.tell(infills=o)
        self.pending = None
        front = archive(self.records)
        self.history.append({'slots': len(self.records), 'min_D': min(r['D'] for r in self.records),
                             'hypervolume': hypervolume([r['costs'] for r in front])})

    def summary(self):
        front = archive(self.records)
        return {'algorithm': self.name, 'outer': self.outer, 'slots': len(self.records), 'records': self.records,
                'front': front, 'selected_plain': select(self.records), 'history': self.history,
                'hypervolume': hypervolume([r['costs'] for r in front])}


def hypervolume(costs):
    return float(HV(ref_point=np.full(5, HV_REFERENCE))(np.asarray(costs, dtype=float)))
