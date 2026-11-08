"""One command for protocol v0.4: preparation -> lock -> P11 training -> test evaluation -> registered analysis.

    PYTHONPATH=. venv/bin/python -m research_v2.p11_v04 run                      # preparation + lock only (safe, ~20 min)
    PYTHONPATH=. venv/bin/python -m research_v2.p11_v04 run --go                 # + P11 training (M3 = go; ~1.5-2.5 days)
    PYTHONPATH=. venv/bin/python -m research_v2.p11_v04 run --go --open-test     # + test evaluation and analysis (irreversible)
    PYTHONPATH=. venv/bin/python -m research_v2.p11_v04 status                   # progress, from any terminal

Every stage is idempotent: re-running the same command after an interruption, a crash or a container restart continues where
it stopped (completed jobs are verified and reused, interrupted ones restart from scratch with the same seeds). SIGTERM/Ctrl-C
stops all shard runners gracefully. Training pauses (exit 75) if free disk falls below --min-free-gib.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from .config import ROOT, load_config, read_json, require

BASE = ROOT / 'results/research_v2/v0.4'
DESIGN = ROOT / 'configs/research_v2/design_v0.4.json'
LOCK = BASE / 'protocol_lock/protocol_lock.json'
STATE = BASE / 'pipeline/state.json'
LOG = BASE / 'pipeline/pipeline.log'
SHARDS = [(2 * i, 2 * i + 1) for i in range(10)]
JDK = '/usr/lib/jvm/java-21-openjdk-amd64'
STOP = {'requested': False}


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


def sh(args, name, timeout=None):
    """Run a module of this package, streaming output into its own log; raise on failure."""
    out = BASE / 'pipeline' / f'{name}.log'
    log(f'  -> {" ".join(args)}  (log: {out.relative_to(ROOT)})')
    env = {**os.environ, 'PYTHONPATH': str(ROOT)}
    with out.open('a') as sink:
        code = subprocess.run([sys.executable, '-u', '-m', *args], cwd=ROOT, env=env, stdout=sink, stderr=subprocess.STDOUT,
                              timeout=timeout).returncode
    require(code == 0, f'Stage step failed: {" ".join(args)} (exit {code}); see {out}')


def free_gib():
    return shutil.disk_usage(ROOT).free / 2 ** 30


def preparation():
    from .fidelity_v03 import require_fidelity_gate
    if not done('preflight'):
        K, learner = require_fidelity_gate(DESIGN)
        quota = Path('/sys/fs/cgroup/cpu.max').read_text().split()
        mark('preflight', K=K, learner=learner, free_disk_gib=round(free_gib()), cpu_max=quota)
        log(f'preflight ok: K={K:,} learner v{learner}, free disk {free_gib():.0f} GiB, cpu.max {quota}')
    dry = BASE / 'dry_run_full/budget_report.json'
    if not done('dry_run'):
        dry.parent.mkdir(parents=True, exist_ok=True)
        env = {**os.environ, 'PYTHONPATH': str(ROOT)}
        text = subprocess.run([sys.executable, '-m', 'research_v2.study_runner', 'plan', '--outers', *map(str, range(20)),
                               '--fidelity-evidence', str(DESIGN)], cwd=ROOT, env=env, capture_output=True, text=True, check=True).stdout
        dry.write_text(text)
        b = json.loads(text)
        mark('dry_run', K=b['K'], B=b['B'], total=b['physical_total_all_outers'])
        log(f'dry run: S={b["S"]:,} V={b["V"]:,} C={b["C"]:,} B={b["B"]:,} total={b["physical_total_all_outers"]:,} decisions')
    if not done('p09_evidence'):
        log('P09 live evidence for v0.4 code (~15-20 min)')
        sh(['research_v2.verify_study', '--root', str(BASE / 'p09_runner_evidence'), '--dry-run', str(dry.relative_to(ROOT)),
            '--parallel-runners', '10'], 'p09_evidence')
        live = read_json(BASE / 'p09_runner_evidence/live_evidence.json')
        mark('p09_evidence', parallel_efficiency=live['parallel'].get('throughput_efficiency'))
    if not done('p09_verification'):
        sh(['research_v2.analysis.verify', 'p09', '--protocol-version', '0.4', '--output', str(BASE / 'P09_verification.json')],
           'p09_verification')
        mark('p09_verification')
    if not done('mini_report'):
        target = BASE / 'mini_report'
        shutil.rmtree(target, ignore_errors=True)
        sh(['research_v2.analysis.report', 'mini', '--study-dir', str(BASE / 'p09_runner_evidence/reference'),
            '--output-dir', str(target)], 'mini_report')
        mark('mini_report')
    if not done('eval_dry_run'):
        target = BASE / 'eval_dry_run'
        shutil.rmtree(target, ignore_errors=True)
        log('evaluation code dry run on the validation split (fixture studies; test stays sealed)')
        sh(['research_v2.p11_eval', 'run', '--output-dir', str(target), '--split', 'validation', '--workers', '10',
            '--studies', str(BASE / 'p09_runner_evidence/reference')], 'eval_dry_run')
        mark('eval_dry_run')
    if not done('resources'):
        sh(['research_v2.analysis.verify', 'resources', '--protocol-version', '0.4', '--output', str(BASE / 'resource_estimate.json')],
           'resources')
        r = read_json(BASE / 'resource_estimate.json')
        mark('resources', recommended_workers=r['worker_limits']['recommended'])
    if not done('deviations'):
        v02 = read_json(ROOT / 'results/research_v2/P10_deviations_from_v02.json')
        extra = [
            'v0.3: learner gamma 1.0 -> 0.97 via configs/research_v2/learner_v0.3.json (simulation config, traces and JAR unchanged); '
            'chosen by a pilot-namespace diagnosis (results/research_v2/P10_learning_diagnosis/report.md).',
            'v0.3: the registered fidelity gate (same thresholds as v0.2, reference = F) failed at every K; v0.3 stopped without a lock.',
            'v0.4: K = F = 102,400 (configs/research_v2/design_v0.4.json); no short-budget proxy and therefore no proxy-fidelity gate.',
            'v0.4: per-decision audit logs are streamed into gzip during training; P11 runs 10 sharded studies in parallel '
            '(container quota 16 CPU / 64 GiB).',
            'Seeds: confirmatory outer runs 0-19 were used for validation-only exploratory checks in P10 (v0.2 learner); no test trace was touched.',
            'Known limitation: in the pilot, independent seeds ranked the 8 pilot weights with median Spearman 0.095 at F; power may be limited.',
            'Archives: v0.2 at tag protocol-v0.2 (its lock verifies there), v0.3 at tag protocol-v0.3.']
        (BASE / 'deviations_from_v02.json').write_text(json.dumps(v02 + extra, indent=2, ensure_ascii=False))
        mark('deviations', entries=len(v02) + len(extra))
    if not done('lock'):
        if not LOCK.exists():
            sh(['research_v2.analysis.lock', 'create', '--protocol-version', '0.4', '--output', str(LOCK),
                '--fidelity-evidence', str(DESIGN), '--resource-estimate', str(BASE / 'resource_estimate.json'),
                '--deviations', str(BASE / 'deviations_from_v02.json')], 'lock')
        sh(['research_v2.analysis.lock', 'verify', '--lock', str(LOCK), '--deep'], 'lock')
        mark('lock', lock_sha256=read_json(LOCK)['lock_sha256'])
        log(f'protocol lock v0.4 created and verified: {LOCK.relative_to(ROOT)}')
    if not done('p10_verification'):
        sh(['research_v2.analysis.verify', 'p10', '--protocol-version', '0.4', '--output', str(BASE / 'P10_verification.json'),
            '--lock', str(LOCK)], 'p10_verification')
        mark('p10_verification')


def shard_dir(i):
    return BASE / 'p11' / f'shard_{i:02d}'


def training(min_free):
    from .analysis.lock import require_valid_lock
    require_valid_lock(LOCK)
    env = {**os.environ, 'PYTHONPATH': str(ROOT)}
    for i, outers in enumerate(SHARDS):
        if not (shard_dir(i) / 'protocol.json').exists():
            subprocess.run([sys.executable, '-m', 'research_v2.study_runner', 'prepare', '--study-dir', str(shard_dir(i)),
                            '--outers', *map(str, outers), '--fidelity-evidence', str(DESIGN)], cwd=ROOT, env=env,
                           capture_output=True, text=True, check=True)
    pending = [i for i in range(len(SHARDS)) if not (shard_dir(i) / 'summary.json').exists()]
    log(f'P11 training: {len(pending)} of {len(SHARDS)} shards to run (2 outer runs each)')
    running = {}
    for i in pending:
        sink = (BASE / 'p11' / f'shard_{i:02d}.log').open('a')
        running[i] = subprocess.Popen([sys.executable, '-u', '-m', 'research_v2.study_runner', 'resume', '--study-dir', str(shard_dir(i)),
                                       '--jdk-home', JDK], cwd=ROOT, env=env, stdout=sink, stderr=subprocess.STDOUT)
    last = 0
    while running:
        for i, process in list(running.items()):
            if process.poll() is not None:
                code = running.pop(i).returncode
                log(f'shard {i:02d} exited {code}' + (' (complete)' if code == 0 else ''))
                require(code in (0, 75), f'Shard {i:02d} failed with exit {code}; see results/research_v2/v0.4/p11/shard_{i:02d}.log')
        low = free_gib() < min_free
        if (STOP['requested'] or low) and running:
            log('stopping all shards gracefully: ' + ('free disk below threshold' if low else 'stop requested'))
            for process in running.values():
                process.send_signal(signal.SIGTERM)
            for process in running.values():
                process.wait()
            raise SystemExit(75)
        if time.monotonic() - last > 900:
            log(progress_line())
            last = time.monotonic()
        time.sleep(10)
    complete = all((shard_dir(i) / 'summary.json').exists() for i in range(len(SHARDS)))
    require(complete, 'Some shards are not complete; re-run the same command to resume')
    mark('p11_training')
    log('P11 training complete for all 20 outer runs')


def progress_line():
    total = done_jobs = 0
    for i in range(len(SHARDS)):
        if (shard_dir(i) / 'protocol.json').exists():
            jobs = read_json(shard_dir(i) / 'protocol.json')['jobs']
            total += len(jobs)
            done_jobs += sum((shard_dir(i) / 'jobs' / j['id'] / 'complete.json').exists() for j in jobs)
    return f'progress: {done_jobs}/{total} jobs complete, free disk {free_gib():.0f} GiB'


def evaluation():
    target = BASE / 'p11' / 'test_evaluation'
    log('opening the TEST split (lock verified first) and evaluating all models + heuristics')
    sh(['research_v2.p11_eval', 'run', '--output-dir', str(target), '--split', 'test', '--lock', str(LOCK), '--workers', '12',
        '--studies', *[str(shard_dir(i)) for i in range(len(SHARDS))]], 'test_evaluation')
    report = read_json(target / 'report.json')
    mark('p11_test_and_analysis', confirmatory=report['confirmatory'],
         primary=[(x['id'], x['mean_difference'], x['holm_adjusted_p']) for x in report['primary']])
    log(f'analysis written: {(target / "report.md").relative_to(ROOT)}')


def status():
    s = state()
    print(json.dumps(s, indent=2))
    if (BASE / 'p11').exists():
        print(progress_line())
    print(f'log: {LOG}')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    r = sub.add_parser('run')
    r.add_argument('--go', action='store_true', help='M3 decision = go: run P11 training after the lock')
    r.add_argument('--open-test', action='store_true', help='after training, open the test split and run the registered analysis')
    r.add_argument('--min-free-gib', type=float, default=60.0)
    sub.add_parser('status')
    args = parser.parse_args()
    if args.command == 'status':
        status()
        return
    require(not args.open_test or args.go, '--open-test requires --go')
    signal.signal(signal.SIGTERM, lambda *_: STOP.update(requested=True))
    signal.signal(signal.SIGINT, lambda *_: STOP.update(requested=True))
    log(f'=== p11_v04 run (go={args.go}, open_test={args.open_test}) pid={os.getpid()} ===')
    preparation()
    if not args.go:
        log('preparation complete; lock verified. Re-run with --go to start P11 training.')
        return
    if not done('p11_training'):
        mark('m3_go', decided_by='operator flag --go')
        training(args.min_free_gib)
    if not args.open_test:
        log('training complete. Re-run with --go --open-test to evaluate the test split and run the analysis.')
        return
    if not done('p11_test_and_analysis'):
        evaluation()
    log('=== all stages complete ===')


if __name__ == '__main__':
    main()
