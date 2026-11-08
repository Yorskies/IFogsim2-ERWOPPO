"""P10 report: runs the registered analysis on a loaded Table and renders JSON + Markdown.

CLI (fixture end-to-end on the validation namespace; the test split is never read):
    python -m research_v2.analysis.report mini --study-dir <P09 mini study> --output-dir <dir>
"""
import argparse
import json
from pathlib import Path

import numpy as np

from ..config import load_config, require, sha256
from .loader import FIXTURE_MAPPING, compute_cost, load_study_cells, rows_to_table
from .stats import COSTS, PRIMARY, analyse, exploratory, physical_summary

LABELS = {'confirmatory_primary': 'confirmatory (3 tests, one Holm family, alpha 0.05)',
          'secondary_prespecified': 'secondary, pre-specified (60 tests, own Holm family; not confirmatory)',
          'exploratory_unadjusted': 'exploratory (unregistered family, no multiplicity control)'}


def f(x, digits=4):
    return 'undefined' if x is None else f'{x:.{digits}f}'


def p(x):
    return f'{x:.3e}' if x < 1e-3 else f'{x:.4f}'


def render(report, *, fixture_note=None):
    pr = report['protocol']
    lines = ['# P10 analysis report', '']
    if fixture_note:
        lines += [f'> **FIXTURE / PILOT DATA — NOT STUDY EVIDENCE.** {fixture_note}', '']
    lines += [f'Unit of inference: **outer training run** (n = {pr["n_units"]}). Traces per workload: '
              f'{pr["traces_per_workload"]}. Tasks/episodes are never pooled into replicates and p-values are never averaged.',
              f'Sign convention: difference = D(comparator) − D(NSGA-II); **positive = NSGA-II better**. '
              f'Bootstrap: {pr["bootstrap"]["draws"]} crossed paired draws (seed {pr["bootstrap"]["seed"]}); '
              f'secondary sign-flip: {pr["secondary_signflip"]["draws"]} Monte Carlo draws (seed {pr["secondary_signflip"]["seed"]}).',
              'Assumption of the sign-flip tests: the paired differences are symmetric about zero under the null; pairing does '
              'not by itself guarantee this. Non-significant means insufficient evidence, not equivalence.', '',
              f'## 1. Primary comparisons — {LABELS["confirmatory_primary"]}', '',
              '| Test | Comparator vs NSGA-II | mean diff | 95% CI | rel. improvement (95% CI) | ≥1% screen | dz | raw p (exact) | Holm p |',
              '|---|---|---:|---|---|:-:|---:|---:|---:|']
    for r in report['primary']:
        dz = r['effect_size_dz']
        rel_ci = r['ci95_relative']
        lines.append(f'| {r["id"]} | {r["comparator"]} | {f(r["mean_difference"])} | [{f(r["ci95_difference"][0])}, {f(r["ci95_difference"][1])}] '
                     f'| {f(100 * r["relative_improvement"], 2)}% ([{f(100 * rel_ci[0], 2)}, {f(100 * rel_ci[1], 2)}]) '
                     f'| {"yes" if r["meets_1pct_reporting_screen"] else "no"} | {f(dz["dz"], 3) if dz["dz"] is not None else dz["status"]} '
                     f'| {p(r["raw_p_exact_signflip"])} | {p(r["holm_adjusted_p"])} |')
    lines += ['', 'The ≥1% screen is a reporting convention, not an SLA and not evidence of practical benefit by itself.', '',
              '## 2. Method summary (Dglobal, between-run uncertainty)', '',
              '| Method | Dglobal mean | SD between runs | SE | ' + ' | '.join(f'Dw {w}' for w in pr['traces_per_workload']) + ' |',
              '|---|---:|---:|---:|' + '---:|' * len(pr['traces_per_workload'])]
    for m, s in report['methods'].items():
        lines.append(f'| {m} | {f(s["Dglobal_mean"])} | {f(s["Dglobal_sd_between_runs"])} | {f(s["Dglobal_se"])} | '
                     + ' | '.join(f(s['Dw_mean'][w]) for w in pr['traces_per_workload']) + ' |')
    lines += ['', 'Mean cost vector F per method (workload macro-average):', '',
              '| Method | ' + ' | '.join(COSTS) + ' | worst workload (run counts) |', '|---|' + '---:|' * len(COSTS) + '---|']
    for m, s in report['methods'].items():
        lines.append(f'| {m} | ' + ' | '.join(f(s['cost_means_F'][c]) for c in COSTS) + f' | {s["worst_workload_counts"]} |')
    lines += ['', f'## 3. Secondary — {LABELS["secondary_prespecified"]}', '',
              'All 60 results are reported. Monte Carlo p = (b+1)/(M+1).', '',
              '| id | mean diff | 95% CI | dz | raw p | Holm p |', '|---|---:|---|---:|---:|---:|']
    for r in report['secondary']:
        dz = r['effect_size_dz']
        lines.append(f'| {r["id"]} | {f(r["mean_difference"])} | [{f(r["ci95_difference"][0])}, {f(r["ci95_difference"][1])}] '
                     f'| {f(dz["dz"], 3) if dz["dz"] is not None else dz["status"]} | {p(r["raw_p_montecarlo_signflip"])} | {p(r["holm_adjusted_p"])} |')
    if report.get('exploratory'):
        lines += ['', f'## 4. Exploratory — {LABELS["exploratory_unadjusted"]}', '',
                  '| comparator vs treatment | mean diff | 95% CI | dz | raw p |', '|---|---:|---|---:|---:|']
        for r in report['exploratory']:
            dz = r['effect_size_dz']
            lines.append(f'| {r["comparator"]} vs {r["treatment"]} | {f(r["mean_difference"])} | [{f(r["ci95_difference"][0])}, '
                         f'{f(r["ci95_difference"][1])}] | {f(dz["dz"], 3) if dz["dz"] is not None else dz["status"]} | {p(r["raw_p_exact_signflip"])} |')
    if report.get('physical'):
        lines += ['', '## 5. Practical meaning (paired, comparator − NSGA-II, mean over runs)', '',
                  'Dynamic energy J = zE × 50 J × N per trace; idle energy is identical for all methods on a trace, so total-Joule '
                  'differences equal dynamic differences. Violation/reliability are percentage points.', '',
                  '| comparison | Δ dynamic energy (J/trace) | Δ violation (pp) | Δ reliability (pp) |', '|---|---:|---:|---:|']
        for name, row in report['physical'].items():
            lines.append(f'| {name} | {f(row["dynamic_energy_j"]["mean_paired_difference_comparator_minus_treatment"], 2)} | '
                         f'{f(row["violation_pp"]["mean_paired_difference_comparator_minus_treatment"], 3)} | '
                         f'{f(row["reliability_pp"]["mean_paired_difference_comparator_minus_treatment"], 3)} |')
    if report.get('compute_cost'):
        lines += ['', '## 6. Computational cost (one worker, from P09 profiles)', '',
                  '| job | training decisions | validation decisions | wall s | CPU s | peak RSS GiB | gradient updates |', '|---|---:|---:|---:|---:|---:|---:|']
        for r in report['compute_cost']:
            lines.append(f'| {r["job"]} | {r["training_decisions"]} | {r["validation_decisions"]} | {r["wall_s"]:.1f} | '
                         f'{r["cpu_s"]:.1f} | {r["max_rss_gib"]:.2f} | {r["gradient_updates"]} |')
    return '\n'.join(lines) + '\n'


def build_report(table, config, *, bootstrap_draws=None, signflip_draws=None, expected_outers=None,
                 exploratory_pairs=(), compute=None):
    report = analyse(table, config, bootstrap_draws=bootstrap_draws, signflip_draws=signflip_draws,
                     primary_units_expected=expected_outers if expected_outers is not None else table.outers)
    if exploratory_pairs:
        report['exploratory'] = exploratory(table, list(exploratory_pairs), config, bootstrap_draws=bootstrap_draws)
    if table.physical:
        report['physical'] = {f'{a} − {b}': physical_summary(table, b, a) for _, a, b, _ in PRIMARY}
    if compute:
        report['compute_cost'] = compute
    report['config_sha256'] = sha256(config)
    return report


def mini(args):
    config = load_config()
    study = Path(args.study_dir)
    summary = json.loads((study / 'protocol.json').read_text())
    require(summary['fixture_only'], 'The mini report only accepts a fixture study (validation namespace)')
    outers = tuple(summary['outers'])
    table = rows_to_table(load_study_cells(study, outers), config)
    report = build_report(table, config, bootstrap_draws=args.bootstrap_draws, signflip_draws=args.signflip_draws,
                          expected_outers=outers, exploratory_pairs=[('manual_B', 'equal_B'), ('manual_F', 'equal_F')],
                          compute=compute_cost(study, outers))
    report['fixture_mapping'] = {k: list(v) for k, v in FIXTURE_MAPPING.items()}
    report['namespace'] = 'validation'
    report['test_accessed'] = False
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=False)
    (out / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    note = ('Labels nsga2/random are placeholders for the P09 fixture jobs (one weight vector, 1,024 decisions; '
            "'random' is the manual-weight baseline). Only the pipeline is being exercised, on the validation namespace.")
    (out / 'report.md').write_text(render(report, fixture_note=note))
    print(json.dumps({'n_units': len(outers), 'primary': [(r['id'], r['raw_p_exact_signflip'], r['holm_adjusted_p'])
                                                          for r in report['primary']]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    m = sub.add_parser('mini')
    m.add_argument('--study-dir', type=Path, required=True)
    m.add_argument('--output-dir', type=Path, required=True)
    m.add_argument('--bootstrap-draws', type=int)
    m.add_argument('--signflip-draws', type=int)
    args = parser.parse_args()
    mini(args)


if __name__ == '__main__':
    main()
