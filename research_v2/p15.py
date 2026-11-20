"""P15: full MOEA benchmark for PPO reward weights with a noise-reduced evaluator — one command, resumable.

    PYTHONPATH=. venv/bin/python -m research_v2.p15 run        # preflight, lock, 100 searches
    PYTHONPATH=. venv/bin/python -m research_v2.p15 status

Plan: docs/research_v2/P15_P16_IMPLEMENTATION_PLAN.md (decisions in section 9). Searches: NSGA-II, NSGA-III, MOEA/D, SPEA2,
random search (research_v2.p14_search) x outer 0-19, population 15, 90 slots. Evaluator: 4 PPO models per candidate (F decisions,
learner v0.3, train_candidate streams), scored on 20 dev_validation traces; after every 15 evaluated candidates the 3 best
candidates that are not yet elite receive 8 more models (12 in total). Selection: lowest 12-model D among elites.
The P15 lock (written before any search job) also registers the whole P16 design and seals p16_test.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import time

import numpy as np

from .config import ROOT, load_config, read_json, require, sha256
from . import p15_jobs as J

SMOKE = os.environ.get('P15_SMOKE') == '1'
OUT = Path(os.environ.get('P15_OUT', ROOT / 'results/research_v2/p15'))
require(not SMOKE or 'P15_OUT' in os.environ, 'P15_SMOKE requires P15_OUT outside the real output directory')
LOCK = OUT / 'protocol_lock/p15_lock.json'
STATE, LOG = OUT / 'pipeline/state.json', OUT / 'pipeline/pipeline.log'
V04_LOCK = ROOT / 'results/research_v2/v0.4/protocol_lock/protocol_lock.json'
PLAN = ROOT / 'docs/research_v2/P15_P16_IMPLEMENTATION_PLAN.md'
STOP = {'requested': False}

F = 1024 if SMOKE else 102_400
OUTERS = [0, 1] if SMOKE else list(range(20))
SLOTS = 30 if SMOKE else 90
BASE_MODELS, ELITE_EXTRA = (2, 2) if SMOKE else (4, 8)
ELITE_PER_GENERATION, GENERATION = 3, 15
SEARCH_IDS = (40000, 40000) if SMOKE else (40000, 40004)
CANDIDATE_LOG_ROWS, FINAL_LOG_ROWS = 1024, 10240
P15_SEED_BASE, P16_SEED_BASE, FINAL_SEEDS = 700_000, 800_000, (2 if SMOKE else 4)
DELTA = 0.02
EQUAL = [0.2] * 5
LEAN_ZD = [0.1, 0.1, 0.6, 0.1, 0.1]
SEARCH_METHODS = ('nsga2', 'nsga3', 'moead', 'spea2', 'random')
MOEAS = ('nsga2', 'nsga3', 'moead', 'spea2')
P16_TEST_IDS = (50000, 50001) if SMOKE else (50000, 50099)
SOURCES = ['research_v2/p15.py', 'research_v2/p15_jobs.py', 'research_v2/p16.py', 'research_v2/p16_traces.py',
           'research_v2/p14_search.py', 'research_v2/p14_traces.py', 'research_v2/p13_traces.py', 'research_v2/search.py',
           'research_v2/learning.py', 'research_v2/learner.py', 'research_v2/learning_instrumentation.py', 'research_v2/study_final.py',
           'research_v2/gym_env.py', 'research_v2/rpc_client.py', 'research_v2/baselines.py', 'research_v2/config.py',
           'research_v2/contracts.py', 'research_v2/traces.py', 'research_v2/trace_access.py', 'research_v2/schema_definitions.py',
           'research_v2/analysis/stats.py', 'research_v2/analysis/loader.py', 'configs/research_v2/default.json',
           'configs/research_v2/learner_v0.3.json', 'configs/research_v2/wire_contract.json', 'run_p15.sh', 'run_p16.sh',
           'docs/research_v2/P15_P16_IMPLEMENTATION_PLAN.md', 'ifogsim/build/research_v2/build_receipt.json']


# ------------------------------------------------------------------------------------------------ plumbing

def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def log(message):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f'[{now()}] {message}'
    print(line, flush=True)
    with LOG.open('a') as sink:
        sink.write(line + '\n')


def state():
    return read_json(STATE) if STATE.exists() else {'stages': {}}


def mark(stage, **info):
    s = state()
    s['stages'][stage] = {'done_utc': now(), **info}
    J.dump(STATE, s)


def done(stage):
    return stage in state()['stages']


def stopped():
    if STOP['requested']:
        log('stop requested: exiting; re-run the same command to resume')
        raise SystemExit(75)


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sources():
    return {name: file_sha256(ROOT / name) for name in SOURCES}


# ------------------------------------------------------------------------------------------------ lock

def seal(lock):
    body = {k: v for k, v in lock.items() if k != 'lock_sha256'}
    return {**body, 'lock_sha256': sha256(body)}


def verify_lock(path=LOCK):
    lock = read_json(path)
    require(seal(lock)['lock_sha256'] == lock['lock_sha256'], 'P15 lock content does not match its hash')
    require(read_json(V04_LOCK)['lock_sha256'] == lock['v04_lock_sha256'], 'P15 lock refers to another v0.4 lock')
    current = sources()
    drift = sorted(k for k, v in lock['sources'].items() if current.get(k) != v)
    require(not drift, f'P15/P16 sources changed after the lock: {drift[:5]}')
    return lock


def p11_equal_B():
    """{outer: (checkpoint, model sha)} of the frozen P11 PPO-Equal B models, from the completion pointers."""
    out = {}
    budget = None
    for shard in sorted(p for p in (ROOT / 'results/research_v2/v0.4/p11').glob('shard_*') if p.is_dir()):
        plan = read_json(shard / 'protocol.json')
        budget = plan['budget']['B']
        for outer in plan['outers']:
            pointer = read_json(shard / 'jobs' / f'r{outer:02d}_equal' / 'complete.json')
            checkpoint = shard / pointer['attempt'] / 'data/training' / f'checkpoint_{budget:08d}'
            out[outer] = (checkpoint.relative_to(ROOT).as_posix(), read_json(checkpoint / 'state.json')['model_sha256'])
    return out, budget


def stage_lock():
    from . import p16_traces
    from .p14_search import POPULATION
    config = load_config()
    log('lock: preparing the sealed p16_test manifest (inputs only, no outcome)')
    manifest = p16_traces.manifest(config, P16_TEST_IDS)
    J.dump(OUT / 'protocol_lock/p16_test_manifest.json', manifest)
    equal_b, budget_b = p11_equal_B()
    lock = seal({
        'protocol': 'research-v2-p15-p16-1', 'created_utc': now(), 'smoke': SMOKE, 'plan': PLAN.relative_to(ROOT).as_posix(),
        'v04_lock_sha256': read_json(V04_LOCK)['lock_sha256'], 'config_sha256': sha256(config), 'sources': sources(),
        'deviation': 'Full benchmark run although P14 gates G1/G2 failed: researcher decision of 20 November 2026, recorded before '
                     'any P15/P16 data (plan section 0); results are analysed whatever they show.',
        'search': {'methods': list(SEARCH_METHODS), 'outers': OUTERS, 'population': POPULATION, 'slots': SLOTS, 'budget_F': F,
                   'learner': '0.3', 'stream': 'train_candidate (repeat = model index mod 2)',
                   'seeds': f'{P15_SEED_BASE} + 100*outer + j, shared by all candidates and methods of an outer',
                   'evaluator': {'base_models': BASE_MODELS, 'elite_extra_models': ELITE_EXTRA, 'elites_per_generation':
                                 ELITE_PER_GENERATION, 'generation': GENERATION, 'traces': {'split': 'dev_validation', 'ids': list(SEARCH_IDS)}},
                   'selection': 'lowest 12-model D among elites; ties to the earlier slot', 'decision_log_rows': CANDIDATE_LOG_ROWS},
        'final': {'arms': [*SEARCH_METHODS, 'equal_F', 'lean_zD', 'equal_B_p11'], 'lean_zD': LEAN_ZD, 'budget_F': F,
                  'seeds': f'{P16_SEED_BASE} + 10*outer + k, k < {FINAL_SEEDS}, shared by all arms of an outer',
                  'stream': 'train_final outer r', 'models_per_arm_and_outer': FINAL_SEEDS, 'decision_log_rows': FINAL_LOG_ROWS,
                  'equal_B_p11': {'budget': budget_b, 'checkpoints': {str(o): v for o, v in sorted(equal_b.items()) if o in OUTERS}},
                  'unit': 'outer run; per-trace costs averaged over the arm\'s models of that outer'},
        'p16_test': {k: manifest[k] for k in ('split', 'trace_ids', 'traces', 'tasks_total', 'rows_sha256')},
        'hypotheses': {
            'orientation': 'difference = D(comparator) - D(treatment); positive = treatment better',
            'primary': {'H1': [['equal_F', m] for m in MOEAS], 'H2': [['random', m] for m in MOEAS],
                        'test': 'exact sign-flip over outer runs; Holm within H1 and within H2; alpha 0.05'},
            'secondary': {'H3': 'Friedman over the 5 search methods (blocks = outer runs); pairwise Wilcoxon + Holm',
                          'H4': [['equal_B_p11', m] for m in SEARCH_METHODS], 'H5': [['equal_F', 'lean_zD']],
                          'E1': {'pairs': 'H1', 'margin_D': DELTA, 'rule': '90% crossed-bootstrap CI inside (-delta, delta)'}},
            'descriptive': ['winner\'s curse (search score vs final test D)', 'P11 selection rule vs 12-model rule',
                            'anytime minimum score, hypervolume and IGD+', 'compute', 'physical metrics', 'cost PCA'],
            'bootstrap': {'draws': config['statistics']['bootstrap_draws'], 'seed': config['seeds']['bootstrap']}},
    })
    J.dump(LOCK, lock)
    verify_lock()
    mark('lock', lock_sha256=lock['lock_sha256'], p16_test_traces=manifest['traces'])
    log(f'P15 lock written: {LOCK.relative_to(ROOT)} ({lock["lock_sha256"][:12]}...), p16_test {manifest["traces"]} traces sealed')


# ------------------------------------------------------------------------------------------------ search

def candidate_spec(weights, outer, j):
    return {'kind': 'train', 'weights': J.weights_of(weights), 'stream': {'split': 'train_candidate', 'outer': outer, 'repeat': j % 2},
            'seed': P15_SEED_BASE + 100 * outer + j, 'budget': F, 'eval': {'split': 'dev_validation', 'ids': list(SEARCH_IDS)},
            'log_rows': CANDIDATE_LOG_ROWS, 'learner': '0.3'}


def model_specs(weights, outer, count):
    return [candidate_spec(weights, outer, j) for j in range(count)]


def score(weights, outer, count):
    from .search import rms
    costs = np.mean([J.result(OUT, s)['macro_costs'] for s in model_specs(weights, outer, count)], axis=0)
    return costs, rms(costs)


class Driver:
    """One search plus its elite resampling; never blocks on elite jobs."""
    def __init__(self, method, outer):
        from .p14_search import Search
        self.search, self.outer, self.batch = Search(method, outer, SLOTS), outer, None
        self.elites, self.triggered = [], 0

    def specs_ready(self, weights, count):
        return all(J.is_done(OUT, s) for s in model_specs(weights, self.outer, count))

    def advance(self, pool):
        while True:
            if self.batch is None:
                if self.search.done:
                    break
                self.batch = self.search.next_batch()
                if self.batch is None:
                    break
                for w in self.batch:
                    for s in model_specs(w, self.outer, BASE_MODELS):
                        pool.submit(s)
            if not all(self.specs_ready(w, BASE_MODELS) for w in self.batch):
                break
            self.search.tell([score(w, self.outer, BASE_MODELS)[0] for w in self.batch])
            self.batch = None
            while len(self.search.records) // GENERATION > self.triggered:
                self.triggered += 1
                taken = {tuple(e) for e in self.elites}
                added = 0
                for r in sorted(self.search.records, key=lambda r: (r['D'], r['slot'])):
                    if added == ELITE_PER_GENERATION:
                        break
                    if tuple(r['weights']) in taken:      # MOEA/D can propose the same weights in several slots
                        continue
                    added += 1
                    self.elites.append(r['weights'])
                    taken.add(tuple(r['weights']))
                    for s in model_specs(r['weights'], self.outer, BASE_MODELS + ELITE_EXTRA)[BASE_MODELS:]:
                        pool.submit(s)

    @property
    def done(self):
        return self.search.done and self.batch is None and all(self.specs_ready(w, BASE_MODELS + ELITE_EXTRA) for w in self.elites)

    def summary(self):
        s = self.search.summary()
        first = {}
        for r in s['records']:
            first.setdefault(tuple(r['weights']), r['slot'])
        elites = []
        for w in self.elites:
            _, d12 = score(w, self.outer, BASE_MODELS + ELITE_EXTRA)
            _, d4 = score(w, self.outer, BASE_MODELS)
            elites.append({'weights': w, 'slot': first[tuple(w)], 'D_4_models': d4, 'D_12_models': d12})
        chosen = min(elites, key=lambda e: (e['D_12_models'], e['slot']))
        return {**s, 'elites': elites, 'selected': chosen, 'selected_p11_rule': s['selected_plain']}


def stage_search(workers):
    verify_lock()
    drivers = [Driver(m, o) for o in OUTERS for m in SEARCH_METHODS]
    pool = J.Pool(OUT, workers, 'search', log, stopped)
    try:
        while True:
            for d in drivers:
                d.advance(pool)
            if all(d.done for d in drivers):
                break
            pool.step()
            time.sleep(1)
    finally:
        pool.close()
    for d in drivers:
        J.dump(OUT / 'searches' / f'{d.search.name}_o{d.outer:02d}.json', d.summary())
    walls = [read_json(p)['total_wall_s'] for p in (OUT / 'runs').glob('*/result.json')]
    mark('search', searches=len(drivers), models=len(walls), cpu_hours=float(np.sum(walls)) / 3600)
    log(f'search: {len(drivers)} searches complete, {len(walls)} PPO models, {np.sum(walls) / 3600:.0f} CPU-hours')


def stage_determinism():
    from .p14_search import Search
    fake = lambda w: [w[0] ** 2, w[1], 1 - w[2], w[3] * w[4], (w[4] - .2) ** 2]
    for name in SEARCH_METHODS:
        runs = []
        for _ in range(2):
            s = Search(name, OUTERS[0], SLOTS)
            while not s.done:
                b = s.next_batch()
                if b is None:
                    break
                s.tell([fake(w) for w in b])
            runs.append([r['weights'] for r in s.records])
        require(runs[0] == runs[1], f'{name}: search replay is not deterministic')
    s = [{**candidate_spec(EQUAL, OUTERS[0], 0), 'budget': 1024, 'replica': r} for r in (0, 1)]
    J.run_specs(OUT / 'determinism', s, 2, 'determinism', log, stopped)
    a, b = (J.result(OUT / 'determinism', x) for x in s)
    require(a['policy_tensor_sha256'] == b['policy_tensor_sha256'] and a['macro_costs'] == b['macro_costs'], 'PPO training not deterministic')
    shutil.rmtree(OUT / 'determinism', ignore_errors=True)
    mark('determinism')
    log('determinism ok: search replays and PPO training identical')


def progress():
    n = len(list((OUT / 'runs').glob('*/result.json'))) if (OUT / 'runs').exists() else 0
    s = len(list((OUT / 'searches').glob('*.json'))) if (OUT / 'searches').exists() else 0
    expected = len(SEARCH_METHODS) * len(OUTERS) * (SLOTS * BASE_MODELS + SLOTS // GENERATION * ELITE_PER_GENERATION * ELITE_EXTRA)
    return f'  PPO models done: {n} (about {expected - 4800 * (not SMOKE)} expected)\n  searches written: {s}/{len(SEARCH_METHODS) * len(OUTERS)}'


def status():
    print(json.dumps({k: {kk: vv for kk, vv in v.items()} for k, v in state()['stages'].items()}, indent=2))
    print(progress())
    print(f'log: {LOG}')


def run(workers):
    if not done('preflight'):
        free = shutil.disk_usage(ROOT).free / 2 ** 30
        require(free > 120, f'only {free:.0f} GiB free; P15+P16 need about 80 GiB')
        from .analysis.lock import verify_lock as verify_v04
        problems, _ = verify_v04(V04_LOCK, deep=False)
        require(not problems, f'v0.4 lock problems: {problems}')
        mark('preflight', free_disk_gib=round(free), smoke=SMOKE)
        log(f'preflight ok: {free:.0f} GiB free; v0.4 lock verified')
    if not done('lock'):
        stage_lock()
    stopped()
    if not done('determinism'):
        stage_determinism()
    stopped()
    if not done('search'):
        stage_search(workers)
    log('=== P15 complete: run P16 (./run_p16.sh) for the final models and the sealed test ===')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    r = sub.add_parser('run')
    r.add_argument('--workers', type=int, default=12)
    sub.add_parser('status')
    args = parser.parse_args()
    if args.command == 'status':
        status()
    else:
        signal.signal(signal.SIGTERM, lambda *_: STOP.update(requested=True))
        signal.signal(signal.SIGINT, lambda *_: STOP.update(requested=True))
        log(f'=== p15 run pid={os.getpid()} workers={args.workers} smoke={SMOKE} ===')
        run(args.workers)


if __name__ == '__main__':
    main()
