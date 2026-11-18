"""P12 for protocol v0.4: zero-shot sensitivity, final audit, reproduction package and claims table — one command.

    PYTHONPATH=. venv/bin/python -m research_v2.p12 run        # every stage; idempotent, resumable
    PYTHONPATH=. venv/bin/python -m research_v2.p12 status     # progress, from any terminal

Registered rules (protocol lock v0.4, block `sensitivity`), applied here without change:
  * one factor at a time on the frozen main models (the 120 P11 checkpoints), zero-shot: no retraining, no re-search;
  * homogeneous fog is a control; heterogeneous fog stays the main result;
  * normalization/penalty sensitivity is recomputed on validation data only; the main definition is always reported;
  * z > 1 under sensitivity is flagged out-of-reference, never clipped, and never adjusts the main normalization.
All sensitivity results are `exploratory_unadjusted` (effect, CI, raw p; no multiplicity control, no confirmatory claim).

How a physical variant reaches the simulator: the JVM reads its configuration only from the resource
`research_v2/default.json` inside the JAR. A variant JAR is the main JAR with exactly that one entry replaced; every other
entry (all classes) is copied byte for byte and this is checked. The variant handshake verifies the variant config file,
the variant JAR hash and the canonical hash the server is bound to. An `identity` variant (the main config through the
same mechanism) must reproduce the P11 test rows exactly before any sensitivity result is accepted.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import zipfile

import numpy as np

from .config import ROOT, close, load_config, read_json, require, sha256, validate_config

BASE = ROOT / 'results/research_v2/v0.4'
OUT = BASE / 'p12'
LOCK = BASE / 'protocol_lock/protocol_lock.json'
P11_EVAL = BASE / 'p11/test_evaluation'
STUDIES = [BASE / 'p11' / f'shard_{i:02d}' for i in range(10)]
STATE = OUT / 'pipeline/state.json'
LOG = OUT / 'pipeline/pipeline.log'
JDK = '/usr/lib/jvm/java-21-openjdk-amd64'
CONFIG_ENTRY = 'research_v2/default.json'
# The JAR manifest resolves its libraries as ../jars/*.jar, so variant JARs live next to ifogsim/dist.
VARIANT_JARS = ROOT / 'ifogsim/dist_p12'
STOP = {'requested': False}
MAIN_PAIRS = [('equal_F', 'nsga2'), ('random', 'nsga2'), ('equal_B', 'nsga2')]   # RQ1-RQ3 orientation
PAIR_IDS = ('RQ1', 'RQ2', 'RQ3')


# ------------------------------------------------------------------------------------------------ pipeline plumbing

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
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(s, indent=2))
    tmp.replace(STATE)


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


# ------------------------------------------------------------------------------------------------ variants

def variant_specs(main):
    """Ordered {name: (description, mutate(config) or None, options)} from the registered factor levels."""
    s = main['sensitivity']
    specs = {'identity': ('main config through the variant-JAR mechanism (control; must equal P11 exactly)', lambda c: None, {})}

    def timeout(k):
        def mutate(c):
            t = c['timing']
            t['timeout_factor'] = k
            t['horizon_s'] = t['arrival_window_s'] + k * t['deadline_max_s']
        return mutate

    def queue(q):
        def mutate(c):
            for fog in c['topology']['fogs']:
                fog['queue_waiting'] = q
        return mutate

    def wan(p):
        def mutate(c):
            c['network']['wan']['propagation_s'] = p
        return mutate

    def power(m):
        def mutate(c):
            topo, net = c['topology'], c['network']
            for node in [topo['iot'], *topo['fogs'], topo['cloud']]:
                node['busy_w'] = node['idle_w'] + m * (node['busy_w'] - node['idle_w'])
            for key in ('radio_tx_increment_w', 'radio_rx_increment_w', 'ap_tx_increment_w', 'ap_rx_increment_w',
                        'lan_j_per_bit_hop', 'wan_j_per_bit_hop'):
                net[key] = m * net[key]
        return mutate

    for k in s['timeout_factors']:
        specs[f'timeout_k{k:g}'] = (f'timeout factor k = {k:g} (main {main["timing"]["timeout_factor"]:g}); horizon T + k*Dmax; '
                                    'latency reference and penalty unchanged', timeout(k), {})
    for q in s['fog_queue_waiting']:
        specs[f'fog_queue_{q}'] = (f'fog waiting-queue capacity {q} on F1-F5 (main {main["topology"]["fogs"][0]["queue_waiting"]})',
                                   queue(q), {})
    for p in s['wan_propagation_s']:
        specs[f'wan_prop_{p:g}'] = (f'WAN propagation {p:g} s (main {main["network"]["wan"]["propagation_s"]:g} s)', wan(p), {})
    for m in s['dynamic_power_multipliers']:
        specs[f'dyn_power_x{m:g}'] = (f'dynamic power x{m:g}: node busy-idle increments, radio/AP increments and per-bit '
                                      'network energy; idle power and the energy reference unchanged', power(m), {})
    specs['homogeneous_fog'] = ('homogeneous fog control: every fog uses the F3 profile (main JAR, reset option)', None,
                                {'homogeneous_fog': True})
    return specs


def validate_variant(config, main):
    """Every main-config contract except the one the registered k=4 level breaks by design (latency reference >= k*Dmax:
    the main normalization is kept, so successful latencies may exceed it and are flagged out-of-reference)."""
    probe = copy.deepcopy(config)
    probe['timing'] = copy.deepcopy(main['timing'])
    validate_config(probe)
    t = config['timing']
    require(close(t['horizon_s'], t['arrival_window_s'] + t['timeout_factor'] * t['deadline_max_s']), 'variant horizon != T + k*Dmax')
    require(t['timeout_factor'] > 0, 'variant timeout factor must be positive')
    changed = sorted(k for k in config if config[k] != main[k])
    require(set(changed) <= {'timing', 'topology', 'network'}, f'variant changes unregistered blocks: {changed}')
    require(config['evaluation'] == main['evaluation'] and config['observation'] == main['observation'],
            'a physical variant must never change normalization or observation scales')
    return changed


def jar_entries(path):
    with zipfile.ZipFile(path) as z:
        return {i.filename: hashlib.sha256(z.read(i)).hexdigest() for i in z.infolist()}


def build_variant_jar(source, target, config_bytes):
    """Copy every entry of the main JAR except CONFIG_ENTRY, which gets config_bytes. Same order, metadata, compression."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + '.tmp')
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(tmp, 'w') as dst:
        names = [i.filename for i in src.infolist()]
        require(names.count(CONFIG_ENTRY) == 1, 'main JAR does not contain exactly one config resource')
        for info in src.infolist():
            data = config_bytes if info.filename == CONFIG_ENTRY else src.read(info)
            dst.writestr(info, data, compress_type=info.compress_type)
    tmp.replace(target)
    a, b = jar_entries(source), jar_entries(target)
    require(list(a) == list(b), 'variant JAR entry list differs')
    differing = [n for n in a if a[n] != b[n]]
    require(differing in ([], [CONFIG_ENTRY]), f'variant JAR differs outside the config resource: {differing[:5]}')
    return {'jar': str(target.relative_to(ROOT)), 'jar_sha256': file_sha256(target), 'entries': len(a),
            'entries_identical_to_main_except_config': True, 'config_entry_changed': differing == [CONFIG_ENTRY]}


def variant_dir(name):
    return OUT / 'variants' / name


def build_variants():
    from .engine_runner import JAR
    main = load_config()
    receipt = read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')
    require(file_sha256(JAR) == receipt['artifact_sha256'], 'main JAR differs from its build receipt')
    with zipfile.ZipFile(JAR) as z:
        resource = z.read(CONFIG_ENTRY)
    require(resource == (ROOT / 'configs/research_v2/default.json').read_bytes(), 'JAR config resource differs from the repo config')
    out = {}
    for name, (description, mutate, options) in variant_specs(main).items():
        record = {'name': name, 'description': description, 'options': options}
        if mutate is None:
            record.update(mode='main_jar', config_sha256=sha256(main), changed_blocks=[])
        else:
            config = copy.deepcopy(main)
            mutate(config)
            record['changed_blocks'] = validate_variant(config, main)
            data = resource if name == 'identity' else (json.dumps(config, indent=2) + '\n').encode()
            require(json.loads(data) == config, 'variant config bytes do not parse back to the variant')
            path = variant_dir(name) / 'default.json'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            record.update(mode='variant_jar', config_file=str(path.relative_to(ROOT)), config_file_sha256=file_sha256(path),
                          config_sha256=sha256(config), **build_variant_jar(JAR, VARIANT_JARS / f'research-v2-{name}.jar', data))
            if name == 'identity':
                require(record['config_sha256'] == sha256(main) and not record['config_entry_changed'], 'identity variant is not the main config')
        dump(variant_dir(name) / 'variant.json', record)
        out[name] = record
    dump(OUT / 'variants/index.json', out)
    return out


def variant_config(record):
    return read_json(ROOT / record['config_file']) if record['mode'] == 'variant_jar' else load_config()


def install_variant(record):
    """In this process only: start servers from the variant JAR and verify its identity instead of the main receipt."""
    if record['mode'] != 'variant_jar':
        return
    from . import gym_env, rpc_client
    jar, config_file = ROOT / record['jar'], ROOT / record['config_file']
    require(file_sha256(jar) == record['jar_sha256'] and file_sha256(config_file) == record['config_file_sha256'],
            f'variant {record["name"]} files changed after they were built')
    rpc_client.JAR = jar

    def verify(handshake, config, *, require_jar_hash=True):
        problems = []
        if handshake.get('schema_version') != rpc_client.SCHEMA:
            problems.append('schema_version')
        if handshake.get('config_file_sha256') != record['config_file_sha256']:
            problems.append('config resource in the JAR is not the variant config')
        if handshake.get('wire_contract_file_sha256') != file_sha256(ROOT / 'configs/research_v2/wire_contract.json'):
            problems.append('wire contract differs')
        if handshake.get('bound_config_sha256') != sha256(config) or sha256(config) != record['config_sha256']:
            problems.append('server not bound to the variant canonical config hash')
        if handshake.get('jar_sha256') != record['jar_sha256']:
            problems.append('running JAR is not the variant JAR')
        require(not problems, f'variant {record["name"]} handshake: ' + '; '.join(problems))
        return handshake
    gym_env.verify_handshake = verify


def variant_trace(trace, config):
    """Same arrivals/tasks as the main trace; per-task timeout = k * deadline and horizon from the variant config."""
    from .contracts import trace_payload_sha256, validate_contract
    out = copy.deepcopy(trace)
    k = config['timing']['timeout_factor']
    for task in out['tasks']:
        task['timeout_relative_s'] = k * task['deadline_relative_s']
    out['horizon_s'] = config['timing']['horizon_s']
    out['config_sha256'] = sha256(config)
    out['payload_sha256'] = trace_payload_sha256(out)
    validate_contract('trace', out, config)
    return out


# ------------------------------------------------------------------------------------------------ evaluation

def episodes_dir(variant, split):
    return OUT / ('validation_main' if split == 'validation' else f'sensitivity/{variant}') / 'episodes'


def evaluate(policy, weights, out_file, split, record, jdk_home=JDK):
    """Complete deterministic episodes on every trace of the split under one variant. Out-of-reference costs are kept."""
    from .gym_env import OffloadingEnv
    from .learning import COSTS, append_json
    from .p11_eval import SPLITS
    from .trace_access import TraceKey
    from .traces import TraceGenerator
    main = load_config()
    config = variant_config(record)
    ids, role = SPLITS[split]
    generator = TraceGenerator(main)
    holder = {}
    env = OffloadingEnv(lambda seed, index: holder['trace'], weights, config=config, jdk_home=jdk_home, any_port=True,
                        validate=False, homogeneous_fog=record['options'].get('homogeneous_fog', False))
    temporary = Path(str(out_file) + '.partial')
    temporary.unlink(missing_ok=True)
    try:
        low, high = main['seeds'][ids]
        for workload in main['training']['workload_order']:
            for trace_id in range(low, high + 1):
                key = TraceKey(main['seeds']['master'], split, None, None, trace_id, workload)
                trace = generator.generate(key, role=role).to_dict()
                main_sha = trace['payload_sha256']
                if record['mode'] == 'variant_jar':
                    trace = variant_trace(trace, config)
                holder['trace'] = trace
                obs, info = env.reset(seed=0)
                steps, reward_sum, actions, invalid = 0, 0.0, np.zeros(7, dtype=np.int64), 0
                while True:
                    action = int(policy(obs, info['raw_snapshot']))
                    obs, reward, done_, truncated, info = env.step(action)
                    require(not truncated, 'Evaluation episode truncated')
                    steps, reward_sum = steps + 1, reward_sum + reward
                    invalid += not info['observation_valid'] and not done_   # the terminal observation is always a placeholder
                    actions[action] += 1
                    if done_:
                        break
                metrics = info['summary']['metrics']
                z = [metrics['costs'][c] for c in COSTS]
                require(steps == trace['task_count'], 'Evaluation did not finish the trace')
                require(np.isclose(reward_sum, -100 * np.dot(weights, z), rtol=1e-6, atol=1e-8), 'Reward identity failed')
                append_json(temporary, {'namespace': key.to_dict(), 'trace_sha256': trace['payload_sha256'],
                                        'main_trace_sha256': main_sha, 'variant': record['name'], 'decisions': steps,
                                        'reward': reward_sum, 'action_counts': actions.tolist(),
                                        'invalid_observations': invalid, 'metrics': metrics})
    finally:
        env.close()
    temporary.replace(out_file)


def task(variant, split, label, outer, checkpoint):
    from . import trace_access
    from .p11_eval import HEURISTICS
    record = read_json(variant_dir(variant) / 'variant.json') if variant != 'main' else \
        {'name': 'main', 'mode': 'main_jar', 'options': {}, 'config_sha256': sha256(load_config())}
    install_variant(record)
    if split == 'test':
        trace_access.unseal_test(LOCK)
    target = episodes_dir(variant, split) / f'{label}_r{outer:02d}.jsonl'
    target.parent.mkdir(parents=True, exist_ok=True)
    if label in HEURISTICS:
        from . import baselines
        choose = getattr(baselines, label)
        evaluate(lambda obs, snap: choose(snap), [0.2] * 5, target, split, record)
        return
    from stable_baselines3 import PPO
    from .gym_env import check_policy_interface
    from .learning import file_hash, setup_torch
    checkpoint = Path(checkpoint)
    st = read_json(checkpoint / 'state.json')
    require(st['model_sha256'] == file_hash(checkpoint / 'model.zip'), 'Checkpoint hash mismatch')
    manifest = read_json(checkpoint.parent / 'manifest.json')
    require(manifest['config_sha256'] == sha256(load_config()), 'Checkpoint was trained under another simulation config')
    setup_torch(load_config())
    model = PPO.load(checkpoint / 'model.zip', device='cpu')
    check_policy_interface(model.observation_space.shape[0], model.action_space.n)
    evaluate(lambda obs, snap: model.predict(obs, deterministic=True)[0], manifest['weights'], target, split, record)


def all_tasks(variants, split, only=None):
    from .p11_eval import HEURISTICS, model_table
    models = model_table(STUDIES)
    out = []
    for v in variants:
        jobs = [(label, outer, str(path)) for (label, outer), path in sorted(models.items())] + [(h, 0, '') for h in HEURISTICS]
        if only is not None:
            jobs = [j for j in jobs if (j[0], j[1]) in only]
        out += [(v, split, *j) for j in jobs]
    return out


def pending(tasks):
    return [t for t in tasks if not (episodes_dir(t[0], t[1]) / f'{t[2]}_r{t[3]:02d}.jsonl').exists()]


def run_pool(tasks, workers, name):
    todo = pending(tasks)
    log(f'{name}: {len(todo)} of {len(tasks)} evaluation tasks to run ({workers} workers)')
    logs = OUT / 'pipeline/task_logs'
    logs.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, 'PYTHONPATH': str(ROOT)}
    running, finished, last = [], len(tasks) - len(todo), time.monotonic()
    try:
        while todo or running:
            still = []
            for process, t in running:
                if process.poll() is None:
                    still.append((process, t))
                else:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)    # a failed task may leave its JVM behind
                    except ProcessLookupError:
                        pass
                    require(process.returncode == 0, f'Evaluation task {t[:4]} failed (exit {process.returncode}); see '
                            f'{logs.relative_to(ROOT)}/{t[0]}_{t[1]}_{t[2]}_r{t[3]:02d}.log')
                    finished += 1
            running = still
            stopped()
            while todo and len(running) < workers:
                t = todo.pop(0)
                sink = open(logs / f'{t[0]}_{t[1]}_{t[2]}_r{t[3]:02d}.log', 'w')
                command = [sys.executable, '-m', 'research_v2.p12', 'task', '--variant', t[0], '--split', t[1], '--label', t[2],
                           '--outer', str(t[3]), '--checkpoint', t[4]]
                running.append((subprocess.Popen(command, cwd=ROOT, env=env, stdout=sink, stderr=subprocess.STDOUT,
                                                 start_new_session=True), t))
            if time.monotonic() - last > 900:
                log(f'{name}: {finished}/{len(tasks)} tasks complete')
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
    log(f'{name}: all {len(tasks)} tasks complete')


# ------------------------------------------------------------------------------------------------ stages

def stage_preflight():
    from .analysis.lock import verify_lock
    problems, warnings = verify_lock(LOCK, deep=False)
    require(not problems, f'protocol lock problems: {problems}')
    opened = read_json(ROOT / 'results/research_v2/TEST_OPENED.json')
    require(opened['lock_sha256'] == read_json(LOCK)['lock_sha256'], 'TEST_OPENED refers to another lock')
    report = read_json(P11_EVAL / 'report.json')
    require(report['confirmatory'] and report['split'] == 'test', 'P11 registered analysis is missing or not confirmatory')
    require(sum(1 for _ in (P11_EVAL / 'episodes').glob('*.jsonl')) == 124, 'P11 test episodes incomplete')
    free = shutil.disk_usage(ROOT).free / 2 ** 30
    require(free > 20, f'only {free:.0f} GiB free')
    mark('preflight', lock_sha256=read_json(LOCK)['lock_sha256'], lock_warnings=len(warnings), free_disk_gib=round(free))
    log(f'preflight ok: lock verified (0 problems, {len(warnings)} warning(s): files added after the lock), P11 complete')


def stage_identity(workers):
    """The variant mechanism with the main config must reproduce P11 test rows exactly."""
    checks = [('nsga2', 0), ('equal_B', 7), ('greedy_eft', 0)]
    tasks = all_tasks(['identity'], 'test', only=set(checks))
    run_pool(tasks, workers, 'identity check')
    fields = ('namespace', 'trace_sha256', 'decisions', 'reward', 'action_counts', 'metrics')
    compared = 0
    for label, outer in checks:
        mine = [json.loads(x) for x in (episodes_dir('identity', 'test') / f'{label}_r{outer:02d}.jsonl').read_text().splitlines()]
        ref = [json.loads(x) for x in (P11_EVAL / 'episodes' / f'{label}_r{outer:02d}.jsonl').read_text().splitlines()]
        require(len(mine) == len(ref) == 400, f'identity {label}_r{outer:02d}: row count')
        for a, b in zip(mine, ref):
            require({f: a[f] for f in fields} == {f: b[f] for f in fields},
                    f'identity variant does not reproduce P11 for {label}_r{outer:02d} {a["namespace"]}')
            compared += 1
    mark('identity_check', episodes_compared=compared, models=[f'{l}_r{o:02d}' for l, o in checks])
    log(f'identity check passed: {compared} test episodes identical to P11 (metrics, actions, reward)')


def table_from(directory, labels, outers, split, transform=None):
    from .analysis.loader import read_rows, rows_to_table
    from .p11_eval import HEURISTICS
    cells = {}
    for label in labels:
        for outer in outers:
            rows = read_rows(Path(directory) / f'{label}_r{(0 if label in HEURISTICS else outer):02d}.jsonl')
            cells[(label, outer)] = [transform(r) for r in rows] if transform else rows
    return rows_to_table(cells, load_config(), allowed_splits=(split,))


def summarize(table, config, pairs, draws):
    from .analysis.stats import aggregate, exploratory
    agg = aggregate(table)
    methods = {m: {'Dglobal_mean': float(agg['D'][i].mean()), 'Dglobal_sd': float(agg['D'][i].std(ddof=1)),
                   'F_mean': agg['F'][i].mean(axis=0).tolist(),
                   'Dw_mean': dict(zip(table.workloads, agg['Dw'][i].mean(axis=0).tolist()))}
               for i, m in enumerate(table.methods)}
    rows = exploratory(table, pairs, config, bootstrap_draws=draws)
    return methods, rows


def out_of_reference(directory):
    counts = {}
    for path in sorted(Path(directory).glob('*.jsonl')):
        rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
        flagged = [r for r in rows if r['metrics']['diagnosis_required']]
        counts[path.stem] = {'episodes': len(rows), 'flagged': len(flagged),
                             'costs': sorted({c for r in flagged for c in r['metrics']['out_of_reference']}),
                             'invalid_observations': sum(r.get('invalid_observations', 0) for r in rows)}
    return counts


def spearman(a, b):
    from scipy.stats import spearmanr
    return float(spearmanr(a, b).statistic)


def normalization_variants(main):
    ms = main['sensitivity']['normalization_multipliers']
    out = {}
    for m in ms:
        out[f'latency_ref_x{m:g}'] = ('latency reference and failure penalty x' + f'{m:g}', m, 1, 1, 1)
        out[f'failure_penalty_x{m:g}'] = ('failure latency penalty only x' + f'{m:g}', 1, m, 1, 1)
        out[f'energy_ref_x{m:g}'] = ('energy reference x' + f'{m:g}', 1, 1, m, 1)
        out[f'imbalance_ref_x{m:g}'] = ('imbalance reference x' + f'{m:g}', 1, 1, 1, m)
    return out


def renormalize(row, main, lat_m, pen_m, energy_m, imb_m):
    """Recompute the costs of one episode row under scaled references (z is never clipped)."""
    ev, m = main['evaluation'], row['metrics']
    c = m['costs']
    n, failed, completed = m['task_count'], m['failed'], m['latency']['completed_tasks']
    latency_sum = (m['latency']['mean_s'] or 0.0) * completed
    l_ref, pen = ev['latency_reference_s'], ev['failure_latency_penalty_s']
    require(math.isclose((latency_sum + failed * pen) / (n * l_ref), c['zL'], rel_tol=1e-9, abs_tol=1e-12),
            'zL cannot be reconstructed from the row; refusing to renormalize')
    out = copy.deepcopy(row)
    oc = out['metrics']['costs']
    oc['zL'] = (latency_sum + failed * pen * lat_m * pen_m) / (n * l_ref * lat_m)
    oc['zE'] = c['zE'] / energy_m
    oc['zB'] = c['zB'] / imb_m
    return out


def dz_text(dz):
    value = dz.get('dz') if isinstance(dz, dict) else dz
    return 'undefined' if value is None else f'{value:.3f}'


def render_sensitivity(report):
    lines = ['# P12 — sensitivity analysis (protocol v0.4)', '',
             '**All results here are exploratory_unadjusted**: effect, 95% crossed-bootstrap CI, raw exact sign-flip p; no multiplicity',
             'control and no confirmatory status. The confirmatory result is P11 (`p11/test_evaluation/report.md`).',
             'Frozen P11 models, zero-shot, one factor at a time, test split; normalization always the main definition.',
             'Difference = D(comparator) - D(NSGA-II); positive = NSGA-II better.', '',
             f'Variant mechanism control: identity variant reproduced {report["identity_check"]["episodes_compared"]} P11 test episodes exactly.', '',
             '## 1. Physical factors (test split)', '']
    methods = report['method_order']
    lines += ['| variant | ' + ' | '.join(methods) + ' | rank rho vs main | flagged episodes |',
              '|---|' + '---:|' * (len(methods) + 2)]
    for name, v in report['physical'].items():
        lines.append(f'| {name} | ' + ' | '.join(f'{v["methods"][m]["Dglobal_mean"]:.4f}' for m in methods) +
                     f' | {v["rank_spearman_vs_main"]:.3f} | {v["flagged_episodes"]} |')
    lines += ['', 'Dglobal mean over the 20 outer runs (lower is better). Flagged = episodes with a cost outside [0, 1] '
              '(kept unclipped, out-of-reference).', '', '### Registered comparisons under each variant', '',
              '| variant | test | comparator | mean diff | 95% CI | dz | raw p | same sign as main |', '|---|---|---|---:|---|---:|---:|:-:|']
    for name, v in report['physical'].items():
        for c in v['comparisons']:
            ci = c['ci95_difference']
            lines.append(f'| {name} | {c.get("id", "")} | {c["comparator"]} | {c["mean_difference"]:.4f} | [{ci[0]:.4f}, {ci[1]:.4f}] | '
                         f'{dz_text(c["effect_size_dz"])} | '
                         f'{c["raw_p_exact_signflip"]:.4g} | {"yes" if c["same_sign_as_main"] else "**no**"} |')
    lines += ['', '## 2. Normalization and penalty (validation split only)', '',
              'Recomputed from the same validation episodes (5 traces x 4 workloads, main physics). The main definition is the first row.', '',
              '| definition | ' + ' | '.join(methods) + ' | RQ1 diff (raw p) | RQ2 diff (raw p) | RQ3 diff (raw p) |',
              '|---|' + '---:|' * (len(methods) + 3)]
    for name, v in report['normalization'].items():
        cells = [f'{c["mean_difference"]:.4f} ({c["raw_p_exact_signflip"]:.3g})' for c in v['comparisons']]
        lines.append(f'| {name} | ' + ' | '.join(f'{v["methods"][m]["Dglobal_mean"]:.4f}' for m in methods) + ' | ' + ' | '.join(cells) + ' |')
    lines += ['', '## 3. Definitions', '']
    for name, v in report['physical'].items():
        lines.append(f'- `{name}`: {v["description"]}')
    for name, v in report['normalization'].items():
        lines.append(f'- `{name}`: {v["description"]}')
    return '\n'.join(lines) + '\n'


def stage_analysis(draws):
    from .p11_eval import HEURISTICS, PPO_LABELS
    main = load_config()
    labels, outers = (*PPO_LABELS, *HEURISTICS), list(range(main['seeds']['outer_runs']))
    pairs = MAIN_PAIRS + [(h, 'nsga2') for h in HEURISTICS]
    index = read_json(OUT / 'variants/index.json')
    log('analysis: main reference from the P11 test episodes')
    ref_methods, ref_rows = summarize(table_from(P11_EVAL / 'episodes', labels, outers, 'test'), main, pairs, draws)
    ref_rank = [ref_methods[m]['Dglobal_mean'] for m in labels]
    physical = {'main (P11)': {'description': 'main configuration (registered P11 result, recomputed from its episodes)',
                               'methods': ref_methods, 'comparisons': ref_rows, 'rank_spearman_vs_main': 1.0, 'flagged_episodes': 0}}
    for name, record in index.items():
        if name == 'identity':
            continue
        stopped()
        log(f'analysis: {name}')
        directory = episodes_dir(name, 'test')
        methods, rows = summarize(table_from(directory, labels, outers, 'test'), main, pairs, draws)
        oor = out_of_reference(directory)
        physical[name] = {'description': record['description'], 'config_sha256': record['config_sha256'],
                          'methods': methods, 'comparisons': rows, 'out_of_reference': oor,
                          'flagged_episodes': sum(v['flagged'] for v in oor.values()),
                          'rank_spearman_vs_main': spearman(ref_rank, [methods[m]['Dglobal_mean'] for m in labels])}
    for v in physical.values():
        for k, c in enumerate(v['comparisons']):
            c['id'] = PAIR_IDS[k] if k < 3 else 'heuristic'
            c['same_sign_as_main'] = bool(np.sign(c['mean_difference']) == np.sign(ref_rows[k]['mean_difference']))
    normalization = {}
    val_dir = episodes_dir('main', 'validation')
    variants = {'main definition': ('main normalization (registered)', 1, 1, 1, 1), **normalization_variants(main)}
    for name, (description, *factors) in variants.items():
        stopped()
        log(f'analysis: normalization {name} (validation)')
        transform = (lambda r, f=factors: renormalize(r, main, *f))
        methods, rows = summarize(table_from(val_dir, labels, outers, 'validation', transform), main, MAIN_PAIRS, draws)
        normalization[name] = {'description': description, 'multipliers': dict(zip(('latency_ref', 'failure_penalty', 'energy_ref',
                                                                                     'imbalance_ref'), factors)),
                               'methods': methods, 'comparisons': rows}
    report = {'label': 'exploratory_unadjusted', 'protocol_version': '0.4', 'lock_sha256': read_json(LOCK)['lock_sha256'],
              'rules': read_json(LOCK)['sensitivity'], 'method_order': list(labels), 'bootstrap_draws': draws,
              'identity_check': state()['stages']['identity_check'], 'physical': physical, 'normalization': normalization}
    dump(OUT / 'sensitivity/report.json', report)
    (OUT / 'sensitivity/report.md').write_text(render_sensitivity(report))
    kept = sum(c['same_sign_as_main'] for n, v in physical.items() if n != 'main (P11)' for c in v['comparisons'][:3])
    total = 3 * (len(physical) - 1)
    mark('sensitivity_analysis', registered_comparisons_same_sign=f'{kept}/{total}')
    log(f'sensitivity report written: {(OUT / "sensitivity/report.md").relative_to(ROOT)} ({kept}/{total} RQ directions kept)')


def stage_audit():
    """Trace the P11 numbers back to checkpoints, episodes, traces, the lock and the build."""
    from .analysis.lock import verify_lock
    from .learning import file_hash
    from .p11_eval import HEURISTICS, analyse, model_table
    from . import trace_access
    from .trace_access import TraceKey
    from .traces import TraceGenerator
    from .engine_runner import JAR
    config = load_config()
    lock = read_json(LOCK)
    checks = {}
    problems, warnings = verify_lock(LOCK, deep=True)
    checks['lock_deep_verify'] = {'pass': not problems, 'problems': problems, 'warnings': warnings}
    receipt = read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')
    checks['build_and_config'] = {'pass': file_sha256(JAR) == receipt['artifact_sha256'] == lock['build']['jar_sha256']
                                  and sha256(config) == lock['config']['canonical_sha256'],
                                  'jar_sha256': file_sha256(JAR), 'config_sha256': sha256(config)}
    opened = read_json(ROOT / 'results/research_v2/TEST_OPENED.json')
    checks['test_opened_record'] = {'pass': opened['lock_sha256'] == lock['lock_sha256'] and opened['models'] == 120, **opened}
    # Checkpoints: hash, config, learner, budget.
    models = model_table(STUDIES)
    bad, weights = [], {}
    for (label, outer), ck in sorted(models.items()):
        st, manifest = read_json(ck / 'state.json'), read_json(ck.parent / 'manifest.json')
        ok = (st['model_sha256'] == file_hash(ck / 'model.zip') and manifest['config_sha256'] == sha256(config)
              and manifest.get('learner_version') == '0.3' and int(ck.name.split('_')[1]) == st['decisions'])
        if not ok:
            bad.append(f'{label}_r{outer:02d}')
        weights[f'{label}_r{outer:02d}'] = {'weights': manifest['weights'], 'model_sha256': st['model_sha256'],
                                            'decisions': st['decisions'], 'checkpoint': str(ck.relative_to(ROOT))}
    checks['checkpoints'] = {'pass': not bad and len(models) == 120, 'count': len(models), 'bad': bad}
    dump(OUT / 'audit/model_index.json', weights)
    # Episode rows: every row on a regenerated test trace, complete, unclipped and consistent with the reward identity.
    trace_access.unseal_test(LOCK)
    generator = TraceGenerator(config)
    low, high = config['seeds']['test_trace_ids']
    expected = {}
    for w in config['training']['workload_order']:
        for t in range(low, high + 1):
            trace = generator.generate(TraceKey(config['seeds']['master'], 'test', None, None, t, w), role='test_evaluator')
            expected[(w, t)] = (trace.payload_sha256, trace.task_count)
    row_problems, rows_checked = [], 0
    for path in sorted((P11_EVAL / 'episodes').glob('*.jsonl')):
        rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
        keys = [(r['namespace']['workload'], r['namespace']['trace_id']) for r in rows]
        if sorted(keys) != sorted(expected):
            row_problems.append(f'{path.name}: trace set differs')
        for r, key in zip(rows, keys):
            rows_checked += 1
            sha, n = expected.get(key, (None, None))
            if r['trace_sha256'] != sha or r['decisions'] != n or r['metrics']['diagnosis_required'] or sum(r['action_counts']) != n:
                row_problems.append(f'{path.name} {key}')
    checks['episodes'] = {'pass': not row_problems, 'rows_checked': rows_checked, 'files': 124, 'problems': row_problems[:20]}
    # Recompute the registered analysis from raw episodes in a scratch directory and compare with the published report.
    scratch = OUT / 'audit/recomputed_p11'
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True)
    (scratch / 'episodes').symlink_to(P11_EVAL / 'episodes', target_is_directory=True)
    recomputed = analyse(scratch, [str(s) for s in STUDIES], 'test', list(range(20)))
    published = read_json(P11_EVAL / 'report.json')
    same = json.loads(json.dumps(recomputed, allow_nan=False)) == published
    (scratch / 'episodes').unlink()
    checks['report_recomputed'] = {'pass': same, 'note': 'P11 report.json recomputed from raw episode rows (bootstrap and sign-flip '
                                   'seeds are fixed), compared for exact equality'}
    # Job ledger: per outer run, search (S + V) + final (F) = C for both methods and each baseline trained to B.
    ledger_bad, jobs = [], 0
    for study in STUDIES:
        plan = read_json(study / 'protocol.json')
        b = plan['budget']
        profile = {}
        for job in plan['jobs']:
            jobs += 1
            complete = read_json(study / 'jobs' / job['id'] / 'complete.json')
            profile[job['id']] = read_json(study / complete['attempt'] / 'profile.json')
        for outer in plan['outers']:
            for method in ('nsga2', 'random'):
                s_, f_ = profile[f'r{outer:02d}_{method}_search'], profile[f'r{outer:02d}_{method}_final']
                if (s_['training_interactions'], s_['candidate_validation_interactions'], f_['training_interactions']) != (b['S'], b['V'], b['F']):
                    ledger_bad.append(f'r{outer:02d}_{method}')
            for method in ('equal', 'manual'):
                if profile[f'r{outer:02d}_{method}']['training_interactions'] != b['B']:
                    ledger_bad.append(f'r{outer:02d}_{method}')
    checks['job_ledger'] = {'pass': not ledger_bad and jobs == 120, 'jobs': jobs, 'mismatch': ledger_bad,
                            'budget': {k: read_json(STUDIES[0] / 'protocol.json')['budget'][k] for k in ('S', 'V', 'F', 'C', 'B')}}
    git = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    audit = {'created_utc': now(), 'git_head': git, 'lock_sha256': lock['lock_sha256'], 'checks': checks,
             'pass': all(c['pass'] for c in checks.values())}
    dump(OUT / 'audit/audit.json', audit)
    require(audit['pass'], 'final audit failed: ' + ', '.join(k for k, c in checks.items() if not c['pass']) +
            f'; see {(OUT / "audit/audit.json").relative_to(ROOT)}')
    mark('audit', checks={k: c['pass'] for k, c in checks.items()}, rows_checked=rows_checked)
    log(f'final audit passed: {len(checks)} checks, {rows_checked} test episode rows traced to regenerated traces')


REPRO_WORKER = r'''
import json, sys
from pathlib import Path
import numpy as np
mode, out = sys.argv[1], Path(sys.argv[2])
from research_v2.config import load_config, sha256
from research_v2.learning import setup_torch
config = load_config()
if mode == 'physical':
    from stable_baselines3 import PPO
    from research_v2 import baselines
    from research_v2.gym_env import OffloadingEnv
    from research_v2.trace_access import TraceKey
    from research_v2.traces import TraceGenerator
    checkpoint = Path(sys.argv[3])
    setup_torch(config)
    model = PPO.load(checkpoint / 'model.zip', device='cpu')
    weights = json.loads((checkpoint.parent / 'manifest.json').read_text())['weights']
    rows = []
    for name, policy, w in (('greedy_eft', lambda o, s: baselines.greedy_eft(s), [0.2] * 5),
                            ('checkpoint', lambda o, s: model.predict(o, deterministic=True)[0], weights)):
        for workload in ('light', 'heavy'):
            trace = TraceGenerator(config).generate(TraceKey(config['seeds']['master'], 'validation', None, None, 10000, workload),
                                                    role='search_validator').to_dict()
            env = OffloadingEnv([trace], w, config=config, jdk_home=sys.argv[4], any_port=True, validate=True)
            try:
                obs, info = env.reset(seed=0)
                actions, done = [], False
                while not done:
                    a = int(policy(obs, info['raw_snapshot']))
                    actions.append(a)
                    obs, r, done, _, info = env.step(a)
                rows.append({'policy': name, 'workload': workload, 'trace_sha256': trace['payload_sha256'],
                             'actions_sha256': sha256(actions), 'metrics': info['summary']['metrics'],
                             'energy': info['summary'].get('energy')})
            finally:
                env.close()
    out.write_text(json.dumps(rows, indent=2))
elif mode == 'learn':
    from stable_baselines3 import PPO
    from research_v2.learning import run_training
    from research_v2.learning_instrumentation import tensor_digest
    run_training(out / 'run', 100, 0, 1024, [0.2] * 5, sys.argv[3], training_split='pilot_train', phase='P11',
                 checkpoint_at=[1024], learner_version='0.3')
    ck = out / 'run' / 'checkpoint_00001024'
    model = PPO.load(ck / 'model.zip', device='cpu')
    curve = (out / 'run' / 'learning_curve.jsonl').read_text() if (out / 'run' / 'learning_curve.jsonl').exists() else ''
    (out / 'result.json').write_text(json.dumps({'policy_tensor_sha256': tensor_digest(model.policy.state_dict()),
        'num_timesteps': model.num_timesteps, 'learning_curve_sha256': sha256(curve)}, indent=2))
'''


def stage_repro():
    """Clean clone of HEAD: rebuild the JAR, then one physical case and one small learning run in both trees."""
    repro = OUT / 'repro'
    clone = repro / 'clone'
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    tracked_dirty = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=no', '--', 'research_v2', 'ifogsim/src',
                                    'ifogsim/build_v2.py', 'configs', 'schemas'], cwd=ROOT, capture_output=True, text=True).stdout
    require(not tracked_dirty.strip(), f'tracked source differs from HEAD; commit first:\n{tracked_dirty}')
    shutil.rmtree(repro, ignore_errors=True)
    repro.mkdir(parents=True)
    log(f'reproduction: clean clone of {head[:12]} and JAR rebuild')
    subprocess.run(['git', 'clone', '--quiet', '--no-hardlinks', str(ROOT), str(clone)], check=True)
    subprocess.run(['git', 'checkout', '--quiet', head], cwd=clone, check=True)
    env_clone = {**os.environ, 'PYTHONPATH': str(clone)}
    env_main = {**os.environ, 'PYTHONPATH': str(ROOT)}
    with (repro / 'build.log').open('w') as sink:
        code = subprocess.run([sys.executable, 'ifogsim/build_v2.py', '--jdk-home', JDK], cwd=clone, env=env_clone,
                              stdout=sink, stderr=subprocess.STDOUT).returncode
    require(code == 0, f'clean-clone JAR build failed; see {repro / "build.log"}')
    from .engine_runner import JAR
    a, b = jar_entries(JAR), jar_entries(clone / 'ifogsim/dist/research-v2-foundation.jar')
    content = {n: h for n, h in a.items() if not n.endswith('/') and n != 'META-INF/MANIFEST.MF'}
    rebuilt = {n: h for n, h in b.items() if not n.endswith('/') and n != 'META-INF/MANIFEST.MF'}
    jar_same = content == rebuilt
    differing = sorted(n for n in set(content) | set(rebuilt) if content.get(n) != rebuilt.get(n))
    worker = repro / 'worker.py'
    worker.write_text(REPRO_WORKER)
    checkpoint = read_json(OUT / 'audit/model_index.json')['nsga2_r00']['checkpoint']
    results = {}
    for tree, cwd, env in (('main', ROOT, env_main), ('clone', clone, env_clone)):
        stopped()
        log(f'reproduction: physical case and 1,024-decision learning run in the {tree} tree')
        for mode, extra in (('physical', [str(ROOT / checkpoint), JDK]), ('learn', [JDK])):
            target = repro / f'{tree}_{mode}'
            target_arg = target.with_suffix('.json') if mode == 'physical' else target
            if mode == 'learn':
                target.mkdir()
            with (repro / f'{tree}_{mode}.log').open('w') as sink:
                code = subprocess.run([sys.executable, str(worker), mode, str(target_arg), *extra], cwd=cwd, env=env,
                                      stdout=sink, stderr=subprocess.STDOUT).returncode
            require(code == 0, f'reproduction {tree}/{mode} failed; see {repro / f"{tree}_{mode}.log"}')
        results[tree] = {'physical': json.loads((repro / f'{tree}_physical.json').read_text()),
                         'learn': json.loads((repro / f'{tree}_learn/result.json').read_text())}
    physical_same = results['main']['physical'] == results['clone']['physical']
    learn_same = results['main']['learn'] == results['clone']['learn']
    result = {'created_utc': now(), 'head': head, 'clone': 'git clone of HEAD (removed after the check)',
              'environment': 'same container and Python venv; clean git clone of HEAD; JAR rebuilt from source in the clone',
              'jar_rebuild': {'class_and_resource_entries_identical': jar_same, 'differing_entries': differing[:20],
                              'main_jar_sha256': file_sha256(JAR),
                              'rebuilt_jar_sha256': file_sha256(clone / 'ifogsim/dist/research-v2-foundation.jar'),
                              'note': 'whole-file hashes may differ by zip timestamps; entry contents are compared'},
              'physical_case': {'identical': physical_same, 'cases': len(results['main']['physical']),
                                'description': 'greedy_eft and the nsga2_r00 P11 checkpoint on validation trace 10000 (light, heavy)'},
              'learning_run': {'identical': learn_same, **results['main']['learn'],
                               'description': '1,024-decision PPO run (pilot outer 100, repeat 0, equal weights, learner v0.3)'}}
    result['pass'] = jar_same and physical_same and learn_same
    dump(repro / 'result.json', result)
    shutil.rmtree(clone, ignore_errors=True)     # ~1 GiB; the result, logs and both trees' outputs are kept
    require(result['pass'], f'reproduction differs; see {(repro / "result.json").relative_to(ROOT)}')
    mark('repro', jar_entries_identical=jar_same, physical_identical=physical_same, learning_identical=learn_same)
    log('reproduction passed: rebuilt JAR entries, physical case and learning run identical in a clean clone')


def stage_package(hash_decision_logs=False):
    pkg = OUT / 'package'
    pkg.mkdir(parents=True, exist_ok=True)
    tracked = subprocess.run(['git', 'ls-files', '-z', '--', 'results/research_v2/v0.4', 'docs/research_v2', 'configs/research_v2'],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout.split('\0')
    tracked = [t for t in tracked if t and (ROOT / t).is_file()]
    index = {'created_utc': now(), 'lock_sha256': read_json(LOCK)['lock_sha256'],
             'git_head': subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
             'in_git': {}, 'local_only': {}}
    for t in tracked:
        index['in_git'][t] = {'bytes': (ROOT / t).stat().st_size, 'sha256': file_sha256(ROOT / t)}
    for name, entry in read_json(OUT / 'audit/model_index.json').items():
        path = ROOT / entry['checkpoint'] / 'model.zip'
        index['local_only'][str(path.relative_to(ROOT))] = {'bytes': path.stat().st_size, 'sha256': file_sha256(path), 'model': name}
    logs = sorted((BASE / 'p11').glob('shard_*/jobs/*/attempt_*/data/**/decisions.jsonl.gz'))
    index['decision_logs'] = {'files': len(logs), 'bytes': sum(p.stat().st_size for p in logs), 'hashed': hash_decision_logs}
    if hash_decision_logs:
        for p in logs:
            stopped()
            index['local_only'][str(p.relative_to(ROOT))] = {'bytes': p.stat().st_size, 'sha256': file_sha256(p)}
    dump(pkg / 'ARTIFACT_INDEX.json', index)
    sums = [f'{v["sha256"]}  {k}' for k, v in sorted({**index['in_git'], **index['local_only']}.items())]
    (pkg / 'SHA256SUMS').write_text('\n'.join(sums) + '\n')
    (pkg / 'README_REPRODUCTION.md').write_text(README.format(lock=index['lock_sha256'], head=index['git_head'],
                                                              logs=index['decision_logs']['files'],
                                                              gib=index['decision_logs']['bytes'] / 2 ** 30))
    mark('package', in_git=len(index['in_git']), local_only=len(index['local_only']))
    log(f'package written: {pkg.relative_to(ROOT)} ({len(index["in_git"])} tracked files, {len(index["local_only"])} local checkpoints hashed)')


README = """# Reproduction package — research v2, protocol v0.4

Protocol lock `P10-lock-3`, sha256 `{lock}`; source at git `{head}`.

## What is where

| Item | Location |
|---|---|
| Confirmatory result (P11) | `results/research_v2/v0.4/p11/test_evaluation/report.md` (+ `report.json`, per-episode rows in `episodes/`) |
| Protocol, lock, deviations | `docs/research_v2/PROTOCOL_v0.4.md`, `results/research_v2/v0.4/protocol_lock/protocol_lock.json`, `deviations_from_v02.json` |
| Test opening record | `results/research_v2/TEST_OPENED.json` |
| Sensitivity (exploratory) | `results/research_v2/v0.4/p12/sensitivity/report.md` |
| Final audit | `results/research_v2/v0.4/p12/audit/audit.json`, model index `audit/model_index.json` |
| Clean-clone reproduction | `results/research_v2/v0.4/p12/repro/result.json` |
| Claims and limits | `results/research_v2/v0.4/p12/claims.md` |
| Checksums | `SHA256SUMS`, `ARTIFACT_INDEX.json` (git-tracked files and the 120 evaluated checkpoints) |

Not in git (archive separately with `SHA256SUMS`): the 120 evaluated `model.zip` checkpoints and their per-checkpoint metadata,
{logs} gzip decision logs (~{gib:.0f} GiB), and the remaining intermediate checkpoints (`results/research_v2/ARTIFACTS_NOT_IN_GIT.md`).

## Reproduce

```bash
git clone <repo> && cd IFogsim2-ERWOPPO && git checkout {head}
python3.12 -m venv venv && venv/bin/pip install -r requirements-v2-learning.txt -r requirements-v2-analysis.txt
venv/bin/python ifogsim/build_v2.py --jdk-home /path/to/jdk-21          # JAR; entry contents must match the lock
PYTHONPATH=. venv/bin/python -m research_v2.analysis.lock verify --lock results/research_v2/v0.4/protocol_lock/protocol_lock.json
./run_p11_v04.sh go-open-test     # full P11 (~1.5-2.5 days on 16 CPUs): training, test evaluation, registered analysis
./run_p12.sh                      # sensitivity, audit, reproduction checks, package, claims (~8-10 h)
```

To re-check the published numbers without retraining: restore the archived checkpoints at the paths listed in
`ARTIFACT_INDEX.json` (verify with `sha256sum -c SHA256SUMS`), then run the P11 analysis from the stored episode rows
(`research_v2.p12` stage `audit` does exactly this and compares with `report.json`).

The analysis is deterministic (fixed bootstrap and sign-flip seeds). PPO training is deterministic on the same CPU build of
PyTorch with one thread; across machines, small numerical differences in training are possible and are not hidden.
"""


def fmt_ci(c):
    return f'[{c[0]:.4f}, {c[1]:.4f}]'


def stage_claims():
    p11 = read_json(P11_EVAL / 'report.json')
    sens = read_json(OUT / 'sensitivity/report.json')
    primary = {x['id']: x for x in p11['primary']}
    variants = [n for n in sens['physical'] if n != 'main (P11)']
    budget = read_json(STUDIES[0] / 'protocol.json')['budget']

    def kept(k):
        return sum(sens['physical'][v]['comparisons'][k]['same_sign_as_main'] for v in variants)

    def status(x, better):
        sig = x['holm_adjusted_p'] < 0.05
        if sig and (x['mean_difference'] > 0) == better:
            return 'supported'
        if sig:
            return 'contradicted (significant in the opposite direction)'
        return 'not supported (insufficient evidence; not equivalence)'
    lines = ['# P12 — claims table (protocol v0.4)', '',
             'Status follows the registered P11 analysis; sensitivity is exploratory and only qualifies robustness.', '',
             '| # | Claim | Evidence | Status |', '|---|---|---|---|']
    texts = {'RQ1': 'NSGA-II reward weights make PPO better than equal weights at the same final budget F',
             'RQ2': 'NSGA-II reward weights make PPO better than random-search weights',
             'RQ3': 'Weight search + training at F is better than equal weights trained with the same total compute B'}
    for k, rq in enumerate(PAIR_IDS):
        x = primary[rq]
        lines.append(f'| {rq} | {texts[rq]} | diff {x["mean_difference"]:.4f}, 95% CI {fmt_ci(x["ci95_difference"])}, '
                     f'Holm p {x["holm_adjusted_p"]:.3g}; direction kept in {kept(k)}/{len(variants)} sensitivity variants | '
                     f'{status(x, True)} |')
    heur = {r['comparator']: r for r in p11['exploratory'] if r['treatment'] == 'nsga2'}
    for name, r in heur.items():
        verdict = 'exploratory: PPO better' if r['raw_p_exact_signflip'] < 0.05 and r['mean_difference'] > 0 else \
            ('exploratory: heuristic better' if r['raw_p_exact_signflip'] < 0.05 else 'exploratory: no clear difference')
        lines.append(f'| E | NSGA-II PPO vs `{name}` heuristic | diff {r["mean_difference"]:.4f}, CI {fmt_ci(r["ci95_difference"])}, '
                     f'raw p {r["raw_p_exact_signflip"]:.3g} | {verdict} |')
    lines += ['', '## Limits of every claim', '',
              '- Simulation only (iFogSim2/CloudSim, synthetic parameters; F3 power anchored to one example). No real testbed.',
              '- Workloads are synthetic Poisson traces in four regimes; 100 test traces per workload; one topology (100 IoT, 5 fogs, 1 cloud).',
              '- Energy model: linear idle/busy power plus per-bit network energy; idle energy identical across methods on a trace.',
              '- Observability: the 108-feature public snapshot; heuristics see the same snapshot; no look-ahead.',
              '- One learner configuration (PPO, gamma 0.97 from a pilot diagnosis; protocol v0.3), n = 20 outer training runs.',
              '- The registered design changed twice before the test was opened (v0.2 -> v0.3 -> v0.4); all versions are archived.',
              f'- Compute: each weight search costs S + V = {budget["S"] + budget["V"]:,} decisions per outer run before the final model '
              f'(F = {budget["F"]:,}); the compute-matched baseline trains for B = {budget["B"]:,}.',
              '- Sensitivity is zero-shot and one factor at a time on frozen models (exploratory); it does not show retrained robustness.',
              '- Non-significant results mean insufficient evidence, not equivalence. Test findings were not used to retune anything.',
              '- Literature mapping / novelty statement: still to be updated by the authors before any state-of-the-art claim.']
    (OUT / 'claims.md').write_text('\n'.join(lines) + '\n')
    mark('claims')
    log(f'claims table written: {(OUT / "claims.md").relative_to(ROOT)}')


# ------------------------------------------------------------------------------------------------ entry points

def progress():
    index = read_json(OUT / 'variants/index.json') if (OUT / 'variants/index.json').exists() else {}
    lines = []
    for name in [n for n in index if n != 'identity'] + ['validation']:
        directory = episodes_dir('main', 'validation') if name == 'validation' else episodes_dir(name, 'test')
        n = len(list(directory.glob('*.jsonl'))) if directory.exists() else 0
        lines.append(f'  {name:<18} {n:>3}/124 evaluation tasks')
    return '\n'.join(lines)


def status():
    print(json.dumps(state(), indent=2))
    print(progress())
    print(f'log: {LOG}')


def run(workers, draws, hash_logs):
    if not done('preflight'):
        stage_preflight()
    if not done('variants'):
        index = build_variants()
        mark('variants', variants=list(index))
        log(f'variants built: {", ".join(index)} (variant JARs differ from the main JAR only in the config resource)')
    if not done('identity_check'):
        stage_identity(workers)
    stopped()
    if not done('audit'):
        stage_audit()
    stopped()
    if not done('repro'):
        stage_repro()
    stopped()
    if not done('evaluations'):
        index = read_json(OUT / 'variants/index.json')
        tasks = all_tasks(['main'], 'validation') + all_tasks([n for n in index if n != 'identity'], 'test')
        run_pool(tasks, workers, 'sensitivity evaluation')
        mark('evaluations', tasks=len(tasks))
    stopped()
    if not done('sensitivity_analysis'):
        stage_analysis(draws)
    stopped()
    if not done('package'):
        stage_package(hash_logs)
    if not done('claims'):
        stage_claims()
    log('=== P12 all stages complete ===')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    r = sub.add_parser('run')
    r.add_argument('--workers', type=int, default=12)
    r.add_argument('--bootstrap-draws', type=int, default=None, help='default: the registered statistics.bootstrap_draws')
    r.add_argument('--hash-decision-logs', action='store_true', help='also checksum the ~490 GiB of decision logs (slow)')
    sub.add_parser('status')
    t = sub.add_parser('task')
    t.add_argument('--variant', required=True)
    t.add_argument('--split', choices=('test', 'validation'), required=True)
    t.add_argument('--label', required=True)
    t.add_argument('--outer', type=int, required=True)
    t.add_argument('--checkpoint', default='')
    args = parser.parse_args()
    if args.command == 'status':
        status()
    elif args.command == 'task':
        task(args.variant, args.split, args.label, args.outer, args.checkpoint)
    else:
        signal.signal(signal.SIGTERM, lambda *_: STOP.update(requested=True))
        signal.signal(signal.SIGINT, lambda *_: STOP.update(requested=True))
        log(f'=== p12 run pid={os.getpid()} workers={args.workers} ===')
        draws = args.bootstrap_draws or load_config()['statistics']['bootstrap_draws']
        run(args.workers, draws, args.hash_decision_logs)


if __name__ == '__main__':
    main()
