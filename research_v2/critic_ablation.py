"""Frozen single-factor vf_coef pilot; prepare is read-only with respect to training."""
import argparse
import copy
from datetime import datetime, timezone
from pathlib import Path

from .config import ROOT, load_config, read_json, sha256
from .learning import write_json, file_hash
from .lambda_ablation import run

CONDITIONS={'vf050':0.5,'vf005':0.05}


def prepare(root):
    root.mkdir(parents=True,exist_ok=False);config=load_config();specs={}
    for name,coef in CONDITIONS.items():
        effective=copy.deepcopy(config);effective['ppo']['vf_coef']=coef
        spec={'protocol':'P07-critic-scale-ablation-1','condition':name,'factor':'vf_coef',
              'simulation_config_sha256':sha256(config),'ppo':effective['ppo'],
              'effective_config_sha256':sha256(effective)}
        write_json(root/f'{name}.json',spec);specs[name]=file_hash(root/f'{name}.json')
    protocol={'protocol':'P07-critic-scale-ablation-1','prepared_utc':datetime.now(timezone.utc).isoformat(),
        'status':'prepared','factor':'vf_coef','conditions':CONDITIONS,'seeds':[100,101,102],
        'repeat':0,'weights':[.2]*5,'pilot_decisions':10240,'smoke_decisions':512,'long_prefix_decisions':10752,
        'spec_file_hashes':specs,'simulation_config_sha256':sha256(config),
        'jar_sha256':read_json(ROOT/'ifogsim/build/research_v2/build_receipt.json')['artifact_sha256'],
        'rationale':'Prior initial-rollout critic/actor gradient ratio was 18-28 at lambda=.95; multiplying vf_coef by .1 tests reducing this imbalance without changing target rewards, GAE, or clipping rule.',
        'primary':'Paired deterministic D at 10,240: all seeds, mean/median differences; descriptive only.',
        'secondary':'Linear equal cost, five costs, reliability, violation, action share; sampling diagnostic only.',
        'mechanism':'Critic-weighted gradient, global clipping frequency, actor/critic parameter deltas, GAE/value/return statistics.',
        'fixed':'lambda=.95, gamma=1, global clip max=.5, all PPO settings except vf_coef; same initial policy, JAR, physics, trace payloads and budget.',
        'namespace':'pilot_train and pilot_validation only; no confirmatory/test access.',
        'decision_rule':'No automatic adoption or seed selection; report all results. No significance/superiority claim. Do not proceed to P08 in this batch.',
        'training_decisions_planned':83968,'evaluation_episodes_planned':360,
        'prefix_scope':'10,240 vs 10,752 pilot only; no F checkpoint reuse claim for vf_coef=.05.',
        'config_separation':'Immutable simulator config/JAR and separately hashed full effective learner config.'}
    write_json(root/'protocol.json',protocol)
    write_json(root/'source_hashes.json',{p.relative_to(ROOT).as_posix():file_hash(p)
               for p in sorted((ROOT/'research_v2').glob('*.py'))})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('prepare','run'))
    p.add_argument('--evidence-dir',type=Path,required=True)
    p.add_argument('--jdk-home',type=Path,default=Path('/usr/lib/jvm/java-21-openjdk-amd64'))
    args=p.parse_args()
    if args.command=='prepare':prepare(args.evidence_dir)
    else:run(args.evidence_dir,args.jdk_home)


if __name__=='__main__':main()
