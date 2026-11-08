"""P10 learning-stability diagnosis: one-factor PPO ablations on the PILOT namespace (outer 100-102 x repeat 0/1).

No confirmatory seed (outer 0-19), no validation split used by the search, and no test trace is touched. The simulator config
is unchanged; only the learner (PPO) config differs, recorded per run as learner_spec.json / effective_learner_config.json
under protocol 'P10-stability-diagnosis-1'. Locked source files are not modified: the accepted protocol is registered here.
    PYTHONPATH=. venv/bin/python results/research_v2/P10_learning_diagnosis/run_ablation.py [--workers 12]
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

from research_v2 import learning
from research_v2.config import load_config, read_json, require, sha256, validate_config  # noqa: F401

OUT = Path(__file__).resolve().parent
JDK = Path('/usr/lib/jvm/java-21-openjdk-amd64')
F = 102400
CHECKPOINTS = [51200, F]
PROTOCOL = 'P10-stability-diagnosis-1'
VARIANTS = {'base': {}, 'gamma099': {'gamma': 0.99}, 'gamma097': {'gamma': 0.97}, 'ent003': {'ent_coef': 0.03},
            'rollout2048': {'n_steps': 2048, 'batch_size': 512}, 'lr1e4': {'learning_rate': 1e-4}}
ALLOWED = {'gamma', 'ent_coef', 'n_steps', 'batch_size', 'learning_rate'}
SEEDS = [(o, r) for o in (100, 101, 102) for r in (0, 1)]
ACTIONS = ['source_iot', 'F1', 'F2', 'F3', 'F4', 'F5', 'cloud']


def effective_learner(config, spec_path=None):
    """Diagnostic registration of PROTOCOL; everything else falls back to the locked implementation."""
    if spec_path is None:
        return copy.deepcopy(config), None
    spec = read_json(spec_path)
    if spec['protocol'] != PROTOCOL:
        return ORIGINAL(config, spec_path)
    require(spec['simulation_config_sha256'] == sha256(config), 'Simulation config drift')
    require(set(spec['overrides']) <= ALLOWED, 'Override outside the registered diagnostic factors')
    # Schema-validate everything except the overridden learner keys (the v0.2 schema fixes e.g. gamma = 1.0, so a gamma
    # ablation is a protocol deviation by definition; it is recorded in the spec, never written back to the config).
    validate_config(config)
    bounds = {'gamma': (0.9, 1.0), 'ent_coef': (0.0, 0.1), 'learning_rate': (1e-5, 1e-3), 'n_steps': (128, 8192), 'batch_size': (32, 2048)}
    for key, value in spec['overrides'].items():
        low, high = bounds[key]
        require(low <= value <= high, f'Diagnostic override {key}={value} out of bounds')
    effective = copy.deepcopy(config)
    effective['ppo'].update(spec['overrides'])
    require(effective['ppo']['n_steps'] % effective['ppo']['batch_size'] == 0, 'batch must divide rollout')
    require(spec['ppo'] == effective['ppo'] and spec['effective_config_sha256'] == sha256(effective), 'Effective learner mismatch')
    return effective, spec


ORIGINAL = learning.effective_learner


def spec_for(variant):
    config = load_config()
    effective = copy.deepcopy(config)
    effective['ppo'].update(VARIANTS[variant])
    path = OUT / 'specs' / f'{variant}.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({'protocol': PROTOCOL, 'variant': variant, 'overrides': VARIANTS[variant],
                                'schema_exception': 'diagnostic only: overridden learner keys are outside the v0.2 schema contract',
                                'simulation_config_sha256': sha256(config), 'ppo': effective['ppo'],
                                'effective_config_sha256': sha256(effective)}, indent=2))
    return path


def heuristics():
    """Deterministic references on the same 20 pilot_validation traces."""
    from research_v2 import baselines
    from research_v2.gym_env import OffloadingEnv
    from research_v2.trace_access import TraceKey
    from research_v2.traces import TraceGenerator
    config = load_config()
    out = {}
    policies = {'always_local': baselines.always_local, 'always_cloud': lambda s: 6,
                'greedy_eft': baselines.greedy_eft, 'least_fog': baselines.least_fog}
    for name, choose in policies.items():
        generator, holder, rows = TraceGenerator(config), {}, []
        env = OffloadingEnv(lambda seed, index: holder['trace'], [0.2] * 5, config=config, jdk_home=JDK, any_port=True, validate=False)
        try:
            for workload in config['training']['workload_order']:
                low, high = config['seeds']['validation_trace_ids']
                for trace_id in range(low, high + 1):
                    key = TraceKey(config['seeds']['master'], 'pilot_validation', None, None, trace_id, workload)
                    holder['trace'] = generator.generate(key, role='pilot_validator').to_dict()
                    _, info = env.reset(seed=0)
                    while True:
                        _, _, done, _, info = env.step(int(choose(info['raw_snapshot'])))
                        if done:
                            break
                    rows.append({'namespace': key.to_dict(), 'metrics': info['summary']['metrics']})
        finally:
            env.close()
        s = learning.aggregate_costs(rows, config['training']['workload_order'])
        out[name] = {'D_macro': s['D_macro'], 'linear': float(np.mean(s['macro_costs'])), 'macro_costs': s['macro_costs']}
    (OUT / 'heuristics_pilot_validation.json').write_text(json.dumps(out, indent=2))


def worker(variant, outer, repeat):
    from research_v2.study_worker import compress_decision_logs
    learning.effective_learner = effective_learner
    directory = OUT / 'runs' / f'{variant}_o{outer}r{repeat}'
    started = time.monotonic()
    learning.run_training(directory / 'train', outer, repeat, F, [0.2] * 5, JDK, learner_spec=OUT / 'specs' / f'{variant}.json',
                          training_split='pilot_train', phase='P07', checkpoint_at=CHECKPOINTS, fast_rpc=True)
    result = {'variant': variant, 'outer': outer, 'repeat': repeat}
    for n, mode in ((51200, True), (F, True), (F, False)):
        label = f'{n}_{"det" if mode else "sampled"}'
        target = directory / f'eval_{label}'
        learning.run_evaluation(directory / 'train' / f'checkpoint_{n:08d}', target, JDK, deterministic=mode,
                                split='pilot_validation', fast_rpc=True)
        s = json.loads((target / 'summary.json').read_text())
        rows = [json.loads(l) for l in (target / 'episodes.jsonl').read_text().splitlines()]
        counts = np.sum([r['action_counts'] for r in rows], axis=0)
        result[label] = {'D_macro': s['D_macro'], 'linear': float(np.mean(s['macro_costs'])), 'macro_costs': s['macro_costs'],
                         'top_action_share': float(counts.max() / counts.sum()), 'top_action': ACTIONS[int(counts.argmax())]}
    curve = [json.loads(l) for l in (directory / 'train' / 'learning_curve.jsonl').read_text().splitlines()]
    result['entropy_last'] = -curve[-1]['train/entropy_loss']
    eps = [json.loads(l) for l in (directory / 'train' / 'episodes.jsonl').read_text().splitlines()]
    def macro(subset):
        by = {}
        for e in subset:
            by.setdefault(e['namespace']['workload'], []).append(np.mean(list(e['metrics']['costs'].values())))
        return float(np.mean([np.mean(v) for v in by.values()]))
    q = max(1, len(eps) // 4)
    result['onpolicy_linear_first_quarter'], result['onpolicy_linear_last_quarter'] = macro(eps[:q]), macro(eps[-q:])
    result['episodes'] = len(eps)
    compress_decision_logs(directory)
    result['wall_s'] = time.monotonic() - started
    (directory / 'result.json').write_text(json.dumps(result, indent=2))


def aggregate():
    ref = json.loads((OUT / 'heuristics_pilot_validation.json').read_text())
    local = ref['always_local']['D_macro']
    table = {}
    for variant in VARIANTS:
        rows = [json.loads((OUT / 'runs' / f'{variant}_o{o}r{r}' / 'result.json').read_text()) for o, r in SEEDS]
        get = lambda key, sub='D_macro': np.array([x[key][sub] for x in rows])
        table[variant] = {
            'D_F_det': get(f'{F}_det').tolist(), 'D_F_det_mean': float(get(f'{F}_det').mean()), 'D_F_det_sd': float(get(f'{F}_det').std(ddof=1)),
            'D_51200_det_mean': float(get('51200_det').mean()),
            'D_F_sampled_mean': float(get(f'{F}_sampled').mean()),
            'linear_F_det_mean': float(get(f'{F}_det', 'linear').mean()),
            'seeds_better_than_always_local': int((get(f'{F}_det') < local).sum()),
            'collapsed_seeds_F': int(sum(x[f'{F}_det']['top_action_share'] >= 0.98 for x in rows)),
            'entropy_last_mean': float(np.mean([x['entropy_last'] for x in rows])),
            'onpolicy_linear_first_to_last': [float(np.mean([x['onpolicy_linear_first_quarter'] for x in rows])),
                                              float(np.mean([x['onpolicy_linear_last_quarter'] for x in rows]))]}
    base = np.array(table['base']['D_F_det'])
    for variant in VARIANTS:
        diff = np.array(table[variant]['D_F_det']) - base
        table[variant]['paired_diff_vs_base'] = diff.tolist()
        table[variant]['seeds_improved_vs_base'] = int((diff < -1e-9).sum())
    report = {'protocol': PROTOCOL, 'namespace': 'pilot_train / pilot_validation', 'seeds': SEEDS, 'F': F,
              'heuristics': ref, 'variants': table, 'test_accessed': False, 'confirmatory_seeds_used': False}
    (OUT / 'ablation.json').write_text(json.dumps(report, indent=2))
    print(f"heuristics: " + ', '.join(f"{k} D={v['D_macro']:.3f} lin={v['linear']:.3f}" for k, v in ref.items()))
    print(f"{'variant':12s} {'D_F mean':>8s} {'sd':>6s} {'D_51k':>6s} {'D_samp':>6s} {'lin':>6s} {'>local':>6s} {'collapse':>8s} {'ent':>5s} {'improved':>8s}  onpolicy")
    for v, t in table.items():
        print(f"{v:12s} {t['D_F_det_mean']:8.3f} {t['D_F_det_sd']:6.3f} {t['D_51200_det_mean']:6.3f} {t['D_F_sampled_mean']:6.3f} "
              f"{t['linear_F_det_mean']:6.3f} {t['seeds_better_than_always_local']:4d}/6 {t['collapsed_seeds_F']:6d}/6 {t['entropy_last_mean']:5.2f} "
              f"{t['seeds_improved_vs_base']:6d}/6  {t['onpolicy_linear_first_to_last'][0]:.3f}->{t['onpolicy_linear_first_to_last'][1]:.3f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, default=12)
    parser.add_argument('--worker', nargs=3)
    parser.add_argument('--heuristics', action='store_true')
    args = parser.parse_args()
    if args.worker:
        worker(args.worker[0], int(args.worker[1]), int(args.worker[2]))
        return
    if args.heuristics:
        heuristics()
        return
    (OUT / 'runs').mkdir(exist_ok=True)
    for variant in VARIANTS:
        spec_for(variant)
    tasks = [('heuristics',)] if not (OUT / 'heuristics_pilot_validation.json').exists() else []
    tasks += [(v, o, r) for v in VARIANTS for o, r in SEEDS if not (OUT / 'runs' / f'{v}_o{o}r{r}' / 'result.json').exists()]
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
            name = '_'.join(map(str, t))
            log = open(OUT / 'runs' / f'{name}.log', 'w')
            cmd = [sys.executable, __file__, '--heuristics'] if t[0] == 'heuristics' else [sys.executable, __file__, '--worker', *map(str, t)]
            running.append((subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT), t))
        time.sleep(2)
    print('finished in', round(time.monotonic() - started), 's', flush=True)
    aggregate()


if __name__ == '__main__':
    main()
