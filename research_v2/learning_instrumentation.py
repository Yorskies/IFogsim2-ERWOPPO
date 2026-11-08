"""Passive rollout/gradient instrumentation around SB3's existing PPO update."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch
from stable_baselines3.common.callbacks import BaseCallback

from .config import require


def tensor_digest(state):
    digest=hashlib.sha256()
    for name,tensor in sorted(state.items()):
        value=tensor.detach().cpu().contiguous().numpy()
        digest.update(name.encode());digest.update(str(value.dtype).encode())
        digest.update(str(value.shape).encode());digest.update(value.tobytes())
    return digest.hexdigest()


def recompute_gae(rewards, values, starts, last_values, last_dones, gamma, lam):
    advantages=np.zeros_like(rewards);last=0
    for t in reversed(range(len(rewards))):
        nonterminal=1.0-(last_dones.astype(np.float32) if t==len(rewards)-1 else starts[t+1])
        following=last_values if t==len(rewards)-1 else values[t+1]
        delta=rewards[t]+gamma*following*nonterminal-values[t]
        last=delta+gamma*lam*nonterminal*last
        advantages[t]=last
    return advantages,advantages+values


def gradient_clip_recorder(original, records):
    def record(parameters, max_norm, *args, **kwargs):
        parameters=list(parameters)
        pre=original(parameters,max_norm,*args,**kwargs)
        grads=[p.grad.detach() for p in parameters if p.grad is not None]
        post=torch.linalg.vector_norm(torch.stack([torch.linalg.vector_norm(g,2) for g in grads]),2) if grads else torch.tensor(0.)
        require(torch.isfinite(pre).item() and torch.isfinite(post).item(),'Nonfinite gradient norm')
        records.append({'minibatch_index':len(records),'pre_clip_norm':float(pre),
                        'post_clip_norm':float(post),'max_norm':float(max_norm),
                        'was_clipped':bool(pre>max_norm)})
        return pre
    return record


class RolloutInstrumentation(BaseCallback):
    def __init__(self, directory):
        super().__init__()
        self.directory=Path(directory)/'instrumentation';self.directory.mkdir()
        self.gradients=[]

    def _on_step(self):
        return True

    def _on_rollout_end(self):
        model=self.model;buffer=model.rollout_buffer
        self.current=self.directory/f'rollout_{model.num_timesteps:08d}.npz'
        last=self.locals['values'].detach().cpu().numpy().flatten()
        dones=np.asarray(self.locals['dones'])
        calculated,returns=recompute_gae(buffer.rewards,buffer.values,buffer.episode_starts,
                                        last,dones,model.gamma,model.gae_lambda)
        require(np.allclose(calculated,buffer.advantages,rtol=1e-5,atol=1e-5),'GAE audit mismatch')
        require(np.allclose(returns,buffer.returns,rtol=1e-5,atol=1e-5),'Return audit mismatch')
        np.savez_compressed(self.current, observations=buffer.observations,actions=buffer.actions,
            rewards=buffer.rewards,values=buffer.values,advantages=buffer.advantages,returns=buffer.returns,
            episode_starts=buffer.episode_starts,old_log_probs=buffer.log_probs,
            last_values=last,last_dones=dones,gamma=np.array(model.gamma),gae_lambda=np.array(model.gae_lambda))
        self.before=[p.detach().clone() for p in model.policy.parameters()]
        self.gradients=[]

    @contextmanager
    def capture_gradients(self):
        original=torch.nn.utils.clip_grad_norm_
        with patch('torch.nn.utils.clip_grad_norm_',new=gradient_clip_recorder(original,self.gradients)):
            yield

    def after_update(self, model):
        delta=float(torch.sqrt(sum(torch.sum((p.detach()-before)**2) for p,before in zip(model.policy.parameters(),self.before))))
        with np.load(self.current) as data:
            metrics={}
            for name in ('values','advantages','returns','rewards'):
                a=data[name];require(np.isfinite(a).all(),f'Nonfinite {name}')
                metrics[name]={'mean':float(a.mean()),'std':float(a.std()),'min':float(a.min()),'max':float(a.max())}
        metrics.update(decisions=model.num_timesteps,parameter_delta_l2=delta,
                       optimizer_steps=len(self.gradients),gradient_clipped_steps=sum(g['was_clipped'] for g in self.gradients),
                       gradients=self.gradients,raw_advantages_before_SB3_minibatch_normalization=True,
                       probability_ratio_clip_fraction=float(model.logger.name_to_value['train/clip_fraction']),
                       gae_audit_pass=True)
        with (self.directory/'updates.jsonl').open('a') as sink:
            sink.write(json.dumps(metrics,allow_nan=False)+'\n')
        del self.before
