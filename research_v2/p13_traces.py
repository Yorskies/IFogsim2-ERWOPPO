"""P13 sealed split `benchmark_test`: 100 new traces per workload (ids 30000-30099), never generated before P13.

The locked v0.4 modules (traces.py, trace_access.py, schema_definitions.py) are not changed. This module rebuilds traces with
exactly the same generator algorithm (`build` mirrors TraceGenerator.generate line for line; a unit test proves byte
identity on locked splits) and a key whose seed text names the split `benchmark_test`, so all six RNG streams are new and
independent of every split used before. The trace envelope is checked against the locked trace schema with the split label
mapped to a schema-known value (only the enum differs). The simulator never reads the namespace; it checks the declared
payload hash, which is computed with the locked trace_payload_sha256.

Seal: before the P13 protocol lock, only `prepare` (payload hash and task count, no outcomes) is allowed. Evaluation requires
open_benchmark(lock), which verifies the P13 lock and the opening record.
"""
from dataclasses import dataclass
import hashlib
import math

import numpy as np

from . import SCHEMA_VERSION
from .config import require, sha256, validate_config
from .contracts import trace_payload_sha256, validate_contract
from .schema_definitions import COMPONENTS, WORKLOADS
from .traces import arrival_times, access_fog

SPLIT = 'benchmark_test'
TRACE_IDS = (30000, 30099)
_OPENED = None


@dataclass(frozen=True, slots=True)
class BenchmarkKey:
    master: int
    trace_id: int
    workload: str
    split: str = SPLIT

    def validate(self, config):
        require(self.split == SPLIT, 'BenchmarkKey is only for the benchmark_test split')
        require(self.master == config['seeds']['master'], 'Trace master seed differs from config')
        require(self.workload in WORKLOADS, f'Unknown workload: {self.workload}')
        require(type(self.trace_id) is int and TRACE_IDS[0] <= self.trace_id <= TRACE_IDS[1],
                f'trace_id outside benchmark_test range {TRACE_IDS}')
        return self

    def to_dict(self):
        return {'master': self.master, 'split': self.split, 'outer_run': None, 'model_repeat': None,
                'trace_id': self.trace_id, 'workload': self.workload}

    def seed_text(self, component):
        require(component in COMPONENTS, f'Unknown RNG component: {component}')
        return '|'.join(str(f) for f in (self.master, self.split, '-', '-', self.trace_id, self.workload, component))

    def seed(self, component):
        return int.from_bytes(hashlib.sha256(self.seed_text(component).encode('utf-8')).digest()[:8], 'little', signed=False)


def build(config, key):
    """Same algorithm as traces.TraceGenerator.generate (research-v2.trace-1); `key` needs seed(), to_dict(), workload."""
    rng = {name: np.random.Generator(np.random.PCG64(key.seed(name))) for name in COMPONENTS}
    classes = config['tasks']['classes']
    probabilities = [c['probability'] for c in classes]
    tasks = []
    for task_id, at in enumerate(arrival_times(config['workloads'][key.workload], rng['arrival'])):
        profile = classes[int(rng['class'].choice(len(classes), p=probabilities))]
        source = int(rng['source'].integers(0, config['topology']['iot_count']))
        cpu = int(rng['cpu_mi'].integers(profile['cpu_mi'][0], profile['cpu_mi'][1] + 1))
        size = math.ceil(float(rng['input_bytes'].uniform(*profile['input_mib'])) * 2**20)
        deadline = float(rng['deadline'].uniform(*profile['deadline_s']))
        tasks.append({'task_id': task_id, 'source_iot': source, 'access_fog': access_fog(source),
                      'class_id': profile['id'], 'arrival_s': at, 'cpu_mi': cpu,
                      'input_bytes': size, 'output_bytes': math.ceil(config['tasks']['output_fraction'] * size),
                      'deadline_relative_s': deadline, 'timeout_relative_s': config['timing']['timeout_factor'] * deadline,
                      'working_set_bytes': config['tasks']['working_set_bytes']})
    require(bool(tasks), 'N=0 trace rejected; no resampling or forced task')
    trace = {'schema_version': SCHEMA_VERSION, 'config_sha256': sha256(config), 'payload_sha256': '0' * 64,
             'seed_namespace': key.to_dict(), 'arrival_window_s': config['timing']['arrival_window_s'],
             'horizon_s': config['timing']['horizon_s'], 'task_count': len(tasks), 'tasks': tasks}
    trace['payload_sha256'] = trace_payload_sha256(trace)
    return trace


def check_envelope(trace, config):
    """Locked trace schema and task semantics; the split label is mapped only for the enum check."""
    require(trace['payload_sha256'] == trace_payload_sha256(trace), 'benchmark trace payload hash mismatch')
    probe = {**trace, 'seed_namespace': {**trace['seed_namespace'], 'split': 'test'}}
    probe['payload_sha256'] = trace_payload_sha256(probe)      # the probe's own hash; the real one is checked above
    validate_contract('trace', probe, config)
    for task in trace['tasks']:
        validate_contract('task', task, config)


def generate(config, key, *, purpose):
    validate_config(config)
    key.validate(config)
    require(purpose in ('prepare', 'evaluate'), f'Unknown purpose {purpose}')
    if purpose == 'evaluate':
        require(_OPENED is not None, 'benchmark_test is sealed: open_benchmark() with a valid P13 lock first')
    trace = build(config, key)
    check_envelope(trace, config)
    return trace


def keys(config):
    for workload in config['training']['workload_order']:
        for trace_id in range(TRACE_IDS[0], TRACE_IDS[1] + 1):
            yield BenchmarkKey(config['seeds']['master'], trace_id, workload)


def manifest(config):
    """Preparation only: payload hashes and task counts (inputs), no outcome is simulated."""
    rows = [{'workload': k.workload, 'trace_id': k.trace_id, 'tasks': t['task_count'], 'payload_sha256': t['payload_sha256']}
            for k in keys(config) for t in [generate(config, k, purpose='prepare')]]
    return {'split': SPLIT, 'trace_ids': list(TRACE_IDS), 'traces': len(rows), 'tasks_total': sum(r['tasks'] for r in rows),
            'rows_sha256': sha256(rows), 'rows': rows}


def open_benchmark(lock_path):
    global _OPENED
    from .p13 import verify_p13_lock, OPENED
    from .config import read_json
    lock = verify_p13_lock(lock_path)
    require(OPENED.exists() and read_json(OPENED)['p13_lock_sha256'] == lock['lock_sha256'],
            'benchmark_test opening record missing or bound to another lock')
    _OPENED = lock['lock_sha256']
