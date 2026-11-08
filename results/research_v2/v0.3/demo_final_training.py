"""Exploratory look at v0.3 final training (learner gamma 0.97) at the real final budget. Validation only; test is never touched.

This is NOT P11: the v0.3 fidelity gate failed, so no confirmatory run exists under v0.3. Run from the repository root:
    PYTHONPATH=. venv/bin/python results/research_v2/v0.3/demo_final_training.py --outer 0 --weights equal
Progress while it trains:  tail -f <output-dir>/training/learning_curve.jsonl   (one line per PPO update, 200 lines in total)
"""
import argparse
import json
from pathlib import Path
import time

import numpy as np

from research_v2.config import load_config, require
from research_v2.search import pilot_weights
from research_v2.study_final import run_final_training, run_final_validation
from research_v2.study_worker import compress_decision_logs

HERE = Path(__file__).resolve().parent
JDK = Path('/usr/lib/jvm/java-21-openjdk-amd64')
REFERENCE = HERE.parent / 'P10_learning_check' / 'check.json'     # heuristics on the same 20 validation traces


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--outer', type=int, default=0, help='train_final namespace 0..19 (validation-only use here)')
    parser.add_argument('--weights', default='equal', help='equal, manual, vertex0..vertex4, simplex, or five comma-separated numbers')
    parser.add_argument('--decisions', type=int, default=102400)
    parser.add_argument('--checkpoints', default='10240,51200,102400')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    named = {w['id']: w['weights'] for w in pilot_weights(load_config())}
    weights = named[args.weights] if args.weights in named else [float(x) for x in args.weights.split(',')]
    require(len(weights) == 5, 'Five weights are required')
    checkpoints = sorted({int(x) for x in args.checkpoints.split(',')} | {args.decisions})
    out = (args.output_dir or HERE / 'demo_runs' / f'{args.weights}_r{args.outer:02d}_{time.strftime("%Y%m%dT%H%M%S")}').resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f'output: {out}\nweights: {weights}  learner: v0.3 (gamma 0.97)  decisions: {args.decisions:,}', flush=True)
    print(f'progress: tail -f "{out}/training/learning_curve.jsonl"', flush=True)
    started = time.monotonic()
    run_final_training(out / 'training', args.outer, args.decisions, weights, checkpoints, JDK, learner_version='0.3')
    print(f'training finished in {time.monotonic() - started:.0f} s; evaluating {len(checkpoints)} checkpoints on 20 validation traces', flush=True)
    rows = []
    for n in checkpoints:
        run_final_validation(out / 'training' / f'checkpoint_{n:08d}', out / f'validation_{n:08d}', JDK)
        s = json.loads((out / f'validation_{n:08d}' / 'summary.json').read_text())
        episodes = [json.loads(l) for l in (out / f'validation_{n:08d}' / 'episodes.jsonl').read_text().splitlines()]
        counts = np.sum([e['action_counts'] for e in episodes], axis=0)
        share = counts / counts.sum()
        rows.append({'decisions': n, 'D': s['D_macro'], 'local': share[0], 'fog': share[1:6].sum(), 'cloud': share[6]})
        print(f'  checkpoint {n:>7,}: D = {s["D_macro"]:.4f}   local {share[0]:.0%}  fog {share[1:6].sum():.0%}  cloud {share[6]:.0%}', flush=True)
    if REFERENCE.exists():
        ref = json.loads(REFERENCE.read_text())['results']
        print('  reference (same traces): ' + ', '.join(f'{k} D = {ref[k]["D_macro"]:.4f}' for k in ('greedy_eft', 'always_local', 'uniform_random')))
    compress_decision_logs(out)
    (out / 'demo_summary.json').write_text(json.dumps({'outer': args.outer, 'weights': weights, 'learner_version': '0.3',
                                                        'validation_only': True, 'test_accessed': False, 'checkpoints': rows,
                                                        'wall_s': time.monotonic() - started}, indent=2))
    print(f'done in {time.monotonic() - started:.0f} s -> {out}/demo_summary.json', flush=True)


if __name__ == '__main__':
    main()
