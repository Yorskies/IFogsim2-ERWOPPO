"""P09 live evidence for the study runner. Fixture-sized studies only; test split is never opened.

Scenarios (all against real JVM servers, small mini studies):
  prefix      F-only training equals the F checkpoint of a longer B run with the same weights/seed.
  reference   uninterrupted mini study, four outers (sequential, one worker).
  interrupt   second-writer refusal, SIGTERM, resume, runner crash, stale lock, worker crash + technical retry,
              completed-job reuse; final artifacts compared with `reference`.
  drift       tampered source/config/artifact on copies of the completed study is refused.
  parallel    four independent single-outer studies run concurrently (own runner, JVM, port) and compared with
              `reference`.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from .config import ROOT, read_json
from .learning import compare_checkpoints, file_hash, write_json
from .study_final import run_final_training

PY = sys.executable


def runner(args, log, wait=False):
    process = subprocess.Popen([PY, '-m', 'research_v2.study_runner', *args], cwd=ROOT,
                               stdout=open(log, 'ab'), stderr=subprocess.STDOUT)
    if wait:
        process.wait()
    return process


def v2_servers():
    """PIDs of research-v2 JVM servers (the legacy iFogSim process has no --config-sha256)."""
    found = {}
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            command = (entry / 'cmdline').read_bytes().split(b'\0')
        except OSError:
            continue
        if b'--config-sha256' in command and any(b'java' in part for part in command[:1]):
            found[int(entry.name)] = [part.decode() for part in command]
    return found


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def pgroup_alive(pgid):
    for entry in Path('/proc').iterdir():
        if entry.name.isdigit():
            try:
                stat = (entry / 'stat').read_text().rsplit(')', 1)[1].split()
            except (OSError, IndexError):
                continue
            if int(stat[2]) == pgid and stat[0] != 'Z':
                return True
    return False


def wait_for(predicate, timeout, what):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.2)
    raise TimeoutError(what)


def attempt_status(study, job, index):
    path = study / 'jobs' / job / f'attempt_{index:03d}' / 'status.json'
    return read_json(path)['status'] if path.exists() else None


def complete(study, job):
    return (study / 'jobs' / job / 'complete.json').exists()


def lock_child(study):
    path = study / '.owner.lock'
    return read_json(path).get('child_pid') if path.exists() else None


def attempts(study):
    return {p.name: sorted(x.name for x in p.glob('attempt_*')) for p in sorted((study / 'jobs').glob('*'))}


def prepare(study, outers, log):
    code = runner(['prepare', '--study-dir', str(study), '--mini', '--outers', *map(str, outers)], log, wait=True)
    assert code.returncode == 0, f'prepare failed for {study}'


def job_content(study, job_id):
    """Deterministic content only: weights, RNG, optimizer, stream counters, validation rows."""
    pointer = read_json(study / 'jobs' / job_id / 'complete.json')
    attempt = study / pointer['attempt']
    data = attempt / 'data'
    out = {'result': {k: v for k, v in read_json(data / 'result.json').items()}, 'checkpoints': {}, 'validation': {}}
    roots = [data / 'training'] if (data / 'training').exists() else sorted((data / 'candidates').glob('slot_*/model_*'))
    for root in roots:
        for checkpoint in sorted(root.glob('checkpoint_*')):
            out['checkpoints'][str(checkpoint.relative_to(data))] = checkpoint
    for summary in sorted(data.glob('**/summary.json')):
        rows = [json.loads(line) for line in (summary.parent / 'episodes.jsonl').read_text().splitlines()]
        out['validation'][str(summary.parent.relative_to(data))] = [
            {k: r[k] for k in ('namespace', 'trace_sha256', 'decisions', 'reward', 'action_counts')} for r in rows]
    return out


VOLATILE_KEYS = ('wall_s', 'checkpoint_sha256')  # timing, and zip bytes (zip headers embed a timestamp)


def strip_volatile(value):
    if isinstance(value, dict):
        return {k: strip_volatile(v) for k, v in value.items() if k not in VOLATILE_KEYS}
    if isinstance(value, list):
        return [strip_volatile(v) for v in value]
    return value


def compare_jobs(first, second, job_id):
    a, b = job_content(first, job_id), job_content(second, job_id)
    mismatches = []
    if strip_volatile(a['result']) != strip_volatile(b['result']):
        mismatches.append('result.json')
    if a['validation'] != b['validation']:
        mismatches.append('validation episodes')
    if a['checkpoints'].keys() != b['checkpoints'].keys():
        mismatches.append('checkpoint set')
    for name in sorted(set(a['checkpoints']) & set(b['checkpoints'])):
        if not compare_checkpoints(a['checkpoints'][name], b['checkpoints'][name])['pass']:
            mismatches.append(name)
    return {'job': job_id, 'checkpoints_compared': len(a['checkpoints']), 'mismatches': mismatches}


def scenario_prefix(root, jdk):
    short, long = root / 'prefix_F_only', root / 'prefix_B_run'
    for path in (short, long):
        shutil.rmtree(path, ignore_errors=True)
    weights = [0.2] * 5
    from .learner import CURRENT
    run_final_training(short / 'training', 0, 1024, weights, [1024], jdk, learner_version=CURRENT)
    run_final_training(long / 'training', 0, 2048, weights, [1024, 2048], jdk, learner_version=CURRENT)
    result = compare_checkpoints(short / 'training/checkpoint_00001024', long / 'training/checkpoint_00001024')
    return {'weights': weights, 'F': 1024, 'B': 2048, 'learner_version': CURRENT, 'comparison': result, 'pass': result['pass']}


def scenario_reference(root, jdk):
    study = root / 'reference'
    shutil.rmtree(study, ignore_errors=True)
    log = root / 'reference.log'
    prepare(study, [0, 1, 2, 3], log)
    code = runner(['run', '--study-dir', str(study), '--jdk-home', str(jdk)], log, wait=True)
    summary = read_json(study / 'summary.json')
    budget = read_json(study / 'budget_report.json')
    per_outer = budget['S'] + budget['F'] + 2 * budget['B']
    ok = code.returncode == 0 and summary['status'] == 'complete'
    ok = ok and summary['total_training_decisions'] == 4 * per_outer
    ok = ok and summary['candidate_validation_decisions'] == 4 * budget['V']
    ok = ok and not summary['test_accessed']
    ok = ok and all(attempts(study)[j['id']] == ['attempt_000'] for j in read_json(study / 'protocol.json')['jobs'])
    return {'outers': [0, 1, 2, 3], 'training_decisions': summary['total_training_decisions'],
            'ledger_training_decisions': 4 * per_outer, 'validation_decisions': summary['candidate_validation_decisions'],
            'ledger_validation_decisions': 4 * budget['V'], 'single_attempt_per_job': True, 'pass': ok}


def scenario_interrupt(root, jdk):
    study = root / 'interrupt'
    shutil.rmtree(study, ignore_errors=True)
    log = root / 'interrupt.log'
    prepare(study, [0], log)
    baseline_servers = set(v2_servers())
    events = []
    ok = True

    # 1. active owner refuses a second writer; SIGTERM mid-job leaves only an interrupted attempt.
    first = runner(['run', '--study-dir', str(study), '--jdk-home', str(jdk)], log)
    wait_for(lambda: attempt_status(study, 'r00_equal', 0) == 'running', 300, 'r00_equal start')
    time.sleep(6)
    second = runner(['run', '--study-dir', str(study), '--jdk-home', str(jdk)], log, wait=True)
    refused = second.returncode != 0
    child = lock_child(study)
    first.send_signal(signal.SIGTERM)
    code = first.wait(timeout=60)
    still = pgroup_alive(child) if child else False
    events.append({'step': 'second_writer_refused_then_SIGTERM', 'second_writer_refused': refused,
                   'runner_exit': code, 'worker_group_survived': still,
                   'equal_status': attempt_status(study, 'r00_equal', 0),
                   'equal_complete_pointer': complete(study, 'r00_equal'),
                   'earlier_jobs_complete': complete(study, 'r00_mini_search') and complete(study, 'r00_mini_final'),
                   'lock_released': not (study / '.owner.lock').exists(),
                   'new_v2_servers': sorted(set(v2_servers()) - baseline_servers)})
    ok &= refused and code == 75 and not still and attempt_status(study, 'r00_equal', 0) == 'interrupted'
    ok &= not complete(study, 'r00_equal') and not events[-1]['new_v2_servers'] and events[-1]['lock_released']

    # 2. resume reuses completed jobs; runner SIGKILL leaves a live owner/child that blocks recovery.
    second_log = root / 'interrupt_resume.log'
    resumed = runner(['resume', '--study-dir', str(study), '--jdk-home', str(jdk)], second_log)
    wait_for(lambda: complete(study, 'r00_equal') and attempt_status(study, 'r00_manual', 0) == 'running', 400,
             'r00_manual start')
    time.sleep(6)
    worker = lock_child(study)
    resumed.kill()
    resumed.wait()
    blocked = runner(['resume', '--study-dir', str(study), '--jdk-home', str(jdk)], second_log, wait=True)
    blocked_by_live_child = blocked.returncode != 0 and alive(worker) and (study / '.owner.lock').exists()
    os.killpg(worker, signal.SIGKILL)
    wait_for(lambda: not pgroup_alive(worker), 30, 'worker group exit')
    events.append({'step': 'runner_SIGKILL_then_host_crash_equivalent', 'blocked_while_child_alive': blocked_by_live_child,
                   'manual_complete_pointer': complete(study, 'r00_manual'),
                   'manual_attempt_status_on_disk': attempt_status(study, 'r00_manual', 0),
                   'equal_attempts': attempts(study)['r00_equal'],
                   'stale_lock_present': (study / '.owner.lock').exists()})
    ok &= blocked_by_live_child and not complete(study, 'r00_manual')

    # 3. resume from stale lock; kill only the worker python -> technical failure -> automatic retry, same seeds.
    third = runner(['resume', '--study-dir', str(study), '--jdk-home', str(jdk)], second_log)
    wait_for(lambda: attempt_status(study, 'r00_manual', 1) == 'running' and lock_child(study), 300, 'retry attempt')
    time.sleep(6)
    victim = lock_child(study)
    servers_during = sorted(set(v2_servers()) - baseline_servers)
    os.kill(victim, signal.SIGKILL)
    wait_for(lambda: attempt_status(study, 'r00_manual', 1) == 'failed', 60, 'failure recorded')
    time.sleep(2)
    code = third.wait(timeout=900)
    leftover = sorted(set(v2_servers()) - baseline_servers)
    stale = sorted(path.name for path in study.glob('.owner.stale.*.json'))
    events.append({'step': 'stale_lock_recovery_and_worker_crash_retry', 'runner_exit': code,
                   'manual_attempts': attempts(study)['r00_manual'],
                   'attempt_statuses': [attempt_status(study, 'r00_manual', i) for i in range(3)],
                   'stale_lock_archives': stale, 'servers_while_running': servers_during,
                   'leftover_v2_servers_after_run': leftover})
    statuses = events[-1]['attempt_statuses']
    ok &= code == 0 and statuses[:3] == ['interrupted', 'failed', 'complete'] and len(stale) >= 1 and not leftover
    for orphan in leftover:
        try:
            os.kill(orphan, signal.SIGKILL)
        except ProcessLookupError:
            pass

    # 4. complete study is never repeated.
    before = attempts(study)
    again = runner(['resume', '--study-dir', str(study), '--jdk-home', str(jdk)], second_log, wait=True)
    reused = again.returncode == 0 and attempts(study) == before
    events.append({'step': 'resume_complete_study', 'exit': again.returncode, 'attempt_dirs_unchanged': reused})
    ok &= reused

    # 5. interrupted/crashed history produces the same trained content as the uninterrupted reference.
    reference = root / 'reference'
    comparisons = [compare_jobs(study, reference, job) for job in
                   ('r00_mini_search', 'r00_mini_final', 'r00_equal', 'r00_manual')]
    events.append({'step': 'content_equals_uninterrupted_reference', 'comparisons': comparisons})
    ok &= all(not c['mismatches'] for c in comparisons)
    return {'events': events, 'pass': bool(ok)}


def scenario_drift(root):
    source = root / 'interrupt'
    results = []
    for name, mutate, needle in (
            ('source_hash', lambda p: p['source_hashes'].update({'research_v2/search.py': '0' * 64}), 'source drift'),
            ('config_hash', lambda p: p.update(config_sha256='0' * 64), 'config drift'),
            ('jar_hash', lambda p: p.update(jar_sha256='0' * 64), 'JAR drift'),
            ('validation_trace_manifest', lambda p: p.update(validation_manifest_sha256='0' * 64), 'trace drift')):
        copy = root / f'drift_{name}'
        shutil.rmtree(copy, ignore_errors=True)
        shutil.copytree(source, copy)
        plan = read_json(copy / 'protocol.json')
        mutate(plan)
        write_json(copy / 'protocol.json', plan)
        before = attempts(copy)
        run = subprocess.run([PY, '-m', 'research_v2.study_runner', 'resume', '--study-dir', str(copy)], cwd=ROOT,
                             capture_output=True, text=True)
        results.append({'case': name, 'exit': run.returncode, 'refused': needle.lower() in (run.stderr + run.stdout).lower(),
                        'nothing_started': attempts(copy) == before})
    copy = root / 'drift_artifact'
    shutil.rmtree(copy, ignore_errors=True)
    shutil.copytree(source, copy)
    target = next((copy / 'jobs/r00_equal').glob('attempt_*/data/training/checkpoint_00001024/rng.pt'))
    target.write_bytes(target.read_bytes() + b'\0')
    before = attempts(copy)
    run = subprocess.run([PY, '-m', 'research_v2.study_runner', 'resume', '--study-dir', str(copy)], cwd=ROOT,
                         capture_output=True, text=True)
    results.append({'case': 'completed_artifact_modified', 'exit': run.returncode,
                    'refused': 'Completed artifact changed' in run.stderr + run.stdout,
                    'nothing_started': attempts(copy) == before})
    for p in root.glob('drift_*'):
        shutil.rmtree(p)
    return {'cases': results, 'pass': all(r['exit'] != 0 and r['refused'] and r['nothing_started'] for r in results)}


def job_walls(study):
    out = {}
    for job in read_json(study / 'protocol.json')['jobs']:
        pointer = read_json(study / 'jobs' / job['id'] / 'complete.json')
        out[job['id']] = (job['role'], job['method'], read_json(study / pointer['attempt'] / 'profile.json')['wall_s'])
    return out


def scenario_parallel(root, jdk, runners=12):
    """`runners` independent single-outer studies at once. Content is compared with the sequential reference for the outer
    runs it contains; efficiency compares each job's wall time with the uncontended reference job of the same role/method."""
    reference = root / 'reference'
    studies = {}
    logs = {}
    for outer in range(runners):
        study = root / f'parallel_outer{outer}'
        shutil.rmtree(study, ignore_errors=True)
        log = root / f'parallel_outer{outer}.log'
        prepare(study, [outer], log)
        studies[outer], logs[outer] = study, log
    baseline = set(v2_servers())
    started = time.monotonic()
    processes = {o: runner(['run', '--study-dir', str(s), '--jdk-home', str(jdk)], logs[o]) for o, s in studies.items()}
    peak, seen_ports, seen_pids = 0, set(), set()
    while any(p.poll() is None for p in processes.values()):
        current = {pid: cmd for pid, cmd in v2_servers().items() if pid not in baseline}
        peak = max(peak, len(current))
        seen_pids |= set(current)
        for pid in current:
            try:
                for line in subprocess.run(['ss', '-ltnpH'], capture_output=True, text=True).stdout.splitlines():
                    if f'pid={pid},' in line:
                        seen_ports.add(line.split()[3].rsplit(':', 1)[1])
            except OSError:
                pass
        time.sleep(1)
    wall = time.monotonic() - started
    ids_ok = all(p.returncode == 0 and read_json(s / 'summary.json')['status'] == 'complete' for s, p in
                 ((studies[o], processes[o]) for o in studies))
    reference_outers = read_json(reference / 'protocol.json')['outers']
    comparisons = []
    for outer, study in studies.items():
        if outer in reference_outers:
            for job in read_json(study / 'protocol.json')['jobs']:
                comparisons.append({'outer': outer, **compare_jobs(study, reference, job['id'])})
    ref_walls = job_walls(reference)
    by_kind = {}
    for role, method, w in ref_walls.values():
        by_kind.setdefault((role, method), []).append(w)
    uncontended = {k: sum(v) / len(v) for k, v in by_kind.items()}
    jobs = [w for s in studies.values() if (s / 'summary.json').exists() for w in job_walls(s).values()]
    per_job = [uncontended[(role, method)] / w for role, method, w in jobs]
    equivalent = sum(uncontended[(role, method)] for role, method, _ in jobs)
    out = {'concurrent_runners': runners, 'peak_concurrent_v2_jvm_servers': peak, 'distinct_jvm_pids_seen': len(seen_pids),
           'distinct_listening_ports_seen': sorted(seen_ports), 'wall_s': wall,
           'exit_codes': {o: p.returncode for o, p in processes.items()}, 'comparisons': comparisons,
           'content_compared_outers': sorted(o for o in studies if o in reference_outers),
           'job_efficiency_median': sorted(per_job)[len(per_job) // 2] if per_job else None,
           'job_efficiency_min': min(per_job) if per_job else None,
           'throughput_efficiency': equivalent / (runners * wall) if jobs else None,
           'speedup_vs_one_worker': equivalent / wall if jobs else None,
           'leftover_v2_servers': sorted(set(v2_servers()) - baseline)}
    out['pass'] = (ids_ok and peak >= 2 and bool(comparisons) and all(not c['mismatches'] for c in comparisons)
                   and not out['leftover_v2_servers'])
    return out


def scenario_capacity(root, dry_run):
    """Extrapolate full-study time and disk from measured fixture jobs. An estimate, not a measurement."""
    reference = root / 'reference'
    full = read_json(ROOT / dry_run)
    summary = read_json(reference / 'summary.json')
    rows = {x['job']['id']: x for x in summary['jobs']}
    base = [x for x in summary['jobs'] if x['job']['role'] == 'baseline']
    search = [x for x in summary['jobs'] if x['job']['role'] == 'search']
    final = [x for x in summary['jobs'] if x['job']['role'] == 'final']
    train_rate = sum(x['training_decisions'] / x['profile']['wall_s'] for x in base) / len(base)
    # Search wall = training of 2*K decisions + validation of 2*Ntrace decisions (one fixture slot).
    val_rates = []
    for x in search:
        train_share = x['training_decisions'] / train_rate
        val_rates.append(x['validation_decisions'] / (x['profile']['wall_s'] - train_share))
    val_rate = sum(val_rates) / len(val_rates)
    def per_decision(group):
        return sum(x['profile']['decision_log_raw_bytes'] for x in group) / sum(x['training_decisions'] for x in group), \
               sum(x['profile']['decision_log_gzip_bytes'] for x in group) / sum(x['training_decisions'] for x in group)
    base_raw, base_gz = per_decision(base)
    search_raw, search_gz = per_decision(search)
    def other_bytes(job_id):
        pointer = read_json(reference / 'jobs' / job_id / 'complete.json')
        attempt = reference / pointer['attempt']
        return sum(f.stat().st_size for f in attempt.rglob('*') if f.is_file()) - rows[job_id]['profile']['decision_log_gzip_bytes']
    S, V, F, B = full['S'], full['V'], full['F'], full['B']
    search_wall = S / train_rate + V / val_rate
    final_wall = F / train_rate
    base_wall = B / train_rate
    per_outer_wall = 2 * search_wall + 2 * final_wall + 2 * base_wall
    gb = 1024 ** 3
    def gib(x):
        return x / gb
    # Candidate checkpoints and manifests: measured per fixture slot, scaled by 80 slots.
    slot_other = other_bytes(search[0]['job']['id'])
    per_outer_disk_gz = (2 * (S * search_gz + 80 * slot_other) + 2 * (F * base_gz + other_bytes(final[0]['job']['id'])) +
                         2 * (B * base_gz + other_bytes(base[0]['job']['id'])))
    per_outer_disk_raw = 2 * S * search_raw + 2 * F * base_raw + 2 * B * base_raw
    free = shutil.disk_usage(root).free
    out = {'basis': 'extrapolated from fixture jobs of the reference study; not a measurement of the full study',
           'measured': {'training_decisions_per_s_incl_ppo_updates': train_rate,
                        'candidate_validation_decisions_per_s': val_rate,
                        'decision_log_bytes_per_decision_raw': base_raw, 'decision_log_bytes_per_decision_gzip': base_gz,
                        'search_log_bytes_per_decision_raw': search_raw,
                        'baseline_peak_rss_gib': max(x['profile']['max_rss_kib'] for x in base) / 2 ** 20},
           'per_outer': {'search_hours_each_method': search_wall / 3600, 'final_hours_each': final_wall / 3600,
                         'baseline_hours_each': base_wall / 3600, 'sequential_hours': per_outer_wall / 3600,
                         'disk_gib_with_gzip_logs': gib(per_outer_disk_gz), 'disk_gib_if_logs_stayed_raw': gib(per_outer_disk_raw)},
           'all_20_outers': {'sequential_hours_one_worker': 20 * per_outer_wall / 3600,
                             'sequential_days_one_worker': 20 * per_outer_wall / 86400,
                             'wall_days_if_4_independent_shards': 5 * per_outer_wall / 86400,
                             'disk_gib_with_gzip_logs': gib(20 * per_outer_disk_gz),
                             'disk_gib_if_logs_stayed_raw': gib(20 * per_outer_disk_raw),
                             'free_disk_gib_now': gib(free)},
           'fits_free_disk_with_gzip_logs': 20 * per_outer_disk_gz < 0.8 * free,
           'fits_free_disk_if_logs_stayed_raw': 20 * per_outer_disk_raw < 0.8 * free}
    out['pass'] = out['fits_free_disk_with_gzip_logs'] and base_gz < base_raw / 5
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--jdk-home', type=Path, default=Path('/usr/lib/jvm/java-21-openjdk-amd64'))
    parser.add_argument('--only', nargs='+', choices=['prefix', 'reference', 'interrupt', 'drift', 'parallel', 'capacity'])
    parser.add_argument('--parallel-runners', type=int, default=12)
    parser.add_argument('--dry-run', default='results/research_v2/v0.3/dry_run_full/budget_report.json',
                        help='full-study budget report used by the capacity scenario (v0.2: results/research_v2/P09_dry_run_full/...)')
    args = parser.parse_args()
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    names = args.only or ['prefix', 'reference', 'interrupt', 'drift', 'parallel', 'capacity']
    report_path = root / 'live_evidence.json'
    report = read_json(report_path) if report_path.exists() else {}
    functions = {'prefix': lambda: scenario_prefix(root, args.jdk_home),
                 'reference': lambda: scenario_reference(root, args.jdk_home),
                 'interrupt': lambda: scenario_interrupt(root, args.jdk_home),
                 'drift': lambda: scenario_drift(root),
                 'parallel': lambda: scenario_parallel(root, args.jdk_home, args.parallel_runners),
                 'capacity': lambda: scenario_capacity(root, args.dry_run)}
    for name in names:
        print('SCENARIO', name, flush=True)
        started = time.monotonic()
        try:
            result = functions[name]()
        except BaseException as error:  # keep failed evidence rather than hiding it
            result = {'pass': False, 'error': repr(error)}
        result['wall_s'] = time.monotonic() - started
        report[name] = result
        report['jar_sha256'] = read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256']
        report['source_hashes'] = {p.relative_to(ROOT).as_posix(): file_hash(p)
                                   for p in sorted((ROOT / 'research_v2').glob('*.py'))}
        write_json(report_path, report)
        print(name, 'PASS' if result['pass'] else 'FAIL', flush=True)
    report['test_accessed'] = False
    write_json(report_path, report)
    sys.exit(0 if all(report.get(n, {}).get('pass') for n in names) else 1)


if __name__ == '__main__':
    main()
