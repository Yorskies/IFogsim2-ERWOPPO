# Research v2 data contracts

`config.schema.json` and `contracts.schema.json` use JSON Schema draft 2020-12.
`contracts.schema.json` is a definitions catalog: select a record using
`$ref: "#/$defs/task"` (or resource, route, event, outcome, cost_vector, trace,
manifest, rpc_request). The bare catalog does not validate a specific record.

Use `research_v2.contracts.validate_contract(kind, value, config)` to also enforce
cross-field invariants. JSON numbers must be finite, unknown keys are rejected,
and byte/MI/ID fields represent integers. UTF-8 timestamps use JSON round-trip
binary64, not rounded display strings. Absolute deadline/timeout are derived
from arrival plus the relative fields. Physical outcomes are never predictions.

Generate the committed exports with `python -m research_v2 export-schemas`;
check drift with `python -m research_v2 export-schemas --check`.
`configs/research_v2/wire_contract.json` fixes objective/action/feature ordering
and is packaged unchanged in the Java foundation artifact. Read its hash at
both ends before adding RPC in P05. Request schema is provisional until P05;
there is no working v2 socket server in P00.

P01 adds `trace_bundle.schema.json` for the immutable bundle sidecar, without
changing the P00 trace envelope. Use `trace_store.read_bundle` for content hashes,
config/namespace/seed consistency and role-based access checks. Test bundles are
sealed and cannot be read/described by P01 consumers; schema validity alone does
not authorize access. See [trace protocol](../../docs/research_v2/TRACES.md).
