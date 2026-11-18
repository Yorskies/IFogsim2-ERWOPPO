
import json, sys
from pathlib import Path
import numpy as np
mode, out = sys.argv[1], Path(sys.argv[2])
from research_v2.config import load_config, sha256
from research_v2.learning import setup_torch
config = load_config()
if mode == 'physical':
    from stable_baselines3 import PPO
    from research_v2 import baselines
    from research_v2.gym_env import OffloadingEnv
    from research_v2.trace_access import TraceKey
    from research_v2.traces import TraceGenerator
    checkpoint = Path(sys.argv[3])
    setup_torch(config)
    model = PPO.load(checkpoint / 'model.zip', device='cpu')
    weights = json.loads((checkpoint.parent / 'manifest.json').read_text())['weights']
    rows = []
    for name, policy, w in (('greedy_eft', lambda o, s: baselines.greedy_eft(s), [0.2] * 5),
                            ('checkpoint', lambda o, s: model.predict(o, deterministic=True)[0], weights)):
        for workload in ('light', 'heavy'):
            trace = TraceGenerator(config).generate(TraceKey(config['seeds']['master'], 'validation', None, None, 10000, workload),
                                                    role='search_validator').to_dict()
            env = OffloadingEnv([trace], w, config=config, jdk_home=sys.argv[4], any_port=True, validate=True)
            try:
                obs, info = env.reset(seed=0)
                actions, done = [], False
                while not done:
                    a = int(policy(obs, info['raw_snapshot']))
                    actions.append(a)
                    obs, r, done, _, info = env.step(a)
                rows.append({'policy': name, 'workload': workload, 'trace_sha256': trace['payload_sha256'],
                             'actions_sha256': sha256(actions), 'metrics': info['summary']['metrics'],
                             'energy': info['summary'].get('energy')})
            finally:
                env.close()
    out.write_text(json.dumps(rows, indent=2))
elif mode == 'learn':
    from stable_baselines3 import PPO
    from research_v2.learning import run_training
    from research_v2.learning_instrumentation import tensor_digest
    run_training(out / 'run', 100, 0, 1024, [0.2] * 5, sys.argv[3], training_split='pilot_train', phase='P11',
                 checkpoint_at=[1024], learner_version='0.3')
    ck = out / 'run' / 'checkpoint_00001024'
    model = PPO.load(ck / 'model.zip', device='cpu')
    curve = (out / 'run' / 'learning_curve.jsonl').read_text() if (out / 'run' / 'learning_curve.jsonl').exists() else ''
    (out / 'result.json').write_text(json.dumps({'policy_tensor_sha256': tensor_digest(model.policy.state_dict()),
        'num_timesteps': model.num_timesteps, 'learning_curve_sha256': sha256(curve)}, indent=2))
