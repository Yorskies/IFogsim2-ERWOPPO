"""JSON Schema 2020-12 definitions; no simulator or training dependency.

Exported copies are committed for Java/other consumers. Change the schema version
when changing wire compatibility. Tests check exports against these definitions.
"""

from . import SCHEMA_VERSION

OBJECTIVES = ["latency", "energy", "deadline", "imbalance", "qos_failure"]
WORKLOADS = ["light", "moderate", "heavy", "dynamic"]
SPLITS = ["calibration", "pilot_train", "pilot_validation", "train_candidate", "train_final", "validation", "test"]
COMPONENTS = ["arrival", "source", "class", "cpu_mi", "input_bytes", "deadline"]
TERMINALS = ["ON_TIME", "LATE_SUCCESS", "FAILED"]
FAILURES = ["CPU_QUEUE_FULL", "RAM_EXHAUSTED", "NETWORK_QUEUE_FULL", "SERVICE_TIMEOUT"]
EVENT_PRIORITIES = {"CPU_COMPLETE": 0, "TRANSFER_COMPLETE": 0, "RESULT_DELIVERED": 0,
                    "DEADLINE": 1, "TIMEOUT": 1, "ARRIVAL": 2, "HORIZON": 3}


def obj(properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


def number(minimum=0, *, positive=False, maximum=None):
    result = {"type": "number", "exclusiveMinimum" if positive else "minimum": minimum}
    if maximum is not None:
        result["maximum"] = maximum
    return result


def integer(minimum=0, maximum=None):
    result = {"type": "integer", "minimum": minimum}
    if maximum is not None:
        result["maximum"] = maximum
    return result


def array(items, length=None, minimum=1):
    result = {"type": "array", "items": items, "minItems": minimum if length is None else length}
    if length is not None:
        result["maxItems"] = length
    return result


def enum(values):
    return {"enum": values}


def const(value):
    return {"const": value}


def document(name, schema):
    return {"$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"urn:erwo:{SCHEMA_VERSION}:{name}", **schema}


STRING = {"type": "string", "minLength": 1}
HASH = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
FRACTION = number(maximum=1)
POSITIVE = number(positive=True)
BOOL = {"type": "boolean"}
NODE = obj({"id": STRING, "pes": integer(1), "mips_per_pe": POSITIVE,
            "ram_bytes": integer(1), "storage_bytes": integer(1), "queue_waiting": integer(),
            "idle_w": number(), "busy_w": number()})
RANGE = array(POSITIVE, 2)
WEIGHTS = array(FRACTION, 5)
SEGMENT = obj({"start_s": number(), "end_s": POSITIVE, "rate_per_s": POSITIVE})
LINK = obj({"bandwidth_bit_per_s": POSITIVE, "propagation_s": number(),
            "queue_waiting": integer(), "duplex": enum(["half", "full"])})


def config_schema():
    return document("config", obj({
        "protocol_version": const("0.2"), "schema_version": const(SCHEMA_VERSION), "parameter_origin": STRING,
        "units": obj({key: const(value) for key, value in {
            "time": "s", "cpu_work": "MI", "cpu_capacity": "MIPS_per_PE", "data": "byte",
            "bandwidth": "bit_per_s", "power": "W", "energy": "J"}.items()}),
        "timing": obj({"arrival_window_s": POSITIVE, "timeout_factor": number(1, positive=True),
                       "deadline_max_s": POSITIVE, "horizon_s": POSITIVE,
                       "comparison_epsilon_s": POSITIVE, "min_event_spacing_s": POSITIVE}),
        "topology": obj({"iot_count": const(100), "iot_per_access_fog": const(20),
                         "fog_mode": enum(["homogeneous", "heterogeneous"]), "iot": NODE,
                         "fogs": array(NODE, 5), "cloud": NODE,
                         "scheduler": const("fcfs_nonpreemptive_one_pe"), "overbooking": const(False),
                         "reroute_on_rejection": const(False)}),
        "tasks": obj({"working_set_bytes": integer(1), "output_fraction": number(positive=True, maximum=1),
                      "classes": array(obj({"id": enum(["light", "medium", "heavy"]),
                                            "probability": FRACTION, "cpu_mi": array(integer(1), 2),
                                            "input_mib": RANGE, "deadline_s": RANGE}), 3)}),
        "workloads": obj({w: array(SEGMENT) for w in WORKLOADS}),
        "network": obj({"access": LINK, "lan": LINK, "wan": LINK, **{key: number() for key in [
            "radio_idle_w", "radio_tx_increment_w", "radio_rx_increment_w", "ap_idle_w",
            "ap_tx_increment_w", "ap_rx_increment_w", "lan_idle_w", "wan_idle_w",
            "lan_j_per_bit_hop", "wan_j_per_bit_hop"]}}),
        "evaluation": obj({"objective_order": const(OBJECTIVES), "weights": const([.2] * 5),
                           "latency_reference_s": POSITIVE, "failure_latency_penalty_s": POSITIVE,
                           "energy_reference_j_per_arrival": POSITIVE, "imbalance_reference": POSITIVE,
                           "workload_weights": const([.25] * 4), "clip_costs": const(False)}),
        "observation": obj({"dimension": const(108), **{key: POSITIVE for key in [
            "mips_reference", "pes_reference", "cpu_mi_reference", "input_reference_mib",
            "output_reference_mib", "deadline_reference_s", "timeout_reference_s",
            "bandwidth_reference_bit_per_s", "cpu_increment_reference_j_per_mi",
            "time_squash_reference_s", "arrival_squash_reference_per_s",
            "communication_squash_reference_j", "ema_time_constant_s", "remaining_deadline_reference_s"]}}),
        "reward": obj({"scale": POSITIVE, "discount": const(1.0), "clip": const(False), "adaptive_normalization": const(False)}),
        "ppo": obj({"device": const("cpu"), "environments": const(1), "torch_threads": const(1),
                    "torch_interop_threads": const(1), "actor_layers": array(integer(1)), "critic_layers": array(integer(1)),
                    "activation": const("Tanh"), "learning_rate": POSITIVE, "n_steps": integer(1),
                    "batch_size": integer(2), "n_epochs": integer(1), "gamma": const(1.0),
                    "gae_lambda": FRACTION, "clip_range": FRACTION, "ent_coef": number(), "vf_coef": number(),
                    "max_grad_norm": POSITIVE, "target_kl": POSITIVE, "normalize_advantage": const(True),
                    "deterministic_evaluation": const(True)}),
        "training": obj({**{key: integer(1) for key in ["smoke_decisions", "pilot_decisions", "candidate_decisions",
            "ranking_reference_decisions", "final_decisions", "checkpoint_decisions"]}, "workload_order": const(WORKLOADS)}),
        "search": obj({**{key: integer(1) for key in ["population", "generations_including_initial", "candidate_slots",
            "model_repeats", "validation_traces_per_workload"]}, "weight_floor": number(positive=True, maximum=.199999),
            "dirichlet_alpha": POSITIVE, "equal_weights": const([.2] * 5), "manual_weights": WEIGHTS,
            "sbx_probability": FRACTION, "sbx_eta": POSITIVE, "mutation_probability": FRACTION,
            "mutation_probability_per_variable": FRACTION, "mutation_eta": POSITIVE, "tie_epsilon": POSITIVE,
            "hypervolume_reference": array(number(1, positive=True), 5),
            **{key: integer() for key in ["initial_rng_base", "nsga_rng_base", "random_rng_base"]}}),
        "seeds": obj({**{key: integer() for key in ["master", "candidate_model_base", "final_model_base",
            "pilot_simplex", "bootstrap", "secondary_signflip"]}, "outer_runs": integer(2),
            "pilot_outer_ids": {**array(integer(), 3), "uniqueItems": True},
            **{key: array(integer(), 2) for key in ["calibration_trace_ids", "validation_trace_ids", "test_trace_ids"]},
            "generator": const("PCG64"), "digest": const("SHA-256"), "separator": const("|"),
            "unused_field": const("-"), "seed_bytes": const(8), "byte_order": const("little")}),
        "statistics": obj({"alpha": number(positive=True, maximum=1), "primary_family_size": const(3),
            "secondary_family_size": const(60), "bootstrap_draws": integer(1), "secondary_signflip_draws": integer(1),
            "practical_relative_improvement": FRACTION, "unit": const("outer_training_run"), "multiplicity": const("Holm")}),
        "pilot": obj({"candidate_budget_ladder": array(integer(1)), "minimum_median_spearman": FRACTION,
            "minimum_spearman": number(-1, maximum=1), "solo_feasible_fraction": FRACTION,
            "heavy_failure_fraction_gt": FRACTION, "heavy_reliability_gt": FRACTION}),
        "sensitivity": obj({"timeout_factors": array(number(1, positive=True), 2),
            "fog_queue_waiting": array(integer(), 2), "wan_propagation_s": RANGE,
            "dynamic_power_multipliers": RANGE, "normalization_multipliers": RANGE}),
        "execution": obj({"workers": integer(1, 4), "allowed_ports": {**array(integer(1024, 65535), 4), "uniqueItems": True},
            "heartbeat_wall_s": POSITIVE, "rpc_timeout_wall_s": POSITIVE, "technical_retries": integer(),
            "python_fallback": const(False), "resume_scope": const("completed_run"),
            "output_namespace": const("results/research_v2"), "target_python": const("3.12"), "target_java_release": const(21)})
    }))


def contract_schema():
    task = obj({"task_id": integer(), "source_iot": integer(0, 99), "access_fog": integer(1, 5),
                "class_id": enum(["light", "medium", "heavy"]), "arrival_s": number(), "cpu_mi": integer(1),
                "input_bytes": integer(1), "output_bytes": integer(1), "deadline_relative_s": POSITIVE,
                "timeout_relative_s": POSITIVE, "working_set_bytes": integer(1)})
    event = obj({"episode_id": STRING, "task_id": {"type": ["integer", "null"], "minimum": 0},
                 "at_s": number(), "kind": enum(list(EVENT_PRIORITIES)), "priority": integer(0, 3),
                 "sequence": integer(), "generation": integer(), "resource_id": {"type": ["string", "null"]}})
    outcome = obj({"episode_id": STRING, "task_id": integer(), "terminal": enum(TERMINALS),
                   "failure_reason": {"enum": [None, *FAILURES]}, "at_s": number(),
                   "result_received_s": {"type": ["number", "null"], "minimum": 0},
                   "dynamic_energy_j": number(), "deadline_violated": BOOL})
    resource = obj({"resource_id": STRING, "kind": enum(["iot", "fog", "cloud"]),
                    "pes": integer(1), "mips_per_pe": POSITIVE, "ram_bytes": integer(1),
                    "storage_bytes": integer(1), "queue_waiting": integer(), "idle_w": number(), "busy_w": number()})
    hop = obj({"link_id": STRING, "from_id": STRING, "to_id": STRING,
               "bandwidth_bit_per_s": POSITIVE, "propagation_s": number(),
               "server_id": STRING, "queue_waiting": integer()})
    route = obj({"source_iot": integer(0, 99), "action": integer(0, 6),
                 "input_hops": array(hop, minimum=0), "result_hops": array(hop, minimum=0)})
    costs = obj({"objective_order": const(OBJECTIVES), "values": array(number(), 5),
                 "out_of_reference": BOOL})
    trace = obj({"schema_version": const(SCHEMA_VERSION), "config_sha256": HASH, "payload_sha256": HASH,
                 "seed_namespace": obj({"master": integer(), "split": enum(SPLITS),
                    "outer_run": {"type": ["integer", "null"], "minimum": 0},
                    "model_repeat": {"type": ["integer", "null"], "minimum": 0},
                    "trace_id": integer(), "workload": enum(WORKLOADS)}),
                 "arrival_window_s": POSITIVE, "horizon_s": POSITIVE,
                 "task_count": integer(1), "tasks": array({"$ref": "#/$defs/task"})})
    manifest = obj({"schema_version": const(SCHEMA_VERSION), "study_id": STRING, "run_id": STRING,
                    "status": enum(["pending", "running", "complete", "failed", "interrupted"]),
                    "attempt": integer(1), "source_sha256": HASH, "config_sha256": HASH,
                    "build_sha256": HASH, "trace_sha256": array(HASH),
                    "artifacts": {"type": "object", "additionalProperties": HASH}, "invariants_valid": BOOL})
    rpc = obj({"schema_version": const(SCHEMA_VERSION), "request_id": STRING,
               "episode_id": STRING, "config_sha256": HASH, "trace_sha256": HASH,
               "operation": enum(["reset", "step", "close", "heartbeat"]),
               "action": {"type": ["integer", "null"], "minimum": 0, "maximum": 6}})
    return document("contracts", {"$defs": {"task": task, "resource": resource, "route": route,
        "event": event, "outcome": outcome, "cost_vector": costs, "trace": trace,
        "manifest": manifest, "rpc_request": rpc}})


def wire_contract():
    node_features = ["busy_pe_fraction", "queue_fraction", "earliest_pe_free_delay_s", "queued_mi_over_mips_s",
        "mips_per_pe", "pes", "cpu_increment_j_per_mi", "remaining_mi_over_mips_s", "minimum_remaining_deadline_s"]
    route_features = ["estimated_input_delay_s", "estimated_result_delay_s", "bottleneck_bit_per_s", "estimated_dynamic_energy_j"]
    nodes = ["source_iot", "F1", "F2", "F3", "F4", "F5", "cloud"]
    features = [f"node.{n}.{f}" for n in nodes for f in node_features]
    features += [f"route.{n}.{f}" for n in nodes for f in route_features]
    features += ["task.cpu_mi", "task.input_bytes", "task.output_bytes", "task.deadline_relative_s",
        "task.timeout_relative_s", "task.class.light", "task.class.medium", "task.class.heavy"]
    features += [f"source.access_fog.F{i}" for i in range(1, 6)]
    features += ["global.time_fraction", "global.arrival_ema_per_s", "global.mean_iot_utilization", "global.interarrival_s"]
    return {"schema_version": SCHEMA_VERSION, "objective_order": OBJECTIVES,
            "actions": nodes, "observation_features": features, "event_priorities": EVENT_PRIORITIES,
            "terminal_states": TERMINALS, "failure_reasons": FAILURES, "splits": SPLITS,
            "rng_components": COMPONENTS, "timestamp_encoding": "IEEE-754 binary64 JSON round-trip",
            "event_tie_order": ["at_s", "priority", "task_id (null last)", "sequence"],
            "idempotency_key": ["episode_id", "task_id", "generation", "kind", "sequence"],
            "terminal_idempotency_key": ["episode_id", "task_id"],
            "rpc_framing": "UTF-8 JSON Lines; one object per line; no NaN/Infinity",
            "rpc_max_frame_bytes": 16777216}


def trace_bundle_schema():
    """P01 sidecar; leaves the P00 trace/wire format unchanged."""
    return document("trace-bundle", obj({
        "bundle_version": const("research-v2.trace-bundle-1"),
        "generator_version": const("research-v2.trace-1"),
        "status": enum(["ready", "sealed"]),
        "seed_namespace": contract_schema()["$defs"]["trace"]["properties"]["seed_namespace"],
        "task_count": integer(1), "payload_sha256": HASH, "config_sha256": HASH,
        "files": obj({"trace.json": HASH, "config.json": HASH}),
        "units": config_schema()["properties"]["units"],
        "component_seeds": obj({name: integer() for name in COMPONENTS}),
        "producer": obj({"python": STRING, "numpy": STRING, "source_sha256": HASH}),
    }))
