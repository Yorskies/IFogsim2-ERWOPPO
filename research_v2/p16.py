"""P16: final models, the sealed p16_test split, and the analysis registered in the P15 lock — one command, resumable.

    PYTHONPATH=. venv/bin/python -m research_v2.p16 run
    PYTHONPATH=. venv/bin/python -m research_v2.p16 status

Stages: verify the P15 lock and the 100 completed searches -> train every final model (4 seeds per arm and outer; no test access)
-> write P16_TEST_OPENED.json -> evaluate all final models and the frozen P11 equal_B checkpoints on p16_test -> analysis
(H1/H2 primary, H3/H4/H5/E1 secondary, D1-D4 descriptive) -> report and claims table. Uses the same P15_OUT/P15_SMOKE switches.
"""
import argparse
import json
import os
import signal

import numpy as np

from .config import ROOT, load_config, read_json, require
from . import p15 as P
from . import p15_jobs as J

OUT = P.OUT / 'p16'
STOP = P.STOP


def log(message):
    P.log('[p16] ' + message)


def stopped():
    P.stopped()


def mark(stage, **info):
    P.mark('p16_' + stage, **info)


def done(stage):
    return P.done('p16_' + stage)


def lock_path():
    return P.LOCK.relative_to(ROOT).as_posix()


def selected_weights(method, outer):
    return read_json(P.OUT / 'searches' / f'{method}_o{outer:02d}.json')['selected']['weights']


def arm_weights(arm, outer):
    if arm == 'equal_F':
        return P.EQUAL
    if arm == 'lean_zD':
        return P.LEAN_ZD
    return selected_weights(arm, outer)


ARMS = (*P.SEARCH_METHODS, 'equal_F', 'lean_zD')


def train_spec(arm, outer, k):
    return {'kind': 'train', 'weights': J.weights_of(arm_weights(arm, outer)), 'stream': {'split': 'train_final', 'outer': outer, 'repeat': 0},
            'seed': P.P16_SEED_BASE + 10 * outer + k, 'budget': P.F, 'eval': None, 'log_rows': P.FINAL_LOG_ROWS, 'learner': '0.3'}


def eval_spec(arm, outer, k=None):
    if arm == 'equal_B_p11':
        checkpoint, sha = read_json(P.LOCK)['final']['equal_B_p11']['checkpoints'][str(outer)]
        weights = P.EQUAL
    else:
        trained = J.result(OUT, train_spec(arm, outer, k))
        checkpoint, sha, weights = trained['checkpoint_path'], trained['model_sha256'], trained['weights']
    return {'kind': 'checkpoint', 'checkpoint': checkpoint, 'model_sha256': sha, 'weights': weights,
            'eval': {'split': 'p16_test', 'ids': list(P.P16_TEST_IDS)}, 'lock': lock_path()}


def models_of(arm, outer):
    return [eval_spec(arm, outer)] if arm == 'equal_B_p11' else [eval_spec(arm, outer, k) for k in range(P.FINAL_SEEDS)]


# ------------------------------------------------------------------------------------------------ analysis

def averaged_rows(specs):
    """Per-trace mean of the models of one arm and outer (costs and the physical metrics the loader reads)."""
    per_model = [J.eval_rows(OUT, s) for s in specs]
    out = []
    for rows in zip(*per_model):
        first = rows[0]
        require(all(r['trace_sha256'] == first['trace_sha256'] for r in rows), 'models evaluated different traces')
        metrics = {'task_count': first['metrics']['task_count'],
                   'violation': float(np.mean([r['metrics']['violation'] for r in rows])),
                   'reliability': float(np.mean([r['metrics']['reliability'] for r in rows])),
                   'costs': {c: float(np.mean([r['metrics']['costs'][c] for r in rows])) for c in J.COSTS}}
        out.append({'namespace': first['namespace'], 'trace_sha256': first['trace_sha256'], 'metrics': metrics})
    return out


def build_table():
    from .analysis.loader import rows_to_table
    arms = (*ARMS, 'equal_B_p11')
    cells = {(a, o): averaged_rows(models_of(a, o)) for a in arms for o in P.OUTERS}
    return rows_to_table(cells, load_config(), allowed_splits=('p16_test',))


def family(table, pairs, config, ids):
    from .analysis.stats import exploratory, holm, physical_summary
    rows = exploratory(table, pairs, config)
    adjusted = holm([r['raw_p_exact_signflip'] for r in rows])
    for hid, (c, t), r, p in zip(ids, pairs, rows, adjusted):
        r.update(id=hid, holm_p=float(p), significant=bool(p < config['statistics']['alpha']), physical=physical_summary(table, t, c))
    return rows


def equivalence(table, pairs, config):
    from .analysis.stats import bootstrap
    b = bootstrap(table, pairs, draws=config['statistics']['bootstrap_draws'], seed=config['seeds']['bootstrap'], level=0.90)
    out = []
    for k, (c, t) in enumerate(pairs):
        lo, hi = (float(x) for x in b['diff_ci'][:, k])
        out.append({'comparator': c, 'treatment': t, 'ci90': [lo, hi], 'margin': P.DELTA,
                    'equivalent': bool(-P.DELTA < lo and hi < P.DELTA)})
    return out


def friedman(table):
    from itertools import combinations
    from scipy.stats import friedmanchisquare, wilcoxon
    from .analysis.stats import aggregate, holm
    D = aggregate(table)['D']
    idx = {m: i for i, m in enumerate(table.methods)}
    data = [D[idx[m]] for m in P.SEARCH_METHODS]
    stat = friedmanchisquare(*data)
    pairs = list(combinations(P.SEARCH_METHODS, 2))
    raw = []
    for a, b in pairs:
        d = D[idx[a]] - D[idx[b]]
        raw.append(1.0 if np.allclose(d, 0) else float(wilcoxon(D[idx[a]], D[idx[b]]).pvalue))
    adj = holm(raw)
    ranks = np.argsort(np.argsort(np.stack(data), axis=0), axis=0).mean(axis=1) + 1
    return {'statistic': float(stat.statistic), 'p': float(stat.pvalue), 'mean_rank': dict(zip(P.SEARCH_METHODS, ranks.tolist())),
            'pairwise': [{'a': a, 'b': b, 'raw_p': r, 'holm_p': float(h)} for (a, b), r, h in zip(pairs, raw, adj)]}


def descriptive(table):
    from pymoo.indicators.igd_plus import IGDPlus
    from .analysis.stats import aggregate
    from .search import archive
    D = aggregate(table)['D']
    idx = {m: i for i, m in enumerate(table.methods)}
    curse, rule, anytime, hv, igd = {}, {}, {}, {}, {}
    for m in P.SEARCH_METHODS:
        rows = []
        for k, o in enumerate(table.outers):
            s = read_json(P.OUT / 'searches' / f'{m}_o{o:02d}.json')
            rows.append({'score_4': s['selected']['D_4_models'], 'score_12': s['selected']['D_12_models'], 'final': float(D[idx[m]][k]),
                         'p11_rule_same': s['selected_p11_rule']['weights'] == s['selected']['weights']})
            anytime.setdefault(m, []).append([h['min_D'] for h in s['history']])
            hv.setdefault(m, []).append(s['hypervolume'])
        curse[m] = {k: float(np.mean([r[k] for r in rows])) for k in ('score_4', 'score_12', 'final')}
        rule[m] = float(np.mean([r['p11_rule_same'] for r in rows]))
        L = min(len(a) for a in anytime[m])
        anytime[m] = np.mean([a[:L] for a in anytime[m]], axis=0).tolist()
        hv[m] = float(np.mean(hv[m]))
    for o in table.outers:
        searches = {m: read_json(P.OUT / 'searches' / f'{m}_o{o:02d}.json') for m in P.SEARCH_METHODS}
        ref = np.array([r['costs'] for r in archive([r for s in searches.values() for r in s['records']])])
        for m, s in searches.items():
            igd.setdefault(m, []).append(float(IGDPlus(ref)(np.array([r['costs'] for r in s['front']]))))
    return {'winners_curse': curse, 'p11_rule_agrees_with_12_model_rule': rule, 'anytime_min_score': anytime,
            'hypervolume_mean': hv, 'igd_plus_mean': {m: float(np.mean(v)) for m, v in igd.items()}}


def cost_pca():
    from scipy.stats import spearmanr
    macro = np.array([J.result(OUT, s)['macro_costs'] for a in ARMS for o in P.OUTERS for s in models_of(a, o)])
    z = (macro - macro.mean(0)) / np.where(macro.std(0) > 0, macro.std(0), 1)
    eig = np.sort(np.linalg.eigvalsh(np.cov(z.T)))[::-1]
    return {'explained': (eig / eig.sum()).tolist(), 'spearman': spearmanr(macro).statistic.tolist()}


def compute():
    out = {}
    for m in P.SEARCH_METHODS:
        walls = []
        for o in P.OUTERS:
            s = read_json(P.OUT / 'searches' / f'{m}_o{o:02d}.json')
            weights = [r['weights'] for r in s['records']]
            elites = [e['weights'] for e in s['elites']]
            specs = [x for w in weights for x in P.model_specs(w, o, P.BASE_MODELS)] + \
                    [x for w in elites for x in P.model_specs(w, o, P.BASE_MODELS + P.ELITE_EXTRA)[P.BASE_MODELS:]]
            uniq = {json.dumps(x, sort_keys=True): x for x in specs}.values()
            walls.append((sum(J.result(P.OUT, x)['total_wall_s'] for x in uniq), len(uniq) * P.F))
        out[m] = {'search_cpu_hours_per_outer': float(np.mean([w for w, _ in walls])) / 3600,
                  'search_training_decisions_per_outer': float(np.mean([n for _, n in walls]))}
    return out


def stage_analysis():
    config = load_config()
    lock = P.verify_lock()
    table = build_table()
    from .analysis.stats import aggregate
    agg = aggregate(table)
    methods = {m: {'Dglobal_mean': float(agg['D'][i].mean()), 'Dglobal_sd': float(agg['D'][i].std(ddof=1)),
                   'F_mean': agg['F'][i].mean(axis=0).tolist()} for i, m in enumerate(table.methods)}
    h1 = family(table, [('equal_F', m) for m in P.MOEAS], config, [f'H1{c}' for c in 'abcd'])
    h2 = family(table, [('random', m) for m in P.MOEAS], config, [f'H2{c}' for c in 'abcd'])
    h4 = family(table, [('equal_B_p11', m) for m in P.SEARCH_METHODS], config, [f'H4{c}' for c in 'abcde'])
    h5 = family(table, [('equal_F', 'lean_zD')], config, ['H5'])
    report = {'lock_sha256': lock['lock_sha256'], 'opened_utc': read_json(opened())['opened_utc'], 'smoke': P.SMOKE,
              'orientation': lock['hypotheses']['orientation'], 'methods': methods, 'H1': h1, 'H2': h2, 'H3': friedman(table),
              'H4': h4, 'H5': h5, 'E1': equivalence(table, [('equal_F', m) for m in P.MOEAS], config),
              'descriptive': descriptive(table), 'cost_pca': cost_pca(), 'compute': compute(),
              'selected_weights': {m: {o: selected_weights(m, o) for o in P.OUTERS} for m in P.SEARCH_METHODS}}
    J.dump(OUT / 'report/report.json', report)
    (OUT / 'report/report.md').write_text(render(report))
    mark('analysis', H1=[(r['id'], r['mean_difference'], r['holm_p']) for r in h1], H2=[(r['id'], r['mean_difference'], r['holm_p']) for r in h2])
    log(f'report written: {(OUT / "report/report.md").relative_to(ROOT)}')


def ci(c):
    return f'[{c[0]:.4f}; {c[1]:.4f}]'


def dz(d):
    v = d.get('dz') if isinstance(d, dict) else d
    return 'undef.' if v is None else f'{v:.3f}'


def render(r):
    k = 'mean_paired_difference_comparator_minus_treatment'
    lines = ['# P16 — final evaluation of the P15 MOEA benchmark (sealed p16_test)', '',
             f'P15 lock `{r["lock_sha256"][:12]}…`; p16_test opened {r["opened_utc"]}{" — SMOKE RUN" if r["smoke"] else ""}. '
             f'{r["orientation"]}. Unit: outer run; each arm\'s per-trace costs are the mean of its {P.FINAL_SEEDS} final models '
             '(equal_B_p11: one frozen P11 model per outer).', '',
             '## Methods (Dglobal, lower is better)', '', '| arm | mean | SD between outers |', '|---|---:|---:|']
    for m, v in sorted(r['methods'].items(), key=lambda kv: kv[1]['Dglobal_mean']):
        lines.append(f'| {m} | {v["Dglobal_mean"]:.4f} | {v["Dglobal_sd"]:.4f} |')
    for fam, title in (('H1', 'H1 — MOEA vs equal_F (primary, Holm)'), ('H2', 'H2 — MOEA vs random search (primary, Holm)'),
                       ('H4', 'H4 — search vs P11 equal_B (secondary, Holm)'), ('H5', 'H5 — lean_zD vs equal_F (secondary)')):
        lines += ['', f'## {title}', '', '| id | comparator | treatment | mean diff | 95% CI | dz | raw p | Holm p | energy J | violation pp | reliability pp |',
                  '|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|']
        for c in r[fam]:
            ph = c['physical']
            sig = '**' if c['significant'] else ''
            lines.append(f'| {c["id"]} | {c["comparator"]} | {c["treatment"]} | {c["mean_difference"]:+.4f} | {ci(c["ci95_difference"])} | '
                         f'{dz(c["effect_size_dz"])} | {c["raw_p_exact_signflip"]:.3g} | {sig}{c["holm_p"]:.3g}{sig} | '
                         f'{ph["dynamic_energy_j"][k]:.1f} | {ph["violation_pp"][k]:.2f} | {ph["reliability_pp"][k]:.2f} |')
    f = r['H3']
    lines += ['', '## H3 — Friedman over the five search methods', '',
              f'chi² = {f["statistic"]:.3f}, p = {f["p"]:.3g}; mean rank (1 = best): ' +
              ', '.join(f'{m} {v:.2f}' for m, v in sorted(f['mean_rank'].items(), key=lambda kv: kv[1])), '',
              '| pair | raw p | Holm p |', '|---|---:|---:|'] + [f'| {p["a"]} vs {p["b"]} | {p["raw_p"]:.3g} | {p["holm_p"]:.3g} |' for p in f['pairwise']]
    lines += ['', f'## E1 — equivalence of each MOEA with equal_F (margin ±{P.DELTA} D, 90% CI)', '', '| MOEA | 90% CI | equivalent |', '|---|---|:-:|']
    lines += [f'| {e["treatment"]} | {ci(e["ci90"])} | {"yes" if e["equivalent"] else "no"} |' for e in r['E1']]
    d = r['descriptive']
    lines += ['', '## Descriptive', '', '| method | search score (4 models) | search score (12 models) | final test D | P11 rule picks the same | HV | IGD+ |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for m in P.SEARCH_METHODS:
        c = d['winners_curse'][m]
        lines.append(f'| {m} | {c["score_4"]:.4f} | {c["score_12"]:.4f} | {c["final"]:.4f} | {d["p11_rule_agrees_with_12_model_rule"][m]:.0%} | '
                     f'{d["hypervolume_mean"][m]:.4f} | {d["igd_plus_mean"][m]:.4f} |')
    lines += ['', 'Cost PCA (final models), explained variance: ' + ', '.join(f'{v:.2f}' for v in r['cost_pca']['explained']),
              '', '| method | search CPU-hours per outer |', '|---|---:|'] + \
             [f'| {m} | {v["search_cpu_hours_per_outer"]:.1f} |' for m, v in r['compute'].items()]
    return '\n'.join(lines) + '\n'


def claims(r):
    def status(c):
        if c['significant']:
            return 'supported (treatment better)' if c['mean_difference'] > 0 else 'contradicted (comparator better)'
        return 'not supported (insufficient evidence; not equivalence)'
    eq = {e['treatment']: e['equivalent'] for e in r['E1']}
    lines = ['# P16 — claims table (P15 MOEA benchmark)', '', '| id | claim | evidence | status |', '|---|---|---|---|']
    for fam in ('H1', 'H2', 'H4', 'H5'):
        for c in r[fam]:
            extra = f'; equivalent within ±{P.DELTA}: {"yes" if eq.get(c["treatment"]) else "no"}' if fam == 'H1' else ''
            lines.append(f'| {c["id"]} | {c["treatment"]} better than {c["comparator"]} | diff {c["mean_difference"]:+.4f}, CI {ci(c["ci95_difference"])}, '
                         f'Holm p {c["holm_p"]:.3g}{extra} | {status(c)} |')
    lines += ['', f'H3 Friedman: chi² {r["H3"]["statistic"]:.3f}, p {r["H3"]["p"]:.3g}.', '',
              'Limits: simulation only; one topology; synthetic workloads; P15 ran although the P14 pilot gates G1/G2 failed '
              '(researcher decision recorded in the lock before any data); n = 20 outer runs with low power for effects below ~0.02 D.']
    return '\n'.join(lines) + '\n'


def opened():
    from .p16_traces import opened_record
    return opened_record(P.LOCK)


def run(workers):
    P.verify_lock()
    require(P.done('search'), 'P15 searches are not complete')
    if not done('train'):
        specs = [train_spec(a, o, k) for a in ARMS for o in P.OUTERS for k in range(P.FINAL_SEEDS)]
        J.run_specs(OUT, specs, workers, 'final training', log, stopped)
        mark('train', models=len(specs))
    stopped()
    if not done('open'):
        if not opened().exists():
            J.dump(opened(), {'split': 'p16_test', 'opened_utc': P.now(), 'p15_lock_sha256': read_json(P.LOCK)['lock_sha256'],
                              'note': 'opened once after every final model was trained; results are not used to retune anything'})
        mark('open', opened_utc=read_json(opened())['opened_utc'])
        log(f'p16_test opened at {read_json(opened())["opened_utc"]}')
    if not done('evaluation'):
        specs = [s for a in (*ARMS, 'equal_B_p11') for o in P.OUTERS for s in models_of(a, o)]
        J.run_specs(OUT, specs, workers, 'final evaluation', log, stopped)
        mark('evaluation', models=len(specs))
    stopped()
    if not done('analysis'):
        stage_analysis()
    if not done('claims'):
        (OUT / 'report/claims.md').write_text(claims(read_json(OUT / 'report/report.json')))
        mark('claims')
        log(f'claims table written: {(OUT / "report/claims.md").relative_to(ROOT)}')
    log('=== P16 complete ===')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    r = sub.add_parser('run')
    r.add_argument('--workers', type=int, default=12)
    sub.add_parser('status')
    args = parser.parse_args()
    if args.command == 'status':
        print(json.dumps({k: v for k, v in P.state()['stages'].items() if k.startswith('p16_')}, indent=2))
        n = len(list((OUT / 'runs').glob('*/result.json'))) if (OUT / 'runs').exists() else 0
        print(f'P16 jobs done: {n} (expected {len(ARMS) * len(P.OUTERS) * P.FINAL_SEEDS * 2 + len(P.OUTERS)})')
    else:
        signal.signal(signal.SIGTERM, lambda *_: STOP.update(requested=True))
        signal.signal(signal.SIGINT, lambda *_: STOP.update(requested=True))
        log(f'=== p16 run pid={os.getpid()} workers={args.workers} ===')
        run(args.workers)


if __name__ == '__main__':
    main()
