"""P08 frozen pilot fidelity. prepare/report do not train; run launches isolated model workers."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import os
from pathlib import Path
import queue
import socket
import subprocess
import sys

import numpy as np

from .config import ROOT,load_config,read_json,require,sha256
from .learning import (write_json,file_hash,run_training,run_evaluation,compare_checkpoints)
from .search import pilot_weights,repeated_objectives,fidelity_gate


def prepare(root):
    root.mkdir(parents=True,exist_ok=False);config=load_config();weights=pilot_weights(config)
    available=[]
    for port in config['execution']['allowed_ports']:
        s=socket.socket()
        try:s.bind(('127.0.0.1',port));available.append(port)
        except OSError:pass
        finally:s.close()
    ports=available[:3];require(ports,'No unused simulator port')
    jobs=[{'id':f'r{r}_m{m}_{w["id"]}','outer':r,'repeat':m,'weight_id':w['id'],'weights':w['weights']}
          for r in config['seeds']['pilot_outer_ids'] for w in weights for m in (0,1)]
    require(len({j['id'] for j in jobs})==48,'Duplicate fidelity jobs')
    protocol={'phase':'P08','version':'P08-fidelity-1','prepared_utc':datetime.now(timezone.utc).isoformat(),
        'config_sha256':sha256(config),'jar_sha256':read_json(ROOT/'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256'],
        'weights':weights,'jobs':jobs,'reference_decisions':51200,'ladder':[5120,10240,20480],
        'workers':len(ports),'ports':ports,'torch_threads_per_worker':1,'fast_rpc':True,
        'primary':'Spearman D ranking across eight weights, mean objective vector over two models before RMS; three outer pilots.',
        'gate':'Smallest K with median rho>=.60 and all rho>=0; average ranks for ties.',
        'undefined':'Undefined short ranking fails that K; any constant reference ranking stops for diagnosis.',
        'training':'Reference and each tested K trained independently from scratch; compare full policy/optimizer/RNG/counters at matching prefix.',
        'budget_reference':2457600,'budget_train_minimum':2703360,'budget_train_maximum':4177920,
        'evaluation_episodes_minimum':1920,'evaluation_episodes_maximum':3840,
        'execution':'Up to three independent processes/JVMs, reserved free configured ports; parallel wall-clock labelled, not compared with prior serial time.',
        'splits':['pilot_train','pilot_validation'],'test_accessed':False,
        'ppo':config['ppo'],'full_search_launched':False,
        'source_hashes':{p.relative_to(ROOT).as_posix():file_hash(p) for p in sorted((ROOT/'research_v2').glob('*.py'))}}
    write_json(root/'protocol.json',protocol)


def check_protocol(root):
    p=read_json(root/'protocol.json');require(p['config_sha256']==sha256(load_config()),'Config drift')
    require(read_json(ROOT/'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256']==p['jar_sha256'],'JAR drift')
    for name,digest in p['source_hashes'].items():require(file_hash(ROOT/name)==digest,f'Source drift: {name}')
    return p


def ensure_training(path,job,budget,checkpoints,port,jdk):
    if not path.exists():
        run_training(path,job['outer'],job['repeat'],budget,job['weights'],jdk,phase='P08',
                     checkpoint_at=checkpoints,fast_rpc=True,worker_port=port)
    outcome=read_json(path/'outcome.json');manifest=read_json(path/'manifest.json')
    require(outcome['status']=='complete' and outcome['decisions']==budget,'Incomplete training; no partial resume')
    require(manifest['weights']==job['weights'] and manifest['model_seed']==200000+2*job['outer']+job['repeat'],'Model identity mismatch')
    for n in checkpoints:
        state=read_json(path/f'checkpoint_{n:08d}/state.json')
        require(state['model_sha256']==file_hash(path/f'checkpoint_{n:08d}/model.zip'),'Corrupt checkpoint')


def ensure_evaluation(checkpoint,path,port,jdk):
    if not path.exists():run_evaluation(checkpoint,path,jdk,fast_rpc=True,worker_port=port)
    summary=read_json(path/'summary.json');state=read_json(checkpoint/'state.json')
    require(summary['status']=='complete' and summary['episodes']==20 and summary['split']=='pilot_validation','Incomplete pilot validation')
    require(summary['model_sha256']==state['model_sha256'],'Evaluation belongs to a different checkpoint')
    return summary


def worker(root,index,budget,port,jdk):
    p=check_protocol(root);job=p['jobs'][index];base=root/'models'/job['id'];base.mkdir(parents=True,exist_ok=True)
    if budget==5120:
        print('reference training',job['id'],flush=True)
        ensure_training(base/'reference',job,51200,[512,5120,10240,20480,51200],port,jdk)
        ensure_evaluation(base/'reference/checkpoint_00051200',base/'reference_validation',port,jdk)
    print('short training',job['id'],budget,flush=True)
    label=f'K{budget:06d}'
    ensure_training(base/label,job,budget,[budget],port,jdk)
    ensure_evaluation(base/label/f'checkpoint_{budget:08d}',base/(label+'_validation'),port,jdk)
    comparison=compare_checkpoints(base/label/f'checkpoint_{budget:08d}',base/'reference'/f'checkpoint_{budget:08d}')
    write_json(base/(label+'_prefix.json'),comparison);require(comparison['pass'],'Independent short/reference prefix mismatch')
    write_json(base/(label+'_complete.json'),{'status':'complete','job':job,'budget':budget,'prefix_pass':True})
    print('completed',job['id'],budget,flush=True)


def rankings(root,budget):
    p=read_json(root/'protocol.json');short=[];reference=[];records=[]
    for outer in (100,101,102):
        x=[];y=[]
        for w in p['weights']:
            chosen=[j for j in p['jobs'] if j['outer']==outer and j['weight_id']==w['id']]
            require(len(chosen)==2,'Missing model repeat')
            vectors={}
            for label in (f'K{budget:06d}_validation','reference_validation'):
                vectors[label]=repeated_objectives([read_json(root/'models'/j['id']/label/'summary.json')['macro_costs'] for j in chosen])
            x.append(vectors[f'K{budget:06d}_validation']['D']);y.append(vectors['reference_validation']['D'])
            records.append({'outer':outer,'weight_id':w['id'],'weights':w['weights'],'short':vectors[f'K{budget:06d}_validation'],'reference':vectors['reference_validation']})
        short.append(x);reference.append(y)
    return {'K':budget,**fidelity_gate(short,reference),'short_D':short,'reference_D':reference,'records':records}


def run(root,jdk):
    p=check_protocol(root);ports=queue.Queue()
    for port in p['ports']:ports.put(port)
    env=os.environ.copy()
    for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):env[key]='1'
    stages=[]
    for budget in p['ladder']:
        complete=0
        def execute(index):
            job=p['jobs'][index];base=root/'models'/job['id']
            marker=base/f'K{budget:06d}_complete.json'
            port=ports.get()
            try:
                cmd=[sys.executable,'-m','research_v2.fidelity','worker','--evidence-dir',str(root),
                     '--index',str(index),'--budget',str(budget),'--port',str(port),'--jdk-home',str(jdk)]
                log=root/f'{job["id"]}_K{budget:06d}.log'
                with log.open('a') as sink:result=subprocess.run(cmd,env=env,stdout=sink,stderr=subprocess.STDOUT)
                require(result.returncode==0,f'Worker failed: {log}; inspect preserved evidence')
                return job['id']
            finally:ports.put(port)
        with ThreadPoolExecutor(max_workers=p['workers']) as pool:
            futures=[pool.submit(execute,i) for i in range(48)]
            for future in as_completed(futures):
                job=future.result();complete+=1
                write_json(root/'progress.json',{'K':budget,'completed_jobs':complete,'total_jobs':48,'last_job':job})
                print(f'K={budget} complete {complete}/48: {job}',flush=True)
        stage=rankings(root,budget);stages.append(stage);write_json(root/f'fidelity_K{budget:06d}.json',stage)
        print('GATE',budget,stage['correlations'],stage['pass'],flush=True)
        if stage['pass']:break
        if any(np.ptp(row)==0 for row in stage['reference_D']):break
    selected=next((s['K'] for s in stages if s['pass']),None)
    result={'phase':'P08','status':'fidelity_pass' if selected else 'fidelity_failed_stop',
            'selected_K':selected,'stages':stages,'training_decisions':48*51200+48*sum(s['K'] for s in stages),
            'evaluation_episodes':48*20*(1+len(stages)),'full_search_launched':False,'test_accessed':False}
    write_json(root/'result.json',result);print(result['status'],'selected_K',selected,flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('prepare','run','worker'))
    p.add_argument('--evidence-dir',type=Path,required=True);p.add_argument('--jdk-home',type=Path,default=Path('/usr/lib/jvm/java-21-openjdk-amd64'))
    p.add_argument('--index',type=int);p.add_argument('--budget',type=int);p.add_argument('--port',type=int)
    args=p.parse_args()
    if args.command=='prepare':prepare(args.evidence_dir)
    elif args.command=='run':run(args.evidence_dir,args.jdk_home)
    else:worker(args.evidence_dir,args.index,args.budget,args.port,args.jdk_home)


if __name__=='__main__':main()
