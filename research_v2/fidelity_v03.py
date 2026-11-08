"""Protocol v0.3 fidelity gate: re-select the candidate budget K with the v0.3 learner (gamma 0.97). Pilot namespace only.

Registered before any v0.3 run (8 November 2026); changing anything below requires a new protocol version:
- Models: pilot outers 100/101/102 x repeats 0/1 x the 8 registered pilot weights = 48 models, learner v0.3, each trained once to
  R = 102,400 decisions with checkpoints on the ladder (prefix checkpoints; prefix equivalence is re-checked on 3 independent models).
- Ladder K: 10,240 -> 20,480 -> 30,720 -> 51,200. Reference R = 102,400 = the final budget F (v0.2 used 51,200; under v0.3
  learning still changes between 51,200 and 102,400, and the purpose of the gate is to predict final-budget quality).
- Per outer run: mean of the two repeats' macro cost vectors per weight, D = RMS of that mean vector; ranking of the 8 weights
  at K versus at R; Spearman correlation with average ranks for ties.
- Gate (thresholds unchanged from v0.2, config `pilot`): median of the 3 correlations >= 0.60 and none < 0.0; the smallest
  passing K is selected. An undefined short ranking fails at that K; a constant reference ranking stops the gate as uninformative.
- If no K passes: status `fidelity_failed_stop`; no ladder extension inside this protocol.
- Reported, never gated: agreement between independent seeds at R (repeat-0 vs repeat-1 ranking per outer run). The same pilot
  seeds were used in the P10 diagnosis, so this value is descriptive, not a fresh test.
Evaluation is deterministic on the 20 pilot_validation traces. No confirmatory seed, search validation split or test trace is used.

    PYTHONPATH=. venv/bin/python -m research_v2.fidelity_v03 run --output-dir results/research_v2/v0.3/fidelity --workers 12
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from scipy.stats import spearmanr

from .config import ROOT, load_config, read_json, require, sha256
from .learner import effective_learner
from .learning import (COSTS, compare_checkpoints, file_hash, provenance, run_evaluation, run_training, write_json)
from .search import pilot_weights

PROTOCOL = 'P10-fidelity-v0.3'
LEARNER = '0.3'
OUTERS = (100, 101, 102)
REPEATS = (0, 1)
LADDER = (10240, 20480, 30720, 51200)
REFERENCE = 102400
PREFIX_CHECK_K = 10240
CRITICAL = ('research_v2/learning.py', 'research_v2/learner.py', 'research_v2/search.py', 'research_v2/search_runner.py',
            'research_v2/gym_env.py', 'research_v2/rpc_client.py', 'research_v2/traces.py', 'research_v2/fidelity_v03.py',
            'configs/research_v2/learner_v0.3.json')
JDK = Path('/usr/lib/jvm/java-21-openjdk-amd64')


def weights():
    return {w['id']: w['weights'] for w in pilot_weights(load_config())}


def model_dir(root, weight, outer, repeat):
    return Path(root) / 'models' / f'{weight}_o{outer}r{repeat}'


def protocol(config):
    _, meta = effective_learner(config, LEARNER)
    return {'version': PROTOCOL, 'learner': meta, 'outers': list(OUTERS), 'repeats': list(REPEATS), 'weights': weights(),
            'ladder': list(LADDER), 'reference_decisions': REFERENCE, 'prefix_check_K': PREFIX_CHECK_K,
            'gate': {'minimum_median_spearman': config['pilot']['minimum_median_spearman'],
                     'minimum_spearman': config['pilot']['minimum_spearman'], 'select': 'smallest passing K',
                     'ties': 'average ranks', 'aggregation': 'mean of the two repeats cost vectors per weight, then RMS'},
            'config_sha256': sha256(config),
            'jar_sha256': read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256'],
            'source_hashes': {name: file_hash(ROOT / name) for name in CRITICAL},
            'predecessor': {'version': 'P08-fidelity-extension-1', 'selected_K': 30720, 'learner': '0.2',
                            'status': 'superseded: selected with the gamma 1.0 learner'},
            'test_accessed': False}


def train_worker(root, weight, outer, repeat):
    from .study_worker import compress_decision_logs
    directory = model_dir(root, weight, outer, repeat)
    run_training(directory / 'train', outer, repeat, REFERENCE, weights()[weight], JDK, training_split='pilot_train', phase='P10',
                 checkpoint_at=[*LADDER, REFERENCE], fast_rpc=True, learner_version=LEARNER)
    for n in (*LADDER, REFERENCE):
        run_evaluation(directory / 'train' / f'checkpoint_{n:08d}', directory / f'eval_{n:08d}', JDK, deterministic=True,
                       split='pilot_validation', fast_rpc=True)
    compress_decision_logs(directory)
    write_json(directory / 'done.json', {'status': 'complete'})


def prefix_worker(root, outer):
    from .study_worker import compress_decision_logs
    directory = Path(root) / 'prefix' / f'equal_o{outer}r0'
    run_training(directory, outer, 0, PREFIX_CHECK_K, weights()['equal'], JDK, training_split='pilot_train', phase='P10',
                 checkpoint_at=[PREFIX_CHECK_K], fast_rpc=True, learner_version=LEARNER)
    result = compare_checkpoints(directory / f'checkpoint_{PREFIX_CHECK_K:08d}',
                                 model_dir(root, 'equal', outer, 0) / 'train' / f'checkpoint_{PREFIX_CHECK_K:08d}')
    compress_decision_logs(directory)
    write_json(directory.parent / f'equal_o{outer}r0.json', result)


def macro_costs(eval_dir):
    return read_json(Path(eval_dir) / 'summary.json')['macro_costs']


def rms(vector):
    return float(np.sqrt(np.mean(np.square(vector))))


def rank_correlation(a, b):
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return None
    return float(spearmanr(a, b).statistic)


def analyse(root, cost_reader=macro_costs):
    """Pure function of the evaluation summaries, so the audit can recompute it from raw episode rows."""
    config = load_config()
    ids = list(weights())
    D = {}
    for n in (*LADDER, REFERENCE):
        for outer in OUTERS:
            D[(n, outer)] = [rms(np.mean([cost_reader(model_dir(root, w, outer, r) / f'eval_{n:08d}') for r in REPEATS], axis=0))
                             for w in ids]
    ladder = []
    selected = None
    stop = None
    for n in LADDER:
        rho = []
        for outer in OUTERS:
            if np.ptp(D[(REFERENCE, outer)]) == 0:
                stop = f'constant reference ranking on outer {outer}'
            rho.append(rank_correlation(D[(n, outer)], D[(REFERENCE, outer)]))
        defined = all(x is not None for x in rho)
        passed = (stop is None and defined and float(np.median(rho)) >= config['pilot']['minimum_median_spearman']
                  and min(rho) >= config['pilot']['minimum_spearman'])
        ladder.append({'K': n, 'spearman_by_outer': dict(zip(map(str, OUTERS), rho)),
                       'median': float(np.median(rho)) if defined else None, 'minimum': min(rho) if defined else None,
                       'pass': bool(passed)})
        if passed and selected is None:
            selected = n
    cross = {}
    for outer in OUTERS:
        per_repeat = [[rms(cost_reader(model_dir(root, w, outer, r) / f'eval_{REFERENCE:08d}')) for w in ids] for r in REPEATS]
        cross[str(outer)] = rank_correlation(*per_repeat)
    status = 'fidelity_stopped_uninformative' if stop else ('fidelity_passed' if selected else 'fidelity_failed_stop')
    return {'version': PROTOCOL, 'status': status, 'selected_K': selected, 'ladder': ladder, 'stop_reason': stop,
            'weights_order': ids, 'D_by_budget_and_outer': {f'{n}:{o}': v for (n, o), v in D.items()},
            'cross_seed_spearman_at_reference': cross,
            'cross_seed_note': 'descriptive only; these pilot seeds were already seen in the P10 diagnosis',
            'test_accessed': False}


def episode_costs(eval_dir):
    """Independent recomputation for the audit: raw episode rows -> per-workload means -> macro vector."""
    rows = [json.loads(l) for l in (Path(eval_dir) / 'episodes.jsonl').read_text().splitlines() if l.strip()]
    order = load_config()['training']['workload_order']
    require(len(rows) == 20 and sorted({r['namespace']['workload'] for r in rows}) == sorted(order), 'Incomplete evaluation')
    by = {w: [[r['metrics']['costs'][c] for c in COSTS] for r in rows if r['namespace']['workload'] == w] for w in order}
    return np.mean([np.mean(v, axis=0) for v in by.values()], axis=0).tolist()


def audit(root):
    root = Path(root)
    result = read_json(root / 'result.json')
    again = analyse(root, cost_reader=episode_costs)
    prefix = [read_json(p) for p in sorted((root / 'prefix').glob('equal_o*r0.json'))]
    complete = all((model_dir(root, w, o, r) / 'done.json').exists() for w in weights() for o in OUTERS for r in REPEATS)
    rounded = lambda ladder: [[None if x is None else round(x, 10) for x in step['spearman_by_outer'].values()] for step in ladder]
    same = (again['status'] == result['status'] and again['selected_K'] == result['selected_K'] and
            rounded(again['ladder']) == rounded(result['ladder']))
    report = {'version': PROTOCOL, 'status': 'pass' if same and complete and len(prefix) == 3 and all(p['pass'] for p in prefix) else 'fail',
              'recomputed_from_episode_rows': same, 'all_48_models_complete': complete,
              'independent_prefix_checks': len(prefix), 'prefix_checks_pass': [p['pass'] for p in prefix],
              'selected_K': result['selected_K'], 'result_sha256': file_hash(root / 'result.json')}
    write_json(root / 'audit.json', report)
    return report


def require_v03_gate(path):
    path = Path(path)
    p, result, a = read_json(path / 'protocol.json'), read_json(path / 'result.json'), read_json(path / 'audit.json')
    config = load_config()
    require(p['version'] == PROTOCOL and result['status'] == 'fidelity_passed' and result['selected_K'] in LADDER,
            'v0.3 fidelity gate did not pass')
    require(a['status'] == 'pass' and a['selected_K'] == result['selected_K'] and a['result_sha256'] == file_hash(path / 'result.json'),
            'v0.3 fidelity audit missing, failed or stale')
    require(p['config_sha256'] == sha256(config), 'Config changed after the v0.3 gate')
    require(p['jar_sha256'] == read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256'], 'JAR changed after the v0.3 gate')
    for name, digest in p['source_hashes'].items():
        require(file_hash(ROOT / name) == digest, f'Source changed after the v0.3 gate: {name}')
    return result['selected_K']


def require_fidelity_gate(path):
    """(K, learner_version) for any registered fidelity evidence."""
    version = read_json(Path(path) / 'protocol.json')['version']
    if version == PROTOCOL:
        return require_v03_gate(path), LEARNER
    from .search_runner_extension import require_extension_gate
    return require_extension_gate(path), '0.2'


def run(root, workers):
    root = Path(root)
    config = load_config()
    plan = protocol(config)
    if (root / 'protocol.json').exists():
        require(read_json(root / 'protocol.json') == plan, 'Existing v0.3 fidelity directory was planned differently')
    else:
        root.mkdir(parents=True, exist_ok=False)
        write_json(root / 'protocol.json', plan)
        write_json(root / 'provenance.json', provenance(config))
    tasks = [('train', w, str(o), str(r)) for o in OUTERS for r in REPEATS for w in plan['weights']
             if not (model_dir(root, w, o, r) / 'done.json').exists()]
    started = time.monotonic()
    execute(root, tasks, workers)
    execute(root, [('prefix', str(o)) for o in OUTERS if not (root / 'prefix' / f'equal_o{o}r0.json').exists()], workers)
    result = analyse(root)
    result['wall_s'] = time.monotonic() - started
    write_json(root / 'result.json', result)
    report = audit(root)
    print(json.dumps({'status': result['status'], 'selected_K': result['selected_K'],
                      'ladder': [(x['K'], x['median'], x['minimum'], x['pass']) for x in result['ladder']],
                      'cross_seed_at_reference': result['cross_seed_spearman_at_reference'], 'audit': report['status']}, indent=1))


def execute(root, tasks, workers):
    (Path(root) / 'logs').mkdir(parents=True, exist_ok=True)
    running = []
    while tasks or running:
        still = []
        for process, task in running:
            if process.poll() is None:
                still.append((process, task))
            else:
                require(process.returncode == 0, f'v0.3 fidelity task {task} failed with exit {process.returncode}')
        running = still
        while tasks and len(running) < workers:
            task = tasks.pop(0)
            log = open(Path(root) / 'logs' / ('_'.join(task) + '.log'), 'w')
            command = [sys.executable, '-m', 'research_v2.fidelity_v03', 'task', '--output-dir', str(root), *task]
            running.append((subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT), task))
        time.sleep(2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    r = sub.add_parser('run')
    r.add_argument('--output-dir', type=Path, required=True)
    r.add_argument('--workers', type=int, default=12)
    t = sub.add_parser('task')
    t.add_argument('--output-dir', type=Path, required=True)
    t.add_argument('task', nargs='+')
    a = sub.add_parser('audit')
    a.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'run':
        run(args.output_dir.resolve(), args.workers)
    elif args.command == 'audit':
        print(json.dumps(audit(args.output_dir.resolve()), indent=1))
    elif args.task[0] == 'train':
        train_worker(args.output_dir, args.task[1], int(args.task[2]), int(args.task[3]))
    else:
        prefix_worker(args.output_dir, int(args.task[1]))


if __name__ == '__main__':
    main()
