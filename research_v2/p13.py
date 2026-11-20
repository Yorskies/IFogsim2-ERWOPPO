"""P13: additional RL benchmark (DQN, tabular Q-Learning, DDPG vs PPO-Equal) — one command, resumable.

    PYTHONPATH=. venv/bin/python -m research_v2.p13 run        # every stage; idempotent, resumable
    PYTHONPATH=. venv/bin/python -m research_v2.p13 status

Design: docs/research_v2/P13_RL_BENCHMARK_DESIGN.md. Stages:
  preflight    v0.4 lock verifies, P12 complete, disk; source hashes recorded
  determinism  each algorithm trained twice (1,024 decisions, pilot) must give identical parameters
  tuning       registered grid (8 configs x 3 pilot seeds) at F on pilot_train, scored on pilot_validation
  lock         P13 lock: sources, selected hyperparameters, sealed benchmark_test manifest, hypotheses
  training     3 algorithms x {F, B} x outer 0-19 on train_final (the PPO-Equal streams and seeds)
  open         benchmark_test opened once (record written before the first episode)
  evaluation   benchmark_test: all methods; P11 test: the new methods (PPO and heuristics reused from P11)
  analysis     B1-B3 primary (Holm), B4-B9 secondary (Holm), descriptive learning curves and compute
  claims       P13 claims table
P13 never changes a locked v0.4 file and never changes a P11 claim.
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

BASE = ROOT / 'results/research_v2/v0.4'
# P13_SMOKE=1 (with P13_OUT pointing elsewhere) exercises every stage with tiny budgets, 2 outers and 2 traces per workload.
SMOKE = os.environ.get('P13_SMOKE') == '1'
OUT = Path(os.environ.get('P13_OUT', ROOT / 'results/research_v2/p13'))
require(not SMOKE or 'P13_OUT' in os.environ, 'P13_SMOKE requires P13_OUT outside the real output directory')
V04_LOCK = BASE / 'protocol_lock/protocol_lock.json'
P13_LOCK = OUT / 'protocol_lock/p13_lock.json'
OPENED = OUT / 'BENCHMARK_OPENED.json'
P11_EVAL = BASE / 'p11/test_evaluation'
P12_STATE = BASE / 'p12/pipeline/state.json'
STUDIES = [BASE / 'p11' / f'shard_{i:02d}' for i in range(10)]
DESIGN = ROOT / 'docs/research_v2/P13_RL_BENCHMARK_DESIGN.md'
STATE = OUT / 'pipeline/state.json'
LOG = OUT / 'pipeline/pipeline.log'
JDK = '/usr/lib/jvm/java-21-openjdk-amd64'
STOP = {'requested': False}
PILOT_OUTERS = (100,) if SMOKE else (100, 101, 102)
PPO_REUSED = ('equal_B', 'equal_F', 'nsga2')
PRIMARY = (('B1', 'dqn_B', 'equal_B'), ('B2', 'tabq_B', 'equal_B'), ('B3', 'ddpg_B', 'equal_B'))
SECONDARY = (('B4', 'dqn_F', 'equal_F'), ('B5', 'tabq_F', 'equal_F'), ('B6', 'ddpg_F', 'equal_F'),
             ('B7', 'greedy_eft', 'dqn_B'), ('B8', 'greedy_eft', 'tabq_B'), ('B9', 'greedy_eft', 'ddpg_B'))
ORIENTATION = ('difference = D(comparator) - D(treatment). B1-B6: comparator = new algorithm, treatment = PPO-Equal, '
               'positive = PPO-Equal better. B7-B9: comparator = greedy_eft, positive = new algorithm better.')


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
    dump(STATE, s)


def done(stage):
    return stage in state()['stages']


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def stopped():
    if STOP['requested']:
        log('stop requested: exiting; re-run the same command to resume')
        raise SystemExit(75)


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def read_rows(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]


def budgets():
    if SMOKE:
        return {'F': 1024, 'B': 2048}
    plan = read_json(STUDIES[0] / 'protocol.json') if (STUDIES[0] / 'protocol.json').exists() else None
    config = load_config()
    F = config['training']['final_decisions']
    B = plan['budget']['B'] if plan else 19_637_248
    return {'F': F, 'B': B}


def n_configs(algorithm):
    from .p13_learners import GRIDS
    return 2 if SMOKE else len(GRIDS[algorithm])


def outers():
    return [0, 1] if SMOKE else list(range(load_config()['seeds']['outer_runs']))


def source_files():
    names = sorted(ROOT.glob('research_v2/**/*.py')) + sorted(ROOT.glob('configs/research_v2/*.json'))
    names += [DESIGN, ROOT / 'run_p13.sh', ROOT / 'ifogsim/build/research_v2/build_receipt.json']
    # Jupyter autosaves (.ipynb_checkpoints/*.py) are editor artifacts, not sources; hashing them would stop a run mid-way.
    skip = {'__pycache__', '.ipynb_checkpoints'}
    return {rel(p): file_sha256(p) for p in names if p.is_file() and not skip & set(p.parts)}


def p11_models():
    """{(label, outer): checkpoint dir} of the P11 PPO models, verified once (study_runner.verify_complete re-hashes every
    artifact, ~15 min) at preflight and cached with each model hash; every use re-checks the model hash."""
    cache = OUT / 'pipeline/p11_models.json'
    if not cache.exists():
        from .p11_eval import model_table
        rows = [{'label': l, 'outer': o, 'checkpoint': rel(c), 'model_sha256': read_json(c / 'state.json')['model_sha256']}
                for (l, o), c in sorted(model_table(STUDIES).items())]
        dump(cache, rows)
    out = {}
    for r in read_json(cache):
        out[(r['label'], r['outer'])] = ROOT / r['checkpoint']
    return out


# ------------------------------------------------------------------------------------------------ lock

def seal(lock):
    body = {k: v for k, v in lock.items() if k != 'lock_sha256'}
    return {**body, 'lock_sha256': sha256(body)}


def verify_p13_lock(path=P13_LOCK):
    lock = read_json(path)
    require(seal(lock)['lock_sha256'] == lock['lock_sha256'], 'P13 lock content does not match its hash')
    require(read_json(V04_LOCK)['lock_sha256'] == lock['predecessor_lock_sha256'], 'P13 lock refers to another v0.4 lock')
    current = source_files()
    drift = sorted(k for k, v in lock['sources'].items() if current.get(k) != v)
    require(not drift, f'P13 sources changed after the lock: {drift[:5]}')
    return lock


# ------------------------------------------------------------------------------------------------ evaluation

def trace_source(split):
    """Yield (namespace, trace) for every evaluation trace of the split, in workload order."""
    from .trace_access import TraceKey
    from .traces import TraceGenerator
    config = load_config()
    if split == 'benchmark_test':
        from . import p13_traces
        p13_traces.open_benchmark(P13_LOCK)
        for key in p13_traces.keys(config):
            if SMOKE and key.trace_id > p13_traces.TRACE_IDS[0] + 1:
                continue
            yield key.to_dict(), p13_traces.generate(config, key, purpose='evaluate')
        return
    if split == 'test':
        from . import trace_access
        trace_access.unseal_test(V04_LOCK)
        ids, role = config['seeds']['test_trace_ids'], 'test_evaluator'
    else:
        require(split == 'pilot_validation', f'Unknown evaluation split {split}')
        ids, role = config['seeds']['validation_trace_ids'], 'pilot_validator'
    generator = TraceGenerator(config)
    for workload in config['training']['workload_order']:
        for trace_id in range(ids[0], (ids[0] + 1) if SMOKE else ids[1] + 1):
            key = TraceKey(config['seeds']['master'], split, None, None, trace_id, workload)
            yield key.to_dict(), generator.generate(key, role=role).to_dict()


def evaluate(policy, weights, out_file, split):
    """policy(obs, raw_snapshot) -> (action, unseen_state). Complete episodes, deterministic; z is never clipped."""
    from .gym_env import OffloadingEnv
    from .learning import COSTS, append_json
    config = load_config()
    holder = {}
    env = OffloadingEnv(lambda seed, index: holder['trace'], weights, config=config, jdk_home=JDK, any_port=True, validate=False)
    out_file = Path(out_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(out_file) + '.partial')
    temporary.unlink(missing_ok=True)
    try:
        for namespace, trace in trace_source(split):
            holder['trace'] = trace
            obs, info = env.reset(seed=0)
            steps, reward_sum, unseen, actions = 0, 0.0, 0, np.zeros(7, dtype=np.int64)
            while True:
                action, flag = policy(obs, info['raw_snapshot'])
                obs, reward, terminated, truncated, info = env.step(int(action))
                require(not truncated, 'Evaluation episode truncated')
                steps, reward_sum, unseen = steps + 1, reward_sum + reward, unseen + int(flag)
                actions[int(action)] += 1
                if terminated:
                    break
            metrics = info['summary']['metrics']
            z = [metrics['costs'][c] for c in COSTS]
            require(steps == trace['task_count'], 'Evaluation did not finish the trace')
            require(np.isclose(reward_sum, -100 * np.dot(weights, z), rtol=1e-6, atol=1e-8), 'Reward identity failed')
            append_json(temporary, {'namespace': namespace, 'trace_sha256': trace['payload_sha256'], 'decisions': steps,
                                    'reward': reward_sum, 'action_counts': actions.tolist(), 'unseen_states': unseen,
                                    'metrics': metrics})
    finally:
        env.close()
    temporary.replace(out_file)


def policy_for(label, checkpoint):
    """(policy, weights) for a heuristic, a reused P11 PPO checkpoint or a P13 checkpoint."""
    from .p11_eval import HEURISTICS
    from .learning import file_hash, setup_torch
    if label in HEURISTICS:
        from . import baselines
        choose = getattr(baselines, label)
        return (lambda obs, snap: (choose(snap), False)), [0.2] * 5
    if label in PPO_REUSED:
        from stable_baselines3 import PPO
        from .gym_env import check_policy_interface
        checkpoint = Path(checkpoint)
        digest = file_hash(checkpoint / 'model.zip')
        cached = {r['checkpoint']: r['model_sha256'] for r in read_json(OUT / 'pipeline/p11_models.json')}
        require(read_json(checkpoint / 'state.json')['model_sha256'] == digest == cached[rel(checkpoint)], 'PPO checkpoint hash')
        manifest = read_json(checkpoint.parent / 'manifest.json')
        setup_torch(load_config())
        model = PPO.load(checkpoint / 'model.zip', device='cpu')
        check_policy_interface(model.observation_space.shape[0], model.action_space.n)
        return (lambda obs, snap: (int(model.predict(obs, deterministic=True)[0]), False)), manifest['weights']
    from .p13_learners import EQUAL, load_policy
    return load_policy(label.rsplit('_', 1)[0], checkpoint), EQUAL


# ------------------------------------------------------------------------------------------------ job commands

def cmd_train(algorithm, hp_index, split, outer, budget, directory):
    from .p13_learners import GRIDS, train
    directory = Path(directory)
    complete = directory / 'complete.json'
    require(not complete.exists(), 'job already complete')
    if (directory / 'run').exists():
        shutil.rmtree(directory / 'run')
    if split == 'train_final':
        lock = verify_p13_lock()
        require(lock['selected'][algorithm]['index'] == hp_index, 'Training hyperparameters differ from the P13 lock')
    checkpoint = train(directory / 'run', algorithm, GRIDS[algorithm][hp_index], split, outer, budget, JDK)
    outcome = read_json(directory / 'run/outcome.json')
    require(outcome['status'] == 'complete' and outcome['audit']['decisions'] == budget, 'training outcome incomplete')
    dump(complete, {'checkpoint': rel(checkpoint), 'state_sha256': file_sha256(checkpoint / 'state.json'),
                    'wall_s': outcome['wall_s'], 'completed_utc': now()})


def cmd_tune(algorithm, hp_index, outer, directory):
    from .learning import aggregate_costs
    directory = Path(directory)
    if (directory / 'summary.json').exists():
        return
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    F = budgets()['F']
    cmd_train(algorithm, hp_index, 'pilot_train', outer, F, directory)
    checkpoint = ROOT / read_json(directory / 'complete.json')['checkpoint']
    policy, weights = policy_for(f'{algorithm}_F', checkpoint)
    evaluate(policy, weights, directory / 'pilot_validation.jsonl', 'pilot_validation')
    rows = read_rows(directory / 'pilot_validation.jsonl')
    aggregation = aggregate_costs(rows, load_config()['training']['workload_order'])
    dump(directory / 'summary.json', {'algorithm': algorithm, 'hp_index': hp_index, 'outer': outer,
                                      'D_macro': aggregation['D_macro'], 'D_by_workload': aggregation['D_by_workload'],
                                      'train_wall_s': read_json(directory / 'complete.json')['wall_s'],
                                      'flagged_episodes': sum(r['metrics']['diagnosis_required'] for r in rows)})


def cmd_eval(split, label, outer, checkpoint, out_file):
    if split != 'pilot_validation':
        verify_p13_lock()
    policy, weights = policy_for(label, ROOT / checkpoint if checkpoint else None)
    evaluate(policy, weights, ROOT / out_file, split)


def pool(jobs, workers, name):
    """jobs: dicts with id, args (list for `-m research_v2.p13`), done (path). Separate process groups; JVMs are reaped."""
    todo = [j for j in jobs if not Path(j['done']).exists()]
    log(f'{name}: {len(todo)} of {len(jobs)} jobs to run ({workers} workers)')
    logs = OUT / 'pipeline/job_logs'
    logs.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'PYTHONPATH': str(ROOT)}
    running, finished, last = [], len(jobs) - len(todo), time.monotonic()
    try:
        while todo or running:
            still = []
            for process, job in running:
                if process.poll() is None:
                    still.append((process, job))
                    continue
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                require(process.returncode == 0 and Path(job['done']).exists(),
                        f'{name}: job {job["id"]} failed (exit {process.returncode}); see {rel(logs)}/{job["id"]}.log')
                finished += 1
            running = still
            stopped()
            while todo and len(running) < workers:
                job = todo.pop(0)
                sink = open(logs / f'{job["id"]}.log', 'w')
                command = [sys.executable, '-m', 'research_v2.p13', *map(str, job['args'])]
                running.append((subprocess.Popen(command, cwd=ROOT, env=env, stdout=sink, stderr=subprocess.STDOUT,
                                                 start_new_session=True), job))
            if time.monotonic() - last > 900:
                log(f'{name}: {finished}/{len(jobs)} jobs complete, {len(running)} running')
                last = time.monotonic()
            time.sleep(2)
    finally:
        for process, _ in running:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        for process, _ in running:
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
    log(f'{name}: all {len(jobs)} jobs complete')


# ------------------------------------------------------------------------------------------------ stages

def stage_preflight():
    from .analysis.lock import verify_lock
    problems, warnings = verify_lock(V04_LOCK, deep=False)
    require(not problems, f'v0.4 protocol lock problems: {problems}')
    require(P12_STATE.exists() and 'claims' in read_json(P12_STATE)['stages'], 'P12 is not complete')
    require(DESIGN.exists(), 'P13 design document missing')
    free = shutil.disk_usage(ROOT).free / 2 ** 30
    require(free > 60, f'only {free:.0f} GiB free; P13 needs about 40 GiB')
    import importlib.metadata
    log('preflight: verifying the 120 completed P11 jobs (one-time, about 15 minutes)')
    models = p11_models()
    require(len(models) == 120, f'expected 120 P11 PPO checkpoints, found {len(models)}')
    mark('preflight', p11_models_sha256=file_sha256(OUT / 'pipeline/p11_models.json'), v04_lock_sha256=read_json(V04_LOCK)['lock_sha256'], lock_warnings=len(warnings), free_disk_gib=round(free),
         sources=source_files(), budgets=budgets(), sb3=importlib.metadata.version('stable-baselines3'))
    log(f'preflight ok: v0.4 lock verified ({len(warnings)} warning(s): files added after the lock), P12 complete, {free:.0f} GiB free')


def stage_determinism():
    import torch
    from .p13_learners import ALGORITHMS, GRIDS, load_tabular, train
    base = OUT / 'determinism'
    shutil.rmtree(base, ignore_errors=True)
    result = {}
    for algorithm in ALGORITHMS:
        digests = []
        for copy in ('a', 'b'):
            checkpoint = train(base / algorithm / copy, algorithm, GRIDS[algorithm][0], 'pilot_train', PILOT_OUTERS[0], 1024, JDK)
            if algorithm == 'tabq':
                q, visits = load_tabular(checkpoint)
                digests.append(hashlib.sha256(q.tobytes() + visits.tobytes()).hexdigest())
            else:
                from .learning_instrumentation import tensor_digest
                from .p13_learners import DDPG, DQN
                model = (DQN if algorithm == 'dqn' else DDPG).load(checkpoint / 'model.zip', device='cpu')
                digests.append(tensor_digest(model.policy.state_dict()))
            episodes = (base / algorithm / copy / 'episodes.jsonl').read_text() if (base / algorithm / copy / 'episodes.jsonl').exists() else ''
            digests[-1] += '|' + hashlib.sha256(episodes.encode()).hexdigest()
        require(digests[0] == digests[1], f'{algorithm}: two identical runs differ (non-deterministic)')
        result[algorithm] = digests[0]
    shutil.rmtree(base, ignore_errors=True)
    mark('determinism', digests=result, decisions=1024)
    log('determinism ok: each algorithm reproduced its parameters exactly (1,024 decisions, pilot)')


def tuning_jobs():
    from .p13_learners import ALGORITHMS, GRIDS
    jobs = []
    for algorithm in ('ddpg', 'dqn', 'tabq'):
        for index in range(n_configs(algorithm)):
            for outer in PILOT_OUTERS:
                d = OUT / 'tuning' / algorithm / f'c{index}' / f'p{outer}'
                jobs.append({'id': f'tune_{algorithm}_c{index}_p{outer}', 'done': d / 'summary.json',
                             'args': ['tune', '--algo', algorithm, '--hp-index', index, '--outer', outer, '--dir', rel(d)]})
    require({j['id'].split('_')[1] for j in jobs} == set(ALGORITHMS), 'tuning jobs')
    return jobs


def stage_tuning(workers):
    from .p13_learners import ALGORITHMS, GRIDS
    pool(tuning_jobs(), workers, 'tuning')
    B, F = budgets()['B'], budgets()['F']
    report, selected = {}, {}
    for algorithm in ALGORITHMS:
        configs = []
        for index, hp in enumerate(GRIDS[algorithm][:n_configs(algorithm)]):
            runs = [read_json(OUT / 'tuning' / algorithm / f'c{index}' / f'p{o}' / 'summary.json') for o in PILOT_OUTERS]
            configs.append({'index': index, 'hyperparameters': hp, 'D_macro_by_seed': [r['D_macro'] for r in runs],
                            'D_macro_mean': float(np.mean([r['D_macro'] for r in runs])),
                            'train_wall_s_mean': float(np.mean([r['train_wall_s'] for r in runs])),
                            'flagged_episodes': sum(r['flagged_episodes'] for r in runs)})
        best = min(configs, key=lambda c: (c['D_macro_mean'], c['index']))
        selected[algorithm] = {'index': best['index'], 'hyperparameters': best['hyperparameters'], 'D_macro_mean': best['D_macro_mean']}
        report[algorithm] = configs
        log(f'tuning {algorithm}: selected c{best["index"]} {best["hyperparameters"]} (pilot D {best["D_macro_mean"]:.4f}); '
            f'B-run estimate {best["train_wall_s_mean"] * B / F / 3600:.1f} h')
    dump(OUT / 'tuning/report.json', {'rule': 'lowest mean D_macro on pilot_validation over pilot outers 100-102 at F; '
                                      'ties to the lower grid index', 'configs': report, 'selected': selected})
    (OUT / 'tuning/report.md').write_text(render_tuning(report, selected))
    mark('tuning', selected=selected, report_sha256=file_sha256(OUT / 'tuning/report.json'))


def render_tuning(report, selected):
    from .p13_learners import NAMES
    lines = ['# P13 — hyperparameter tuning (pilot namespace only)', '',
             'Budget F = 102,400 decisions per run; pilot_train outer 100-102; score = D_macro on 20 pilot_validation traces.',
             'Selection: lowest mean D; ties to the lower grid index. No confirmatory seed, validation-search or test trace is used.', '']
    for algorithm, configs in report.items():
        lines += [f'## {NAMES[algorithm]}', '', '| # | hyperparameters | D seed 100 | D seed 101 | D seed 102 | mean D | train wall (s) |',
                  '|---|---|---:|---:|---:|---:|---:|']
        for c in configs:
            star = ' **selected**' if c['index'] == selected[algorithm]['index'] else ''
            lines.append(f'| c{c["index"]}{star} | `{json.dumps(c["hyperparameters"])}` | ' +
                         ' | '.join(f'{d:.4f}' for d in c['D_macro_by_seed']) + f' | {c["D_macro_mean"]:.4f} | {c["train_wall_s_mean"]:.0f} |')
        lines.append('')
    return '\n'.join(lines)


def stage_lock():
    from . import p13_traces
    from .p13_learners import FIXED, GRIDS, LOG_WINDOW
    config = load_config()
    recorded = state()['stages']['preflight']['sources']
    current = source_files()
    drift = sorted(k for k in set(recorded) | set(current) if recorded.get(k) != current.get(k))
    require(not drift, f'sources changed between preflight/tuning and lock: {drift[:5]}')
    log('lock: preparing the sealed benchmark_test manifest (inputs only, no outcome)')
    manifest = p13_traces.manifest(config)
    dump(OUT / 'protocol_lock/benchmark_test_manifest.json', manifest)
    v04 = read_json(V04_LOCK)
    lock = seal({
        'protocol': 'research-v2-p13-benchmark-1', 'created_utc': now(), 'predecessor_lock_sha256': v04['lock_sha256'],
        'design': rel(DESIGN), 'config_sha256': sha256(config), 'sources': current, 'budgets': budgets(),
        'methods': {'new': ['dqn', 'tabq', 'ddpg'], 'reused_ppo': list(PPO_REUSED), 'heuristics': ['always_local', 'nearest_fog',
                    'least_fog', 'greedy_eft']},
        'grids': GRIDS, 'fixed': FIXED, 'selected': state()['stages']['tuning']['selected'],
        'tuning_report_sha256': state()['stages']['tuning']['report_sha256'],
        'training': {'split': 'train_final', 'outers': outers(), 'weights': [0.2] * 5,
                     'seeds': 'final_model_base + outer (as PPO-Equal)', 'separate_F_and_B_runs': True},
        'decision_log': {'window': LOG_WINDOW, 'rule': 'all rows up to 2 windows; otherwise first and last window'},
        'benchmark_test': {k: manifest[k] for k in ('split', 'trace_ids', 'traces', 'tasks_total', 'rows_sha256')},
        'hypotheses': {'primary': [list(h) for h in PRIMARY], 'secondary': [list(h) for h in SECONDARY], 'orientation': ORIENTATION,
                       'multiplicity': 'Holm within each family', 'alpha': config['statistics']['alpha'],
                       'test': 'exact sign-flip over 20 paired outer runs; crossed bootstrap 95% CI; paired dz',
                       'bootstrap_draws': config['statistics']['bootstrap_draws'], 'bootstrap_seed': config['seeds']['bootstrap']},
        'smoke': SMOKE,
        'status': 'P13 benchmark, registered before benchmark_test is opened; separate from the P11 confirmatory claims'})
    dump(P13_LOCK, lock)
    verify_p13_lock()
    mark('lock', lock_sha256=lock['lock_sha256'], benchmark_traces=manifest['traces'], benchmark_tasks=manifest['tasks_total'])
    log(f'P13 lock written: {rel(P13_LOCK)} ({lock["lock_sha256"][:12]}...), benchmark_test {manifest["traces"]} traces sealed')


def training_jobs():
    lock = read_json(P13_LOCK)
    b = budgets()
    jobs = []
    for budget in ('B', 'F'):
        for algorithm in ('ddpg', 'dqn', 'tabq'):          # longest first
            for outer in lock['training']['outers']:
                d = OUT / 'training' / f'{algorithm}_{budget}' / f'r{outer:02d}'
                jobs.append({'id': f'train_{algorithm}_{budget}_r{outer:02d}', 'done': d / 'complete.json',
                             'args': ['train', '--algo', algorithm, '--hp-index', lock['selected'][algorithm]['index'],
                                      '--split', 'train_final', '--outer', outer, '--budget', b[budget], '--dir', rel(d)]})
    return jobs


def checkpoint_of(label, outer, p11_models):
    if label in PPO_REUSED:
        return rel(p11_models[(label, outer)])
    from .p11_eval import HEURISTICS
    if label in HEURISTICS:
        return ''
    return read_json(OUT / 'training' / label / f'r{outer:02d}' / 'complete.json')['checkpoint']


NEW_LABELS = tuple(f'{a}_{b}' for b in ('B', 'F') for a in ('dqn', 'tabq', 'ddpg'))


def eval_jobs():
    from .p11_eval import HEURISTICS
    models = p11_models()
    outers = read_json(P13_LOCK)['training']['outers']
    jobs = []
    for split, labels in (('benchmark_test', (*NEW_LABELS, *PPO_REUSED, *HEURISTICS)), ('test', NEW_LABELS)):
        for label in labels:
            for outer in ([0] if label in HEURISTICS else outers):
                target = OUT / 'evaluation' / split / f'{label}_r{outer:02d}.jsonl'
                jobs.append({'id': f'eval_{split}_{label}_r{outer:02d}', 'done': target,
                             'args': ['eval', '--split', split, '--label', label, '--outer', outer,
                                      '--checkpoint', checkpoint_of(label, outer, models) or '-', '--out', rel(target)]})
    return jobs


def stage_open():
    lock = verify_p13_lock()
    if not OPENED.exists():
        dump(OPENED, {'split': 'benchmark_test', 'opened_utc': now(), 'p13_lock_sha256': lock['lock_sha256'],
                      'note': 'Opened once after all P13 training completed; results are not used to retune anything.'})
    require(read_json(OPENED)['p13_lock_sha256'] == lock['lock_sha256'], 'opening record bound to another lock')
    mark('open', opened_utc=read_json(OPENED)['opened_utc'])
    log(f'benchmark_test opened at {read_json(OPENED)["opened_utc"]}')


# ------------------------------------------------------------------------------------------------ analysis

def table(split):
    from .analysis.loader import rows_to_table
    from .p11_eval import HEURISTICS
    outers = read_json(P13_LOCK)['training']['outers']
    labels = (*PPO_REUSED, *NEW_LABELS, *HEURISTICS)
    cells = {}
    for label in labels:
        for outer in outers:
            name = f'{label}_r{(0 if label in HEURISTICS else outer):02d}.jsonl'
            if split == 'test' and label not in NEW_LABELS:
                cells[(label, outer)] = read_rows(P11_EVAL / 'episodes' / name)
            else:
                cells[(label, outer)] = read_rows(OUT / 'evaluation' / split / name)
    if SMOKE:       # the reused P11 rows cover all 100 test traces; keep the smoke subset only
        keep = {(r['namespace']['workload'], r['namespace']['trace_id']) for r in cells[(NEW_LABELS[0], outers[0])]}
        cells = {k: [r for r in v if (r['namespace']['workload'], r['namespace']['trace_id']) in keep] for k, v in cells.items()}
    return rows_to_table(cells, load_config(), allowed_splits=(split,))


def family(t, hypotheses, config):
    from .analysis.stats import exploratory, holm, physical_summary
    rows = exploratory(t, [(c, tr) for _, c, tr in hypotheses], config)
    adjusted = holm([r['raw_p_exact_signflip'] for r in rows])
    for (hid, c, tr), r, p in zip(hypotheses, rows, adjusted):
        r.update(id=hid, holm_p=float(p), significant=bool(p < config['statistics']['alpha']),
                 label='p13_registered', physical=physical_summary(t, tr, c))
    return rows


def analyse_split(split):
    from .analysis.stats import aggregate
    config = load_config()
    t = table(split)
    agg = aggregate(t)
    methods = {m: {'Dglobal_mean': float(agg['D'][i].mean()), 'Dglobal_sd': float(agg['D'][i].std(ddof=1)),
                   'F_mean': agg['F'][i].mean(axis=0).tolist(), 'Dw_mean': dict(zip(t.workloads, agg['Dw'][i].mean(axis=0).tolist()))}
               for i, m in enumerate(t.methods)}
    flagged, unseen = {}, {}
    for m in t.methods:
        if m in NEW_LABELS or split == 'benchmark_test':
            paths = sorted((OUT / 'evaluation' / split).glob(f'{m}_r*.jsonl'))
            rows = [r for p in paths for r in read_rows(p)]
            flagged[m] = sum(r['metrics']['diagnosis_required'] for r in rows)
            if m.startswith('tabq'):
                unseen[m] = sum(r['unseen_states'] for r in rows) / sum(r['decisions'] for r in rows)
    return {'split': split, 'methods': methods, 'primary': family(t, PRIMARY, config), 'secondary': family(t, SECONDARY, config),
            'flagged_episodes': flagged, 'tabq_unseen_state_fraction': unseen}


def learning_curves(windows=16):
    """Descriptive: D of the training episodes per budget window (B runs), mean over outer runs."""
    from .learning import aggregate_costs
    config, B = load_config(), budgets()['B']
    workloads = config['training']['workload_order']
    runs = outers()
    sources = {f'{a}_B': [OUT / 'training' / f'{a}_B' / f'r{o:02d}' / 'run' / 'episodes.jsonl' for o in runs]
               for a in ('dqn', 'tabq', 'ddpg')}
    p11 = p11_models()
    sources['equal_B'] = [] if SMOKE else [p11[('equal_B', o)].parent / 'episodes.jsonl' for o in runs]
    curves = {}
    for label, paths in sources.items():
        if not paths or not all(p.exists() for p in paths):
            curves[label] = None
            continue
        per_run = []
        for path in paths:
            rows, seen, buckets = read_rows(path), 0, [[] for _ in range(windows)]
            for r in rows:
                buckets[min(windows - 1, seen * windows // B)].append(r)
                seen += r['decisions']
            per_run.append([aggregate_costs(b, workloads)['D_macro'] if {x['namespace']['workload'] for x in b} == set(workloads)
                            else None for b in buckets])
        curves[label] = [float(np.mean([v[k] for v in per_run if v[k] is not None])) if any(v[k] is not None for v in per_run)
                         else None for k in range(windows)]
    return {'windows': windows, 'budget': B, 'curves': curves}


def compute_hours():
    out = {}
    for label in NEW_LABELS:
        walls = [read_json(OUT / 'training' / label / f'r{o:02d}' / 'complete.json')['wall_s'] for o in outers()]
        out[label] = {'train_wall_h_mean': float(np.mean(walls)) / 3600, 'train_wall_h_total': float(np.sum(walls)) / 3600}
    p11 = p11_models()
    walls = []
    for o in ([] if SMOKE else outers()):
        profile = p11[('equal_B', o)].parents[2] / 'profile.json'
        if profile.exists():
            walls.append(read_json(profile)['wall_s'])
    if walls:
        out['equal_B'] = {'train_wall_h_mean': float(np.mean(walls)) / 3600, 'train_wall_h_total': float(np.sum(walls)) / 3600,
                          'note': 'P11 job (B run with checkpoint at F, full decision log)'}
    return out


def ci(c):
    return f'[{c[0]:.4f}; {c[1]:.4f}]'


def dz(d):
    v = d.get('dz') if isinstance(d, dict) else d
    return 'undef.' if v is None else f'{v:.3f}'


def render_report(report):
    from .p13_learners import NAMES
    lines = ['# P13 — RL benchmark: DQN, tabular Q-Learning, DDPG vs PPO-Equal', '',
             f'P13 lock `{report["lock_sha256"][:12]}…`; benchmark_test opened {report["opened_utc"]}. '
             'Registered P13 benchmark, separate from the P11 confirmatory claims.',
             'All methods: same environment, 108 public features, 7 actions, equal reward weights, gamma 0.97, train_final streams',
             'and seeds of PPO-Equal, budgets in environment decisions (F = 102,400; B = 19,637,248). n = 20 paired outer runs.',
             ORIENTATION, '']
    for split, title in (('benchmark_test', 'benchmark_test (new sealed split, primary)'), ('test', 'P11 test split (supplementary, '
                         'not blind: PPO results were known)')):
        r = report['splits'][split]
        lines += [f'## {title}', '', '| method | Dglobal mean | SD | light | moderate | heavy | dynamic | flagged episodes |',
                  '|---|---:|---:|---:|---:|---:|---:|---:|']
        for m, v in sorted(r['methods'].items(), key=lambda kv: kv[1]['Dglobal_mean']):
            w = v['Dw_mean']
            lines.append(f'| {m} | {v["Dglobal_mean"]:.4f} | {v["Dglobal_sd"]:.4f} | ' + ' | '.join(f'{w[k]:.4f}' for k in
                         ('light', 'moderate', 'heavy', 'dynamic')) + f' | {r["flagged_episodes"].get(m, "—")} |')
        lines += ['', '| id | comparator | treatment | mean diff | 95% CI | dz | raw p | Holm p | energy J | violation pp | reliability pp |',
                  '|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|']
        for fam in ('primary', 'secondary'):
            for c in r[fam]:
                ph = c['physical']
                k = 'mean_paired_difference_comparator_minus_treatment'
                lines.append(f'| {c["id"]} | {c["comparator"]} | {c["treatment"]} | {c["mean_difference"]:.4f} | '
                             f'{ci(c["ci95_difference"])} | {dz(c["effect_size_dz"])} | {c["raw_p_exact_signflip"]:.3g} | '
                             f'{"**" if c["significant"] else ""}{c["holm_p"]:.3g}{"**" if c["significant"] else ""} | '
                             f'{ph["dynamic_energy_j"][k]:.1f} | {ph["violation_pp"][k]:.2f} | {ph["reliability_pp"][k]:.2f} |')
        if r['tabq_unseen_state_fraction']:
            lines += ['', 'Q-Learning decisions in a state never visited during training (action 0 = local): ' +
                      ', '.join(f'{m} {v:.2%}' for m, v in r['tabq_unseen_state_fraction'].items())]
        lines.append('')
    lines += ['Physical columns: paired comparator − treatment, dynamic energy per trace (J), deadline violation and reliability',
              '(percentage points). Holm within each family (B1–B3; B4–B9); bold = Holm p < 0.05.', '',
              '## Training D per budget window (descriptive, training episodes, mean over 20 runs)', '']
    lc = report['learning_curves']
    labels = [k for k, v in lc['curves'].items() if v]
    lines += ['| window | ' + ' | '.join(labels) + ' |', '|---|' + '---:|' * len(labels)]
    for k in range(lc['windows']):
        lines.append(f'| {k + 1}/{lc["windows"]} | ' + ' | '.join('—' if lc['curves'][m][k] is None else f'{lc["curves"][m][k]:.4f}'
                                                                 for m in labels) + ' |')
    lines += ['', '## Compute (training wall time per run, 1 CPU)', '', '| method | mean h | total h |', '|---|---:|---:|']
    for m, v in report['compute'].items():
        lines.append(f'| {m} | {v["train_wall_h_mean"]:.2f} | {v["train_wall_h_total"]:.1f} |')
    lines += ['', '## Methods', ''] + [f'- `{a}`: {n}' for a, n in NAMES.items()]
    lines += [f'- selected hyperparameters: `{json.dumps({a: s["hyperparameters"] for a, s in report["selected"].items()})}`',
              '- `equal_B`, `equal_F`, `nsga2`: frozen P11 PPO checkpoints (no retraining)']
    return '\n'.join(lines) + '\n'


def stage_analysis():
    lock = verify_p13_lock()
    report = {'lock_sha256': lock['lock_sha256'], 'opened_utc': read_json(OPENED)['opened_utc'], 'orientation': ORIENTATION,
              'selected': lock['selected'], 'splits': {}}
    for split in ('benchmark_test', 'test'):
        stopped()
        log(f'analysis: {split}')
        report['splits'][split] = analyse_split(split)
    log('analysis: learning curves and compute')
    report['learning_curves'] = learning_curves()
    report['compute'] = compute_hours()
    dump(OUT / 'report/report.json', report)
    (OUT / 'report/report.md').write_text(render_report(report))
    prim = report['splits']['benchmark_test']['primary']
    mark('analysis', primary={c['id']: {'diff': c['mean_difference'], 'holm_p': c['holm_p']} for c in prim})
    log(f'report written: {rel(OUT / "report/report.md")}')


def stage_claims():
    from .p13_learners import NAMES
    report = read_json(OUT / 'report/report.json')
    r = report['splits']['benchmark_test']
    name = {'dqn': NAMES['dqn'], 'tabq': NAMES['tabq'], 'ddpg': NAMES['ddpg']}

    def verdict(c, positive_is_ppo):
        if not c['significant']:
            return 'no clear difference (insufficient evidence; not equivalence)'
        better = c['mean_difference'] > 0
        if positive_is_ppo:
            return 'PPO-Equal better' if better else 'new algorithm better'
        return 'new algorithm better' if better else 'greedy_eft better'

    lines = ['# P13 — claims table (RL benchmark)', '',
             'Registered P13 benchmark on the new sealed split `benchmark_test`; separate from the P11 confirmatory claims.', '',
             '| # | Claim | Evidence (benchmark_test) | Status |', '|---|---|---|---|']
    for c in r['primary'] + r['secondary']:
        algo = (c['comparator'] if c['id'] <= 'B6' else c['treatment']).split('_')[0]
        what = (f'{name[algo]} vs PPO-Equal at {c["comparator"][-1]}' if c['id'] <= 'B6' else f'{name[algo]} (B) vs greedy_eft')
        lines.append(f'| {c["id"]} | {what} | diff {c["mean_difference"]:.4f}, CI {ci(c["ci95_difference"])}, Holm p '
                     f'{c["holm_p"]:.3g} | {verdict(c, c["id"] <= "B6")} |')
    lines += ['', '## Limits', '',
              '- Same simulation limits as P11/P12 (one topology, synthetic workloads, simulation only).',
              '- Hyperparameters tuned on the pilot namespace only, 8 configurations x 3 seeds per new algorithm at F; PPO was not '
              're-tuned (learner v0.3 from the P10 diagnosis). Tuning effort is comparable, not identical.',
              '- DDPG is adapted to discrete actions by a continuous score relaxation with argmax; Wolpertinger/SAC-Discrete were not run.',
              '- Tabular Q-Learning sees a 6,561-state discretization of the public snapshot (estimated finish time vs deadline per '
              'destination and task class), not the full 108 features.',
              '- B runs keep the first and last 102,400 per-decision log rows plus every episode row (disk policy registered in the lock).',
              '- The P11 test split results are supplementary: that split was opened before P13 and PPO results were known.']
    (OUT / 'claims_p13.md').write_text('\n'.join(lines) + '\n')
    mark('claims')
    log(f'claims table written: {rel(OUT / "claims_p13.md")}')


# ------------------------------------------------------------------------------------------------ CLI

def progress():
    lines = []
    for name, glob in (('tuning', 'tuning/*/*/*/summary.json'), ('training', 'training/*/*/complete.json'),
                       ('evaluation benchmark_test', 'evaluation/benchmark_test/*.jsonl'), ('evaluation test', 'evaluation/test/*.jsonl')):
        total = {'tuning': 72, 'training': 120, 'evaluation benchmark_test': 184, 'evaluation test': 120}[name]
        lines.append(f'  {name:<26} {len(list(OUT.glob(glob))):>3}/{total}')
    return '\n'.join(lines)


def status():
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'sources'} for k, v in state()['stages'].items()}, indent=2))
    print(progress())
    print(f'log: {LOG}')


def run(workers):
    if not done('preflight'):
        stage_preflight()
    if not done('determinism'):
        stage_determinism()
    stopped()
    if not done('tuning'):
        stage_tuning(workers)
    stopped()
    if not done('lock'):
        stage_lock()
    stopped()
    if not done('training'):
        verify_p13_lock()
        pool(training_jobs(), workers, 'training')
        mark('training', jobs=120)
    stopped()
    if not done('open'):
        stage_open()
    if not done('evaluation'):
        jobs = eval_jobs()
        pool(jobs, workers, 'evaluation')
        mark('evaluation', jobs=len(jobs))
    stopped()
    if not done('analysis'):
        stage_analysis()
    if not done('claims'):
        stage_claims()
    log('=== P13 all stages complete ===')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    r = sub.add_parser('run')
    r.add_argument('--workers', type=int, default=12)
    sub.add_parser('status')
    t = sub.add_parser('train')
    for name, kind in (('--algo', str), ('--hp-index', int), ('--split', str), ('--outer', int), ('--budget', int), ('--dir', str)):
        t.add_argument(name, type=kind, required=True)
    u = sub.add_parser('tune')
    for name, kind in (('--algo', str), ('--hp-index', int), ('--outer', int), ('--dir', str)):
        u.add_argument(name, type=kind, required=True)
    e = sub.add_parser('eval')
    for name, kind in (('--split', str), ('--label', str), ('--outer', int), ('--checkpoint', str), ('--out', str)):
        e.add_argument(name, type=kind, required=True)
    args = parser.parse_args()
    if args.command == 'status':
        status()
    elif args.command == 'train':
        cmd_train(args.algo, args.hp_index, args.split, args.outer, args.budget, ROOT / args.dir)
    elif args.command == 'tune':
        cmd_tune(args.algo, args.hp_index, args.outer, ROOT / args.dir)
    elif args.command == 'eval':
        cmd_eval(args.split, args.label, args.outer, '' if args.checkpoint == '-' else args.checkpoint, args.out)
    else:
        signal.signal(signal.SIGTERM, lambda *_: STOP.update(requested=True))
        signal.signal(signal.SIGINT, lambda *_: STOP.update(requested=True))
        log(f'=== p13 run pid={os.getpid()} workers={args.workers} ===')
        run(args.workers)


if __name__ == '__main__':
    main()
