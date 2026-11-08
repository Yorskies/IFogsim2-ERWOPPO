"""Pre-flight learning check (validation namespace only; the test split is never touched).

Trains PPO-Equal for outer run 0 at the frozen final budget F=102,400 (identical to the confirmatory equal_F computation, which
is the F-checkpoint of the longer B run), evaluates four checkpoints on the 20 validation traces, and compares them with the
deterministic heuristics and a uniform-random policy on the same traces. Run from the repo root:
    PYTHONPATH=. venv/bin/python results/research_v2/P10_learning_check/run_check.py
"""
import json
from pathlib import Path
import time

import numpy as np

from research_v2 import baselines
from research_v2.config import load_config, require
from research_v2.learning import aggregate_costs, write_json, COSTS
from research_v2.study_final import TimedOffloadingEnv, run_final_training, run_final_validation
from research_v2.trace_access import TraceKey
from research_v2.traces import TraceGenerator

OUT = Path(__file__).resolve().parent
JDK = Path('/usr/lib/jvm/java-21-openjdk-amd64')
CHECKPOINTS = [2048, 10240, 51200, 102400]
ACTIONS = ['source_iot', 'F1', 'F2', 'F3', 'F4', 'F5', 'cloud']


def evaluate_policy(name, choose, config, weights):
    generator = TraceGenerator(config)
    holder = {}
    env = TimedOffloadingEnv(lambda seed, index: holder['trace'], weights, config=config, jdk_home=JDK, any_port=True, validate=False)
    rows, actions = [], np.zeros(7, dtype=np.int64)
    try:
        for workload in config['training']['workload_order']:
            low, high = config['seeds']['validation_trace_ids']
            for trace_id in range(low, high + 1):
                key = TraceKey(config['seeds']['master'], 'validation', None, None, trace_id, workload)
                holder['trace'] = generator.generate(key, role='search_validator').to_dict()
                obs, info = env.reset(seed=0)
                while True:
                    action = choose(info['raw_snapshot'])
                    actions[action] += 1
                    obs, reward, done, truncated, info = env.step(int(action))
                    require(not truncated, 'truncated')
                    if done:
                        break
                rows.append({'namespace': key.to_dict(), 'metrics': info['summary']['metrics']})
    finally:
        env.close()
    summary = aggregate_costs(rows, config['training']['workload_order'])
    summary['action_share'] = dict(zip(ACTIONS, (actions / actions.sum()).round(4).tolist()))
    return summary


def main():
    config = load_config()
    weights = config['search']['equal_weights']
    results = {}
    started = time.monotonic()
    train_dir = OUT / 'train_equal_F'
    if not train_dir.exists():
        run_final_training(train_dir, 0, 102400, weights, CHECKPOINTS, JDK)
    train_wall = time.monotonic() - started
    outcome = json.loads((train_dir / 'outcome.json').read_text())
    for n in CHECKPOINTS:
        target = OUT / f'validation_{n:08d}'
        if not target.exists():
            run_final_validation(train_dir / f'checkpoint_{n:08d}', target, JDK)
        s = json.loads((target / 'summary.json').read_text())
        rows = [json.loads(l) for l in (target / 'episodes.jsonl').read_text().splitlines()]
        counts = np.sum([r['action_counts'] for r in rows], axis=0)
        s['action_share'] = dict(zip(ACTIONS, (counts / counts.sum()).round(4).tolist()))
        results[f'ppo_equal_{n}'] = s
    rng = np.random.default_rng(0)
    heuristics = {'always_local': baselines.always_local, 'nearest_fog': baselines.nearest_fog,
                  'least_fog': baselines.least_fog, 'greedy_eft': baselines.greedy_eft,
                  'uniform_random': lambda snapshot: int(rng.integers(0, 7))}
    for name, fn in heuristics.items():
        results[name] = evaluate_policy(name, fn, config, weights)
    table = {k: {'D_macro': v['D_macro'], 'D_by_workload': v['D_by_workload'],
                 'macro_costs': dict(zip(COSTS, v['macro_costs'])), 'action_share': v['action_share']} for k, v in results.items()}
    report = {'split': 'validation', 'outer_run': 0, 'weights': weights, 'final_decisions': 102400,
              'training_wall_s': train_wall, 'gradient_updates': outcome['gradient_updates'], 'results': table,
              'test_accessed': False}
    write_json(OUT / 'check.json', report)
    for k, v in table.items():
        print(f'{k:18s} D={v["D_macro"]:.4f}  ' + ' '.join(f'{a}={s:.2f}' for a, s in v['action_share'].items()))


if __name__ == '__main__':
    main()
