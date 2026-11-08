"""P07-lambda-ablation-1: frozen, paired pilot experiment; prepare never trains."""
import argparse
import copy
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

from .config import ROOT, load_config, read_json, require, sha256
from .learning import write_json, file_hash, compare_checkpoints

CONDITIONS={'lambda095':0.95,'lambda100':1.0}


def prepare(root):
    root.mkdir(parents=True,exist_ok=False)
    config=load_config()
    specs={}
    for name,lam in CONDITIONS.items():
        effective=copy.deepcopy(config);effective['ppo']['gae_lambda']=lam
        spec={'protocol':'P07-lambda-ablation-1','condition':name,
              'simulation_config_sha256':sha256(config),'ppo':effective['ppo'],
              'effective_config_sha256':sha256(effective)}
        write_json(root/f'{name}.json',spec);specs[name]=file_hash(root/f'{name}.json')
    protocol={'protocol':'P07-lambda-ablation-1','prepared_utc':datetime.now(timezone.utc).isoformat(),
        'status':'prepared','seeds':[100,101,102],'repeat':0,'weights':[.2]*5,
        'pilot_decisions':10240,'smoke_decisions':512,'long_prefix_decisions':10752,
        'conditions':CONDITIONS,'spec_file_hashes':specs,'simulation_config_sha256':sha256(config),
        'jar_sha256':read_json(ROOT/'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256'],
        'primary':'Paired deterministic D at 10,240 decisions, report each seed and mean/median differences; descriptive only.',
        'secondary':'linear equal cost, five costs, reliability, violation, action shares, sampled evaluation diagnostic only.',
        'mechanism':'GAE/value/return, gradient clipping and parameter deltas; matched first rollout, unchanged .95 baseline.',
        'fixed':'Same physical config/JAR, model initialization, trace IDs/payloads, gamma=1 and all PPO settings except lambda.',
        'namespace':'pilot_train and pilot_validation only; no confirmatory/test access.',
        'training_decisions_planned':83968,'evaluation_episodes_planned':360,
        'decision_rule':'No automatic protocol adoption or selection of best seed. Review all pairs; no superiority/significance claim.',
        'prefix_scope':'Pilot 10,240 vs 10,752 only. Prior .95 F proof retained. New lambda=1 F reuse not certified.',
        'config_separation':'JAR/trace config stays immutable v0.2; separate versioned learner specs contain full effective PPO and effective-config hash.'}
    write_json(root/'protocol.json',protocol)
    write_json(root/'source_hashes.json',{p.relative_to(ROOT).as_posix():file_hash(p)
        for p in sorted((ROOT/'research_v2').glob('*.py'))})


def run(root,jdk):
    protocol=read_json(root/'protocol.json')
    conditions=protocol['conditions']
    require(sha256(load_config())==protocol['simulation_config_sha256'],'Config drift')
    require(read_json(ROOT/'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256']==protocol['jar_sha256'],'JAR drift')
    for name,digest in protocol['spec_file_hashes'].items():require(file_hash(root/f'{name}.json')==digest,'Learner spec changed')
    for name,digest in read_json(root/'source_hashes.json').items():require(file_hash(ROOT/name)==digest,'Source changed since protocol freeze')
    base=[sys.executable,'-m','research_v2.learning'];jdk_args=['--jdk-home',str(jdk)]
    commands=[]
    for condition in conditions:
        spec=['--learner-spec',str(root/f'{condition}.json'),'--instrument']
        commands.append((f'{condition}_smoke',base+['train','--outer','100','--stage','smoke','--output-dir',str(root/condition/'smoke')]+spec+jdk_args))
    for condition in conditions:
        spec=['--learner-spec',str(root/f'{condition}.json'),'--instrument']
        for seed in (100,101,102):
            pilot=root/condition/f'pilot_r{seed}'
            commands.append((f'{condition}_pilot_r{seed}',base+['train','--outer',str(seed),'--stage','pilot','--output-dir',str(pilot)]+spec+jdk_args))
            for n in (512,10240):
                commands.append((f'{condition}_validation_r{seed}_{n}',base+['evaluate','--checkpoint',str(pilot/f'checkpoint_{n:08d}'),
                    '--output-dir',str(root/condition/f'validation_r{seed}_{n}')]+jdk_args))
            commands.append((f'{condition}_sampled_r{seed}',base+['evaluate','--diagnostic-stochastic','--checkpoint',str(pilot/'checkpoint_00010240'),
                '--output-dir',str(root/condition/f'diagnostic_stochastic_r{seed}')]+jdk_args))
    for name,cmd in commands:
        with (root/(name+'.log')).open('x') as log:result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
        print(name,'exit=',result.returncode,flush=True)
        if result.returncode:
            print((root/(name+'.log')).read_text()[-8000:],flush=True);raise SystemExit(result.returncode)
    # One extra update after the pilot budget, trained afresh; no partial simulator resume.
    from .learning import run_training
    for condition in conditions:
        run_training(root/condition/'prefix_long',100,0,10752,[.2]*5,jdk,
                     learner_spec=root/f'{condition}.json',instrument=True)
        comparison=compare_checkpoints(root/condition/'pilot_r100/checkpoint_00010240',
                                       root/condition/'prefix_long/checkpoint_00010240')
        write_json(root/condition/'prefix_comparison.json',comparison)
        require(comparison['pass'],'Pilot prefix equivalence failed')
        print(condition,'prefix passed',flush=True)
    write_json(root/'execution_complete.json',{'status':'complete','training_decisions':83968,'evaluation_episodes':360})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','run'))
    parser.add_argument('--evidence-dir',type=Path,required=True)
    parser.add_argument('--jdk-home',type=Path,default=Path('/usr/lib/jvm/java-21-openjdk-amd64'))
    args=parser.parse_args()
    if args.command=='prepare':prepare(args.evidence_dir)
    else:run(args.evidence_dir,args.jdk_home)


if __name__=='__main__':main()
