"""Predeclared diagnostic extension of the failed P08 fidelity ladder.

This is discovery evidence. The original P08 gate and its result stay intact.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import os
from pathlib import Path
import queue
import socket
import subprocess
import sys

from .config import ROOT, load_config, read_json, require, sha256
from .learning import compare_checkpoints, file_hash, run_evaluation, run_training, write_json
from .search import fidelity_gate, repeated_objectives

LADDER = (30720, 40960, 46080)
REFERENCE = 51200
OLD = ROOT / 'results/research_v2/P08_fidelity_1'


def prepare(root):
    require(read_json(OLD / 'result.json')['selected_K'] is None, 'Original pilot must have failed')
    config = load_config()
    ports = []
    for port in config['execution']['allowed_ports']:
        sock = socket.socket()
        try:
            sock.bind(('127.0.0.1', port))
            ports.append(port)
        except OSError:
            pass
        finally:
            sock.close()
    ports = ports[:3]
    require(ports, 'No free configured port')
    old_protocol = read_json(OLD / 'protocol.json')
    root.mkdir(parents=True, exist_ok=False)
    write_json(root / 'protocol.json', {
        'version': 'P08-fidelity-extension-1',
        'prepared_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Exploratory revision after failed original ladder; original P08 result remains failed.',
        'rationale': 'Diagnose late policy drift and test additional non-reference budgets.',
        'original_result_sha256': file_hash(OLD / 'result.json'),
        'config_sha256': sha256(config),
        'jar_sha256': read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256'],
        'source_hashes': {p.relative_to(ROOT).as_posix(): file_hash(p) for p in sorted((ROOT / 'research_v2').glob('*.py'))},
        'jobs': old_protocol['jobs'], 'weights': old_protocol['weights'],
        'reference_decisions': REFERENCE, 'ladder': list(LADDER),
        'gate': 'Smallest K with median of three Spearman rho >= 0.60 and all rho >= 0; same eight weights, repeats, outer IDs, validation traces and D aggregation as original.',
        'training': 'Fresh 51200-decision trajectories checkpointed at each K; final checkpoint must exactly equal original reference. If K passes, fresh independent short models must match its prefix.',
        'ports': ports, 'workers': len(ports), 'test_accessed': False,
    })


def check(root):
    p = read_json(root / 'protocol.json')
    require(p['config_sha256'] == sha256(load_config()), 'Config drift')
    require(p['jar_sha256'] == read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256'], 'JAR drift')
    require(p['original_result_sha256'] == file_hash(OLD / 'result.json'), 'Original result drift')
    for name, digest in p['source_hashes'].items():
        require(file_hash(ROOT / name) == digest, f'Source drift: {name}')
    return p


def worker(root, index, port, jdk, budget=None):
    p = check(root)
    j = p['jobs'][index]
    base = root / 'models' / j['id']
    base.mkdir(parents=True, exist_ok=True)
    if budget is None:
        path = base / 'reference_extended'
        if not path.exists():
            run_training(path, j['outer'], j['repeat'], REFERENCE, j['weights'], jdk,
                         phase='P08', checkpoint_at=[*LADDER, REFERENCE], fast_rpc=True, worker_port=port)
        require(read_json(path / 'outcome.json')['status'] == 'complete', 'Incomplete extended reference')
        matched = compare_checkpoints(path / f'checkpoint_{REFERENCE:08d}',
                                      OLD / 'models' / j['id'] / 'reference' / f'checkpoint_{REFERENCE:08d}')
        require(matched['pass'], 'Extended reference differs from original')
        for k in LADDER:
            dest = base / f'K{k:06d}_validation'
            if not dest.exists():
                run_evaluation(path / f'checkpoint_{k:08d}', dest, jdk, fast_rpc=True, worker_port=port)
            require(read_json(dest / 'summary.json')['status'] == 'complete', 'Incomplete validation')
        write_json(base / 'extended_complete.json', {'job': j['id'], 'original_final_match': True})
    else:
        require(budget in LADDER, 'Budget outside frozen extension')
        path = base / f'K{budget:06d}_independent'
        if not path.exists():
            run_training(path, j['outer'], j['repeat'], budget, j['weights'], jdk,
                         phase='P08', checkpoint_at=[budget], fast_rpc=True, worker_port=port)
        require(read_json(path / 'outcome.json')['status'] == 'complete', 'Incomplete independent run')
        matched = compare_checkpoints(path / f'checkpoint_{budget:08d}',
                                      base / 'reference_extended' / f'checkpoint_{budget:08d}')
        require(matched['pass'], 'Independent short model differs from extended prefix')
        write_json(base / f'K{budget:06d}_prefix.json', matched)


def parallel(root, jdk, budget=None):
    p = check(root)
    ports = queue.Queue()
    for port in p['ports']:
        ports.put(port)
    env = os.environ.copy()
    for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        env[key] = '1'

    def run_one(index):
        port = ports.get()
        try:
            cmd = [sys.executable, '-m', 'research_v2.fidelity_extension', 'worker',
                   '--evidence-dir', str(root), '--index', str(index), '--port', str(port),
                   '--jdk-home', str(jdk)]
            if budget is not None:
                cmd.extend(['--budget', str(budget)])
            log = root / f'{p["jobs"][index]["id"]}_{"reference" if budget is None else f"K{budget:06d}_independent"}.log'
            with log.open('a') as sink:
                result = subprocess.run(cmd, env=env, stdout=sink, stderr=subprocess.STDOUT)
            require(result.returncode == 0, f'Worker failed: {log}')
            return p['jobs'][index]['id']
        finally:
            ports.put(port)

    with ThreadPoolExecutor(max_workers=p['workers']) as pool:
        futures = [pool.submit(run_one, index) for index in range(len(p['jobs']))]
        for count, future in enumerate(as_completed(futures), 1):
            job = future.result()
            write_json(root / 'progress.json', {'phase': 'extended_reference' if budget is None else 'independent_prefix',
                                               'budget': budget, 'completed': count, 'total': len(futures), 'last_job': job})
            print(count, '/', len(futures), job, flush=True)


def report(root):
    p = check(root)
    stages = []
    for k in LADDER:
        short, ref = [], []
        for outer in (100, 101, 102):
            x, y = [], []
            for w in p['weights']:
                jobs = [j for j in p['jobs'] if j['outer'] == outer and j['weight_id'] == w['id']]
                require(len(jobs) == 2, 'Missing repeats')
                x.append(repeated_objectives([read_json(root / 'models' / j['id'] /
                    f'K{k:06d}_validation' / 'summary.json')['macro_costs'] for j in jobs])['D'])
                y.append(repeated_objectives([read_json(OLD / 'models' / j['id'] /
                    'reference_validation' / 'summary.json')['macro_costs'] for j in jobs])['D'])
            short.append(x); ref.append(y)
        stages.append({'K': k, **fidelity_gate(short, ref), 'short_D': short, 'reference_D': ref})
    selected = next((s['K'] for s in stages if s['pass']), None)
    result = {'version': p['version'], 'status': 'extension_gate_pass' if selected else 'extension_gate_failed',
              'selected_K': selected, 'stages': stages, 'reference_final_matches': 48,
              'independent_prefix_checks': 0, 'test_accessed': False,
              'training_decisions': 48 * REFERENCE, 'evaluation_episodes': 48 * len(LADDER) * 20,
              'original_gate_status': 'fidelity_failed_stop'}
    write_json(root / 'result.json', result)
    print('EXTENSION GATE', [(s['K'], s['correlations'], s['pass']) for s in stages], flush=True)
    if selected is not None:
        print('Independent prefix confirmation needed at', selected, flush=True)
    return selected


def confirm(root, jdk):
    result = read_json(root / 'result.json')
    require(result['selected_K'] in LADDER, 'No passing K')
    parallel(root, jdk, result['selected_K'])
    result['independent_prefix_checks'] = 48
    result['training_decisions'] += 48 * result['selected_K']
    result['status'] = 'extension_confirmed'
    write_json(root / 'result.json', result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'run', 'worker', 'report', 'confirm'))
    parser.add_argument('--evidence-dir', required=True, type=Path)
    parser.add_argument('--jdk-home', type=Path, default=Path('/usr/lib/jvm/java-21-openjdk-amd64'))
    parser.add_argument('--index', type=int)
    parser.add_argument('--port', type=int)
    parser.add_argument('--budget', type=int)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.evidence_dir)
    elif args.command == 'run':
        parallel(args.evidence_dir, args.jdk_home)
    elif args.command == 'worker':
        worker(args.evidence_dir, args.index, args.port, args.jdk_home, args.budget)
    elif args.command == 'report':
        report(args.evidence_dir)
    else:
        confirm(args.evidence_dir, args.jdk_home)


if __name__ == '__main__':
    main()
