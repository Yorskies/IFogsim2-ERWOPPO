"""P07 preparation verifier: forbids training and JVM startup; never certifies the learning gate."""
import argparse
import io
import json
from pathlib import Path
import platform
import sys
import unittest
from unittest.mock import patch

from .config import ROOT
from .learning import file_hash, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    suite = unittest.TestLoader().discover(str(ROOT / 'tests/research_v2'), pattern='test_learning.py')
    log = io.StringIO()
    blocked = RuntimeError('Training or JVM startup is forbidden during preparation verification')
    with patch('stable_baselines3.PPO.learn', side_effect=blocked), \
         patch('stable_baselines3.PPO.train', side_effect=blocked), \
         patch('research_v2.rpc_client.ServerProcess.__init__', side_effect=blocked):
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    passed = result.wasSuccessful() and not result.skipped
    report = {'phase': 'P07', 'scope': 'preparation only; no training, rollout or JVM startup',
              'status': 'pass' if passed else 'failed', 'learning_gate': 'not_run',
              'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'skipped': len(result.skipped), 'test_log': log.getvalue(),
              'environment': {'python': sys.version, 'platform': platform.platform()},
              'source_hashes': {name: file_hash(ROOT/name) for name in (
                  'research_v2/learning.py', 'research_v2/verify_learning.py',
                  'tests/research_v2/test_learning.py', 'requirements-v2-learning.txt')}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('test_log', 'source_hashes')}))
    if not passed:
        print(log.getvalue(), file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
