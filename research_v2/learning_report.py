"""Audit completed P07 evidence and plot curves; never performs training or evaluation."""
import argparse
import json
from pathlib import Path

import numpy as np

from .config import load_config, read_json, require, sha256
from .learning import COSTS, aggregate_costs, compare_checkpoints, file_hash, write_json


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def audit_run(path, budget):
    outcome, manifest = read_json(path/'outcome.json'), read_json(path/'manifest.json')
    require(outcome['status'] == manifest['status'] == 'complete', f'Incomplete run: {path}')
    require(outcome['decisions'] == outcome['audit']['decisions'] == budget, 'Budget drift')
    require(outcome['policy_changed'], 'Unchanged policy')
    require(manifest['config_sha256'] == sha256(load_config()), 'Config drift')
    decisions = 0
    histogram = np.zeros(7, dtype=int)
    episode_reward = 0.0
    episode_delta = np.zeros(5)
    complete_rewards = []
    with (path/'decisions.jsonl').open() as source:
        for line in source:
            row = json.loads(line)
            require(row['episode']['current']['namespace']['split'] == 'pilot_train', 'Training split leak')
            require(row['raw_snapshot'] is not None, 'Missing public snapshot')
            delta = np.asarray(row['cost_delta'])
            require(delta.shape == (5,) and np.isfinite(delta).all(), 'Invalid delta')
            require(np.isclose(row['reward'], -100*np.dot(manifest['weights'], delta), rtol=1e-6, atol=1e-8), 'Step reward mismatch')
            histogram[row['action']] += 1
            episode_reward += row['reward']
            episode_delta += delta
            decisions += 1
            if row['terminated']:
                complete_rewards.append((episode_reward, episode_delta))
                episode_reward, episode_delta = 0.0, np.zeros(5)
    require(decisions == budget, 'Decision log budget mismatch')
    require(histogram.tolist() == outcome['audit']['action_counts'], 'Action count mismatch')
    episodes = rows(path/'episodes.jsonl') if (path/'episodes.jsonl').exists() else []
    require(len(complete_rewards) == len(episodes), 'Episode count mismatch')
    for (reward, delta), episode in zip(complete_rewards, episodes):
        z = [episode['metrics']['costs'][k] for k in COSTS]
        require(np.allclose(delta, z, rtol=1e-6, atol=1e-8), 'Terminal drain/cost conservation mismatch')
        require(np.isclose(reward, episode['reward'], rtol=1e-6, atol=1e-8), 'Episode return mismatch')
        require(not episode['metrics']['diagnosis_required'], 'Out-of-reference physical metric')
    curve = rows(path/'learning_curve.jsonl')
    require([r['decisions'] for r in curve] == list(range(512,budget+1,512)), 'Rollout sequence mismatch')
    for point in curve:
        require(all(v is None or np.isfinite(v) for v in point.values()), 'Nonfinite curve')
    for checkpoint in path.glob('checkpoint_*'):
        state = read_json(checkpoint/'state.json')
        require(state['model_sha256'] == file_hash(checkpoint/'model.zip'), 'Corrupt model checkpoint')
        require(state['rng_sha256'] == file_hash(checkpoint/'rng.pt'), 'Corrupt RNG checkpoint')
    return {'decisions': budget, 'completed_episodes': len(episodes), 'wall_s': outcome['wall_s'],
            'updates': len(curve), 'action_counts': histogram.tolist(),
            'decisions_by_workload': outcome['audit']['decisions_by_workload'],
            'partial_episode': outcome['audit']['active_episode'],
            'first_loss': curve[0]['train/loss'], 'last_loss': curve[-1]['train/loss'],
            'first_entropy': -curve[0]['train/entropy_loss'], 'last_entropy': -curve[-1]['train/entropy_loss'],
            'max_kl': max(r['train/approx_kl'] for r in curve)}


def audit_validation(path):
    episodes = rows(path/'episodes.jsonl')
    expected = {(w,i) for w in load_config()['training']['workload_order'] for i in range(10000,10005)}
    require({(r['namespace']['workload'],r['namespace']['trace_id']) for r in episodes} == expected
            and len(episodes) == 20, 'Incomplete/duplicate validation')
    for row in episodes:
        require(row['namespace']['split'] == 'pilot_validation', 'Validation split leak')
        require(row['decisions'] == row['metrics']['task_count'] == sum(row['action_counts']), 'Partial evaluation')
        require(not row['metrics']['diagnosis_required'], 'Validation requires physical diagnosis')
        z = [row['metrics']['costs'][k] for k in COSTS]
        require(np.isclose(row['reward'], -20 * sum(z), rtol=1e-6, atol=1e-8), 'Equal-weight evaluation reward mismatch')
    aggregation = aggregate_costs(episodes, load_config()['training']['workload_order'])
    summary = read_json(path/'summary.json')
    if not np.isclose(summary['D_macro'], aggregation['D_macro'], rtol=1e-12, atol=1e-12):
        # Preserve the historical summary of the initial aggregation bug; only reaggregate raw evidence.
        backup = path/'summary_before_rms_fix.json'
        if not backup.exists():
            write_json(backup, summary)
        summary.update(aggregation)
        summary['aggregation_correction'] = 'D is RMS of macro cost vector per specification 16.3; raw episodes unchanged'
        write_json(path/'summary.json', summary)
    else:
        require(np.allclose(summary['macro_costs'],aggregation['macro_costs']), 'Macro vector mismatch')
    means = {}
    for w in load_config()['training']['workload_order']:
        group = [r for r in episodes if r['namespace']['workload']==w]
        actions = np.sum([r['action_counts'] for r in group],axis=0)
        means[w] = {k: float(np.mean([r['metrics'][k] for r in group])) for k in ('reliability','violation')}
        means[w]['latency_mean_s'] = float(np.mean([r['metrics']['latency']['mean_s'] for r in group]))
        means[w]['action_share'] = (actions / actions.sum()).tolist()
    return {**aggregation, 'episodes': len(episodes), 'decisions':sum(r['decisions'] for r in episodes),
            'physical_by_workload': means}


def generate(root):
    config = load_config()
    result = {'phase':'P07', 'status':'pass', 'scope':'technical learning pilot; no superiority claim',
              'training':{}, 'validation':{}, 'prefix_checks':{},
              'limitations':['Only equal weights and model repeat 0 in the three learning pilots.',
              'No test or confirmatory split accessed; no hyperparameter changes.',
              'Partial decided outcomes are unavailable in aggregate snapshots and never counted as success.',
              'Prefix equivalence is established for this environment/config/seed; no general resume support.']}
    for outer in (100,101,102):
        result['training'][str(outer)] = audit_run(root/f'pilot_r{outer}',10240)
        for count in (512,10240):
            result['validation'][f'{outer}_{count}'] = audit_validation(root/f'validation_r{outer}_{count}')
    result['validation']['smoke'] = audit_validation(root/'smoke_validation')
    for name in ('prefix_smoke','prefix_F'):
        comparison=read_json(root/name/'comparison.json')
        require(comparison['pass'], 'Failed prefix comparison')
        result['prefix_checks'][name]=comparison
    for name,budget in (('short',102400),('long',102912)):
        result['training'][f'prefix_F_{name}'] = audit_run(root/'prefix_F'/name,budget)
    # Replay pilot after earlier evaluation in separate processes; all early/final checkpoints must match.
    for count in (512,10240):
        comparison=compare_checkpoints(root/'pilot_r100'/f'checkpoint_{count:08d}',
                                       root/'prefix_F/short'/f'checkpoint_{count:08d}')
        require(comparison['pass'], 'Pilot replay mismatch')
        result['prefix_checks'][f'pilot_replay_{count}']=comparison
    result['validation']['diagnostic_F_r100'] = audit_validation(root/'diagnostic_validation_F_r100')
    result['stochastic_diagnosis'] = {}
    for outer in (100,101,102):
        path = root/f'diagnostic_stochastic_r{outer}'
        metadata = read_json(path/'summary.json')
        require(metadata['evaluation_mode'] == 'diagnostic_stochastic' and
                metadata['sampling_seed'] == 200000+2*outer, 'Diagnostic sampling seed/mode mismatch')
        result['stochastic_diagnosis'][str(outer)] = audit_validation(path)
    result['training_decisions_this_batch'] = sum(v['decisions'] for v in result['training'].values())+1536
    result['evaluation_decisions_this_batch'] = sum(v['decisions'] for v in list(result['validation'].values())+list(result['stochastic_diagnosis'].values()))
    result['evaluation_episodes_this_batch'] = sum(v['episodes'] for v in list(result['validation'].values())+list(result['stochastic_diagnosis'].values()))
    result['learning_diagnosis'] = {str(r): {
        'D_512':result['validation'][f'{r}_512']['D_macro'],
        'D_10240':result['validation'][f'{r}_10240']['D_macro'],
        'improved_D':result['validation'][f'{r}_10240']['D_macro'] < result['validation'][f'{r}_512']['D_macro']}
        for r in (100,101,102)}
    result['technical_gate'] = 'pass'
    result['quality_conclusion'] = 'No improvement of deterministic D in the three 10,240-decision pilots; diagnosis retained. This is not a superiority or convergence claim.'
    result['evidence_hashes']={p.relative_to(root).as_posix():file_hash(p) for p in sorted(root.rglob('*.json'))
                             if p.name in ('outcome.json','summary.json','comparison.json','manifest.json')}
    write_json(root/'P07_verification.json',result)
    plot(root)
    return result


def plot(root):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes=plt.subplots(2,2,figsize=(10,7),constrained_layout=True)
    for r in (100,101,102):
        curve=rows(root/f'pilot_r{r}/learning_curve.jsonl')
        for ax,key in zip(axes.flat,('train/loss','train/value_loss','train/entropy_loss','train/approx_kl')):
            ax.plot([c['decisions'] for c in curve],[c[key] for c in curve],label=str(r))
            ax.set(xlabel='Training decisions',ylabel=key)
            ax.legend(title='Outer pilot')
    fig.savefig(root/'learning_curves.svg')
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir',type=Path,required=True)
    args=parser.parse_args()
    result=generate(args.evidence_dir)
    print(json.dumps({k:v for k,v in result.items() if k in ('status','learning_diagnosis',
                    'training_decisions_this_batch','evaluation_decisions_this_batch','evaluation_episodes_this_batch')},indent=2))


if __name__=='__main__':
    main()
