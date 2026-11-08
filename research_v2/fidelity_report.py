"""Independent P08 fidelity evidence audit and plots; no training or simulator startup."""
import argparse
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

from .config import load_config,read_json,require,sha256
from .learning import aggregate_costs,compare_checkpoints,file_hash,write_json,setup_torch
from .learning_report import rows
from .search import repeated_objectives,fidelity_gate,archive,select


def verify_training(path,budget,job,protocol):
    m=read_json(path/'manifest.json');o=read_json(path/'outcome.json')
    require(o['status']=='complete' and m['status']=='complete' and o['decisions']==o['audit']['decisions']==budget,'Incomplete training')
    require(m['phase']=='P08' and m['split']=='pilot_train' and m['weights']==job['weights'],'Wrong training identity')
    require(m['effective_ppo']==protocol['ppo'] and m['config_sha256']==protocol['config_sha256'],'PPO/config drift')
    require(m['model_seed']==200000+2*job['outer']+job['repeat'],'Wrong model seed')
    require(m['provenance']['build_receipt']['artifact_sha256']==protocol['jar_sha256'],'JAR mismatch')
    for name,digest in protocol['source_hashes'].items():require(m['provenance']['source_hashes'][name]==digest,'Training source mismatch')
    curve=rows(path/'learning_curve.jsonl')
    require([r['decisions'] for r in curve]==list(range(512,budget+1,512)),'Missing PPO updates')
    require(all(v is None or np.isfinite(v) for r in curve for v in r.values()),'Nonfinite curve')
    require(sum(o['audit']['action_counts'])==sum(o['audit']['decisions_by_workload'].values())==budget,'Action/workload budget mismatch')
    for ep in rows(path/'episodes.jsonl'):
        z=[ep['metrics']['costs'][k] for k in ('zL','zE','zD','zB','zQ')]
        require(np.isclose(ep['reward'],-100*np.dot(job['weights'],z),rtol=1e-6,atol=1e-8),'Training reward identity failed')
    state=read_json(path/f'checkpoint_{budget:08d}/state.json')
    require(state['model_sha256']==file_hash(path/f'checkpoint_{budget:08d}/model.zip'),'Corrupt model')
    require(state['rng_sha256']==file_hash(path/f'checkpoint_{budget:08d}/rng.pt'),'Corrupt RNG checkpoint')
    model=PPO.load(path/f'checkpoint_{budget:08d}/model.zip',device='cpu')
    require(model.num_timesteps==budget and model.gae_lambda==.95 and model.vf_coef==.5 and model.gamma==1 and model.max_grad_norm==.5,'Saved policy/budget differs from protocol')
    return o


def verify_validation(path,checkpoint,weights,payloads=None):
    summary=read_json(path/'summary.json');eps=rows(path/'episodes.jsonl')
    require(len(eps)==20 and summary['episodes']==20 and summary['evaluation_mode']=='deterministic','Incomplete/non-deterministic validation')
    require(summary['model_sha256']==read_json(checkpoint/'state.json')['model_sha256'],'Wrong validation checkpoint')
    expected={(w,i) for w in load_config()['training']['workload_order'] for i in range(10000,10005)}
    require({(e['namespace']['workload'],e['namespace']['trace_id']) for e in eps}==expected,'Missing validation pairs')
    for e in eps:
        require(e['namespace']['split']=='pilot_validation','Validation split leak')
        require(e['decisions']==e['metrics']['task_count']==sum(e['action_counts']),'Partial episode')
        z=[e['metrics']['costs'][k] for k in ('zL','zE','zD','zB','zQ')]
        require(np.isclose(e['reward'],-100*np.dot(weights,z),rtol=1e-6,atol=1e-8),'Validation reward identity failed')
        require(not e['metrics']['diagnosis_required'],'Physical metric requires diagnosis')
    hashes={(e['namespace']['workload'],e['namespace']['trace_id']):e['trace_sha256'] for e in eps}
    if payloads is not None:require(hashes==payloads,'Validation payload mismatch across weights/models/budgets')
    actual=aggregate_costs(eps,load_config()['training']['workload_order'])
    require(np.allclose(actual['macro_costs'],summary['macro_costs'],rtol=1e-12,atol=1e-12) and
            np.isclose(actual['D_macro'],summary['D_macro'],rtol=1e-12,atol=1e-12),'Wrong macro/RMS aggregation')
    return actual['macro_costs'],sum(e['decisions'] for e in eps),hashes


def audit(root):
    setup_torch(load_config())
    p=read_json(root/'protocol.json');result=read_json(root/'result.json')
    require(p['config_sha256']==sha256(load_config()),'Config drift')
    budgets=[s['K'] for s in result['stages']]
    require(budgets==p['ladder'][:len(budgets)] and budgets,'Ladder order changed')
    data={};payloads=None;training=0;validation=0;initial={};streams={};prefix_count=0
    for job in p['jobs']:
        base=root/'models'/job['id'];reference=base/'reference'
        verify_training(reference,51200,job,p);training+=51200
        common=(job['outer'],job['repeat'])
        digest=read_json(reference/'initial_policy.json')
        sequence=rows(reference/'traces.jsonl')
        if common in initial:require(initial[common]==digest and streams[common]==sequence,'Method/weight changed initialization or external stream')
        else:initial[common]=digest;streams[common]=sequence
        ref,n,payloads=verify_validation(base/'reference_validation',reference/'checkpoint_00051200',job['weights'],payloads)
        validation+=n;data[job['id']]={'reference':ref,'short':{}}
        for budget in budgets:
            label=f'K{budget:06d}';path=base/label
            verify_training(path,budget,job,p);training+=budget
            shortseq=rows(path/'traces.jsonl')
            require(shortseq==sequence[:len(shortseq)],'Short training saw a different stream')
            require(read_json(path/'initial_policy.json')==digest,'Short/reference initial policy mismatch')
            comparison=compare_checkpoints(path/f'checkpoint_{budget:08d}',reference/f'checkpoint_{budget:08d}')
            require(comparison['pass'],'Independent short/reference prefix mismatch');prefix_count+=1
            short,n,_=verify_validation(base/(label+'_validation'),path/f'checkpoint_{budget:08d}',job['weights'],payloads)
            validation+=n;data[job['id']]['short'][budget]=short
    stages=[]
    for budget in budgets:
        short=[];ref=[]
        for outer in (100,101,102):
            x=[];y=[]
            for w in p['weights']:
                chosen=[j for j in p['jobs'] if j['outer']==outer and j['weight_id']==w['id']]
                x.append(repeated_objectives([data[j['id']]['short'][budget] for j in chosen])['D'])
                y.append(repeated_objectives([data[j['id']]['reference'] for j in chosen])['D'])
            short.append(x);ref.append(y)
        stage={'K':budget,**fidelity_gate(short,ref),'short_D':short,'reference_D':ref}
        stored=next(s for s in result['stages'] if s['K']==budget)
        require(stage['correlations']==stored['correlations'] and stage['pass']==stored['pass'],'Gate differs from recomputed raw objectives')
        stages.append(stage)
    selected=next((s['K'] for s in stages if s['pass']),None)
    require(selected==result['selected_K'],'Selected K differs from gate')
    require(training==result['training_decisions'],'Training accounting mismatch')
    require(48*20*(1+len(budgets))==result['evaluation_episodes'],'Validation episode accounting mismatch')
    baseline=compare_checkpoints(root/'models/r100_m0_equal/reference/checkpoint_00051200',
        Path('results/research_v2/P07_completion_20261107T205826Z/prefix_F/short/checkpoint_00051200'))
    require(baseline['pass'],'Performance path altered baseline reference')
    verification={'phase':'P08','status':'pass','fidelity_pass':selected is not None,'selected_K':selected,
        'stages':stages,'independent_prefix_checks':prefix_count,'paired_initializations_and_streams':True,
        'shared_validation_payloads':True,'baseline_51200_matches_old':baseline,
        'training_decisions':training,'evaluation_decisions':validation,'evaluation_episodes':result['evaluation_episodes'],
        'additional_preflight_training_decisions':512,'test_accessed':False,'full_search_launched':False,
        'result_sha256':file_hash(root/'result.json'),'auditor_source_sha256':file_hash(Path(__file__))}
    write_json(root/'fidelity_verification.json',verification);pilot_archives(root,result);selection_diagnostics(root,result,p);plot(root,verification,p)
    print({k:v for k,v in verification.items() if k not in ('stages','baseline_51200_matches_old')})
    return verification


def pilot_archives(root,result):
    from pymoo.indicators.hv import HV
    output={'scope':'Fixed eight-weight pilot only; not an NSGA-II/random-search experiment or a selected final policy.',
            'reference_point':[1.1]*5,'archives':[]}
    for stage in result['stages']:
        for outer in (100,101,102):
            source=[r for r in stage['records'] if r['outer']==outer]
            for label in ('short','reference'):
                records=[{'slot':i,'weight_id':r['weight_id'],'weights':r['weights'],**r[label]} for i,r in enumerate(source)]
                front=archive(records)
                output['archives'].append({'outer':outer,'K':stage['K'],'model_budget':stage['K'] if label=='short' else 51200,
                    'kind':label,'records':records,'nondominated':front,'diagnostic_selection':select(records),
                    'hypervolume':float(HV(ref_point=np.full(5,1.1))(np.array([r['costs'] for r in front])))})
    write_json(root/'pilot_archive.json',output)


def selection_diagnostics(root,result,protocol):
    stage=result['stages'][-1];output={'scope':'Post-hoc diagnostic of the fixed eight-weight pilot, not a new gate or a selected final model. Action shares averaged per trace, workload and model.',
                                      'K':stage['K'],'outer_runs':[]}
    for outer in (100,101,102):
        source=[r for r in stage['records'] if r['outer']==outer]
        records={kind:[{'slot':i,'weight_id':r['weight_id'],'weights':r['weights'],**r[kind]} for i,r in enumerate(source)]
                 for kind in ('short','reference')}
        chosen=select(records['short']);reference_choice=select(records['reference'])
        matched=next(r for r in records['reference'] if r['weight_id']==chosen['weight_id'])
        descriptors=[]
        for record in source:
            entry={'weight_id':record['weight_id'],'short_D':record['short']['D'],'reference_D':record['reference']['D']}
            for kind,label in (('short',f'K{stage["K"]:06d}_validation'),('reference','reference_validation')):
                shares=[];reliability=[];violation=[]
                for repeat in (0,1):
                    eps=rows(root/'models'/f'r{outer}_m{repeat}_{record["weight_id"]}'/label/'episodes.jsonl')
                    for e in eps:
                        shares.append(np.asarray(e['action_counts'])/e['decisions'])
                        reliability.append(e['metrics']['reliability']);violation.append(e['metrics']['violation'])
                mean=np.mean(shares,axis=0)
                entry[kind]={'macro_action_share':mean.tolist(),'dominant_action':int(np.argmax(mean)),
                             'dominant_share':float(mean.max()),'macro_reliability':float(np.mean(reliability)),
                             'macro_violation':float(np.mean(violation))}
            descriptors.append(entry)
        output['outer_runs'].append({'outer':outer,'short_selected_weight':chosen['weight_id'],
            'reference_selected_weight':reference_choice['weight_id'],'reference_D_at_short_selection':matched['D'],
            'best_reference_D':reference_choice['D'],'reference_regret_of_short_selection':matched['D']-reference_choice['D'],
            'weights':descriptors})
    write_json(root/'selection_diagnostics.json',output)


def plot(root,verification,protocol):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7,4),constrained_layout=True)
    for index,label in enumerate(('outer 100','outer 101','outer 102')):
        ax.plot([s['K'] for s in verification['stages']],[np.nan if s['correlations'][index] is None else s['correlations'][index] for s in verification['stages']],marker='o',label=label)
    ax.axhline(0,color='gray',linewidth=.8);ax.set(xlabel='Candidate decisions K',ylabel='Spearman rho',ylim=(-1.05,1.05))
    ax.legend();fig.savefig(root/'fidelity_correlations.svg');plt.close(fig)
    stage=verification['stages'][-1];fig,axes=plt.subplots(1,3,figsize=(12,4),constrained_layout=True)
    for i,ax in enumerate(axes):
        ax.scatter(stage['short_D'][i],stage['reference_D'][i])
        for w,x,y in zip(protocol['weights'],stage['short_D'][i],stage['reference_D'][i]):ax.annotate(w['id'],(x,y),fontsize=7)
        ax.set(title=f'Outer {100+i}, K={stage["K"]}',xlabel='Short-model D',ylabel='Reference D (51,200)')
    fig.savefig(root/'ranking_scatter.svg');plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence-dir',type=Path,required=True)
    audit(p.parse_args().evidence_dir)
