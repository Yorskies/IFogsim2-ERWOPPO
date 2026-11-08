"""P10 protocol lock: freezes everything that determines the confirmatory result *before* the test split is evaluated.

create_lock() writes protocol_lock.json. verify_lock() recomputes every recorded hash from disk and never trusts the
file's own claims. Modified or missing locked files are violations; files added after the lock are listed (P11 may add
a test evaluator) and must be accounted for by the final audit. The test split is never evaluated here: only trace
payload hashes are prepared (inputs, no outcomes).
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

from ..config import ContractError, ROOT, load_config, read_json, require, sha256
from .stats import COSTS, PRIMARY

LOCK_VERSIONS = {'0.2': 'P10-lock-1', '0.3': 'P10-lock-2', '0.4': 'P10-lock-3'}
LOCK_VERSION = LOCK_VERSIONS['0.4']
SOURCE_GLOBS = ('research_v2/**/*.py', 'tests/research_v2/*.py', 'schemas/research_v2/*.json',
                'configs/research_v2/*.json', 'requirements-v2-*.txt', 'run_research_v2.py')
# Per-protocol artifact locations. v0.2 artifacts are never rewritten; v0.3 lives under results/research_v2/v0.3/.
ARTIFACTS = {
    '0.2': {'live_evidence': 'results/research_v2/P09_runner_evidence/live_evidence.json',
            'dry_run': 'results/research_v2/P09_dry_run_full/budget_report.json'},
    '0.3': {'live_evidence': 'results/research_v2/v0.3/p09_runner_evidence/live_evidence.json',
            'dry_run': 'results/research_v2/v0.3/dry_run_full/budget_report.json',
            'predecessor_lock': 'results/research_v2/P10_protocol_lock/protocol_lock.json',
            'diagnosis': ('results/research_v2/P10_learning_diagnosis/report.md',
                          'results/research_v2/P10_learning_diagnosis/ablation.json',
                          'results/research_v2/P10_learning_diagnosis/followup.json',
                          'results/research_v2/P10_learning_check/sensitivity.json',
                          'results/research_v2/P10_learning_check/check.json')},
}
ARTIFACTS['0.4'] = {'live_evidence': 'results/research_v2/v0.4/p09_runner_evidence/live_evidence.json',
                    'dry_run': 'results/research_v2/v0.4/dry_run_full/budget_report.json',
                    'design': 'configs/research_v2/design_v0.4.json',
                    'predecessor_lock': ARTIFACTS['0.3']['predecessor_lock'],
                    'failed_gate': 'results/research_v2/v0.3/fidelity',
                    'diagnosis': ARTIFACTS['0.3']['diagnosis']}
EVIDENCE_FILES = tuple(ARTIFACTS['0.2'][k] for k in ('live_evidence', 'dry_run'))
LIVE_SCENARIOS = ('prefix', 'reference', 'interrupt', 'drift', 'parallel', 'capacity')


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def source_files():
    found = {}
    for pattern in SOURCE_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            if path.is_file() and '__pycache__' not in path.parts:
                found[path.relative_to(ROOT).as_posix()] = path
    return found


def source_hashes():
    return {name: file_sha256(path) for name, path in source_files().items()}


def command(*args):
    try:
        return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None


def git_state():
    head, status = command('git', 'rev-parse', 'HEAD'), command('git', 'status', '--porcelain')
    return {'head': head.stdout.strip() if head and head.returncode == 0 else None,
            'dirty': bool(status and status.stdout.strip()),
            'porcelain_sha256': hashlib.sha256(status.stdout.encode()).hexdigest() if status else None,
            'note': 'Reproducibility rests on the per-file hashes below, not on the commit.'}


def environment():
    java = command('java', '-version')
    cpu = next((l.split(':', 1)[1].strip() for l in Path('/proc/cpuinfo').read_text().splitlines()
                if l.startswith('model name')), None) if Path('/proc/cpuinfo').exists() else None
    freeze = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True).stdout
    packages = {n.lower().replace('_', '-'): v for n, v in (l.split('==', 1) for l in freeze.splitlines() if '==' in l)}
    return {'python': sys.version, 'platform': platform.platform(), 'machine': platform.machine(), 'cpu_model': cpu,
            'java': (java.stderr or java.stdout).strip().splitlines()[0] if java else None,
            'pip_freeze_sha256': hashlib.sha256(freeze.encode()).hexdigest(), 'packages': packages,
            'note': 'pip freeze records versions; package hashes are not available from this environment.'}


def test_trace_manifest(config):
    """Preparation only (role holdout_preparer, operation generate): payload hashes of inputs, no outcomes."""
    from ..trace_access import TraceKey
    from ..traces import TraceGenerator
    generator = TraceGenerator(config)
    low, high = config['seeds']['test_trace_ids']
    rows = []
    for workload in config['training']['workload_order']:
        for trace_id in range(low, high + 1):
            key = TraceKey(config['seeds']['master'], 'test', None, None, trace_id, workload)
            trace = generator.generate(key, role='holdout_preparer')
            rows.append({'workload': workload, 'trace_id': trace_id, 'tasks': trace.task_count,
                         'payload_sha256': trace.payload_sha256})
    return rows


def hypothesis_registry(config):
    workloads = config['training']['workload_order']
    stats = config['statistics']
    return {'primary': [{'id': i, 'comparator': a, 'treatment': b, 'description': d,
                         'metric': 'Dglobal', 'test': 'exact two-sided paired sign-flip, 2^20 enumeration',
                         'family': 'primary', 'multiplicity': 'Holm over 3', 'alpha': stats['alpha']}
                        for i, a, b, d in PRIMARY],
            'secondary_ids': [f'{rq}:{w}:{c}' for rq, _, _, _ in PRIMARY for w in workloads for c in COSTS],
            'secondary_rule': {'test': f'Monte Carlo sign-flip, {stats["secondary_signflip_draws"]} draws, p=(b+1)/(M+1), '
                                       f'seed {config["seeds"]["secondary_signflip"]}', 'multiplicity': 'Holm over 60 (own family)',
                               'status': 'secondary, not confirmatory; all 60 reported'},
            'ci': f'{stats["bootstrap_draws"]} crossed paired bootstrap draws, seed {config["seeds"]["bootstrap"]}, '
                  'outer-run and per-workload trace indices resampled, trace indices shared by all models',
            'sign_convention': 'difference = D(comparator) - D(NSGA-II); positive = NSGA-II better',
            'other_comparisons': 'exploratory: effect + CI + raw p only, no confirmatory claim; adding a confirmatory '
                                 'family requires registration before the test is opened',
            'forbidden': ['automatic fallback from sign-flip to Wilcoxon/t-test', 'choosing a one-sided test after seeing direction',
                          'adding seeds until significant', 'pooling tasks/episodes as training replicates',
                          'averaging p-values', 'tuning anything on test results'],
            'practical_screen': f'relative Dglobal improvement >= {stats["practical_relative_improvement"]}: a reporting convention only'}


def _common(config, K, plan, resource_estimate, deviations, version):
    from .. import study_budget
    validation = study_budget.validation_trace_manifest(config)
    test_manifest = test_trace_manifest(config)
    receipt = read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')
    return {
        'version': LOCK_VERSIONS[version], 'protocol_version': version, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'purpose': 'Freeze before the test split is evaluated. Any change afterwards needs a new protocol version.',
        'git': git_state(), 'environment': environment(),
        'config': {'canonical_sha256': sha256(config), 'protocol_version': config['protocol_version'],
                   'schema_version': config['schema_version']},
        'build': {'jar_sha256': receipt['artifact_sha256'], 'receipt': receipt},
        'sources': source_hashes(),
        'frozen_design': {'candidate_decisions_K': K, 'final_decisions_F': plan['F'], 'baseline_budget_B': plan['B'],
                          'candidate_slots': config['search']['candidate_slots'], 'model_repeats': config['search']['model_repeats'],
                          'budget_per_outer': {k: plan[k] for k in ('S', 'V', 'C', 'B', 'F', 'Ntrace', 'rounding_overhead')},
                          'outer_runs': config['seeds']['outer_runs'], 'seeds': config['seeds'],
                          'ppo': config['ppo'], 'evaluation': config['evaluation'], 'search': config['search'],
                          'execution': config['execution']},
        'traces': {'validation_manifest_sha256': sha256(validation), 'validation_traces': len(validation),
                   'test': {'namespace': {'master': config['seeds']['master'], 'split': 'test',
                                          'trace_ids': config['seeds']['test_trace_ids'],
                                          'workloads': config['training']['workload_order']},
                            'traces': len(test_manifest), 'manifest_sha256': sha256(test_manifest),
                            'tasks_total': sum(r['tasks'] for r in test_manifest),
                            'prepared_only': True, 'outcomes_observed': False}},
        'hypotheses': hypothesis_registry(config),
        'sensitivity': {'registered_factors': config['sensitivity'],
                        'rules': ['one factor at a time on the frozen main models, zero-shot, no retraining or re-search',
                                  'homogeneous fog is a validation control; heterogeneous is the main result',
                                  'normalization/penalty sensitivity is recomputed on validation data only; main definition is always reported',
                                  'z > 1 under sensitivity is flagged out-of-reference, never clipped, and never adjusts the main normalization']},
        'resources': resource_estimate,
        'deviations_from_v02': list(deviations),
        'test_opened': False,
    }


def _seal(lock):
    lock['lock_sha256'] = hashlib.sha256(json.dumps({k: v for k, v in lock.items() if k != 'lock_sha256'},
                                                    sort_keys=True, allow_nan=False).encode()).hexdigest()
    return lock


def _live_passing(path):
    live = read_json(ROOT / path)
    require(all(live[n]['pass'] for n in LIVE_SCENARIOS), 'P09 live evidence is not fully passing')


def build_lock(*, fidelity_evidence, resource_estimate=None, deviations=(), version='0.3'):
    require(version in LOCK_VERSIONS, f'Unknown protocol version {version}')
    config = load_config()
    fidelity_evidence = Path(fidelity_evidence).resolve()
    paths = ARTIFACTS[version]
    if version == '0.2':
        from ..search_runner_extension import require_extension_gate
        K = require_extension_gate(fidelity_evidence)
        learner_version = '0.2'
    else:
        from ..fidelity_v03 import require_fidelity_gate
        K, learner_version = require_fidelity_gate(fidelity_evidence)
        require(learner_version == '0.3', f'v{version} lock needs the v0.3 learner')
    plan = read_json(ROOT / paths['dry_run'])
    require(plan['K'] == K and not plan['fixture_only'], 'Full dry-run budget differs from the frozen K')
    require(plan.get('learner_version', '0.2') == learner_version, 'Dry-run budget was made for another learner')
    _live_passing(paths['live_evidence'])
    lock = _common(config, K, plan, resource_estimate, deviations, version)
    lock['evidence'] = {paths[k]: file_sha256(ROOT / paths[k]) for k in ('live_evidence', 'dry_run')}
    if version == '0.2':
        lock['fidelity'] = {'evidence_dir': fidelity_evidence.relative_to(ROOT).as_posix(),
                            'result_sha256': file_sha256(fidelity_evidence / 'result.json'),
                            'audit_sha256': file_sha256(fidelity_evidence / 'audit.json'),
                            'protocol_sha256': file_sha256(fidelity_evidence / 'protocol.json'),
                            'original_failed_result_sha256': file_sha256(ROOT / 'results/research_v2/P08_fidelity_1/result.json'),
                            'selected_K': K}
        return _seal(lock)
    from ..learner import effective_learner
    _, learner_meta = effective_learner(config, '0.3')
    predecessor = read_json(ROOT / paths['predecessor_lock'])
    lock['learner'] = learner_meta
    lock['frozen_design']['ppo_effective'] = effective_learner(config, '0.3')[0]['ppo']
    if version == '0.4':
        require(fidelity_evidence == (ROOT / paths['design']).resolve(), 'v0.4 lock must be built from the registered design file')
        gate = ROOT / paths['failed_gate']
        lock['design'] = {'path': paths['design'], 'sha256': file_sha256(fidelity_evidence), 'K': K,
                          'rule': 'K = F; no proxy-fidelity gate'}
        lock['fidelity'] = {'evidence_dir': paths['failed_gate'], 'selected_K': None,
                            'files': {n: file_sha256(gate / n) for n in ('protocol.json', 'result.json', 'audit.json')},
                            'role': 'the failed v0.3 gate (predecessor) that motivated K = F; kept for audit'}
    else:
        lock['fidelity'] = {'evidence_dir': fidelity_evidence.relative_to(ROOT).as_posix(), 'selected_K': K,
                            'files': {n: file_sha256(fidelity_evidence / n) for n in ('protocol.json', 'result.json', 'audit.json')},
                            'caveat': 'Re-run of the registered Spearman gate with the v0.3 learner on the pilot namespace; reference = final '
                                      'budget F; the same pilot seeds were used in the P10 diagnosis that motivated v0.3.'}
    lock['predecessor'] = {'protocol_version': '0.2', 'lock_path': paths['predecessor_lock'],
                           'lock_file_sha256': file_sha256(ROOT / paths['predecessor_lock']),
                           'lock_sha256': predecessor['lock_sha256'], 'git_tag': 'protocol-v0.2',
                           'status': 'superseded; M3 no-go because the gamma 1.0 learner did not learn consistently',
                           'note': 'The v0.2 lock verifies at the protocol-v0.2 tag, not on later trees (locked files changed by design).',
                           **({'v0.3': {'git_tag': 'protocol-v0.3', 'status': 'fidelity gate failed at all K; no lock'}}
                              if version == '0.4' else {})}
    lock['diagnosis_evidence'] = {name: file_sha256(ROOT / name) for name in paths['diagnosis']}
    return _seal(lock)


def _check_packages(lock, problems):
    from importlib import metadata
    for name in ('numpy', 'torch', 'stable_baselines3', 'gymnasium', 'scipy', 'jsonschema'):
        recorded = lock['environment']['packages'].get(name.replace('_', '-'))
        try:
            installed = metadata.version(name.replace('_', '-'))
        except metadata.PackageNotFoundError:
            installed = None
        if recorded != installed:
            problems.append(f'package {name}: lock {recorded}, installed {installed}')


def verify_lock(path, *, deep=False):
    """Returns (problems, warnings). deep=True also regenerates the test-trace input manifest."""
    lock = read_json(path)
    problems, warnings = [], []
    body = {k: v for k, v in lock.items() if k != 'lock_sha256'}
    if lock.get('version') not in LOCK_VERSIONS.values():
        problems.append('unknown lock version')
    if hashlib.sha256(json.dumps(body, sort_keys=True, allow_nan=False).encode()).hexdigest() != lock.get('lock_sha256'):
        problems.append('lock file content does not match its own hash')
    if lock.get('test_opened') is not False:
        problems.append('lock claims the test split was already opened')
    now = source_hashes()
    for name, digest in lock['sources'].items():
        if name not in now:
            problems.append(f'locked file missing: {name}')
        elif now[name] != digest:
            problems.append(f'locked file modified: {name}')
    added = sorted(set(now) - set(lock['sources']))
    if added:
        warnings.append(f'{len(added)} file(s) added after the lock (must be audited): {added[:10]}')
    config = load_config()
    if sha256(config) != lock['config']['canonical_sha256']:
        problems.append('config differs from lock')
    receipt = read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')
    if receipt['artifact_sha256'] != lock['build']['jar_sha256']:
        problems.append('JAR differs from lock')
    for name, digest in lock['evidence'].items():
        if file_sha256(ROOT / name) != digest:
            problems.append(f'evidence changed: {name}')
    fidelity = lock['fidelity']
    if lock.get('version') == LOCK_VERSIONS['0.2']:
        for name, key in (('result.json', 'result_sha256'), ('audit.json', 'audit_sha256'), ('protocol.json', 'protocol_sha256')):
            if file_sha256(ROOT / fidelity['evidence_dir'] / name) != fidelity[key]:
                problems.append(f'fidelity evidence changed: {name}')
        if file_sha256(ROOT / 'results/research_v2/P08_fidelity_1/result.json') != fidelity['original_failed_result_sha256']:
            problems.append('original failed pilot result changed')
    else:
        for name, digest in fidelity['files'].items():
            if file_sha256(ROOT / fidelity['evidence_dir'] / name) != digest:
                problems.append(f'fidelity evidence changed: {name}')
        from ..learner import effective_learner
        try:
            if effective_learner(config, '0.3')[1] != lock['learner']:
                problems.append('learner protocol differs from lock')
        except ContractError as error:
            problems.append(f'learner protocol invalid for the current config: {error}')
        if 'design' in lock and file_sha256(ROOT / lock['design']['path']) != lock['design']['sha256']:
            problems.append('v0.4 design file changed')
        pred = lock['predecessor']
        if file_sha256(ROOT / pred['lock_path']) != pred['lock_file_sha256']:
            problems.append('predecessor (v0.2) lock file changed')
        for name, digest in lock['diagnosis_evidence'].items():
            if file_sha256(ROOT / name) != digest:
                problems.append(f'diagnosis evidence changed: {name}')
    from .. import study_budget
    if sha256(study_budget.validation_trace_manifest(config)) != lock['traces']['validation_manifest_sha256']:
        problems.append('validation trace manifest differs from lock')
    if deep and sha256(test_trace_manifest(config)) != lock['traces']['test']['manifest_sha256']:
        problems.append('test trace input manifest differs from lock')
    if config['seeds'] != lock['frozen_design']['seeds']:
        problems.append('seeds differ from lock')
    _check_packages(lock, problems)
    opened = ROOT / 'results/research_v2/TEST_OPENED.json'
    if opened.exists():
        warnings.append('TEST_OPENED.json exists: the test split has been evaluated under this or an earlier lock')
    return problems, warnings


def require_valid_lock(path, *, deep=False):
    problems, _ = verify_lock(path, deep=deep)
    require(not problems, 'Protocol lock invalid: ' + '; '.join(problems))
    return read_json(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    c = sub.add_parser('create')
    c.add_argument('--output', type=Path, required=True)
    c.add_argument('--fidelity-evidence', type=Path, required=True)
    c.add_argument('--resource-estimate', type=Path)
    c.add_argument('--deviations', type=Path, help='JSON list of recorded changes from v0.2')
    c.add_argument('--protocol-version', choices=('0.2', '0.3', '0.4'), default='0.4')
    v = sub.add_parser('verify')
    v.add_argument('--lock', type=Path, required=True)
    v.add_argument('--deep', action='store_true')
    args = parser.parse_args()
    if args.command == 'create':
        require(not args.output.exists(), 'Refusing to overwrite an existing lock')
        lock = build_lock(fidelity_evidence=args.fidelity_evidence,
                          resource_estimate=read_json(args.resource_estimate) if args.resource_estimate else None,
                          deviations=read_json(args.deviations) if args.deviations else (), version=args.protocol_version)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(lock, indent=2, sort_keys=True, allow_nan=False) + '\n')
        print(json.dumps({'lock': str(args.output), 'lock_sha256': lock['lock_sha256'], 'files': len(lock['sources'])}))
    else:
        problems, warnings = verify_lock(args.lock, deep=args.deep)
        print(json.dumps({'problems': problems, 'warnings': warnings}, indent=2))
        raise SystemExit(1 if problems else 0)


if __name__ == '__main__':
    main()
