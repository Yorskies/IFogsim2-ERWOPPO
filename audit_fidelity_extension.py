"""Read-only integrity audit for the exploratory P08 fidelity extension."""
import argparse
from pathlib import Path

from research_v2.config import ROOT, load_config, read_json, require
from research_v2.fidelity_extension import LADDER, OLD, REFERENCE, check
from research_v2.fidelity_report import verify_training, verify_validation
from research_v2.learning import compare_checkpoints, file_hash, write_json
from research_v2.search import fidelity_gate, repeated_objectives


def audit(root):
    p = check(root)
    result = read_json(root / 'result.json')
    protocol = {**p, 'ppo': load_config()['ppo']}
    payloads = None
    reference_matches = 0
    validated = 0
    evaluation_decisions = 0
    prefix_checks = 0
    vectors = {}
    for job in p['jobs']:
        base = root / 'models' / job['id']
        path = base / 'reference_extended'
        verify_training(path, REFERENCE, job, protocol)
        require(compare_checkpoints(path / f'checkpoint_{REFERENCE:08d}',
            OLD / 'models' / job['id'] / 'reference' / f'checkpoint_{REFERENCE:08d}')['pass'],
            'Extended final reference mismatch')
        reference_matches += 1
        vectors[job['id']] = {}
        for k in LADDER:
            label = f'K{k:06d}'
            costs, decisions, payloads = verify_validation(base / (label + '_validation'),
                path / f'checkpoint_{k:08d}', job['weights'], payloads)
            vectors[job['id']][k] = costs
            validated += 1
            evaluation_decisions += decisions
        if result['selected_K'] is not None:
            k = result['selected_K']
            independent = base / f'K{k:06d}_independent'
            verify_training(independent, k, job, protocol)
            require(compare_checkpoints(independent / f'checkpoint_{k:08d}',
                path / f'checkpoint_{k:08d}')['pass'], 'Independent prefix mismatch')
            prefix_checks += 1
    stages = []
    original = read_json(OLD / 'result.json')
    reference = original['stages'][0]['reference_D']
    for k in LADDER:
        short = []
        for outer in (100, 101, 102):
            x = []
            for weight in p['weights']:
                jobs = [j for j in p['jobs'] if j['outer'] == outer and j['weight_id'] == weight['id']]
                require(len(jobs) == 2, 'Missing two repeats')
                x.append(repeated_objectives([vectors[j['id']][k] for j in jobs])['D'])
            short.append(x)
        stages.append({'K': k, **fidelity_gate(short, reference)})
    for stage, stored in zip(stages, result['stages']):
        require(stage['K'] == stored['K'] and stage['correlations'] == stored['correlations']
                and stage['pass'] == stored['pass'], 'Gate mismatch')
    selected = next((s['K'] for s in stages if s['pass']), None)
    require(selected == result['selected_K'], 'Selected K mismatch')
    require(reference_matches == 48 and validated == 144, 'Missing model or validation')
    require(result['evaluation_episodes'] == 20 * validated and result['test_accessed'] is False,
            'Episode accounting or split declaration mismatch')
    expected_training = 48 * REFERENCE + (48 * selected if selected is not None else 0)
    require(result['training_decisions'] == expected_training, 'Training budget accounting mismatch')
    if selected is not None:
        require(prefix_checks == 48 and result['status'] == 'extension_confirmed', 'Missing independent confirmations')
    else:
        require(prefix_checks == 0 and result['status'] == 'extension_gate_failed', 'Wrong failed status')
    output = {'status': 'pass', 'scope': 'exploratory extension; original pilot remains failed',
              'selected_K': selected, 'stages': stages, 'reference_final_matches': reference_matches,
              'complete_validations': validated, 'independent_prefix_checks': prefix_checks,
              'validation_episodes': 20 * validated, 'evaluation_decisions': evaluation_decisions,
              'training_decisions': expected_training, 'result_sha256': file_hash(root / 'result.json'),
              'test_accessed': False}
    write_json(root / 'audit.json', output)
    print({k: v for k, v in output.items() if k != 'stages'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', type=Path, required=True)
    audit(parser.parse_args().evidence_dir)
