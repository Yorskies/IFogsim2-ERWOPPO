"""First-rollout actor/critic gradient decomposition; no optimizer step or new rollout."""
import argparse
from pathlib import Path

import gymnasium as gym
import numpy as np
import torch
from stable_baselines3 import PPO

from .config import load_config, read_json, require
from .learning import ppo_kwargs, setup_torch, write_json, effective_learner
from .learning_instrumentation import tensor_digest


class ShapeEnv(gym.Env):
    observation_space=gym.spaces.Box(-1,2,(108,),dtype=np.float32)
    action_space=gym.spaces.Discrete(7)
    def reset(self,*,seed=None,options=None):
        raise RuntimeError('No environment rollout allowed in loss diagnostic')
    def step(self,action):
        raise RuntimeError('No environment rollout allowed in loss diagnostic')


def norm(grads):
    return float(torch.sqrt(sum(torch.sum(g*g) for g in grads if g is not None)))


def generate(root):
    config=load_config();setup_torch(config);output={
        'scope':'Initial policy, full 512-sample first rollout; diagnostic batch, not the recorded minibatch sequence.',
        'optimizer_steps':0,'new_rollouts':0,'results':{}}
    for condition in read_json(root/'protocol.json')['conditions']:
        effective,_=effective_learner(config,root/f'{condition}.json')
        output['results'][condition]={}
        for seed in (100,101,102):
            path=root/condition/f'pilot_r{seed}'
            require((path/'outcome.json').exists(),'Pilot not complete')
            model=PPO('MlpPolicy',ShapeEnv(),seed=200000+2*seed,**ppo_kwargs(effective))
            require(tensor_digest(model.policy.state_dict())==read_json(path/'initial_policy.json')['tensor_sha256'],
                    'Reconstructed initial policy differs')
            with np.load(path/'instrumentation/rollout_00000512.npz') as data:
                observations=torch.as_tensor(data['observations'].reshape(512,108))
                actions=torch.as_tensor(data['actions'].reshape(-1)).long()
                advantages=torch.as_tensor(data['advantages'].reshape(-1))
                returns=torch.as_tensor(data['returns'].reshape(-1))
                old_logp=torch.as_tensor(data['old_log_probs'].reshape(-1))
            values,logp,entropy=model.policy.evaluate_actions(observations,actions)
            require(torch.allclose(logp,old_logp,rtol=1e-5,atol=1e-5),'First policy log probabilities differ')
            advantages=(advantages-advantages.mean())/(advantages.std()+1e-8)
            ratio=torch.exp(logp-old_logp)
            hp=effective['ppo'];clip=hp['clip_range']
            actor_loss=-torch.minimum(advantages*ratio,advantages*torch.clamp(ratio,1-clip,1+clip)).mean()-hp['ent_coef']*entropy.mean()
            critic_loss=hp['vf_coef']*torch.nn.functional.mse_loss(values.flatten(),returns)
            parameters=list(model.policy.parameters())
            actor_grad=torch.autograd.grad(actor_loss,parameters,retain_graph=True,allow_unused=True)
            critic_grad=torch.autograd.grad(critic_loss,parameters,allow_unused=True)
            an,cn=norm(actor_grad),norm(critic_grad)
            combined=[]
            for a,c in zip(actor_grad,critic_grad):
                if a is not None or c is not None:combined.append((a if a is not None else 0)+(c if c is not None else 0))
            total=norm(combined)
            output['results'][condition][str(seed)]={'actor_with_entropy_gradient_norm':an,
                'weighted_critic_gradient_norm':cn,'critic_over_actor_norm':cn/an,
                'combined_gradient_norm':total,'global_clip_coefficient_diagnostic':min(1.,hp['max_grad_norm']/(total+1e-6)),
                'value_loss_MSE':float((critic_loss/hp['vf_coef']).detach()),
                'policy_unchanged':tensor_digest(model.policy.state_dict())==read_json(path/'initial_policy.json')['tensor_sha256']}
    write_json(root/'first_rollout_loss_decomposition.json',output)
    print(output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence-dir',type=Path,required=True)
    generate(p.parse_args().evidence_dir)
