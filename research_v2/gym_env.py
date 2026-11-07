"""Gymnasium environment for the research v2 offloading engine.

One `step` is one offloading decision for one task arrival. Java owns every outcome; the environment only forwards the
action, converts the reported cost increments into the reward `-100 * sum_j(w_j * delta_C_j)`, and surfaces failures. There
is no Python fallback engine and no look-ahead: a decision is answered by the next decision's response, so completions that
happen several arrivals later reach the reward in the interval where they actually occurred, and the drain to H lands in
the last transition. With gamma = 1 the episode return is exactly `-100 * sum_j(w_j * z_j)`.
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from .config import ContractError, ROOT, load_config, read_json, require, sha256
from .rpc_client import RpcError, ConnectionLostError, ServerProcess, V2Client, verify_handshake

REWARD_SCALE = 100.0
OBJECTIVES = ("latency", "energy", "deadline", "imbalance", "qos_failure")
LEGACY_OBSERVATION_DIM = 46


class LegacyIncompatibleError(ContractError):
    """A legacy (46-feature, four-weight) artifact was offered to the v2 path."""


def validate_weights(weights):
    """Five reward weights on the simplex. Four weights belong to the legacy model and are refused, not padded."""
    weights = list(weights)
    if len(weights) == 4:
        raise LegacyIncompatibleError("four reward weights are the legacy configuration; v2 uses five (latency, energy, deadline, imbalance, qos_failure)")
    require(len(weights) == 5, f"expected 5 reward weights, got {len(weights)}")
    require(all(isinstance(w, (int, float)) and not isinstance(w, bool) and np.isfinite(w) and w >= 0 for w in weights), "weights must be finite and nonnegative")
    require(abs(sum(weights) - 1.0) <= 1e-9, f"weights must sum to 1, got {sum(weights)}")
    return np.asarray(weights, dtype=np.float64)


def check_policy_interface(observation_dim, action_count):
    """Refuse a policy or checkpoint built for the legacy interface before it can act in a v2 episode."""
    if observation_dim == LEGACY_OBSERVATION_DIM:
        raise LegacyIncompatibleError("legacy 46-feature policies cannot be used with the 108-feature v2 observation; retrain")
    require(observation_dim == 108 and action_count == 7, f"policy interface {observation_dim}/{action_count} is not the v2 108/7")


class OffloadingEnv(gym.Env):
    """Discrete(7) actions over a 108-feature public snapshot. Terminates at the physical horizon H, never truncates."""

    metadata = {"render_modes": []}

    def __init__(self, traces, weights, *, config=None, host=None, port=None, jdk_home=None, rpc_timeout_s=120.0,
                 validate=True, detail=False, log_transfers=False, homogeneous_fog=False, any_port=False,
                 server_rpc_timeout_s=None, verify_jar=True, include_events=False):
        """`traces`: a list of trace dicts (selected by seed, else cycled) or a callable(seed, episode_index) -> trace."""
        super().__init__()
        self.config = config or load_config()
        self.weights = validate_weights(weights)
        self._traces = traces
        self._options = {"homogeneous_fog": bool(homogeneous_fog), "log_transfers": bool(log_transfers), "detail": bool(detail),
                         "include_events": bool(include_events)}
        self._config_sha = sha256(self.config)
        self._episode_index = 0
        self._done = True
        self._broken = False
        self._episode_id = "-"
        self._trace_sha = "0" * 64
        self._server = None
        if host is None:
            self._server = ServerProcess(self.config, port=port, any_port=any_port, rpc_timeout_s=server_rpc_timeout_s, jdk_home=jdk_home)
            host, port = self._server.host, self._server.port
        self._client = V2Client(host, port, timeout_s=rpc_timeout_s, validate=validate)
        self.handshake = verify_handshake(self._client.request("hello")["handshake"], self.config, require_jar_hash=verify_jar)
        dim = self.handshake["observation_dimension"]
        self.observation_space = spaces.Box(low=-1.0, high=2.0, shape=(dim,), dtype=np.float32)
        self.action_space = spaces.Discrete(len(self.handshake["actions"]))
        check_policy_interface(dim, self.action_space.n)
        self.feature_names = read_json(ROOT / "configs/research_v2/wire_contract.json")["observation_features"]
        self.last_raw_snapshot = None
        self.last_cost_cumulative = np.zeros(5)

    # ---- helpers -----------------------------------------------------------------------------------------------

    def _pick_trace(self, seed):
        if callable(self._traces):
            return self._traces(seed, self._episode_index)
        require(len(self._traces) > 0, "no traces supplied")
        index = seed % len(self._traces) if seed is not None else self._episode_index % len(self._traces)
        return self._traces[index]

    def _guard(self):
        if self._broken:
            raise ConnectionLostError("the environment lost its connection; create a new environment")

    def _call(self, *args, **kwargs):
        try:
            return self._client.request(*args, **kwargs)
        except ConnectionLostError:
            self._broken = True
            self._done = True
            raise

    def _info(self, response):
        info = {"task_id": response["task_id"], "sim_time_s": response["sim_time_s"], "step_index": response["step_index"],
                "cost_cumulative": np.asarray(response["cost_cumulative"]), "cost_delta": np.asarray(response["cost_delta"]),
                "raw_snapshot": response["raw_snapshot"], "observation_valid": response["observation_valid"]}
        if response["summary"] is not None:
            info["summary"] = response["summary"]
        if response["result"] is not None:
            info["result"] = response["result"]
        return info

    # ---- Gymnasium API -----------------------------------------------------------------------------------------

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self._guard()
        trace = self._pick_trace(seed)
        self._episode_index += 1
        self._episode_id = f"ep{self._episode_index:06d}"
        self._trace_sha = trace["payload_sha256"]
        response = self._call("reset", episode_id=self._episode_id, config_sha256=self._config_sha, trace_sha256=self._trace_sha,
                              trace=trace, options=dict(self._options))
        self._done = False
        self.last_raw_snapshot = response["raw_snapshot"]
        self.last_cost_cumulative = np.asarray(response["cost_cumulative"])
        return np.asarray(response["observation"], dtype=np.float32), self._info(response)

    def step(self, action):
        self._guard()
        if self._done:
            raise RuntimeError("the episode has ended (or was never reset); call reset()")
        response = self._call("step", episode_id=self._episode_id, config_sha256=self._config_sha, trace_sha256=self._trace_sha,
                              action=int(action))
        delta = np.asarray(response["cost_delta"])
        reward = float(-REWARD_SCALE * np.dot(self.weights, delta))
        terminated = bool(response["terminated"])
        self._done = terminated
        self.last_raw_snapshot = response["raw_snapshot"]
        self.last_cost_cumulative = np.asarray(response["cost_cumulative"])
        info = self._info(response)
        info["reward_components"] = -REWARD_SCALE * self.weights * delta
        return np.asarray(response["observation"], dtype=np.float32), reward, terminated, False, info

    def heartbeat(self):
        """Keep the server's RPC timer alive while Python is busy (server timeout is `execution.rpc_timeout_wall_s`)."""
        self._guard()
        return self._call("heartbeat")

    def close(self):
        try:
            if not self._broken:
                self._client.request("close", episode_id=self._episode_id, config_sha256=self._config_sha, trace_sha256=self._trace_sha, raw=True)
        except Exception:
            pass
        finally:
            self._client.close()
            if self._server is not None:
                self._server.close()
