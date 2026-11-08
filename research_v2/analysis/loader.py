"""Build the analysis Table from per-episode evaluation rows (the schema written by P07/P09 validation runs).

Pairing is enforced, not assumed: every (method, outer) cell must evaluate exactly the same (workload, trace_id) set
with identical trace payload hashes. Anything missing is an error. Only the validation/pilot namespaces are read here;
the test split stays sealed until the P10 protocol lock is verified.
"""
import json
from pathlib import Path

import numpy as np

from ..config import ContractError, read_json, require
from .stats import COSTS, Table


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def rows_to_table(cells, config, *, allowed_splits=('validation',)):
    """cells: {(method, outer): [episode rows]}. Methods and outers are ordered deterministically."""
    require(cells, 'No evaluation cells')
    methods = tuple(dict.fromkeys(m for m, _ in cells))
    outers = tuple(sorted({o for _, o in cells}))
    require(set(cells) == {(m, o) for m in methods for o in outers},
            'Missing (method, outer) cell: ' + str(sorted({(m, o) for m in methods for o in outers} - set(cells))[:5]))
    workloads = tuple(config['training']['workload_order'])
    reference = None
    keyed = {}
    for cell, rows in cells.items():
        table = {}
        for row in rows:
            ns = row['namespace']
            require(ns['split'] in allowed_splits, f'Split {ns["split"]} is not readable by this loader')
            require(ns['workload'] in workloads, f'Unknown workload {ns["workload"]}')
            key = (ns['workload'], ns['trace_id'])
            require(key not in table, f'Repeated trace {key} in cell {cell}')
            table[key] = row
        identity = {k: r['trace_sha256'] for k, r in table.items()}
        reference = identity if reference is None else reference
        require(identity == reference, f'Cell {cell} evaluated different traces (pairing broken)')
        keyed[cell] = table
    trace_ids = {w: sorted(t for (ww, t) in reference if ww == w) for w in workloads}
    require(all(trace_ids[w] for w in workloads), 'A workload has no traces')
    shape = lambda w: (len(methods), len(outers), len(trace_ids[w]))
    z = {w: np.empty(shape(w) + (len(COSTS),)) for w in workloads}
    n_tasks = {w: np.empty(shape(w)) for w in workloads}
    physical = {name: {w: np.empty(shape(w)) for w in workloads}
                for name in ('dynamic_energy_j', 'violation_pp', 'reliability_pp')}
    e_ref = config['evaluation']['energy_reference_j_per_arrival']
    for (method, outer), table in keyed.items():
        mi, oi = methods.index(method), outers.index(outer)
        for (w, trace), row in table.items():
            ti = trace_ids[w].index(trace)
            metrics = row['metrics']
            z[w][mi, oi, ti] = [metrics['costs'][c] for c in COSTS]
            n = metrics['task_count']
            n_tasks[w][mi, oi, ti] = n
            # zE = E_dynamic / (50 J * N); idle energy is identical for all methods on one trace.
            physical['dynamic_energy_j'][w][mi, oi, ti] = metrics['costs']['zE'] * e_ref * n
            physical['violation_pp'][w][mi, oi, ti] = 100 * metrics['violation']
            physical['reliability_pp'][w][mi, oi, ti] = 100 * metrics['reliability']
    return Table(methods=methods, outers=outers, workloads=workloads, trace_ids=trace_ids, z=z,
                 n_tasks=n_tasks, physical=physical)


# P09 fixture mapping: labels are placeholders so the pipeline can be exercised end to end on the validation
# namespace. They are NOT method evidence (the fixture "final" is one weight vector trained for 1,024 decisions).
FIXTURE_MAPPING = {
    'nsga2': ('r{o:02d}_mini_final', 'validation_F'),
    'random': ('r{o:02d}_manual', 'validation_F'),
    'equal_F': ('r{o:02d}_equal', 'validation_F'),
    'equal_B': ('r{o:02d}_equal', 'validation_B'),
    'manual_F': ('r{o:02d}_manual', 'validation_F'),
    'manual_B': ('r{o:02d}_manual', 'validation_B'),
}


def load_study_cells(study, outers, mapping=FIXTURE_MAPPING):
    study = Path(study)
    cells = {}
    for method, (job, label) in mapping.items():
        for outer in outers:
            pointer = read_json(study / 'jobs' / job.format(o=outer) / 'complete.json')
            require(pointer['status'] == 'complete', 'Analysis reads completed jobs only')
            cells[(method, outer)] = read_rows(study / pointer['attempt'] / 'data' / label / 'episodes.jsonl')
    return cells


def compute_cost(study, outers):
    """Per-job resources from the P09 profiles (decisions are ledger counts; seconds are wall/CPU of one worker)."""
    study = Path(study)
    rows = []
    for job in read_json(study / 'protocol.json')['jobs']:
        if job['outer'] not in outers:
            continue
        pointer = read_json(study / 'jobs' / job['id'] / 'complete.json')
        attempt = study / pointer['attempt']
        result = read_json(attempt / 'data' / 'result.json')
        profile = read_json(attempt / 'profile.json')
        rows.append({'job': job['id'], 'role': job['role'], 'outer': job['outer'],
                     'training_decisions': result['training_decisions'],
                     'validation_decisions': result.get('validation_decisions', 0),
                     'wall_s': profile['wall_s'], 'cpu_s': profile['cpu_user_s'] + profile['cpu_system_s'],
                     'max_rss_gib': profile['max_rss_kib'] / 2 ** 20,
                     'gradient_updates': profile['gradient_updates']})
    return rows
