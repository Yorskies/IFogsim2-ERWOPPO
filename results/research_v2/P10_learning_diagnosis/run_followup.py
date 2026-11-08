"""Follow-up to run_ablation.py (same protocol P10-stability-diagnosis-1, pilot namespace only, test never touched).

  (a) gamma bracket: 0.95 and 0.98 with equal weights (6 pilot seeds), next to 1.0 / 0.99 / 0.97 from the ablation.
  (b) weight sensitivity with the stable learner (gamma 0.97): the 7 non-equal registered pilot weights x 6 seeds; the equal arm is the
      existing gamma097 runs. Includes a cross-seed selection check that mimics search -> fresh final model: pick the best weight on
      repeat-0 models, score it on repeat-1 models of the same outer runs (and the reverse).
    PYTHONPATH=. venv/bin/python results/research_v2/P10_learning_diagnosis/run_followup.py [--workers 32]
"""
import argparse
import itertools
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_ablation as A  # noqa: E402
from research_v2 import learning  # noqa: E402
from research_v2.config import load_config  # noqa: E402
from research_v2.search import pilot_weights  # noqa: E402

OUT = A.OUT
A.VARIANTS.update({'gamma095': {'gamma': 0.95}, 'gamma098': {'gamma': 0.98}})
WEIGHTS = {w['id']: w['weights'] for w in pilot_weights(load_config())}


def run_dir(variant, weight, outer, repeat):
    if weight == 'equal':
        return OUT / 'runs' / f'{variant}_o{outer}r{repeat}'
    return OUT / 'runs' / f'{variant}_{weight}_o{outer}r{repeat}'


def worker(variant, weight, outer, repeat):
    from research_v2.study_worker import compress_decision_logs
    learning.effective_learner = A.effective_learner
    directory = run_dir(variant, weight, outer, repeat)
    started = time.monotonic()
    learning.run_training(directory / 'train', outer, repeat, A.F, WEIGHTS[weight], A.JDK, learner_spec=OUT / 'specs' / f'{variant}.json',
                          training_split='pilot_train', phase='P07', checkpoint_at=A.CHECKPOINTS, fast_rpc=True)
    result = {'variant': variant, 'weight': weight, 'weights': WEIGHTS[weight], 'outer': outer, 'repeat': repeat}
    for n in (51200, A.F):
        target = directory / f'eval_{n}_det'
        learning.run_evaluation(directory / 'train' / f'checkpoint_{n:08d}', target, A.JDK, deterministic=True,
                                split='pilot_validation', fast_rpc=True)
        s = json.loads((target / 'summary.json').read_text())
        rows = [json.loads(l) for l in (target / 'episodes.jsonl').read_text().splitlines()]
        counts = np.sum([r['action_counts'] for r in rows], axis=0)
        result[f'{n}_det'] = {'D_macro': s['D_macro'], 'linear_equal': float(np.mean(s['macro_costs'])), 'macro_costs': s['macro_costs'],
                              'top_action_share': float(counts.max() / counts.sum()), 'top_action': A.ACTIONS[int(counts.argmax())]}
    compress_decision_logs(directory)
    result['wall_s'] = time.monotonic() - started
    (directory / 'result.json').write_text(json.dumps(result, indent=2))


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def aggregate():
    ref = json.loads((OUT / 'heuristics_pilot_validation.json').read_text())
    D = lambda v, w, o, r: json.loads((run_dir(v, w, o, r) / 'result.json').read_text())[f'{A.F}_det']['D_macro']
    gammas = {}
    for v, g in (('base', 1.0), ('gamma099', 0.99), ('gamma098', 0.98), ('gamma097', 0.97), ('gamma095', 0.95)):
        vals = [D(v, 'equal', o, r) for o, r in A.SEEDS]
        gammas[str(g)] = {'D_F': vals, 'mean': float(np.mean(vals)), 'sd': float(np.std(vals, ddof=1)),
                          'below_always_local': int(sum(x < ref['always_local']['D_macro'] for x in vals)),
                          'below_greedy_eft': int(sum(x < ref['greedy_eft']['D_macro'] for x in vals))}
    ids = list(WEIGHTS)
    table = {w: [D('gamma097', w, o, r) for o, r in A.SEEDS] for w in ids}
    seeds = range(len(A.SEEDS))
    ranks = [[table[w][s] for w in ids] for s in seeds]
    pair = [spearman(ranks[a], ranks[b]) for a, b in itertools.combinations(seeds, 2)]
    # Cross-seed selection: choose on one repeat, evaluate on the other repeat of the same outer runs.
    transfer = []
    for choose_r, score_r in ((0, 1), (1, 0)):
        pick = [i for i, (o, r) in enumerate(A.SEEDS) if r == choose_r]
        score = [i for i, (o, r) in enumerate(A.SEEDS) if r == score_r]
        best = min(ids, key=lambda w: np.mean([table[w][i] for i in pick]))
        transfer.append({'chosen_on_repeat': choose_r, 'best_weight': best,
                         'chosen_D_on_selection_seeds': float(np.mean([table[best][i] for i in pick])),
                         'chosen_D_on_fresh_seeds': float(np.mean([table[best][i] for i in score])),
                         'equal_D_on_fresh_seeds': float(np.mean([table['equal'][i] for i in score])),
                         'fresh_seed_gain_vs_equal': float(np.mean([table['equal'][i] - table[best][i] for i in score]))})
    per_outer_select = []
    for o in (100, 101, 102):
        i0, i1 = A.SEEDS.index((o, 0)), A.SEEDS.index((o, 1))
        for pick, score in ((i0, i1), (i1, i0)):
            best = min(ids, key=lambda w: table[w][pick])
            per_outer_select.append({'outer': o, 'best_weight': best, 'gain_on_fresh_seed_vs_equal': table['equal'][score] - table[best][score]})
    report = {'protocol': A.PROTOCOL, 'namespace': 'pilot', 'learner': 'gamma 0.97 for weight sensitivity', 'heuristics': ref,
              'gamma_bracket': gammas, 'D_F_by_weight': table,
              'D_F_mean_by_weight': {w: float(np.mean(v)) for w, v in table.items()},
              'D_F_sd_by_weight': {w: float(np.std(v, ddof=1)) for w, v in table.items()},
              'paired_diff_vs_equal_mean': {w: float(np.mean(np.array(table[w]) - np.array(table['equal']))) for w in ids},
              'seeds_better_than_equal': {w: int(sum(a < b - 1e-9 for a, b in zip(table[w], table['equal']))) for w in ids},
              'rank_spearman_between_seeds': {'mean': float(np.mean(pair)), 'min': float(np.min(pair)), 'max': float(np.max(pair)), 'pairs': len(pair)},
              'between_weight_sd_within_seed_mean': float(np.mean([np.std(r, ddof=1) for r in ranks])),
              'equal_sd_between_seeds': float(np.std(table['equal'], ddof=1)),
              'cross_seed_selection': transfer, 'per_outer_selection_on_fresh_seed': per_outer_select,
              'test_accessed': False, 'confirmatory_seeds_used': False}
    (OUT / 'followup.json').write_text(json.dumps(report, indent=2))
    print('gamma bracket (equal weights):')
    for g, t in gammas.items():
        print(f"  gamma {g:5s} D_F mean {t['mean']:.3f} sd {t['sd']:.3f}  <local {t['below_always_local']}/6  <greedy {t['below_greedy_eft']}/6")
    print('weights @ gamma 0.97:')
    for w in ids:
        print(f"  {w:8s} mean {report['D_F_mean_by_weight'][w]:.3f} sd {report['D_F_sd_by_weight'][w]:.3f}  diff vs equal {report['paired_diff_vs_equal_mean'][w]:+.3f}  better {report['seeds_better_than_equal'][w]}/6")
    print('rank agreement between seeds', report['rank_spearman_between_seeds'])
    print('within-seed SD across weights', round(report['between_weight_sd_within_seed_mean'], 3), ' equal SD across seeds', round(report['equal_sd_between_seeds'], 3))
    print('cross-seed selection', json.dumps(transfer, indent=1))
    print('per-outer selection gain on fresh seed', [round(x['gain_on_fresh_seed_vs_equal'], 3) for x in per_outer_select])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, default=32)
    parser.add_argument('--worker', nargs=4)
    args = parser.parse_args()
    if args.worker:
        v, w, o, r = args.worker
        worker(v, w, int(o), int(r))
        return
    for variant in A.VARIANTS:
        A.spec_for(variant)
    tasks = [(v, 'equal', o, r) for v in ('gamma095', 'gamma098') for o, r in A.SEEDS]
    tasks += [('gamma097', w, o, r) for w in WEIGHTS if w != 'equal' for o, r in A.SEEDS]
    tasks = [t for t in tasks if not (run_dir(*t) / 'result.json').exists()]
    running, started = [], time.monotonic()
    while tasks or running:
        still = []
        for p, t in running:
            if p.poll() is None:
                still.append((p, t))
            elif p.returncode != 0:
                print('FAILED', t, 'exit', p.returncode, flush=True)
        running = still
        while tasks and len(running) < args.workers:
            t = tasks.pop(0)
            log = open(OUT / 'runs' / ('_'.join(map(str, t)) + '.log'), 'w')
            running.append((subprocess.Popen([sys.executable, __file__, '--worker', *map(str, t)], stdout=log, stderr=subprocess.STDOUT), t))
        time.sleep(2)
    print('finished in', round(time.monotonic() - started), 's', flush=True)
    aggregate()


if __name__ == '__main__':
    main()
