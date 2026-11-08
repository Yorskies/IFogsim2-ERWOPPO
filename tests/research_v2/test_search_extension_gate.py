from pathlib import Path
import tempfile
import unittest

from research_v2.config import ROOT, ContractError, load_config, read_json, sha256
from research_v2.learning import file_hash, write_json
from research_v2.search_runner_extension import require_extension_gate


class ExtensionGateTests(unittest.TestCase):
    def fixture(self, root):
        names = ('learning.py', 'search.py', 'search_runner.py', 'gym_env.py', 'rpc_client.py', 'traces.py')
        original = root.parent / 'P08_fidelity_1' / 'result.json'
        original.parent.mkdir(parents=True)
        write_json(original, {'status': 'fidelity_failed_stop', 'selected_K': None})
        protocol = {'version': 'P08-fidelity-extension-1', 'ladder': [30720, 40960, 46080],
                    'reference_decisions': 51200, 'config_sha256': sha256(load_config()),
                    'jar_sha256': read_json(ROOT / 'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256'],
                    'original_result_sha256': file_hash(original),
                    'source_hashes': {'research_v2/' + n: file_hash(ROOT / 'research_v2' / n) for n in names}}
        result = {'status': 'extension_confirmed', 'selected_K': 30720,
                  'independent_prefix_checks': 48, 'reference_final_matches': 48}
        write_json(root / 'protocol.json', protocol)
        write_json(root / 'result.json', result)
        write_json(root / 'audit.json', {'status': 'pass', 'selected_K': 30720,
            'independent_prefix_checks': 48, 'reference_final_matches': 48,
            'result_sha256': file_hash(root / 'result.json')})

    def test_confirmed_extension_returns_K(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'P08_extension'
            root.mkdir()
            self.fixture(root)
            self.assertEqual(require_extension_gate(root), 30720)

    def test_unconfirmed_extension_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'P08_extension'
            root.mkdir()
            self.fixture(root)
            result = read_json(root / 'result.json')
            result['status'] = 'extension_gate_pass'
            write_json(root / 'result.json', result)
            with self.assertRaises(ContractError):
                require_extension_gate(root)

    def test_modified_result_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'P08_extension'
            root.mkdir()
            self.fixture(root)
            result = read_json(root / 'result.json')
            result['selected_K'] = 40960
            write_json(root / 'result.json', result)
            with self.assertRaises(ContractError):
                require_extension_gate(root)

    def test_training_source_drift_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'P08_extension'
            root.mkdir()
            self.fixture(root)
            protocol = read_json(root / 'protocol.json')
            protocol['source_hashes']['research_v2/learning.py'] = '0' * 64
            write_json(root / 'protocol.json', protocol)
            with self.assertRaises(ContractError):
                require_extension_gate(root)


if __name__ == '__main__':
    unittest.main()
