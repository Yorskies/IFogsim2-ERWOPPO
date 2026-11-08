"""Split/role checks for P01. These are protocol guards, not filesystem security."""

from dataclasses import asdict, dataclass
import hashlib

from .config import ContractError, require
from .schema_definitions import COMPONENTS, SPLITS, WORKLOADS

TRAIN_SPLITS = {"pilot_train", "train_candidate", "train_final"}
ROLES = {
    "calibrator": {"calibration"},
    "pilot_trainer": {"pilot_train"},
    "pilot_validator": {"pilot_validation"},
    "candidate_trainer": {"train_candidate"},
    "search_validator": {"validation"},
    "final_trainer": {"train_final"},
    "holdout_preparer": {"test"},
    "test_evaluator": {"test"},
}
# Set only by unseal_test() after the P10 protocol lock verifies; never by import or configuration.
_TEST_UNSEALED = None


def authorize(role, split, operation):
    require(role in ROLES, f"Unknown trace role: {role}")
    require(split in ROLES[role], f"Role {role} cannot access split {split}")
    require(operation in {"generate", "read", "describe"}, f"Unknown trace operation: {operation}")
    if split == "test":
        if role == "test_evaluator":
            require(_TEST_UNSEALED is not None,
                    "Test is sealed: call unseal_test() with a valid P10 protocol lock before evaluating")
        else:
            require(operation == "generate", "Test is sealed: P01 allows preparation only; evaluation requires P10 protocol freeze")


def unseal_test(lock_path):
    """Allow role test_evaluator on the test split, only if the P10 protocol lock verifies against disk."""
    global _TEST_UNSEALED
    from .analysis.lock import require_valid_lock
    _TEST_UNSEALED = require_valid_lock(lock_path)["lock_sha256"]


def _integer(value, name):
    require(type(value) is int and value >= 0, f"{name} must be a nonnegative Python integer")


@dataclass(frozen=True, slots=True)
class TraceKey:
    master: int
    split: str
    outer_run: int | None
    model_repeat: int | None
    trace_id: int
    workload: str

    def validate(self, config):
        _integer(self.master, "master")
        _integer(self.trace_id, "trace_id")
        require(self.master == config["seeds"]["master"], "Trace master seed differs from config")
        require(self.split in SPLITS, f"Unknown trace split: {self.split}")
        require(self.workload in WORKLOADS, f"Unknown workload: {self.workload}")
        training = self.split in TRAIN_SPLITS
        require((self.outer_run is not None) == training and (self.model_repeat is not None) == training,
                "outer_run/model_repeat must both be present only for training splits")
        if training:
            _integer(self.outer_run, "outer_run")
            _integer(self.model_repeat, "model_repeat")
            if self.split == "pilot_train":
                require(self.outer_run in config["seeds"]["pilot_outer_ids"], "Pilot run is outside pilot namespace")
            else:
                require(self.outer_run < config["seeds"]["outer_runs"], "Training run is outside confirmatory namespace")
            repeats = 1 if self.split == "train_final" else config["search"]["model_repeats"]
            require(self.model_repeat < repeats, "Invalid model_repeat for training role (final uses 0)")
        ranges = {"calibration": "calibration_trace_ids", "pilot_validation": "validation_trace_ids",
                  "validation": "validation_trace_ids", "test": "test_trace_ids"}
        if self.split in ranges:
            low, high = config["seeds"][ranges[self.split]]
            require(low <= self.trace_id <= high, f"trace_id outside {self.split} inclusive range [{low},{high}]")
        return self

    def to_dict(self):
        return asdict(self)

    def seed_text(self, component):
        require(component in COMPONENTS, f"Unknown RNG component: {component}")
        fields = (self.master, self.split, self.outer_run, self.model_repeat,
                  self.trace_id, self.workload, component)
        return "|".join("-" if field is None else str(field) for field in fields)

    def seed(self, component):
        digest = hashlib.sha256(self.seed_text(component).encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "little", signed=False)


def key_from_dict(value, config):
    try:
        return TraceKey(**value).validate(config)
    except TypeError as error:
        raise ContractError(f"Invalid trace namespace: {error}") from error
