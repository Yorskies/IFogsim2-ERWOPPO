"""P14 pilot: is there a reward-weight signal worth searching, how strong must the evaluator be, and do the four MOEAs work?

    PYTHONPATH=. venv/bin/python -m research_v2.p14 run        # every stage; idempotent, resumable
    PYTHONPATH=. venv/bin/python -m research_v2.p14 status

Design: docs/research_v2/P14_MOEA_PILOT_DESIGN.md (decisions in section 12). Development data only: training on pilot_train
(outer 100-102), scoring on dev_validation (p14_traces). No test split is generated or read.

Every PPO run is one content-addressed job (runs/<sha>/): spec.json -> train (learner v0.3, budget, weights, seed, stream)
-> deterministic evaluation on a dev_validation id range -> result.json. Identical specs are never trained twice, and a
restart replays the deterministic searches against the cached results.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

import numpy as np

from .config import ROOT, load_config, read_json, require, sha256

SMOKE = os.environ.get('P14_SMOKE') == '1'
OUT = Path(os.environ.get('P14_OUT', ROOT / 'results/research_v2/p14_pilot'))
require(not SMOKE or 'P14_OUT' in os.environ, 'P14_SMOKE requires P14_OUT outside the real output directory')
STATE, LOG = OUT / 'pipeline/state.json', OUT / 'pipeline/pipeline.log'
JDK = '/usr/lib/jvm/java-21-openjdk-amd64'
STOP = {'requested': False}
F = 1024 if SMOKE else 102_400
LOG_ROWS = 10_240
Q1_SEEDS, Q1_BASE, Q1_OUTER = 4, 600_000, 100
REEVAL_BASE, TRUE_BASE = 610_000, 620_000
PILOT_OUTERS = (100,) if SMOKE else (100, 101, 102)
SLOTS = 30 if SMOKE else 90
TOP_K, REEVAL_SEEDS, TRUE_SEEDS = 3, 2, 4
EQUAL, MANUAL = [0.2] * 5, [0.30, 0.15, 0.25, 0.10, 0.20]
COSTS = ('zL', 'zE', 'zD', 'zB', 'zQ')
GATES = {'icc_min': 0.30, 'gain_min': 0.02, 'reliability': 0.8, 'max_seeds': 4, 'max_full_days': 5.0}


def id_ranges():
    from . import p14_traces as T
    if SMOKE:
        return {'all': (40000, 40001), 'search': (40000, 40000), 'holdout': (40001, 40001)}
    return {'all': T.TRACE_IDS, 'search': T.SEARCH_IDS, 'holdout': T.HOLDOUT_IDS}


# ------------------------------------------------------------------------------------------------ plumbing

def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def log(message):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f'[{now()}] {message}'
    print(line, flush=True)
    with LOG.open('a') as sink:
        sink.write(line + '\n')


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def state():
    return read_json(STATE) if STATE.exists() else {'stages': {}}


def mark(stage, **info):
    s = state()
    s['stages'][stage] = {'done_utc': now(), **info}
    dump(STATE, s)


def done(stage):
    return stage in state()['stages']


def stopped():
    if STOP['requested']:
        log('stop requested: exiting; re-run the same command to resume')
        raise SystemExit(75)


def read_rows(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]


# ------------------------------------------------------------------------------------------------ one PPO job

def weights_of(w):
    a = np.asarray(w, dtype=float)
    require(a.shape == (5,) and a.min() >= 0.02 - 1e-12 and abs(a.sum() - 1) < 1e-9, f'invalid weights {w}')
    return [round(float(x), 12) for x in a]


def spec(weights, outer, repeat, seed, budget, eval_ids, replica=0):
    return {'weights': weights_of(weights), 'outer': outer, 'repeat': repeat, 'seed': seed, 'budget': budget,
            'eval_ids': list(id_ranges()[eval_ids]), 'learner': '0.3', 'replica': replica}


def job_dir(s):
    return OUT / 'runs' / sha256(s)[:16]


def run_job(path):
    """Train, evaluate, write result.json. Called in a fresh process per job."""
    from .learner import effective_learner
    from .learning import AuditedPPO, EpisodeAudit, PilotStream, aggregate_costs, append_json, ppo_kwargs, setup_torch
    from .gym_env import OffloadingEnv
    from .study_final import TimedOffloadingEnv
    from stable_baselines3 import PPO
    from stable_baselines3.common.logger import configure
    from . import p14_traces as T

    class FirstRowsAudit(EpisodeAudit):
        def _write_decision(self, row):
            if self.decisions < LOG_ROWS:
                super()._write_decision(row)

    directory = Path(path)
    s = read_json(directory / 'spec.json')
    for name in ('train', 'eval.jsonl', 'eval.jsonl.partial'):
        target = directory / name
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
    config = load_config()
    learner, _ = effective_learner(config, s['learner'])
    started = time.monotonic()
    stream = PilotStream(config, s['outer'], s['repeat'], split='pilot_train')
    train_dir = directory / 'train'
    train_dir.mkdir()
    env = FirstRowsAudit(TimedOffloadingEnv(stream, s['weights'], config=config, jdk_home=JDK, any_port=True, validate=False),
                         stream, train_dir)
    try:
        setup_torch(config)
        model = AuditedPPO('MlpPolicy', env, seed=s['seed'], **ppo_kwargs(learner))
        model.audit_directory, model.audit_env, model.audit_checkpoint_at = train_dir, env, [s['budget']]
        model.set_logger(configure(str(train_dir / 'sb3'), ['json']))
        model.learn(total_timesteps=s['budget'])
        require(model.num_timesteps == s['budget'] == env.decisions, 'training budget mismatch')
    finally:
        env.close()
    train_wall = time.monotonic() - started
    checkpoint = train_dir / f'checkpoint_{s["budget"]:08d}'
    policy = PPO.load(checkpoint / 'model.zip', device='cpu')
    holder = {}
    env = OffloadingEnv(lambda seed, index: holder['trace'], s['weights'], config=config, jdk_home=JDK, any_port=True, validate=False)
    rows = []
    try:
        for key in T.keys(config, tuple(s['eval_ids'])):
            trace = T.generate(config, key)
            holder['trace'] = trace
            obs, _ = env.reset(seed=0)
            steps, reward_sum, actions = 0, 0.0, np.zeros(7, dtype=np.int64)
            while True:
                action = int(policy.predict(obs, deterministic=True)[0])
                obs, reward, terminated, truncated, info = env.step(action)
                require(not truncated, 'evaluation episode truncated')
                steps, reward_sum = steps + 1, reward_sum + reward
                actions[action] += 1
                if terminated:
                    break
            metrics = info['summary']['metrics']
            z = [metrics['costs'][c] for c in COSTS]
            require(steps == trace['task_count'], 'evaluation did not finish the trace')
            require(np.isclose(reward_sum, -100 * np.dot(s['weights'], z), rtol=1e-6, atol=1e-8), 'reward identity failed')
            row = {'namespace': key.to_dict(), 'trace_sha256': trace['payload_sha256'], 'decisions': steps,
                   'reward': reward_sum, 'action_counts': actions.tolist(), 'metrics': metrics}
            rows.append(row)
            append_json(directory / 'eval.jsonl.partial', row)
    finally:
        env.close()
    (directory / 'eval.jsonl.partial').replace(directory / 'eval.jsonl')
    agg = aggregate_costs(rows, config['training']['workload_order'])
    from .learning_instrumentation import tensor_digest
    dump(directory / 'result.json', {**s, 'D': agg['D_macro'], 'macro_costs': agg['macro_costs'],
                                     'D_by_workload': agg['D_by_workload'], 'train_wall_s': train_wall,
                                     'total_wall_s': time.monotonic() - started,
                                     'action_share': (np.sum([r['action_counts'] for r in rows], axis=0) /
                                                      sum(r['decisions'] for r in rows)).tolist(),
                                     'flagged_episodes': sum(r['metrics']['diagnosis_required'] for r in rows),
                                     'policy_tensor_sha256': tensor_digest(policy.policy.state_dict()), 'completed_utc': now()})


def result(s):
    return read_json(job_dir(s) / 'result.json')


def is_done(s):
    return (job_dir(s) / 'result.json').exists()


# ------------------------------------------------------------------------------------------------ job pool

class Pool:
    """Runs content-addressed jobs in separate process groups; JVMs are reaped with the group."""
    def __init__(self, workers, name):
        self.workers, self.name, self.queue, self.running, self.finished = workers, name, [], {}, 0
        self.env = {**os.environ, 'PYTHONPATH': str(ROOT)}
        self.last = time.monotonic()

    def submit(self, s):
        key = sha256(s)[:16]
        if is_done(s) or key in self.running or any(sha256(q)[:16] == key for q in self.queue):
            return
        self.queue.append(s)

    def step(self):
        for key, (process, s) in list(self.running.items()):
            if process.poll() is None:
                continue
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            del self.running[key]
            require(process.returncode == 0 and is_done(s), f'{self.name}: job {key} failed (exit {process.returncode}); '
                    f'see {job_dir(s) / "job.log"}')
            self.finished += 1
        stopped()
        while self.queue and len(self.running) < self.workers:
            s = self.queue.pop(0)
            d = job_dir(s)
            d.mkdir(parents=True, exist_ok=True)
            dump(d / 'spec.json', s)
            sink = open(d / 'job.log', 'w')
            process = subprocess.Popen([sys.executable, '-m', 'research_v2.p14', 'job', '--dir', str(d)], cwd=ROOT, env=self.env,
                                       stdout=sink, stderr=subprocess.STDOUT, start_new_session=True)
            self.running[sha256(s)[:16]] = (process, s)
        if time.monotonic() - self.last > 900:
            log(f'{self.name}: {self.finished} jobs finished, {len(self.running)} running, {len(self.queue)} queued')
            self.last = time.monotonic()

    @property
    def idle(self):
        return not self.queue and not self.running

    def drain(self):
        while not self.idle:
            self.step()
            time.sleep(2)

    def close(self):
        for process, _ in self.running.values():
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        for process, _ in self.running.values():
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)


def run_specs(specs, workers, name):
    pool = Pool(workers, name)
    try:
        for s in specs:
            pool.submit(s)
        log(f'{name}: {len(pool.queue)} of {len(specs)} jobs to run ({workers} workers)')
        pool.drain()
    finally:
        pool.close()
    log(f'{name}: all {len(specs)} jobs complete')


# ------------------------------------------------------------------------------------------------ Q1 / Q2

def q1_weights():
    from .search import sample_simplex
    lean = [[0.6 if i == k else 0.1 for i in range(5)] for k in range(5)]
    extreme = [[0.92 if i == k else 0.02 for i in range(5)] for k in range(5)]
    rand = sample_simplex(np.random.Generator(np.random.PCG64(600_001)), 12).tolist()
    named = [('equal', EQUAL), ('manual', MANUAL)] + [(f'lean_{c}', w) for c, w in zip(COSTS, lean)] + \
            [(f'extreme_{c}', w) for c, w in zip(COSTS, extreme)] + [(f'random_{i:02d}', w) for i, w in enumerate(rand)]
    if SMOKE:
        named = named[:4]
    return [(n, weights_of(w)) for n, w in named]


Q1_LONG = ('equal', 'manual', 'lean_zL', 'lean_zE', 'lean_zD', 'lean_zB', 'lean_zQ', 'random_00')


def q1_specs(budget):
    names = dict(q1_weights())
    chosen = list(names) if budget == F else [n for n in Q1_LONG if n in names]
    return {(n, k): spec(names[n], Q1_OUTER, 0, Q1_BASE + 100 * i + k, budget, 'all')
            for i, n in enumerate(names) if n in chosen for k in range(Q1_SEEDS)}


def trace_costs(specs, ids=None):
    """{key: array [workload, trace, 5]} from each job's eval rows (optionally restricted to an id range)."""
    config = load_config()
    workloads = config['training']['workload_order']
    out = {}
    for key, s in specs.items():
        rows = read_rows(job_dir(s) / 'eval.jsonl')
        if ids is not None:
            rows = [r for r in rows if ids[0] <= r['namespace']['trace_id'] <= ids[1]]
        out[key] = np.array([[[r['metrics']['costs'][c] for c in COSTS] for r in rows if r['namespace']['workload'] == w]
                             for w in workloads])
    return out


def d_of(arr, idx=None):
    """arr [W, T, 5] -> D (RMS of macro costs, workloads weighted equally)."""
    a = arr if idx is None else np.stack([arr[w][idx[w]] for w in range(arr.shape[0])])
    return float(np.sqrt(np.mean(np.square(a.mean(axis=1).mean(axis=0)))))


def icc1(matrix):
    """One-way random-effects ICC(1) for a [groups, replicates] matrix."""
    m = np.asarray(matrix, dtype=float)
    g, k = m.shape
    msb = k * m.mean(axis=1).var(ddof=1)
    msw = m.var(axis=1, ddof=1).mean()
    return float((msb - msw) / (msb + (k - 1) * msw)) if msb + (k - 1) * msw > 0 else 0.0


SPLITS = (([0, 1], [2, 3]), ([0, 2], [1, 3]), ([0, 3], [1, 2]))


def cv_gain(D, names):
    """Cross-validated gain of the best weight over equal: choose on two seeds, judge on the other two; averaged over the three
    ways to halve four seeds and both directions, so neither the split nor the selection seeds can inflate it."""
    e = names.index('equal')
    gains, picks = [], []
    for a, b in SPLITS:
        for pick, judge in ((a, b), (b, a)):
            best = int(np.argmin(D[:, pick].mean(axis=1)))
            gains.append(D[e, judge].mean() - D[best, judge].mean())
            picks.append(names[best])
    return float(np.mean(gains)), sorted(set(picks))


def spearman_brown(r2, target):
    """Reliability of a 2-seed mean is r2; smallest number of seeds m with reliability >= target (None if unreachable)."""
    if r2 <= 0:
        return None
    for m in range(1, 257):
        k = m / 2
        if k * r2 / (1 + (k - 1) * r2) >= target:
            return m
    return None


def analyse_q1(budget, draws=2000):
    from scipy.stats import spearmanr
    specs = q1_specs(budget)
    names = list(dict.fromkeys(n for n, _ in specs))
    costs = trace_costs(specs)
    D = np.array([[d_of(costs[(n, k)]) for k in range(Q1_SEEDS)] for n in names])
    gain, picks = cv_gain(D, names)
    rng = np.random.Generator(np.random.PCG64(600_002))
    W, T = costs[(names[0], 0)].shape[:2]
    boot_gain, boot_icc = [], []
    for _ in range(draws):
        # crossed bootstrap: traces (shared by all runs) and, independently per weight, its seeds
        idx = [rng.integers(0, T, T) for _ in range(W)]
        Db = np.array([[d_of(costs[(n, k)], idx) for k in rng.integers(0, Q1_SEEDS, Q1_SEEDS)] for n in names])
        boot_gain.append(cv_gain(Db, names)[0])
        boot_icc.append(icc1(Db))
    out = {'budget': budget, 'weights': names, 'D': D.tolist(), 'D_mean': dict(zip(names, D.mean(axis=1).tolist())),
           'icc': icc1(D), 'icc_ci95': np.percentile(boot_icc, [2.5, 97.5]).tolist(),
           'cv_gain_vs_equal': gain, 'cv_gain_ci95': np.percentile(boot_gain, [2.5, 97.5]).tolist(), 'cv_picks': picks,
           'seed_sd_mean': float(D.std(axis=1, ddof=1).mean()), 'between_weight_sd': float(D.mean(axis=1).std(ddof=1))}
    if len(names) >= 4:
        half = spearmanr(D[:, [0, 1]].mean(axis=1), D[:, [2, 3]].mean(axis=1)).statistic
        out['rank_reliability_2_seeds'] = float(half)
        out['seeds_for_reliability'] = spearman_brown(float(half), GATES['reliability'])
        sc = trace_costs(specs, id_ranges()['search'])
        Ds = np.array([[d_of(sc[(n, k)]) for k in range(Q1_SEEDS)] for n in names])
        out['rank_reliability_2_seeds_20_traces'] = float(spearmanr(Ds[:, [0, 1]].mean(axis=1), Ds[:, [2, 3]].mean(axis=1)).statistic)
        out['icc_20_traces'] = icc1(Ds)
    macro = np.array([result(s)['macro_costs'] for s in specs.values()])
    out['cost_spearman'] = spearmanr(macro).statistic.tolist() if np.ptp(macro, axis=0).min() > 0 else None
    centred = (macro - macro.mean(axis=0)) / np.where(macro.std(axis=0) > 0, macro.std(axis=0), 1)
    eig = np.sort(np.linalg.eigvalsh(np.cov(centred.T)))[::-1]
    out['pca_explained'] = (eig / eig.sum()).tolist()
    out['action_share_by_weight'] = {n: np.mean([result(specs[(n, k)])['action_share'] for k in range(Q1_SEEDS)], axis=0).tolist()
                                     for n in names}
    return out


# ------------------------------------------------------------------------------------------------ Q3

def candidate_specs(weights, outer):
    seeds = load_config()['seeds']['candidate_model_base']
    return [spec(weights, outer, r, seeds + 2 * outer + r, F, 'search') for r in (0, 1)]


def objectives(weights, outer):
    return np.mean([result(s)['macro_costs'] for s in candidate_specs(weights, outer)], axis=0)


def run_searches(workers):
    from .p14_search import ALGORITHMS, Search
    searches = [Search(a, o, SLOTS) for o in PILOT_OUTERS for a in ALGORITHMS]
    pool = Pool(workers, 'search')
    batches = {}
    try:
        while True:
            for i, s in enumerate(searches):
                while not s.done:
                    if i not in batches:
                        batch = s.next_batch()
                        if batch is None:
                            break
                        batches[i] = batch
                        for w in batch:
                            for c in candidate_specs(w, s.outer):
                                pool.submit(c)
                    if all(is_done(c) for w in batches[i] for c in candidate_specs(w, s.outer)):
                        s.tell([objectives(w, s.outer) for w in batches.pop(i)])
                    else:
                        break
            if all(s.done for s in searches):
                break
            pool.step()
            time.sleep(1)
    finally:
        pool.close()
    out = {}
    for s in searches:
        summary = s.summary()
        dump(OUT / 'q3/searches' / f'{s.name}_o{s.outer}.json', summary)
        out[(s.name, s.outer)] = summary
    return out


def reeval_specs(summary, index):
    """Top-k front candidates by D, each trained with REEVAL_SEEDS fresh seeds on the search traces."""
    front = sorted(summary['front'], key=lambda r: (r['D'], r['slot']))[:TOP_K]
    return {tuple(r['weights']): [spec(r['weights'], summary['outer'], j % 2, REEVAL_BASE + 100 * index + 10 * k + j, F, 'search')
                                  for j in range(REEVAL_SEEDS)] for k, r in enumerate(front)}


def selected_reeval(summary, index):
    from .search import rms
    best = None
    for w, extra in reeval_specs(summary, index).items():
        costs = [result(s)['macro_costs'] for s in candidate_specs(list(w), summary['outer']) + extra]
        d = rms(np.mean(costs, axis=0))
        if best is None or d < best[0] - 1e-12:
            best = (d, list(w))
    return {'weights': best[1], 'D_4_models': best[0]}


def true_specs(weights, outer):
    return [spec(weights, outer, 0, TRUE_BASE + 10 * (outer - 100) + k, F, 'holdout') for k in range(TRUE_SEEDS)]


def true_D(weights, outer):
    return float(np.mean([result(s)['D'] for s in true_specs(weights, outer)]))


def stage_q3(workers):
    summaries = run_searches(workers)
    keys = sorted(summaries)
    specs = [s for i, k in enumerate(keys) for v in reeval_specs(summaries[k], i).values() for s in v]
    run_specs(specs, workers, 'q3 re-evaluation of elites')
    chosen = {k: {'plain': summaries[k]['selected_plain']['weights'], 'reeval': selected_reeval(summaries[k], i)}
              for i, k in enumerate(keys)}
    specs = [s for (a, o), c in chosen.items() for w in (c['plain'], c['reeval']['weights']) for s in true_specs(w, o)]
    specs += [s for o in PILOT_OUTERS for s in true_specs(EQUAL, o)]
    run_specs(specs, workers, 'q3 true quality on hold-out traces')
    rows = []
    for (a, o) in keys:
        s, c = summaries[(a, o)], chosen[(a, o)]
        eq = true_D(EQUAL, o)
        rows.append({'algorithm': a, 'outer': o, 'search_D_selected': s['selected_plain']['D'],
                     'true_D_plain': true_D(c['plain'], o), 'true_D_reeval': true_D(c['reeval']['weights'], o),
                     'true_D_equal': eq, 'gain_plain': eq - true_D(c['plain'], o),
                     'gain_reeval': eq - true_D(c['reeval']['weights'], o), 'hypervolume': s['hypervolume'],
                     'front_size': len(s['front']), 'weights_plain': c['plain'], 'weights_reeval': c['reeval']['weights'],
                     'anytime_min_D': [(h['slots'], h['min_D']) for h in s['history']]})
    walls = [read_json(p)['total_wall_s'] for p in (OUT / 'runs').glob('*/result.json') if read_json(p)['eval_ids'] == list(id_ranges()['search'])]
    report = {'rows': rows, 'model_job_wall_s_mean': float(np.mean(walls)), 'slots': SLOTS, 'outers': list(PILOT_OUTERS)}
    dump(OUT / 'q3/report.json', report)
    return report


def stage_determinism():
    s = [spec(EQUAL, Q1_OUTER, 0, 699_999, 1024, 'search', replica=r) for r in (0, 1)]
    run_specs(s, 2, 'determinism')
    a, b = result(s[0]), result(s[1])
    same = a['policy_tensor_sha256'] == b['policy_tensor_sha256'] and a['macro_costs'] == b['macro_costs']
    from .p14_search import Search
    replay = True
    for name in ('nsga2', 'nsga3', 'moead', 'spea2', 'random'):
        x, y = Search(name, 100, 30), Search(name, 100, 30)
        fake = lambda w: [w[0] ** 2, w[1], 1 - w[2], w[3] * w[4], (w[4] - .2) ** 2]
        for srch in (x, y):
            while not srch.done:
                batch = srch.next_batch()
                if batch is None:
                    break
                srch.tell([fake(w) for w in batch])
        replay &= [r['weights'] for r in x.records] == [r['weights'] for r in y.records]
    require(same and replay, f'determinism failed (training {same}, search replay {replay})')
    mark('determinism', training_identical=same, search_replay_identical=replay)
    log('determinism ok: identical PPO runs and identical search replays')


# ------------------------------------------------------------------------------------------------ gates and report

def gates(q1f, q1l, q3):
    from .p14_search import ALGORITHMS
    g1 = q1f['icc'] >= GATES['icc_min'] and q1f['cv_gain_vs_equal'] >= GATES['gain_min'] and q1f['cv_gain_ci95'][0] > 0
    g1_long = q1l['icc'] >= GATES['icc_min'] and q1l['cv_gain_vs_equal'] >= GATES['gain_min'] and q1l['cv_gain_ci95'][0] > 0
    m = q1f.get('seeds_for_reliability')
    g2 = m is not None and m <= GATES['max_seeds']
    models = max(2, m or 4) if (m is None or m <= 16) else 16
    per_search = SLOTS * models + TOP_K * REEVAL_SEEDS
    full_jobs = len(ALGORITHMS) * 20 * per_search
    days = full_jobs * q3['model_job_wall_s_mean'] / 12 / 86400
    g3 = days <= GATES['max_full_days'] and state()['stages'].get('determinism', {}).get('training_identical', False)
    if g1 and g2 and g3:
        decision = 'proceed: design and lock the full benchmark with the evaluator size from G2'
    elif not g1 and g1_long:
        decision = 'signal only after 4 x F: full benchmark at candidate budget 4 x F (about 4 x cost) or redesign'
    elif not g1:
        decision = 'stop the full MOEA benchmark in this environment; report the pilot as diagnosis (weights do not matter beyond seed noise)'
    elif not g2:
        decision = 'strengthen the evaluator (more seeds/traces) and recompute the cost before deciding'
    else:
        decision = 'fix the implementation or reduce the full design, then repeat Q3'
    return {'G1_signal': g1, 'G1_signal_at_4F': g1_long, 'G2_evaluator': g2, 'seeds_for_reliability': m,
            'G3_implementation': g3, 'full_benchmark_models_per_candidate': models, 'full_benchmark_days_estimate': days,
            'thresholds': GATES, 'decision': decision}


def fmt(x, d=4):
    return '—' if x is None else f'{x:.{d}f}'


def render(q1f, q1l, q3, g):
    lines = ['# P14 pilot — reward-weight signal, evaluator reliability and four MOEAs', '',
             f'Development data only (pilot_train, dev_validation); no test split. Budget F = {F:,}; {"SMOKE RUN" if SMOKE else "full pilot"}.', '',
             '## Gates (fixed before the pilot)', '',
             '| gate | result |', '|---|---|',
             f'| G1 signal at F (ICC ≥ {GATES["icc_min"]}, CV gain ≥ {GATES["gain_min"]}, CI low > 0) | **{"pass" if g["G1_signal"] else "fail"}** |',
             f'| G1 at 4 × F | {"pass" if g["G1_signal_at_4F"] else "fail"} |',
             f'| G2 seeds per candidate for rank reliability {GATES["reliability"]} ≤ {GATES["max_seeds"]} | **{"pass" if g["G2_evaluator"] else "fail"}** (m = {g["seeds_for_reliability"]}) |',
             f'| G3 implementation and full benchmark ≤ {GATES["max_full_days"]} days | **{"pass" if g["G3_implementation"] else "fail"}** ({g["full_benchmark_days_estimate"]:.1f} days) |',
             '', f'**Decision:** {g["decision"]}', '']
    for title, q in (('Q1 — weight landscape at F', q1f), ('Q1 — weight landscape at 4 × F', q1l)):
        lines += [f'## {title}', '',
                  f'- ICC (share of D variance due to weights): **{q["icc"]:.3f}** [{q["icc_ci95"][0]:.3f}; {q["icc_ci95"][1]:.3f}]',
                  f'- cross-validated gain of the best weight over equal: **{q["cv_gain_vs_equal"]:.4f}** '
                  f'[{q["cv_gain_ci95"][0]:.4f}; {q["cv_gain_ci95"][1]:.4f}] (picked {", ".join(q["cv_picks"])})',
                  f'- mean seed SD {q["seed_sd_mean"]:.4f}; SD between weight means {q["between_weight_sd"]:.4f}']
        if 'rank_reliability_2_seeds' in q:
            lines += [f'- rank reliability of a 2-seed mean: {q["rank_reliability_2_seeds"]:.3f} (100 traces), '
                      f'{q["rank_reliability_2_seeds_20_traces"]:.3f} (20 traces); seeds for {GATES["reliability"]}: {q["seeds_for_reliability"]}']
        lines += ['- PCA of the five macro costs, explained variance: ' + ', '.join(f'{v:.2f}' for v in q['pca_explained']), '',
                  '| weights | mean D | seeds | action share local/F1..F5/cloud |', '|---|---:|---|---|']
        for i, n in enumerate(q['weights']):
            lines.append(f'| {n} | {q["D_mean"][n]:.4f} | ' + ', '.join(f'{d:.3f}' for d in q['D'][i]) + ' | ' +
                         '/'.join(f'{v:.2f}' for v in q['action_share_by_weight'][n]) + ' |')
        lines.append('')
    lines += ['## Q3 — four MOEAs and random search (3 pilot outers: indication only, not a claim)', '',
              '| algorithm | outer | search D (selected) | true D plain | true D re-eval | true D equal | gain plain | gain re-eval | HV | front |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in q3['rows']:
        lines.append(f'| {r["algorithm"]} | {r["outer"]} | {r["search_D_selected"]:.4f} | {r["true_D_plain"]:.4f} | {r["true_D_reeval"]:.4f} | '
                     f'{r["true_D_equal"]:.4f} | {r["gain_plain"]:+.4f} | {r["gain_reeval"]:+.4f} | {r["hypervolume"]:.4f} | {r["front_size"]} |')
    by = {}
    for r in q3['rows']:
        by.setdefault(r['algorithm'], []).append(r)
    lines += ['', '| algorithm | mean gain plain | mean gain re-eval | mean winner\'s-curse drop (true − search) |', '|---|---:|---:|---:|']
    for a, rs in by.items():
        lines.append(f'| {a} | {np.mean([r["gain_plain"] for r in rs]):+.4f} | {np.mean([r["gain_reeval"] for r in rs]):+.4f} | '
                     f'{np.mean([r["true_D_plain"] - r["search_D_selected"] for r in rs]):+.4f} |')
    lines += ['', f'True D: mean of {TRUE_SEEDS} fresh seeds on the hold-out dev_validation traces (not used by any search). '
              f'Gain = D(equal) − D(selected); positive = selected weights better. Mean model job (F training + 20-trace '
              f'evaluation): {q3["model_job_wall_s_mean"]:.0f} s.']
    return '\n'.join(lines) + '\n'


def stage_report():
    q1f = read_json(OUT / 'q1/report_F.json')
    q1l = read_json(OUT / 'q1/report_4F.json')
    q3 = read_json(OUT / 'q3/report.json')
    g = gates(q1f, q1l, q3)
    dump(OUT / 'report.json', {'q1_F': q1f, 'q1_4F': q1l, 'q3': q3, 'gates': g, 'smoke': SMOKE})
    (OUT / 'report.md').write_text(render(q1f, q1l, q3, g))
    mark('report', **{k: v for k, v in g.items() if k != 'thresholds'})
    log(f'report written: {OUT / "report.md"}; decision: {g["decision"]}')


def run(workers):
    if not done('preflight'):
        free = shutil.disk_usage(ROOT).free / 2 ** 30
        require(free > 30, f'only {free:.0f} GiB free')
        files = ['research_v2/p14.py', 'research_v2/p14_search.py', 'research_v2/p14_traces.py', 'research_v2/p13_traces.py',
                 'research_v2/learning.py', 'research_v2/search.py', 'docs/research_v2/P14_MOEA_PILOT_DESIGN.md']
        mark('preflight', free_disk_gib=round(free), sources={f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in files},
             config_sha256=sha256(load_config()), smoke=SMOKE)
        log(f'preflight ok: {free:.0f} GiB free; development data only')
    if not done('determinism'):
        stage_determinism()
    stopped()
    if not done('q1_F'):
        run_specs(list(q1_specs(F).values()), workers, 'q1 at F')
        dump(OUT / 'q1/report_F.json', analyse_q1(F, 200 if SMOKE else 2000))
        mark('q1_F')
    stopped()
    if not done('q1_4F'):
        run_specs(list(q1_specs(4 * F).values()), workers, 'q1 at 4F')
        dump(OUT / 'q1/report_4F.json', analyse_q1(4 * F, 200 if SMOKE else 2000))
        mark('q1_4F')
    stopped()
    if not done('q3'):
        stage_q3(workers)
        mark('q3')
    if not done('report'):
        stage_report()
    log('=== P14 pilot complete ===')


def status():
    print(json.dumps(state(), indent=2)[:4000])
    n = len(list((OUT / 'runs').glob('*/result.json'))) if (OUT / 'runs').exists() else 0
    print(f'completed PPO jobs: {n}')
    print(f'log: {LOG}')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    r = sub.add_parser('run')
    r.add_argument('--workers', type=int, default=12)
    sub.add_parser('status')
    j = sub.add_parser('job')
    j.add_argument('--dir', required=True)
    args = parser.parse_args()
    if args.command == 'status':
        status()
    elif args.command == 'job':
        run_job(args.dir)
    else:
        signal.signal(signal.SIGTERM, lambda *_: STOP.update(requested=True))
        signal.signal(signal.SIGINT, lambda *_: STOP.update(requested=True))
        log(f'=== p14 pilot run pid={os.getpid()} workers={args.workers} ===')
        run(args.workers)


if __name__ == '__main__':
    main()
