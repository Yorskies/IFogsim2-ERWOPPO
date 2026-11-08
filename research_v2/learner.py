"""Learner (PPO) protocol versions.

All versions share one simulation config, so traces, the JVM handshake hash and every P01-P06 result are identical across
versions; only the PPO settings differ. Version 0.2 is the ppo section of the config itself (gamma 1.0). Version 0.3 applies
the registered overrides in configs/research_v2/learner_v0.3.json (gamma 0.97). Callers must name the version explicitly in
new protocol code; the default '0.2' exists only so that v0.2 reproductions keep their exact behaviour.
"""
import copy
import hashlib

from .config import ROOT, read_json, require, sha256, validate_config

VERSIONS = ('0.2', '0.3')
CURRENT = '0.3'
FILES = {'0.3': ROOT / 'configs/research_v2/learner_v0.3.json'}
ALLOWED_OVERRIDES = {'gamma': (0.9, 1.0)}


def file_sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def effective_learner(config, version):
    """Return (learner_config, metadata). learner_config is the simulation config with the PPO section replaced."""
    require(version in VERSIONS, f'Unknown learner protocol version {version!r}')
    validate_config(config)
    if version == '0.2':
        learner = copy.deepcopy(config)
        return learner, {'version': '0.2', 'protocol': 'research-v2-learner-0.2', 'ppo_overrides': {},
                         'learner_config_sha256': sha256(learner), 'file_sha256': None}
    path = FILES[version]
    spec = read_json(path)
    require(spec['protocol'] == f'research-v2-learner-{version}', 'Learner protocol file/version mismatch')
    require(spec['simulation_config_sha256'] == sha256(config), 'Learner protocol was registered for another simulation config')
    overrides = spec['ppo_overrides']
    require(overrides and set(overrides) <= set(ALLOWED_OVERRIDES), 'Learner override outside the registered keys')
    for key, value in overrides.items():
        low, high = ALLOWED_OVERRIDES[key]
        require(type(value) is float and low <= value <= high, f'Learner override {key}={value!r} out of bounds')
    learner = copy.deepcopy(config)
    learner['ppo'].update(overrides)
    return learner, {'version': version, 'protocol': spec['protocol'], 'ppo_overrides': dict(overrides),
                     'learner_config_sha256': sha256(learner), 'file_sha256': file_sha256(path)}
