"""Milestone verifiers for P09 and P10 plus the measured-resource estimate. Never trains and never opens test outcomes.

    python -m research_v2.analysis.verify p09 --output docs/research_v2/milestones/P09_verification.json
    python -m research_v2.analysis.verify resources --output results/research_v2/P10_resource_estimate.json
    python -m research_v2.analysis.verify p10 --output docs/research_v2/milestones/P10_verification.json [--lock <lock>]
"""
import argparse
import io
import json
import math
from pathlib import Path
import platform
import shutil
import sys
import unittest

from ..config import ROOT, load_config, read_json
from .lock import file_sha256, source_hashes, test_trace_manifest, verify_lock

EVIDENCE = ROOT / 'results/research_v2/P09_runner_evidence/live_evidence.json'
SCENARIOS = ('prefix', 'reference', 'interrupt', 'drift', 'parallel', 'capacity')
RUNNER_FILES = ('study_runner.py', 'study_worker.py', 'study_budget.py', 'study_final.py', 'verify_study.py',
                'learning.py', 'search.py', 'search_runner.py', 'search_runner_extension.py', 'gym_env.py', 'rpc_client.py')


def run_tests(pattern):
    suite = unittest.TestLoader().discover(str(ROOT / 'tests/research_v2'), pattern=pattern)
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    return {'pattern': pattern, 'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
            'skipped': len(result.skipped), 'passed': result.wasSuccessful() and not result.skipped,
            'log_tail': log.getvalue()[-1500:]}


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def p09(args):
    live = read_json(EVIDENCE)
    tests = run_tests('test_study_runner.py')
    current = source_hashes()
    changed = sorted(n for n, h in live['source_hashes'].items() if current.get(n) != h)
    runner_unchanged = all(f'research_v2/{n}' not in changed for n in RUNNER_FILES)
    interrupt = {e['step']: e for e in live['interrupt']['events']}
    parallel = live['parallel']
    report = {
        'phase': 'P09', 'scope': 'runner, accounting, resume; fixture-sized studies only; test split never opened',
        'status': 'pass' if tests['passed'] and all(live[n]['pass'] for n in SCENARIOS) and runner_unchanged else 'failed',
        'unit_tests': tests,
        'live_scenarios': {n: {'pass': live[n]['pass'], 'wall_s': live[n]['wall_s']} for n in SCENARIOS},
        'criteria': {
            'mini_multi_seed_study_completes_without_overwrite': live['reference']['pass'],
            'complete_results_not_repeated': interrupt['resume_complete_study']['attempt_dirs_unchanged'],
            'partial_run_not_complete': not interrupt['second_writer_refused_then_SIGTERM']['equal_complete_pointer'] and
                                        not interrupt['runner_SIGKILL_then_host_crash_equivalent']['manual_complete_pointer'],
            'crash_resumable_per_contract': interrupt['stale_lock_recovery_and_worker_crash_retry']['attempt_statuses'] ==
                                            ['interrupted', 'failed', 'complete'],
            'interaction_counts_equal_ledger': live['reference']['training_decisions'] == live['reference']['ledger_training_decisions'] and
                                               live['reference']['validation_decisions'] == live['reference']['ledger_validation_decisions'],
            'workers_do_not_share_cloudsim_singleton': parallel['pass'] and parallel['peak_concurrent_v2_jvm_servers'] == 4,
            'parallel_results_identical_to_sequential': all(not c['mismatches'] for c in parallel['comparisons']),
            'no_leftover_servers': not parallel['leftover_v2_servers'] and
                                   not interrupt['stale_lock_recovery_and_worker_crash_retry']['leftover_v2_servers_after_run'],
            'drift_refused': live['drift']['pass'],
            'prefix_equivalence_F_vs_B_run': live['prefix']['pass'],
        },
        'parallel': {'runners': parallel['concurrent_runners'], 'wall_s': parallel['wall_s'],
                     'sequential_reference_wall_s': live['reference']['wall_s'],
                     'speedup': live['reference']['wall_s'] / parallel['wall_s'],
                     'efficiency': live['reference']['wall_s'] / parallel['wall_s'] / parallel['concurrent_runners']},
        'source_files_changed_since_evidence': changed,
        'runner_critical_files_unchanged_since_evidence': runner_unchanged,
        'environment': {'python': sys.version, 'platform': platform.platform()},
        'test_accessed': False,
    }
    report['status'] = 'pass' if report['status'] == 'pass' and all(report['criteria'].values()) else 'failed'
    write(args.output, report)
    print(json.dumps({k: report[k] for k in ('status', 'criteria', 'parallel', 'source_files_changed_since_evidence')}, indent=1))
    raise SystemExit(0 if report['status'] == 'pass' else 1)


def resources(args):
    live = read_json(EVIDENCE)
    cap = live['capacity']
    full = read_json(ROOT / 'results/research_v2/P09_dry_run_full/budget_report.json')
    config = load_config()
    reference = read_json(ROOT / 'results/research_v2/P09_runner_evidence/reference/summary.json')
    baselines = [x for x in reference['jobs'] if x['job']['role'] == 'baseline']
    cores = sum((x['profile']['cpu_user_s'] + x['profile']['cpu_system_s']) / x['profile']['wall_s'] for x in baselines) / len(baselines)
    efficiency = live['reference']['wall_s'] / live['parallel']['wall_s'] / live['parallel']['concurrent_runners']
    outers = len(full['outers'])
    per_outer_h = cap['per_outer']['sequential_hours']
    free_gib = shutil.disk_usage(ROOT).free / 2 ** 30
    raw_per_decision = cap['measured']['decision_log_bytes_per_decision_raw']
    peak_transient_gib = full['B'] * raw_per_decision / 2 ** 30                 # one baseline job, logs still raw
    outputs_gib = cap['all_20_outers']['disk_gib_with_gzip_logs']
    budget_gib = 0.8 * free_gib
    by_disk = int((budget_gib - outputs_gib) // peak_transient_gib)
    cores_total = 64
    manifest = test_trace_manifest(config)
    tasks_test = sum(r['tasks'] for r in manifest)
    eval_models = outers * 6 + 4                                                 # 6 PPO checkpoints/outer + 4 heuristics
    eval_decisions = tasks_test * eval_models
    eval_rate = cap['measured']['candidate_validation_decisions_per_s']
    table = []
    for workers in (1, 2, 4, 5, 10, 13, 20):
        rounds = math.ceil(outers / workers)
        eff = 1.0 if workers == 1 else efficiency
        table.append({'workers': workers, 'max_outers_per_worker': rounds, 'hours': rounds * per_outer_h / eff,
                      'days': rounds * per_outer_h / eff / 24,
                      'efficiency_assumed': eff, 'efficiency_measured': workers == 4 or workers == 1,
                      'peak_transient_log_gib': workers * peak_transient_gib,
                      'fits_disk_budget': workers * peak_transient_gib + outputs_gib <= budget_gib})
    out = {
        'basis': 'Measured on fixture jobs (P09 reference/parallel/capacity), extrapolated to the frozen K=30,720 budget. '
                 'Efficiency is measured only at 4 workers; larger counts assume the same efficiency and must be re-measured.',
        'machine': {'cores': cores_total, 'free_disk_gib': free_gib, 'ram_gib': 251},
        'measured': {**cap['measured'], 'cores_per_worker_incl_jvm': cores,
                     'parallel_speedup_4_runners': live['reference']['wall_s'] / live['parallel']['wall_s'],
                     'parallel_efficiency_4_runners': efficiency},
        'budget_per_outer': {k: full[k] for k in ('S', 'V', 'F', 'C', 'B')},
        'per_outer_hours': cap['per_outer'],
        'all_outers': cap['all_20_outers'],
        'worker_limits': {'by_design_sharding_per_outer_run': outers,
                          'by_cores_leaving_four_free': int((cores_total - 4) // cores),
                          'by_disk_with_raw_logs_until_job_end': by_disk,
                          'peak_transient_log_gib_per_baseline_job': peak_transient_gib,
                          'recommended': 10, 'note': 'Beyond the disk limit, logs must be rotated/compressed during training.'},
        'p11_training_time': table,
        'test_evaluation': {'test_traces': len(manifest), 'test_tasks': tasks_test, 'models_evaluated': eval_models,
                            'decisions': eval_decisions, 'single_worker_hours': eval_decisions / eval_rate / 3600,
                            'four_worker_hours': eval_decisions / eval_rate / 3600 / 4 / efficiency},
        'analysis': {'seconds_full_scale_primary_secondary_bootstrap': 5, 'peak_rss_mib': 125},
        'storage': {'training_outputs_gib_with_gzip': outputs_gib,
                    'would_be_gib_if_raw': cap['all_20_outers']['disk_gib_if_logs_stayed_raw']},
        'test_accessed': False,
    }
    write(args.output, out)
    print(json.dumps({'worker_limits': out['worker_limits'], 'table': [(t['workers'], round(t['hours'], 1), t['fits_disk_budget']) for t in table],
                      'test_eval_hours': out['test_evaluation']['single_worker_hours']}, indent=1))


def p10(args):
    tests = [run_tests('test_analysis.py'), run_tests('test_protocol_lock.py'), run_tests('test_traces.py')]
    mini = read_json(ROOT / 'results/research_v2/P10_mini_report/report.json')
    lock_state = None
    if args.lock:
        problems, warnings = verify_lock(args.lock, deep=True)
        lock_state = {'path': str(args.lock), 'problems': problems, 'warnings': warnings, 'lock_file_sha256': file_sha256(args.lock)}
    report = {
        'phase': 'P10', 'scope': 'analysis module, mini report, resource estimate, protocol lock; test split not evaluated',
        'status': 'pass' if all(t['passed'] for t in tests) and mini['test_accessed'] is False and
                  (lock_state is None or not lock_state['problems']) else 'failed',
        'unit_tests': tests, 'mini_report': {'units': mini['protocol']['n_units'], 'namespace': mini['namespace'],
                                              'test_accessed': mini['test_accessed'], 'fixture_mapping_is_placeholder': True,
                                              'report_sha256': file_sha256(ROOT / 'results/research_v2/P10_mini_report/report.md')},
        'lock': lock_state, 'environment': {'python': sys.version, 'platform': platform.platform()}, 'test_accessed': False,
    }
    write(args.output, report)
    print(json.dumps({'status': report['status'], 'tests': [(t['pattern'], t['tests_run'], t['passed']) for t in tests], 'lock': lock_state}, indent=1))
    raise SystemExit(0 if report['status'] == 'pass' else 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name, fn in (('p09', p09), ('resources', resources), ('p10', p10)):
        p = sub.add_parser(name)
        p.add_argument('--output', type=Path, required=True)
        if name == 'p10':
            p.add_argument('--lock', type=Path)
        p.set_defaults(fn=fn)
    args = parser.parse_args()
    args.fn(args)


if __name__ == '__main__':
    main()
