from pathlib import Path
import tempfile
import unittest
from research_v2.config import ContractError,load_config,sha256,read_json,ROOT
from research_v2.learning import write_json,file_hash
from research_v2.search_runner import require_gate


class SearchGateTests(unittest.TestCase):
    def fixture(self,path,status='fidelity_pass'):
        write_json(path/'result.json',{'status':status,'selected_K':5120})
        write_json(path/'fidelity_verification.json',{'status':'pass','selected_K':5120,'result_sha256':file_hash(path/'result.json')})
        write_json(path/'protocol.json',{'config_sha256':sha256(load_config()),
            'jar_sha256':read_json(ROOT/'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256'],
            'source_hashes':{'research_v2/'+name:file_hash(ROOT/'research_v2'/name) for name in ('learning.py','search.py','gym_env.py','rpc_client.py','traces.py')}})

    def test_failed_fidelity_blocks_full_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root,'fidelity_failed_stop')
            with self.assertRaises(ContractError):require_gate(root)

    def test_modified_gate_blocks_full_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root)
            write_json(root/'result.json',{'status':'fidelity_pass','selected_K':10240})
            with self.assertRaises(ContractError):require_gate(root)

    def test_source_drift_blocks_full_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root)
            p=read_json(root/'protocol.json');p['source_hashes']['research_v2/learning.py']='0'*64
            write_json(root/'protocol.json',p)
            with self.assertRaises(ContractError):require_gate(root)

    def test_matching_audited_gate_selects_only_K(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.fixture(root)
            self.assertEqual(require_gate(root),5120)


if __name__=='__main__':unittest.main()
