"""Read saved model tensors to measure actual actor/critic parameter movement. No training."""
import argparse
import io
from pathlib import Path
import zipfile

import numpy as np
import torch

from .config import read_json, require
from .learning import write_json


def state(path):
    with zipfile.ZipFile(path/'model.zip') as archive:
        return torch.load(io.BytesIO(archive.read('policy.pth')),map_location='cpu',weights_only=True)


def movement(previous,current,keys):
    return float(torch.sqrt(sum(torch.sum((current[k]-previous[k])**2) for k in keys)))


def generate(root):
    torch.set_num_threads(1)
    result={'scope':'Actual saved parameter displacement between adjacent post-update checkpoints, excluding first update (512 to 10,240). Not a gradient norm or causal attribution.',
            'new_training_decisions':0,'conditions':{}}
    for condition in read_json(root/'protocol.json')['conditions']:
        result['conditions'][condition]={}
        for seed in (100,101,102):
            path=root/condition/f'pilot_r{seed}'
            previous=state(path/'checkpoint_00000512');initial=previous
            actor=[k for k in previous if k.startswith(('mlp_extractor.policy_net.','action_net.'))]
            critic=[k for k in previous if k.startswith(('mlp_extractor.value_net.','value_net.'))]
            require(set(actor+critic)==set(previous),'Unclassified shared policy tensors')
            updates=[]
            for decisions in range(1024,10241,512):
                current=state(path/f'checkpoint_{decisions:08d}')
                updates.append({'decisions':decisions,'actor_delta_l2':movement(previous,current,actor),
                                'critic_delta_l2':movement(previous,current,critic)})
                previous=current
            result['conditions'][condition][str(seed)]={
                'median_actor_delta_per_rollout':float(np.median([r['actor_delta_l2'] for r in updates])),
                'median_critic_delta_per_rollout':float(np.median([r['critic_delta_l2'] for r in updates])),
                'net_actor_delta_from_512':movement(initial,current,actor),
                'net_critic_delta_from_512':movement(initial,current,critic),'updates':updates}
    write_json(root/'actual_parameter_movements.json',result)
    print({c:{s:{k:v for k,v in m.items() if k!='updates'} for s,m in seeds.items()} for c,seeds in result['conditions'].items()})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence-dir',type=Path,required=True)
    generate(p.parse_args().evidence_dir)
