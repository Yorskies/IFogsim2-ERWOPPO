"""Cheap pre-flight checks 2 and 3 (validation namespace only; test never touched; nothing here changes the lock).

  (a) seed consistency: PPO-Equal at F=102,400 for outer runs 0-4.
  (b) weight sensitivity: the 8 registered pilot weight vectors at F for outer runs 0-2.
Each run uses the same train_final stream and model seed for a given outer run, so weights are paired by outer run.
    PYTHONPATH=. venv/bin/python results/research_v2/P10_learning_check/run_sensitivity.py [--workers 8]
"""
import argparse
import itertools
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

from research_v2.config import load_config
from research_v2.learning import write_json
from research_v2.search import pilot_weights

OUT = Path(__file__).resolve().parent / 'runs'
JDK = Path('/usr/lib/jvm/java-21-openjdk-amd64')
F = 102400
EVAL = (51200, 102400)
ACTIONS = ['source_iot', 'F1', 'F2', 'F3', 'F4', 'F5', 'cloud']


def jobs():
    weights = [w['id'] for w in pilot_weights(load_config())]
    todo = [(w, o) for o in (0, 1, 2) for w in weights] + [('equal', 3), ('equal', 4)]
    return todo


def worker(weight_id, outer):
    from research_v2.study_final import run_final_training, run_final_validation
    from research_v2.study_worker import compress_decision_logs
    config = load_config()
    weights = next(w['weights'] for w in pilot_weights(config) if w['id'] == weight_id)
    directory = OUT / f'{weight_id}_r{outer}'
    started = time.monotonic()
    run_final_training(directory / 'train', outer, F, weights, list(EVAL), JDK)
    result = {'weight_id': weight_id, 'outer': outer, 'weights': weights}
    for n in EVAL:
        run_final_validation(directory / 'train' / f'checkpoint_{n:08d}', directory / f'validation_{n}', JDK)
        summary = json.loads((directory / f'validation_{n}' / 'summary.json').read_text())
        rows = [json.loads(l) for l in (directory / f'validation_{n}' / 'episodes.jsonl').read_text().splitlines()]
        counts = np.sum([r['action_counts'] for r in rows], axis=0)
        result[str(n)] = {'D_macro': summary['D_macro'], 'macro_costs': summary['macro_costs'],
                          'D_by_workload': summary['D_by_workload'],
                          'action_share': dict(zip(ACTIONS, (counts / counts.sum()).round(4).tolist()))}
    compress_decision_logs(directory)
    result['wall_s'] = time.monotonic() - started
    write_json(directory / 'result.json', result)


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def aggregate(reference):
    ids = [w['id'] for w in pilot_weights(load_config())]
    data = {}
    for w, o in jobs():
        data[(w, o)] = json.loads((OUT / f'{w}_r{o}' / 'result.json').read_text())
    D = lambda w, o, n=102400: data[(w, o)][str(n)]['D_macro']
    seeds = {n: [D('equal', o, n) for o in range(5)] for n in EVAL}
    table = {w: [D(w, o) for o in range(3)] for w in ids}
    diff = {w: [table[w][o] - table['equal'][o] for o in range(3)] for w in ids}
    pair = [spearman([table[w][a] for w in ids], [table[w][b] for w in ids]) for a, b in itertools.combinations(range(3), 2)]
    within = [float(np.std([table[w][o] for w in ids], ddof=1)) for o in range(3)]
    best = [min(ids, key=lambda w: table[w][o]) for o in range(3)]
    report = {
        'F': F, 'validation_only': True, 'test_accessed': False,
        'reference_validation_D': reference,
        'equal_by_outer': {str(n): seeds[n] for n in EVAL},
        'equal_F_mean': float(np.mean(seeds[102400])), 'equal_F_sd_across_5_outers': float(np.std(seeds[102400], ddof=1)),
        'D_F_by_weight_and_outer': table,
        'D_F_mean_by_weight': {w: float(np.mean(v)) for w, v in table.items()},
        'D_F_sd_by_weight': {w: float(np.std(v, ddof=1)) for w, v in table.items()},
        'diff_vs_equal_by_outer': diff,
        'between_weight_sd_within_outer': within,
        'rank_correlation_between_outers': pair,
        'best_weight_by_outer': best,
        'oracle_gain_vs_equal': [table['equal'][o] - min(table[w][o] for w in ids) for o in range(3)],
        'action_share_F': {w: [data[(w, o)]['102400']['action_share'] for o in range(3)] for w in ids},
        'macro_costs_F': {w: [data[(w, o)]['102400']['macro_costs'] for o in range(3)] for w in ids},
        'wall_s_per_run': float(np.mean([r['wall_s'] for r in data.values()])),
    }
    write_json(OUT.parent / 'sensitivity.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--worker', nargs=2, metavar=('WEIGHT', 'OUTER'))
    args = parser.parse_args()
    if args.worker:
        worker(args.worker[0], int(args.worker[1]))
        return
    OUT.mkdir(exist_ok=True)
    pending = [(w, o) for w, o in jobs() if not (OUT / f'{w}_r{o}' / 'result.json').exists()]
    running = []
    started = time.monotonic()
    while pending or running:
        running = [(p, j) for p, j in running if p.poll() is None]
        while pending and len(running) < args.workers:
            w, o = pending.pop(0)
            log = open(OUT / f'{w}_r{o}.log', 'w')
            running.append((subprocess.Popen([sys.executable, __file__, '--worker', w, str(o)], stdout=log, stderr=subprocess.STDOUT), (w, o)))
            print('START', w, o, flush=True)
        time.sleep(2)
    print('all runs finished in', round(time.monotonic() - started), 's', flush=True)
    check = json.loads((OUT.parent / 'check.json').read_text())['results']
    reference = {k: check[k]['D_macro'] for k in ('greedy_eft', 'always_local', 'uniform_random')}
    report = aggregate(reference)
    print(json.dumps({k: report[k] for k in ('equal_by_outer', 'equal_F_mean', 'equal_F_sd_across_5_outers', 'D_F_mean_by_weight',
                                             'rank_correlation_between_outers', 'between_weight_sd_within_outer', 'best_weight_by_outer',
                                             'oracle_gain_vs_equal')}, indent=1))


if __name__ == '__main__':
    main()
