"""Review P07 evidence and replay recorded actions; no optimizer, learn(), or new policy training."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

import numpy as np
import torch
from stable_baselines3 import PPO

from .config import load_config, read_json, require
from .engine_runner import scenario_from_trace, run_engine
from .gym_env import OffloadingEnv
from .learning import COSTS, setup_torch, write_json, aggregate_costs
from .learning_report import rows
from .trace_access import TraceKey
from .traces import TraceGenerator


def transform(raw, config):
    c = config['observation']
    direct = {'task.cpu_mi':c['cpu_mi_reference'], 'task.input_bytes':c['input_reference_mib']*2**20,
              'task.output_bytes':c['output_reference_mib']*2**20,
              'task.deadline_relative_s':c['deadline_reference_s'], 'task.timeout_relative_s':c['timeout_reference_s']}
    result = []
    for name in read_json(Path(__file__).resolve().parents[1]/'configs/research_v2/wire_contract.json')['observation_features']:
        x = raw[name]
        suffix = name.split('.')[-1]
        if suffix == 'minimum_remaining_deadline_s':
            value = 1.0 if x is None else x/(abs(x)+c['remaining_deadline_reference_s'])
        elif name in direct:
            value = x/direct[name]
        elif suffix in ('mips_per_pe','pes','cpu_increment_j_per_mi','bottleneck_bit_per_s'):
            reference = {'mips_per_pe':'mips_reference','pes':'pes_reference',
                         'cpu_increment_j_per_mi':'cpu_increment_reference_j_per_mi',
                         'bottleneck_bit_per_s':'bandwidth_reference_bit_per_s'}[suffix]
            value = x/c[reference]
        elif suffix in ('earliest_pe_free_delay_s','queued_mi_over_mips_s','remaining_mi_over_mips_s',
                        'estimated_input_delay_s','estimated_result_delay_s','interarrival_s'):
            value = x/(x+c['time_squash_reference_s'])
        elif suffix == 'estimated_dynamic_energy_j':
            value = x/(x+c['communication_squash_reference_j'])
        elif suffix == 'arrival_ema_per_s':
            value = x/(x+c['arrival_squash_reference_per_s'])
        else:
            require(suffix in ('busy_pe_fraction','queue_fraction','time_fraction','mean_iot_utilization') or
                    name.startswith(('task.class.','source.access_fog.')), f'Unknown transform {name}')
            value = x
        result.append(value)
    return np.array(result,dtype=np.float32)


def distribution(values):
    a = np.asarray(values)
    return {'count':len(a), 'mean':float(a.mean()), 'median':float(np.median(a)),
            'p90':float(np.percentile(a,90)), 'p95':float(np.percentile(a,95)), 'max':float(a.max())}


def generate(evidence, output, jdk_home):
    output.mkdir(parents=True,exist_ok=False)
    config=load_config();setup_torch(config)
    generator=TraceGenerator(config);result={'scope':'read-only audit and fixed-action replay; no training',
        'pilots':{}, 'gae_lambda':config['ppo']['gae_lambda'],
        'gamma':config['ppo']['gamma'], 'gae_note':'lambda^lag describes direct TD-residual propagation, not exact causal policy-gradient attenuation; value bootstrapping can carry additional information'}
    holder={};env=OffloadingEnv(lambda seed,index:holder['trace'],[0.2]*5,config=config,any_port=True,jdk_home=jdk_home)
    try:
        for outer in (100,101,102):
            path=evidence/f'pilot_r{outer}'
            groups=defaultdict(list)
            with (path/'decisions.jsonl').open() as source:
                for line in source:
                    row=json.loads(line);ns=row['episode']['current']['namespace']
                    groups[(ns['workload'],ns['trace_id'])].append(row)
            curves=rows(path/'learning_curve.jsonl');outcome=read_json(path/'outcome.json')
            pilot={'workload_decision_share':{w:n/10240 for w,n in outcome['audit']['decisions_by_workload'].items()},
                   'episodes_completed':Counter(r['namespace']['workload'] for r in rows(path/'episodes.jsonl')),
                   'critic_explained_variance':distribution([r['train/explained_variance'] for r in curves if r['train/explained_variance'] is not None]),
                   'critic_negative_explained_variance_updates':sum(r['train/explained_variance'] is not None and r['train/explained_variance']<0 for r in curves),
                   'epochs_executed':curves[-1]['gradient_epochs'], 'rollout_updates':len(curves),
                   'credit_lags':{}, 'replayed_episodes':0, 'snapshot_transform_checks':0}
            obs_arrays=[];terminal_shares=[];terminal_multiples=[];cost_sums=np.zeros(5)
            lags=defaultdict(list);cl_mass=defaultdict(list)
            for (workload,trace_id),decisions in groups.items():
                ns=decisions[0]['episode']['current']['namespace'];trace=generator.generate(TraceKey(**ns),role='pilot_trainer').to_dict()
                require(trace['payload_sha256']==decisions[0]['episode']['current']['payload_sha256'],'Trace mismatch')
                # Independently verify Python audit transform against Java on the same first task.
                holder['trace']=trace;obs,info=env.reset(seed=0)
                require(np.array_equal(obs,transform(info['raw_snapshot'],config)),'Observation transform differs from Java')
                require(np.array_equal(obs,transform(decisions[0]['raw_snapshot'],config)),'Recorded first snapshot differs')
                pilot['snapshot_transform_checks']+=1
                obs_arrays.extend(transform(r['raw_snapshot'],config) for r in decisions)
                if not decisions[-1]['terminated']:
                    continue
                actions={str(r['task_id']):('source_iot' if r['action']==0 else 'cloud' if r['action']==6 else f"F{r['action']}") for r in decisions}
                scenario=scenario_from_trace(trace,actions,topology={'homogeneous_fog':False})
                scenario['network']={}
                episode=run_engine(scenario,jdk_home=jdk_home)['episodes'][0]
                delta=np.sum([r['cost_delta'] for r in decisions],axis=0)
                expected=np.array([episode['metrics']['costs'][k] for k in COSTS])
                require(np.allclose(delta,expected,rtol=1e-8,atol=1e-10),'Fixed-action replay costs differ')
                pilot['replayed_episodes']+=1;cost_sums+=expected
                rewards=np.array([r['reward'] for r in decisions]);terminal_shares.append(abs(rewards[-1]/rewards.sum()))
                terminal_multiples.append(abs(rewards[-1]) / max(float(np.median(np.abs(rewards[:-1]))),1e-12))
                arrivals=np.array([t['arrival_s'] for t in trace['tasks']])
                for task in episode['tasks']:
                    i=task['task_id'];terminal=task['terminal_s']
                    step=min(len(arrivals)-1,max(i,int(np.searchsorted(arrivals,terminal,side='left'))-1))
                    lag=step-i;lags[workload].append(lag)
                    cl=9.0 if task['terminal']=='FAILED' else terminal-arrivals[i]
                    cl_mass[workload].append((cl,lag))
            for w,values in lags.items():
                weights=np.array(cl_mass[w]);gae=np.power(.95,weights[:,1])
                pilot['credit_lags'][w]={**distribution(values),
                    'fraction_lag_gt20':float(np.mean(np.array(values)>20)),
                    'fraction_lag_gt50':float(np.mean(np.array(values)>50)),
                    'lambda_weight_mean':float(gae.mean()),
                    'effective_latency_weighted_lambda_weight':float(np.sum(weights[:,0]*gae)/np.sum(weights[:,0]))}
            pilot['terminal_transition_fraction_of_episode_cost']=distribution(terminal_shares)
            pilot['terminal_reward_over_median_step_reward']=distribution(terminal_multiples)
            pilot['equal_reward_cost_shares_completed_episodes']=dict(zip(COSTS,(cost_sums/cost_sums.sum()).tolist()))
            observations=np.stack(obs_arrays)
            probabilities={}
            for checkpoint in (512,10240):
                model=PPO.load(path/f'checkpoint_{checkpoint:08d}'/'model.zip',device='cpu')
                with torch.no_grad():
                    p=model.policy.get_distribution(torch.as_tensor(observations)).distribution.probs.cpu().numpy()
                top=np.sort(p,axis=1)[:,-2:];modes=np.argmax(p,axis=1)
                probabilities[str(checkpoint)]={'argmax_counts_on_same_training_snapshots':np.bincount(modes,minlength=7).tolist(),
                    'mean_action_probabilities':p.mean(axis=0).tolist(),
                    'modal_probability':distribution(p.max(axis=1)),
                    'top_two_probability_margin':distribution(top[:,1]-top[:,0])}
            pilot['policy_on_same_training_observations']=probabilities
            result['pilots'][str(outer)]=pilot
            print('reviewed',outer,'episodes',pilot['replayed_episodes'],flush=True)
    finally:env.close()
    write_json(output/'review.json',result)
    return result


def baseline_review(output, jdk_home):
    from .baselines import greedy_eft
    config=load_config();generator=TraceGenerator(config);holder={};records=[]
    env=OffloadingEnv(lambda seed,index:holder['trace'],[0.2]*5,config=config,any_port=True,jdk_home=jdk_home)
    try:
        for workload in config['training']['workload_order']:
            for trace_id in range(10000,10005):
                key=TraceKey(config['seeds']['master'],'pilot_validation',None,None,trace_id,workload)
                trace=generator.generate(key,role='pilot_validator').to_dict();holder['trace']=trace
                obs,info=env.reset(seed=0);counts=np.zeros(7,dtype=int);total=0.0
                while True:
                    action=greedy_eft(info['raw_snapshot']);counts[action]+=1
                    obs,reward,done,truncated,info=env.step(action);total+=reward
                    require(not truncated,'Baseline unexpectedly truncated')
                    if done:break
                metrics=info['summary']['metrics']
                require(int(counts.sum())==trace['task_count'],'Partial baseline episode')
                require(np.isclose(total,-20*sum(metrics['costs'].values()),rtol=1e-6,atol=1e-8),'Baseline reward mismatch')
                records.append({'namespace':key.to_dict(),'trace_sha256':trace['payload_sha256'],
                                'metrics':metrics,'action_counts':counts.tolist(),'reward':total})
    finally:env.close()
    summary=aggregate_costs(records,config['training']['workload_order'])
    summary['episodes']=len(records);summary['decisions']=sum(sum(r['action_counts']) for r in records)
    summary['policy']='greedy_eft';summary['training_decisions']=0
    summary['physical_by_workload']={w:{k:float(np.mean([r['metrics'][k] for r in records if r['namespace']['workload']==w]))
                                      for k in ('reliability','violation')} for w in config['training']['workload_order']}
    write_json(output/'greedy_eft_same_validation.json',{'summary':summary,'episodes':records})
    print(json.dumps(summary,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--jdk-home',type=Path)
    parser.add_argument('--baseline-only',action='store_true')
    args=parser.parse_args()
    if args.baseline_only:
        require(args.output_dir.is_dir(), 'Run the evidence review first')
        baseline_review(args.output_dir,args.jdk_home)
    else:
        generate(args.evidence_dir,args.output_dir,args.jdk_home)


if __name__=='__main__':main()
