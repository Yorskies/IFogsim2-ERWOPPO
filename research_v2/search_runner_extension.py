"""Full-search entry point gated by an audited P08 fidelity extension.

Importing this module never trains. The failed original fidelity evidence stays blocked.
"""
import argparse
from pathlib import Path

from .config import ROOT, load_config, read_json, require, sha256
from .learning import file_hash, provenance, write_json
from .search import optimize
from .search_runner import CandidateEvaluator


def require_extension_gate(path):
    path = Path(path)
    protocol = read_json(path / 'protocol.json')
    result = read_json(path / 'result.json')
    audit = read_json(path / 'audit.json')
    require(protocol['version'] == 'P08-fidelity-extension-1', 'Wrong fidelity protocol')
    require(result['status'] == 'extension_confirmed' and result['selected_K'] in protocol['ladder'],
            'Fidelity extension is not confirmed')
    require(result['selected_K'] < protocol['reference_decisions'], 'Candidate must be shorter than reference')
    require(result['independent_prefix_checks'] == 48 and result['reference_final_matches'] == 48,
            'Missing prefix or reference checks')
    require(audit['status'] == 'pass' and audit['selected_K'] == result['selected_K']
            and audit['independent_prefix_checks'] == 48 and audit['reference_final_matches'] == 48,
            'Missing or mismatched independent audit')
    require(audit['result_sha256'] == file_hash(path / 'result.json'), 'Fidelity result changed after audit')
    original = path.parent / 'P08_fidelity_1' / 'result.json'
    require(protocol['original_result_sha256'] == file_hash(original),
            'Original failed pilot changed')
    require(read_json(original)['status'] == 'fidelity_failed_stop',
            'Original pilot status changed')
    require(protocol['config_sha256'] == sha256(load_config()), 'Config changed after fidelity')
    receipt = read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')
    require(receipt['artifact_sha256'] == protocol['jar_sha256'], 'JAR changed after fidelity')
    for name in ('learning.py', 'search.py', 'search_runner.py', 'gym_env.py', 'rpc_client.py', 'traces.py'):
        key = 'research_v2/' + name
        require(file_hash(ROOT / key) == protocol['source_hashes'][key], f'Source changed after fidelity: {name}')
    return result['selected_K']


def run(method, outer, root, evidence, jdk_home=None):
    budget = require_extension_gate(evidence)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    config = load_config()
    write_json(root / 'protocol.json', {'phase': 'P08', 'method': method, 'outer': outer, 'K': budget,
        'candidate_slots': 80, 'model_repeats': 2, 'worker_count': 1,
        'fidelity_evidence': str(Path(evidence).resolve()), 'fidelity_version': 'P08-fidelity-extension-1',
        'provenance': provenance(config), 'test_accessed': False})
    evaluator = CandidateEvaluator(root / 'candidates', outer, budget, jdk_home)
    outcome = optimize(method, outer, evaluator, config)
    outcome.update(status='complete', K=budget, training_decisions=evaluator.training_decisions,
                   validation_decisions=evaluator.validation_decisions, test_accessed=False,
                   final_policy_trained=False,
                   search_cost=evaluator.training_decisions + evaluator.validation_decisions)
    write_json(root / 'result.json', outcome)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--method', choices=('nsga2', 'random'), required=True)
    parser.add_argument('--outer', type=int, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--fidelity-evidence', type=Path, required=True)
    parser.add_argument('--jdk-home', type=Path)
    args = parser.parse_args()
    run(args.method, args.outer, args.output_dir, args.fidelity_evidence, args.jdk_home)


if __name__ == '__main__':
    main()
