"""P11 evaluation of every trained model and the heuristics, then the registered P10 analysis.

split='test' is the real confirmatory evaluation: it requires a verified protocol lock, unseals the test split through
trace_access.unseal_test(lock) in every worker process, and records results/research_v2/TEST_OPENED.json before the first
episode. split='validation' runs the identical code on the validation traces (dry run; the test split stays sealed).
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

from .config import ROOT, load_config, read_json, require, sha256
from .learning import COSTS, append_json, file_hash, write_json

JDK = Path('/usr/lib/jvm/java-21-openjdk-amd64')
SPLITS = {'test': ('test_trace_ids', 'test_evaluator'), 'validation': ('validation_trace_ids', 'search_validator')}
HEURISTICS = ('always_local', 'nearest_fog', 'least_fog', 'greedy_eft')
PPO_LABELS = ('nsga2', 'random', 'equal_F', 'equal_B', 'manual_F', 'manual_B')
FIXTURE = {'nsga2': ('mini_final', 'F'), 'random': ('manual', 'F'), 'equal_F': ('equal', 'F'), 'equal_B': ('equal', 'B'),
           'manual_F': ('manual', 'F'), 'manual_B': ('manual', 'B')}
FULL = {'nsga2': ('nsga2_final', 'F'), 'random': ('random_final', 'F'), 'equal_F': ('equal', 'F'), 'equal_B': ('equal', 'B'),
        'manual_F': ('manual', 'F'), 'manual_B': ('manual', 'B')}
TEST_OPENED = ROOT / 'results/research_v2/TEST_OPENED.json'


def model_table(studies):
    """{(label, outer): checkpoint dir} from completed, re-verified study jobs."""
    from .study_runner import verify_complete, verify_plan
    out = {}
    for study in map(Path, studies):
        plan = verify_plan(study)
        mapping = FIXTURE if plan['fixture_only'] else FULL
        jobs = {j['id']: j for j in plan['jobs']}
        for outer in plan['outers']:
            for label, (suffix, budget) in mapping.items():
                job = jobs[f'r{outer:02d}_{suffix}']
                require(verify_complete(study, job, plan), f'Job {job["id"]} in {study} is not complete')
                attempt = study / read_json(study / 'jobs' / job['id'] / 'complete.json')['attempt']
                n = plan['budget']['F'] if budget == 'F' else plan['budget']['B']
                out[(label, outer)] = attempt / 'data' / 'training' / f'checkpoint_{n:08d}'
    return out


def evaluate(policy, weights, out_file, split, jdk_home=JDK):
    """policy(obs, raw_snapshot) -> action. Complete episodes on every trace of the split, deterministic."""
    from .gym_env import OffloadingEnv
    from .trace_access import TraceKey
    from .traces import TraceGenerator
    config = load_config()
    ids, role = SPLITS[split]
    generator = TraceGenerator(config)
    holder = {}
    env = OffloadingEnv(lambda seed, index: holder['trace'], weights, config=config, jdk_home=jdk_home, any_port=True, validate=False)
    temporary = Path(str(out_file) + '.partial')
    temporary.unlink(missing_ok=True)
    try:
        low, high = config['seeds'][ids]
        for workload in config['training']['workload_order']:
            for trace_id in range(low, high + 1):
                key = TraceKey(config['seeds']['master'], split, None, None, trace_id, workload)
                trace = generator.generate(key, role=role).to_dict()
                holder['trace'] = trace
                obs, info = env.reset(seed=0)
                steps, reward_sum, actions = 0, 0.0, np.zeros(7, dtype=np.int64)
                while True:
                    action = int(policy(obs, info['raw_snapshot']))
                    obs, reward, done, truncated, info = env.step(action)
                    require(not truncated, 'Evaluation episode truncated')
                    steps, reward_sum = steps + 1, reward_sum + reward
                    actions[action] += 1
                    if done:
                        break
                metrics = info['summary']['metrics']
                z = [metrics['costs'][c] for c in COSTS]
                require(steps == trace['task_count'], 'Evaluation did not finish the trace')
                require(np.isclose(reward_sum, -100 * np.dot(weights, z), rtol=1e-6, atol=1e-8), 'Reward identity failed')
                require(not metrics['diagnosis_required'], 'Out-of-reference costs: stop for diagnosis')
                append_json(temporary, {'namespace': key.to_dict(), 'trace_sha256': trace['payload_sha256'], 'decisions': steps,
                                        'reward': reward_sum, 'action_counts': actions.tolist(), 'metrics': metrics})
    finally:
        env.close()
    temporary.replace(out_file)


def task(out, split, lock, label, outer, checkpoint):
    from . import trace_access
    if split == 'test':
        trace_access.unseal_test(lock)
    target = Path(out) / 'episodes' / f'{label}_r{outer:02d}.jsonl'
    if label in HEURISTICS:
        from . import baselines
        choose = getattr(baselines, label)
        evaluate(lambda obs, snap: choose(snap), [0.2] * 5, target, split)
        return
    from stable_baselines3 import PPO
    from .gym_env import check_policy_interface
    from .learning import setup_torch
    checkpoint = Path(checkpoint)
    state = read_json(checkpoint / 'state.json')
    require(state['model_sha256'] == file_hash(checkpoint / 'model.zip'), 'Checkpoint hash mismatch')
    manifest = read_json(checkpoint.parent / 'manifest.json')
    require(manifest['config_sha256'] == sha256(load_config()), 'Checkpoint was trained under another simulation config')
    setup_torch(load_config())
    model = PPO.load(checkpoint / 'model.zip', device='cpu')
    check_policy_interface(model.observation_space.shape[0], model.action_space.n)
    evaluate(lambda obs, snap: model.predict(obs, deterministic=True)[0], manifest['weights'], target, split)


def run(out, studies, split, lock=None, workers=12):
    out = Path(out)
    (out / 'episodes').mkdir(parents=True, exist_ok=True)
    (out / 'logs').mkdir(exist_ok=True)
    models = model_table(studies)
    outers = sorted({o for _, o in models})
    if split == 'test':
        from .analysis.lock import require_valid_lock
        locked = require_valid_lock(lock, deep=True)
        if not TEST_OPENED.exists():
            write_json(TEST_OPENED, {'opened_utc': datetime.now(timezone.utc).isoformat(), 'lock': str(Path(lock).resolve()),
                                     'lock_sha256': locked['lock_sha256'], 'protocol_version': locked.get('protocol_version'),
                                     'models': len(models), 'outers': outers,
                                     'rule': 'Findings on test are recorded and never used to retune this study.'})
    tasks = [(label, outer, str(path)) for (label, outer), path in sorted(models.items())]
    tasks += [(h, 0, '') for h in HEURISTICS]
    tasks = [t for t in tasks if not (out / 'episodes' / f'{t[0]}_r{t[1]:02d}.jsonl').exists()]
    running = []
    while tasks or running:
        still = []
        for process, t in running:
            if process.poll() is None:
                still.append((process, t))
            else:
                require(process.returncode == 0, f'Evaluation task {t[:2]} failed (exit {process.returncode}); see logs')
        running = still
        while tasks and len(running) < workers:
            t = tasks.pop(0)
            log = open(out / 'logs' / f'{t[0]}_r{t[1]:02d}.log', 'w')
            command = [sys.executable, '-m', 'research_v2.p11_eval', 'task', '--output-dir', str(out), '--split', split,
                       '--label', t[0], '--outer', str(t[1]), '--checkpoint', t[2]] + (['--lock', str(lock)] if lock else [])
            running.append((subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT), t))
        time.sleep(2)
    return analyse(out, studies, split, outers)


def analyse(out, studies, split, outers):
    from .analysis.loader import compute_cost, read_rows, rows_to_table
    from .analysis.report import build_report, render
    config = load_config()
    out = Path(out)
    cells = {}
    for label in (*PPO_LABELS, *HEURISTICS):
        for outer in outers:
            source = out / 'episodes' / f'{label}_r{(0 if label in HEURISTICS else outer):02d}.jsonl'
            cells[(label, outer)] = read_rows(source)      # heuristics are seed-free: one evaluation reused per outer run
    table = rows_to_table(cells, config, allowed_splits=(split,))
    confirmatory = split == 'test' and outers == list(range(config['seeds']['outer_runs']))
    exploratory = [('manual_F', 'equal_F'), ('manual_B', 'equal_B'), *[(h, 'nsga2') for h in HEURISTICS]]
    compute = [row for study in studies for row in compute_cost(Path(study), read_json(Path(study) / 'protocol.json')['outers'])]
    report = build_report(table, config, expected_outers=outers, exploratory_pairs=exploratory, compute=compute)
    report.update(split=split, confirmatory=confirmatory, test_accessed=split == 'test', studies=[str(s) for s in studies])
    write_json(out / 'report.json', report)
    note = None if confirmatory else ('DRY RUN on the validation split (fixture/mini studies); not study evidence.'
                                      if split == 'validation' else 'Incomplete outer-run set: not the registered analysis.')
    (out / 'report.md').write_text(render(report, fixture_note=note))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    r = sub.add_parser('run')
    r.add_argument('--output-dir', type=Path, required=True)
    r.add_argument('--studies', type=Path, nargs='+', required=True)
    r.add_argument('--split', choices=tuple(SPLITS), required=True)
    r.add_argument('--lock', type=Path)
    r.add_argument('--workers', type=int, default=12)
    t = sub.add_parser('task')
    t.add_argument('--output-dir', type=Path, required=True)
    t.add_argument('--split', choices=tuple(SPLITS), required=True)
    t.add_argument('--label', required=True)
    t.add_argument('--outer', type=int, required=True)
    t.add_argument('--checkpoint', default='')
    t.add_argument('--lock', type=Path)
    args = parser.parse_args()
    if args.command == 'run':
        require(args.split != 'test' or args.lock, 'Test evaluation needs --lock')
        report = run(args.output_dir, args.studies, args.split, args.lock, args.workers)
        print(json.dumps([(x['id'], x['mean_difference'], x['raw_p_exact_signflip'], x['holm_adjusted_p']) for x in report['primary']]))
    else:
        task(args.output_dir, args.split, args.lock, args.label, args.outer, args.checkpoint)


if __name__ == '__main__':
    main()
