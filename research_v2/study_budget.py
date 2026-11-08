"""P09 study manifest and exact pre-run interaction accounting. No training or test access."""
from .config import load_config, require, sha256
from .trace_access import TraceKey
from .traces import TraceGenerator


def validation_trace_manifest(config=None):
    config = config or load_config()
    generator = TraceGenerator(config)
    low, high = config['seeds']['validation_trace_ids']
    rows = []
    for workload in config['training']['workload_order']:
        for trace_id in range(low, high + 1):
            key = TraceKey(config['seeds']['master'], 'validation', None, None, trace_id, workload)
            trace = generator.generate(key, role='search_validator')
            rows.append({'workload': workload, 'trace_id': trace_id, 'tasks': trace.task_count,
                         'payload_sha256': trace.payload_sha256})
    require(len(rows) == 20, 'Expected 20 validation traces')
    return rows


def budget(config=None, *, K, slots=80, F=None, traces=None):
    config = config or load_config()
    F = config['training']['final_decisions'] if F is None else F
    rollout = config['ppo']['n_steps']
    require(type(K) is int and K > 0 and K % rollout == 0, 'K must align to PPO rollout')
    require(type(F) is int and F > 0 and F % rollout == 0, 'F must align to PPO rollout')
    require(type(slots) is int and slots > 0, 'Positive candidate slots required')
    traces = validation_trace_manifest(config) if traces is None else traces
    require(len(traces) == 20 and len({(t['workload'], t['trace_id']) for t in traces}) == 20,
            'Missing or repeated validation trace')
    ntrace = sum(row['tasks'] for row in traces)
    require(ntrace > 0, 'No validation decisions')
    repeats = config['search']['model_repeats']
    S = slots * repeats * K
    V = slots * repeats * ntrace
    C = S + V + F
    B = ((C + rollout - 1) // rollout) * rollout
    return {'K': K, 'F': F, 'B': B, 'S': S, 'V': V, 'C': C,
            'rounding_overhead': B - C, 'Ntrace': ntrace, 'validation_episodes': len(traces),
            'candidate_slots': slots, 'model_repeats': repeats, 'rollout': rollout,
            'per_method_total': C, 'two_method_search_and_final': 2 * C,
            'two_baseline_training': 2 * B, 'physical_total_per_outer': 2 * (C + B),
            'protocol_A': 'Each method search plus one fresh final PPO(F); equal/manual use checkpoint F of their B run.',
            'protocol_B': 'Same search and final PPO(F) artifacts reused; equal/manual use PPO(B). No search charge twice.'}


def job_manifest(outer, *, mini=False):
    require(type(outer) is int and 0 <= outer < 20, 'Outer run outside 0..19')
    if mini:
        return [
            {'id': f'r{outer:02d}_mini_search', 'outer': outer, 'role': 'search', 'method': 'fixture', 'protocols': ['A', 'B']},
            {'id': f'r{outer:02d}_mini_final', 'outer': outer, 'role': 'final', 'method': 'fixture', 'protocols': ['A', 'B'], 'depends_on': f'r{outer:02d}_mini_search'},
            {'id': f'r{outer:02d}_equal', 'outer': outer, 'role': 'baseline', 'method': 'equal', 'protocols': ['A', 'B']},
            {'id': f'r{outer:02d}_manual', 'outer': outer, 'role': 'baseline', 'method': 'manual', 'protocols': ['A', 'B']},
        ]
    return [
        *[{'id': f'r{outer:02d}_{method}_search', 'outer': outer, 'role': 'search', 'method': method,
           'protocols': ['A', 'B']} for method in ('nsga2', 'random')],
        *[{'id': f'r{outer:02d}_{method}_final', 'outer': outer, 'role': 'final', 'method': method,
           'protocols': ['A', 'B'], 'depends_on': f'r{outer:02d}_{method}_search'} for method in ('nsga2', 'random')],
        *[{'id': f'r{outer:02d}_{method}', 'outer': outer, 'role': 'baseline', 'method': method,
           'protocols': ['A', 'B']} for method in ('equal', 'manual')],
    ]


def build_plan(*, K, outers, mini=False, config=None):
    config = config or load_config()
    traces = validation_trace_manifest(config)
    slots = 1 if mini else config['search']['candidate_slots']
    F = 1024 if mini else config['training']['final_decisions']
    if mini:
        K = 512
    account = budget(config, K=K, slots=slots, F=F, traces=traces)
    if mini:
        account['physical_total_per_outer'] = account['C'] + 2 * account['B']
        account['one_method_search_and_final'] = account['C']
        account.pop('two_method_search_and_final')
    require(outers and len(set(outers)) == len(outers), 'Outer runs must be unique')
    jobs = []
    for outer in outers:
        jobs.extend(job_manifest(outer, mini=mini))
    return {'version': 'P09-study-1', 'fixture_only': mini, 'config_sha256': sha256(config),
            'outers': list(outers), 'jobs': jobs, 'budget': account,
            'validation_traces': traces, 'validation_manifest_sha256': sha256(traces),
            'test_accessed': False, 'workers': 1,
            'reuse': 'One search and one selected final model per method/outer are shared by protocols A and B.'}
