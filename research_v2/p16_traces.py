"""P16 sealed test split `p16_test`: 100 traces per workload (ids 50000-50099), never generated before the P15 lock.

Same generator as the locked one (p13_traces.build, byte-identical algorithm); the seed text names the split, so the six RNG
streams are independent of every other split. Before the P15 lock only `prepare` (payload hash, task count; no outcome) is
allowed. Evaluation requires open_test(lock): the P15 lock must verify and the opening record P16_TEST_OPENED.json, written
next to the lock after all P16 final models are trained, must name that lock.
"""
from dataclasses import dataclass
import hashlib
from pathlib import Path

from .config import read_json, require, validate_config
from .p13_traces import build, check_envelope
from .schema_definitions import COMPONENTS, WORKLOADS

SPLIT = 'p16_test'
TRACE_IDS = (50000, 50099)
_OPENED = None


@dataclass(frozen=True, slots=True)
class TestKey:
    master: int
    trace_id: int
    workload: str
    split: str = SPLIT

    def validate(self, config):
        require(self.split == SPLIT, 'TestKey is only for the p16_test split')
        require(self.master == config['seeds']['master'], 'Trace master seed differs from config')
        require(self.workload in WORKLOADS, f'Unknown workload: {self.workload}')
        require(type(self.trace_id) is int and TRACE_IDS[0] <= self.trace_id <= TRACE_IDS[1],
                f'trace_id outside p16_test range {TRACE_IDS}')
        return self

    def to_dict(self):
        return {'master': self.master, 'split': self.split, 'outer_run': None, 'model_repeat': None,
                'trace_id': self.trace_id, 'workload': self.workload}

    def seed_text(self, component):
        require(component in COMPONENTS, f'Unknown RNG component: {component}')
        return '|'.join(str(f) for f in (self.master, self.split, '-', '-', self.trace_id, self.workload, component))

    def seed(self, component):
        return int.from_bytes(hashlib.sha256(self.seed_text(component).encode('utf-8')).digest()[:8], 'little', signed=False)


def keys(config, ids=TRACE_IDS):
    require(TRACE_IDS[0] <= ids[0] <= ids[1] <= TRACE_IDS[1], 'id range outside p16_test')
    for workload in config['training']['workload_order']:
        for trace_id in range(ids[0], ids[1] + 1):
            yield TestKey(config['seeds']['master'], trace_id, workload)


def generate(config, key, *, purpose):
    validate_config(config)
    key.validate(config)
    require(purpose in ('prepare', 'evaluate'), f'Unknown purpose {purpose}')
    if purpose == 'evaluate':
        require(_OPENED is not None, 'p16_test is sealed: open_test() with a valid P15 lock first')
    trace = build(config, key)
    check_envelope(trace, config)
    return trace


def manifest(config, ids=TRACE_IDS):
    from .config import sha256
    rows = [{'workload': k.workload, 'trace_id': k.trace_id, 'tasks': t['task_count'], 'payload_sha256': t['payload_sha256']}
            for k in keys(config, ids) for t in [generate(config, k, purpose='prepare')]]
    return {'split': SPLIT, 'trace_ids': list(ids), 'traces': len(rows), 'tasks_total': sum(r['tasks'] for r in rows),
            'rows_sha256': sha256(rows), 'rows': rows}


def opened_record(lock_path):
    return Path(lock_path).parent / 'P16_TEST_OPENED.json'


def open_test(lock_path):
    global _OPENED
    from .p15 import verify_lock
    lock = verify_lock(lock_path)
    record = opened_record(lock_path)
    require(record.exists() and read_json(record)['p15_lock_sha256'] == lock['lock_sha256'],
            'p16_test opening record missing or bound to another lock')
    _OPENED = lock['lock_sha256']
