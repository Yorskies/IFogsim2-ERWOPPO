"""P14 development split `dev_validation`: 25 traces per workload (ids 40000-40024), development data only (never a test split).

Same generator as the locked one (p13_traces.build mirrors TraceGenerator.generate byte for byte); the seed text names the
split, so the six RNG streams are independent of every other split. Ids 40000-40004 (5 per workload) score candidates during
search; ids 40005-40024 (20 per workload) are the independent hold-out for the 'true quality' of selected weights.
"""
from dataclasses import dataclass
import hashlib

from .config import require, validate_config
from .p13_traces import build, check_envelope
from .schema_definitions import COMPONENTS, WORKLOADS

SPLIT = 'dev_validation'
TRACE_IDS = (40000, 40024)
SEARCH_IDS = (40000, 40004)
HOLDOUT_IDS = (40005, 40024)


@dataclass(frozen=True, slots=True)
class DevKey:
    master: int
    trace_id: int
    workload: str
    split: str = SPLIT

    def validate(self, config):
        require(self.split == SPLIT, 'DevKey is only for the dev_validation split')
        require(self.master == config['seeds']['master'], 'Trace master seed differs from config')
        require(self.workload in WORKLOADS, f'Unknown workload: {self.workload}')
        require(type(self.trace_id) is int and TRACE_IDS[0] <= self.trace_id <= TRACE_IDS[1],
                f'trace_id outside dev_validation range {TRACE_IDS}')
        return self

    def to_dict(self):
        return {'master': self.master, 'split': self.split, 'outer_run': None, 'model_repeat': None,
                'trace_id': self.trace_id, 'workload': self.workload}

    def seed_text(self, component):
        require(component in COMPONENTS, f'Unknown RNG component: {component}')
        return '|'.join(str(f) for f in (self.master, self.split, '-', '-', self.trace_id, self.workload, component))

    def seed(self, component):
        return int.from_bytes(hashlib.sha256(self.seed_text(component).encode('utf-8')).digest()[:8], 'little', signed=False)


def generate(config, key):
    validate_config(config)
    key.validate(config)
    trace = build(config, key)
    check_envelope(trace, config)
    return trace


def keys(config, ids):
    require(TRACE_IDS[0] <= ids[0] <= ids[1] <= TRACE_IDS[1], 'id range outside dev_validation')
    for workload in config['training']['workload_order']:
        for trace_id in range(ids[0], ids[1] + 1):
            yield DevKey(config['seeds']['master'], trace_id, workload)
