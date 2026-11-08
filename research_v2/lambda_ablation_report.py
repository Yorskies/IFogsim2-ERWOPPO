"""Audit and compare the paired P07 lambda experiment. No training or online evaluation."""
import argparse
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

from .config import load_config, read_json, require, sha256
from .learning import compare_checkpoints, effective_learner, file_hash, write_json
from .learning_instrumentation import recompute_gae
from .learning_report import audit_run, audit_validation, rows

CONDITIONS=('lambda095','lambda100')


def audit_instrumentation(path,budget):
    updates=rows(path/'instrumentation/updates.jsonl')
    require([u['decisions'] for u in updates]==list(range(512,budget+1,512)),'Missing update instrumentation')
    grad_pre=[];grad_post=[];clipped=0;steps=0;adv_std=[];return_std=[];value_std=[]
    for update in updates:
        with np.load(path/f"instrumentation/rollout_{update['decisions']:08d}.npz") as data:
            for field in ('observations','actions','rewards','values','advantages','returns','old_log_probs','last_values'):
                require(np.isfinite(data[field]).all(),f'Nonfinite buffer {field}')
            a,r=recompute_gae(data['rewards'],data['values'],data['episode_starts'],data['last_values'],data['last_dones'],
                              float(data['gamma']),float(data['gae_lambda']))
            require(np.allclose(a,data['advantages'],rtol=1e-5,atol=1e-5),'GAE mismatch in saved buffer')
            require(np.allclose(r,data['returns'],rtol=1e-5,atol=1e-5),'Return mismatch in saved buffer')
            require(len(a)==512 and float(data['gamma'])==1.,'Rollout shape/gamma drift')
            adv_std.append(float(data['advantages'].std()));return_std.append(float(data['returns'].std()))
            value_std.append(float(data['values'].std()))
        require(update['optimizer_steps']==len(update['gradients']),'Optimizer step count drift')
        for g in update['gradients']:
            require(np.isfinite(g['pre_clip_norm']) and np.isfinite(g['post_clip_norm']),'Nonfinite gradient')
            require(g['post_clip_norm']<=g['max_norm']+1e-5,'Gradient clipping limit exceeded')
            grad_pre.append(g['pre_clip_norm']);grad_post.append(g['post_clip_norm']);clipped+=int(g['was_clipped']);steps+=1
    require(steps>0,'No optimizer steps')
    curve=rows(path/'learning_curve.jsonl')
    ev=[u['train/explained_variance'] for u in curve if u['train/explained_variance'] is not None]
    return {'rollouts':len(updates),'optimizer_steps':steps,'clipped_steps':clipped,'gradient_clipped_fraction':clipped/steps,
            'median_pre_clip_norm':float(np.median(grad_pre)),'max_pre_clip_norm':max(grad_pre),
            'max_post_clip_norm':max(grad_post),'median_advantage_std':float(np.median(adv_std)),
            'median_return_std':float(np.median(return_std)),'median_value_std':float(np.median(value_std)),
            'critic_negative_EV_updates':sum(v<0 for v in ev),'mean_critic_EV':float(np.mean(ev)),
            'last_entropy':-curve[-1]['train/entropy_loss'],
            'note':'EV and return statistics use each condition own GAE targets; not a common ground-truth critic accuracy metric.'}


def audit(root,previous):
    protocol=read_json(root/'protocol.json');require((root/'execution_complete.json').exists(),'Batch incomplete')
    report={'protocol':protocol,'status':'pass','pairs':{},'conditions':{},'passivity':{},'pairing':{},'prefix':{},
            'scope':'Paired pilot diagnostic; no confirmatory/test split, no automatic adoption.'}
    frozen=read_json(root/'source_hashes.json')
    require(sha256(load_config())==protocol['simulation_config_sha256'],'Simulation config changed')
    for name in CONDITIONS:
        spec_path=root/f'{name}.json'
        require(file_hash(spec_path)==protocol['spec_file_hashes'][name],'Learner spec changed')
        effective,spec=effective_learner(load_config(),spec_path)
        report['conditions'][name]={}
        audit_run(root/name/'smoke',512);audit_instrumentation(root/name/'smoke',512)
        for seed in (100,101,102):
            path=root/name/f'pilot_r{seed}'
            manifest=read_json(path/'manifest.json')
            require(manifest['effective_ppo']==effective['ppo'] and manifest['learner_config_sha256']==sha256(effective),'Effective learner drift')
            require(manifest['provenance']['build_receipt']['artifact_sha256']==protocol['jar_sha256'],'JAR drift')
            for source,digest in frozen.items():
                require(manifest['provenance']['source_hashes'][source]==digest,'Training source drift')
            train=audit_run(path,10240);inst=audit_instrumentation(path,10240)
            model=PPO.load(path/'checkpoint_00010240/model.zip',device='cpu')
            require(model.gae_lambda==effective['ppo']['gae_lambda'] and model.gamma==1.,'Saved model lambda/gamma mismatch')
            require(model.learning_rate==effective['ppo']['learning_rate'],'Saved model learning rate drift')
            vals={}
            for count in (512,10240):
                p=root/name/f'validation_r{seed}_{count}'
                meta=read_json(p/'summary.json');state=read_json(path/f'checkpoint_{count:08d}/state.json')
                require(meta['evaluation_mode']=='deterministic' and meta['model_sha256']==state['model_sha256'],'Evaluation model/mode mismatch')
                vals[str(count)]=audit_validation(p)
            p=root/name/f'diagnostic_stochastic_r{seed}'
            require(read_json(p/'summary.json')['evaluation_mode']=='diagnostic_stochastic','Wrong diagnostic mode')
            sampled=audit_validation(p)
            report['conditions'][name][str(seed)]={'training':train,'instrumentation':inst,'validation':vals,'sampled':sampled}
        long=root/name/'prefix_long'
        audit_run(long,10752);audit_instrumentation(long,10752)
        c=compare_checkpoints(root/name/'pilot_r100/checkpoint_00010240',long/'checkpoint_00010240')
        require(c['pass'],'Pilot prefix failure');report['prefix'][name]=c
        c=compare_checkpoints(root/name/'smoke/checkpoint_00000512',root/name/'pilot_r100/checkpoint_00000512')
        require(c['pass'],'Smoke/pilot prefix failure');report['prefix'][name+'_smoke']=c
    for seed in (100,101,102):
        a=root/'lambda095'/f'pilot_r{seed}';b=root/'lambda100'/f'pilot_r{seed}'
        require(read_json(a/'initial_policy.json')==read_json(b/'initial_policy.json'),'Different initialization')
        require(rows(a/'traces.jsonl')==rows(b/'traces.jsonl'),'Unpaired external traces')
        with np.load(a/'instrumentation/rollout_00000512.npz') as x,np.load(b/'instrumentation/rollout_00000512.npz') as y:
            require(all(np.array_equal(x[k],y[k]) for k in ('observations','actions','rewards','values','episode_starts','old_log_probs','last_values','last_dones')),
                    'First rollout differs before treatment update')
            require(not np.array_equal(x['advantages'],y['advantages']),'Lambda treatment did not change advantages')
        report['pairing'][str(seed)]={'same_initial_policy':True,'same_trace_stream':True,'same_first_rollout_before_update':True,
                                     'different_first_GAE_advantages':True}
        report['passivity'][str(seed)]={}
        for count in (512,10240):
            comparison=compare_checkpoints(a/f'checkpoint_{count:08d}',previous/f'pilot_r{seed}'/f'checkpoint_{count:08d}')
            require(comparison['pass'],'Instrumentation changed baseline trajectory')
            report['passivity'][str(seed)][str(count)]=comparison
        first=report['conditions']['lambda095'][str(seed)]['validation']['10240']
        second=report['conditions']['lambda100'][str(seed)]['validation']['10240']
        report['pairs'][str(seed)]={'D_lambda095':first['D_macro'],'D_lambda100':second['D_macro'],
            'delta_D_100_minus_095':second['D_macro']-first['D_macro'],
            'linear_cost_lambda095':float(np.mean(first['macro_costs'])),'linear_cost_lambda100':float(np.mean(second['macro_costs'])),
            'macro_reliability_lambda095':float(np.mean([v['reliability'] for v in first['physical_by_workload'].values()])),
            'macro_reliability_lambda100':float(np.mean([v['reliability'] for v in second['physical_by_workload'].values()]))}
    differences=[p['delta_D_100_minus_095'] for p in report['pairs'].values()]
    report['comparison']={'mean_delta_D':float(np.mean(differences)),'median_delta_D':float(np.median(differences)),
        'seeds_with_lower_D_at_lambda100':sum(d<0 for d in differences),'seeds':3,
        'interpretation':'Descriptive paired pilot results; no p-value or superiority/generalization claim.'}
    validation=[v for condition in report['conditions'].values() for p in condition.values()
                for v in list(p['validation'].values())+[p['sampled']]]
    report['accounting']={'training_decisions':83968,'evaluation_episodes':sum(v['episodes'] for v in validation),
        'evaluation_decisions':sum(v['decisions'] for v in validation),'test_accessed':False}
    report['auditor_source_sha256']=file_hash(Path(__file__))
    write_json(root/'ablation_verification.json',report)
    plot(root,report)
    return report


def plot(root,report):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(12,3.7),constrained_layout=True)
    for index,seed in enumerate((100,101,102)):
        for condition,label in (('lambda095','lambda=0.95'),('lambda100','lambda=1.0')):
            vals=report['conditions'][condition][str(seed)]['validation']
            axes[index].plot([512,10240],[vals['512']['D_macro'],vals['10240']['D_macro']],marker='o',label=label)
        axes[index].set(title=f'Outer {seed}',xlabel='Training decisions',ylabel='Deterministic D (lower is better)')
        axes[index].legend()
    fig.savefig(root/'paired_D.svg');plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(12,3.7),constrained_layout=True)
    for seed,ax in zip((100,101,102),axes):
        for condition,label in (('lambda095','lambda=0.95'),('lambda100','lambda=1.0')):
            updates=rows(root/condition/f'pilot_r{seed}/instrumentation/updates.jsonl')
            ax.plot([u['decisions'] for u in updates],[u['advantages']['std'] for u in updates],label=label)
        ax.set(title=f'Outer {seed}',xlabel='Training decisions',ylabel='Raw advantage std');ax.legend()
    fig.savefig(root/'advantage_std.svg');plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir',type=Path,required=True)
    parser.add_argument('--previous-evidence',type=Path,required=True)
    args=parser.parse_args();r=audit(args.evidence_dir,args.previous_evidence)
    print(r['comparison']);print(r['accounting'])


if __name__=='__main__':main()
