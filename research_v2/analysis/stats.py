"""P10 pre-specified statistical analysis (spec section 23). Pure NumPy: no training, JVM or test access.

Unit of inference is the outer training run. Costs are averaged over traces inside each workload, workloads are
macro-averaged with equal weight, and Dglobal = sqrt(sum_j F_j^2 / 5). Episodes/tasks are never pooled into
replicates and p-values are never averaged. Missing or non-finite data is an error, not something to impute.

Sign convention everywhere: difference = D(comparator) - D(NSGA-II); positive means NSGA-II is better.
"""
from dataclasses import dataclass
import itertools

import numpy as np

from ..config import ContractError, require

COSTS = ('zL', 'zE', 'zD', 'zB', 'zQ')
NSGA = 'nsga2'
# Pre-registered primary family (RQ1-RQ3): comparator, treatment.
PRIMARY = (('RQ1', 'equal_F', NSGA, 'PPO-Equal at checkpoint F vs NSGA-II at equal final budget F'),
           ('RQ2', 'random', NSGA, 'Random search vs NSGA-II at equal search and final budget'),
           ('RQ3', 'equal_B', NSGA, 'PPO-Equal at total budget B vs NSGA-II search+final total budget'))
MAX_EXACT_UNITS = 24


@dataclass
class Table:
    """z[w] has shape (methods, outers, traces_w, 5). trace_ids[w] are identical for every method and outer."""
    methods: tuple
    outers: tuple
    workloads: tuple
    trace_ids: dict
    z: dict
    n_tasks: dict | None = None      # w -> (methods, outers, traces_w) tasks per trace, for Joule conversion
    physical: dict | None = None     # name -> {w: (methods, outers, traces_w)}


def validate_table(table, *, expected_outers=None, expected_workloads=None):
    require(len(set(table.methods)) == len(table.methods), 'Duplicate method label')
    require(len(set(table.outers)) == len(table.outers), 'Duplicate outer run')
    if expected_outers is not None:
        require(tuple(sorted(table.outers)) == tuple(expected_outers),
                f'Missing or extra outer runs: have {sorted(table.outers)}, need {list(expected_outers)}')
    if expected_workloads is not None:
        require(tuple(table.workloads) == tuple(expected_workloads), 'Workload set/order differs from config')
    for w in table.workloads:
        array = table.z.get(w)
        require(array is not None, f'Missing workload {w}')
        shape = (len(table.methods), len(table.outers), len(table.trace_ids[w]), len(COSTS))
        require(array.shape == shape, f'Workload {w}: shape {array.shape}, expected {shape}')
        require(len(set(table.trace_ids[w])) == len(table.trace_ids[w]) and shape[2] > 0, f'Workload {w}: repeated/empty traces')
        require(np.isfinite(array).all(), f'Workload {w}: non-finite or missing cost')


def d_from_workload_means(zbar):
    """zbar [..., W, 5] -> (Dglobal [...], Dw [..., W], F [..., 5])."""
    F = zbar.mean(axis=-2)
    dglobal = np.sqrt((F ** 2).sum(axis=-1) / zbar.shape[-1])
    dw = np.sqrt((zbar ** 2).sum(axis=-1) / zbar.shape[-1])
    return dglobal, dw, F


def workload_means(table):
    """[methods, outers, W, 5]: mean over traces inside each workload (trace-level z is never pooled across workloads)."""
    return np.stack([table.z[w].mean(axis=2) for w in table.workloads], axis=2)


def aggregate(table):
    zbar = workload_means(table)
    dglobal, dw, F = d_from_workload_means(zbar)
    worst = np.argmax(dw, axis=-1)
    return {'zbar': zbar, 'D': dglobal, 'Dw': dw, 'F': F, 'worst_workload': worst}


# ---------------------------------------------------------------- hypothesis tests

def _tolerance(diffs):
    return 1e-12 * max(1.0, float(np.abs(diffs).sum()))


def exact_signflip_p(diffs):
    """Two-sided exact paired sign-flip test on the sum of differences: enumerate all 2^n sign assignments.
    Assumes sign symmetry of the differences under the null (not guaranteed by pairing alone)."""
    diffs = np.asarray(diffs, dtype=float)
    n = diffs.size
    require(1 <= n <= MAX_EXACT_UNITS and np.isfinite(diffs).all(), 'Exact sign-flip needs 1..24 finite differences')
    sums = np.zeros(1)
    for d in diffs:
        sums = np.concatenate((sums + d, sums - d))
    observed = abs(float(diffs.sum()))
    count = int((np.abs(sums) >= observed - _tolerance(diffs)).sum())
    return count / sums.size


def make_signs(draws, units, seed):
    rng = np.random.Generator(np.random.PCG64(seed))
    return rng.integers(0, 2, size=(draws, units)).astype(np.int8) * 2 - 1


def montecarlo_signflip_p(diffs, signs):
    """diffs [K, n]; signs [M, n] (+-1) shared across hypotheses. p = (b+1)/(M+1)."""
    diffs = np.atleast_2d(np.asarray(diffs, dtype=float))
    require(np.isfinite(diffs).all() and signs.shape[1] == diffs.shape[1], 'Bad Monte Carlo inputs')
    observed = np.abs(diffs.sum(axis=1))
    tolerance = np.array([_tolerance(row) for row in diffs])
    out = np.empty(diffs.shape[0])
    for k in range(diffs.shape[0]):
        permuted = np.abs(signs @ diffs[k])
        b = int((permuted >= observed[k] - tolerance[k]).sum())
        out[k] = (b + 1) / (signs.shape[0] + 1)
    return out


def holm(pvalues):
    """Holm step-down adjusted p-values, in input order."""
    p = np.asarray(pvalues, dtype=float)
    require(p.ndim == 1 and p.size > 0 and ((p >= 0) & (p <= 1)).all(), 'Invalid p-values for Holm')
    m = p.size
    order = np.argsort(p, kind='stable')
    adjusted = np.empty(m)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (m - rank) * p[index])
        adjusted[index] = min(1.0, running)
    return adjusted


def holm_by_closed_testing(pvalues):
    """Independent reference for small m: Holm equals closed testing with Bonferroni local tests.
    adjusted_i = max over intersection hypotheses I containing i of |I| * min_{j in I} p_j."""
    p = np.asarray(pvalues, dtype=float)
    m = p.size
    require(m <= 14, 'Reference closed testing is exponential; use small m')
    adjusted = np.zeros(m)
    for size in range(1, m + 1):
        for subset in itertools.combinations(range(m), size):
            local = min(1.0, size * p[list(subset)].min())
            for i in subset:
                adjusted[i] = max(adjusted[i], local)
    return adjusted


def paired_dz(diffs):
    """Signed paired dz = mean/SD (ddof=1). SD of zero is undefined (never replaced by 0)."""
    diffs = np.asarray(diffs, dtype=float)
    if diffs.size < 2:
        return {'dz': None, 'status': 'undefined_n_lt_2'}
    sd = float(diffs.std(ddof=1))
    # Floating-point SD of identical values is ~1e-17, not 0: compare against the data scale.
    if sd <= 1e-12 * float(np.abs(diffs).max()):
        return {'dz': None, 'status': 'undefined_zero_sd_nonzero_mean' if diffs.mean() != 0 else 'undefined_zero_sd_zero_mean'}
    return {'dz': float(diffs.mean() / sd), 'status': 'ok'}


# ---------------------------------------------------------------- crossed paired bootstrap

def bootstrap(table, pairs, *, draws, seed, level=0.95):
    """Crossed two-level bootstrap. Each draw resamples outer-run indices and, per workload, trace indices; the drawn
    traces are shared by every method and outer run. Aggregation is recomputed from the resampled traces.

    pairs: list of (comparator, treatment). Returns per-pair CI of mean(D_comp - D_treat), and relative improvement
    mean(diff) / mean(D_comp), plus per-(pair, workload, cost) CI of the mean paired difference of z."""
    index = {m: i for i, m in enumerate(table.methods)}
    require(all(a in index and b in index for a, b in pairs), 'Bootstrap pair references unknown method')
    comp = np.array([index[a] for a, _ in pairs])
    treat = np.array([index[b] for _, b in pairs])
    n_outer = len(table.outers)
    rng = np.random.Generator(np.random.PCG64(seed))
    d_diff = np.empty((draws, len(pairs)))
    d_rel = np.empty((draws, len(pairs)))
    cell = np.empty((draws, len(pairs), len(table.workloads), len(COSTS)))
    for draw in range(draws):
        outer_idx = rng.integers(0, n_outer, n_outer)
        zbar = np.empty((len(table.methods), n_outer, len(table.workloads), len(COSTS)))
        for k, w in enumerate(table.workloads):
            trace_idx = rng.integers(0, len(table.trace_ids[w]), len(table.trace_ids[w]))
            zbar[:, :, k, :] = table.z[w][:, outer_idx][:, :, trace_idx].mean(axis=2)
        dglobal, _, _ = d_from_workload_means(zbar)
        diff = dglobal[comp] - dglobal[treat]
        d_diff[draw] = diff.mean(axis=1)
        d_rel[draw] = diff.mean(axis=1) / dglobal[comp].mean(axis=1)
        cell[draw] = (zbar[comp] - zbar[treat]).mean(axis=1)
    lo, hi = (1 - level) / 2 * 100, (1 + level) / 2 * 100
    pct = lambda a, axis=0: np.percentile(a, [lo, hi], axis=axis)
    return {'draws': draws, 'seed': seed, 'level': level,
            'diff_ci': pct(d_diff), 'relative_ci': pct(d_rel), 'cell_ci': pct(cell)}


# ---------------------------------------------------------------- full analysis

def pair_differences(agg, table, comparator, treatment):
    i, j = table.methods.index(comparator), table.methods.index(treatment)
    return agg['D'][i] - agg['D'][j]


def analyse(table, config, *, bootstrap_draws=None, signflip_draws=None, primary_units_expected=None):
    """Run the registered primary (3, Holm) and secondary (60, Monte Carlo, Holm) families."""
    stats = config['statistics']
    seeds = config['seeds']
    bootstrap_draws = stats['bootstrap_draws'] if bootstrap_draws is None else bootstrap_draws
    signflip_draws = stats['secondary_signflip_draws'] if signflip_draws is None else signflip_draws
    expected_outers = tuple(range(seeds['outer_runs'])) if primary_units_expected is None else tuple(primary_units_expected)
    validate_table(table, expected_outers=expected_outers, expected_workloads=tuple(config['training']['workload_order']))
    for _, a, b, _ in PRIMARY:
        require(a in table.methods and b in table.methods, f'Primary comparison needs methods {a} and {b}')
    require(stats['primary_family_size'] == len(PRIMARY) and stats['secondary_family_size'] == len(PRIMARY) * 4 * 5,
            'Config family sizes differ from the registered hypotheses')
    order = np.argsort(table.outers)
    require(list(np.array(table.outers)[order]) == list(table.outers), 'Outer runs must be supplied in ascending order')
    agg = aggregate(table)
    pairs = [(a, b) for _, a, b, _ in PRIMARY]
    boot = bootstrap(table, pairs, draws=bootstrap_draws, seed=seeds['bootstrap'])

    primary = []
    raw = []
    for k, (rq, comparator, treatment, description) in enumerate(PRIMARY):
        diffs = pair_differences(agg, table, comparator, treatment)
        p = exact_signflip_p(diffs)
        raw.append(p)
        i = table.methods.index(comparator)
        mean_comparator = float(agg['D'][i].mean())
        primary.append({'id': rq, 'label': 'confirmatory_primary', 'description': description,
                        'comparator': comparator, 'treatment': treatment, 'n_outer_runs': int(diffs.size),
                        'differences_by_outer': diffs.tolist(), 'mean_difference': float(diffs.mean()),
                        'sd_difference': float(diffs.std(ddof=1)) if diffs.size > 1 else None,
                        'relative_improvement': float(diffs.mean() / mean_comparator),
                        'meets_1pct_reporting_screen': bool(diffs.mean() / mean_comparator >= stats['practical_relative_improvement']),
                        'ci95_difference': boot['diff_ci'][:, k].tolist(), 'ci95_relative': boot['relative_ci'][:, k].tolist(),
                        'effect_size_dz': paired_dz(diffs), 'raw_p_exact_signflip': p,
                        'test': 'exact two-sided paired sign-flip, 2^n enumeration',
                        'direction': 'positive = NSGA-II lower Dglobal (better)'})
    for row, adjusted in zip(primary, holm(raw)):
        row['holm_adjusted_p'] = float(adjusted)
        row['reject_at_alpha'] = bool(adjusted <= stats['alpha'])

    signs = make_signs(signflip_draws, len(table.outers), seeds['secondary_signflip'])
    secondary_cells = []
    diffs_matrix = []
    zbar = agg['zbar']
    for k, (rq, comparator, treatment, _) in enumerate(PRIMARY):
        i, j = table.methods.index(comparator), table.methods.index(treatment)
        for wi, w in enumerate(table.workloads):
            for ci, cost in enumerate(COSTS):
                diffs = zbar[i, :, wi, ci] - zbar[j, :, wi, ci]
                diffs_matrix.append(diffs)
                secondary_cells.append({'id': f'{rq}:{w}:{cost}', 'label': 'secondary_prespecified', 'primary_pair': rq,
                                        'workload': w, 'cost': cost, 'mean_difference': float(diffs.mean()),
                                        'ci95_difference': boot['cell_ci'][:, k, wi, ci].tolist(),
                                        'effect_size_dz': paired_dz(diffs)})
    p_secondary = montecarlo_signflip_p(np.array(diffs_matrix), signs)
    for cell, p, adjusted in zip(secondary_cells, p_secondary, holm(p_secondary)):
        cell.update(raw_p_montecarlo_signflip=float(p), holm_adjusted_p=float(adjusted),
                    reject_at_alpha=bool(adjusted <= stats['alpha']),
                    test=f'Monte Carlo sign-flip, M={signflip_draws}, p=(b+1)/(M+1)')
    methods = {}
    for i, m in enumerate(table.methods):
        d = agg['D'][i]
        methods[m] = {'Dglobal_mean': float(d.mean()), 'Dglobal_sd_between_runs': float(d.std(ddof=1)) if d.size > 1 else None,
                      'Dglobal_se': float(d.std(ddof=1) / np.sqrt(d.size)) if d.size > 1 else None,
                      'Dw_mean': {w: float(agg['Dw'][i, :, k].mean()) for k, w in enumerate(table.workloads)},
                      'cost_means_F': {c: float(agg['F'][i, :, ci].mean()) for ci, c in enumerate(COSTS)},
                      'worst_workload_counts': {w: int((agg['worst_workload'][i] == k).sum()) for k, w in enumerate(table.workloads)}}
    return {'protocol': {'unit': 'outer_training_run', 'n_units': len(table.outers),
                         'pools_tasks_or_episodes_as_replicates': False, 'p_values_averaged': False,
                         'alpha': stats['alpha'], 'bootstrap': {'draws': bootstrap_draws, 'seed': seeds['bootstrap']},
                         'secondary_signflip': {'draws': signflip_draws, 'seed': seeds['secondary_signflip']},
                         'traces_per_workload': {w: len(table.trace_ids[w]) for w in table.workloads}},
            'primary': primary, 'secondary': secondary_cells, 'methods': methods, 'outers': list(table.outers)}


def exploratory(table, pairs, config, *, bootstrap_draws=None):
    """Other comparisons (manual, heuristics, ...). Effect + CI + raw exact p only; no confirmatory claim."""
    stats, seeds = config['statistics'], config['seeds']
    draws = stats['bootstrap_draws'] if bootstrap_draws is None else bootstrap_draws
    validate_table(table)
    agg = aggregate(table)
    boot = bootstrap(table, pairs, draws=draws, seed=seeds['bootstrap'])
    rows = []
    for k, (comparator, treatment) in enumerate(pairs):
        diffs = pair_differences(agg, table, comparator, treatment)
        rows.append({'label': 'exploratory_unadjusted', 'comparator': comparator, 'treatment': treatment,
                     'mean_difference': float(diffs.mean()), 'ci95_difference': boot['diff_ci'][:, k].tolist(),
                     'effect_size_dz': paired_dz(diffs), 'raw_p_exact_signflip': exact_signflip_p(diffs),
                     'note': 'No multiplicity control and no confirmatory status; unregistered family.'})
    return rows


def physical_summary(table, method, comparator):
    """Practical meaning: paired dynamic-energy Joules (zE * 50 J * N; idle is identical across methods on one trace),
    violation and reliability in percentage points. Requires table.physical and table.n_tasks."""
    require(table.physical and table.n_tasks, 'Physical metrics were not loaded')
    i, j = table.methods.index(comparator), table.methods.index(method)
    out = {}
    for name, per_workload in table.physical.items():
        per_outer = []
        for k in range(len(table.outers)):
            values = [per_workload[w][i, k].mean() - per_workload[w][j, k].mean() for w in table.workloads]
            per_outer.append(float(np.mean(values)))
        out[name] = {'mean_paired_difference_comparator_minus_treatment': float(np.mean(per_outer)), 'by_outer': per_outer}
    return out
