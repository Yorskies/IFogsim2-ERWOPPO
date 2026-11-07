"""Deterministic reference policies for P06, written against the public 108-feature snapshot only.

Every policy takes the raw snapshot of the task being decided (the dict returned as `info["raw_snapshot"]`) and returns an
action index 0..6 (0 = the task's own IoT, 1..5 = F1..F5, 6 = cloud). They see exactly what PPO sees: no future
arrival, no hidden job list, no reservation, and no admission mask. Estimates are estimates from current queues, never
outcomes. Ties within `TIE_S` resolve as documented per policy.
"""

from .config import ROOT, read_json

WIRE = read_json(ROOT / "configs/research_v2/wire_contract.json")
ACTIONS = WIRE["actions"]                 # ["source_iot", "F1", ..., "F5", "cloud"]
FEATURES = frozenset(WIRE["observation_features"])
TIE_S = 1e-9
FOGS = range(1, 6)


class AuditedSnapshot(dict):
    """A snapshot that records every key read, so tests can prove a policy never looks beyond the public features."""

    def __init__(self, data):
        super().__init__(data)
        self.accessed = set()

    def __getitem__(self, key):
        self.accessed.add(key)
        return super().__getitem__(key)


def always_local(snapshot):
    """Calibration baseline: process every task on its own IoT."""
    return 0


def nearest_fog(snapshot):
    """Calibration baseline: send every task to the fog its IoT is attached to."""
    for k in FOGS:
        if snapshot[f"source.access_fog.F{k}"] == 1.0:
            return k
    raise ValueError("snapshot has no access fog")


def least_fog(snapshot):
    """Least Fog: among the five fogs, the smallest (remaining running MI + queued MI) / total MIPS.

    Ties (within 1e-9): shorter transfer path, taken as the smaller estimated input + result delay; then the smaller node id.
    Only fogs are considered; there is no rerouting when admission later fails.
    """
    best, best_key = None, None
    for k in FOGS:
        name = f"F{k}"
        backlog = snapshot[f"node.{name}.remaining_mi_over_mips_s"]
        path = snapshot[f"route.{name}.estimated_input_delay_s"] + snapshot[f"route.{name}.estimated_result_delay_s"]
        if best is None or backlog < best_key[0] - TIE_S or (abs(backlog - best_key[0]) <= TIE_S and path < best_key[1] - TIE_S):
            best, best_key = k, (backlog, path)
    return best


def eft_scores(snapshot):
    """Estimated finish time of every destination: Tin + W + MI/MIPS_per_PE + Tout, with W = max(0, earliest_free + queued - Tin)."""
    mi = snapshot["task.cpu_mi"]
    scores = []
    for action, name in enumerate(ACTIONS):
        node = "source_iot" if action == 0 else name
        tin = snapshot[f"route.{name}.estimated_input_delay_s"]
        tout = snapshot[f"route.{name}.estimated_result_delay_s"]
        wait = max(0.0, snapshot[f"node.{node}.earliest_pe_free_delay_s"] + snapshot[f"node.{node}.queued_mi_over_mips_s"] - tin)
        scores.append(tin + wait + mi / snapshot[f"node.{node}.mips_per_pe"] + tout)
    return scores


def greedy_eft(snapshot):
    """Greedy-EFT over all seven destinations from queue statistics; no admission mask, no reservation, ties to the smaller id."""
    scores = eft_scores(snapshot)
    best = 0
    for action in range(1, len(scores)):
        if scores[action] < scores[best] - TIE_S:
            best = action
    return best


POLICIES = {"always_local": always_local, "nearest_fog": nearest_fog, "least_fog": least_fog, "greedy_eft": greedy_eft}
