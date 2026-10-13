## Context
Fresh generation stays authoritative; identical checker inputs can reuse a proven pure result.
## Reuse ladder
| Candidate | Coverage | Gap | Maintenance signal, lookup date | Verdict |
|---|---|---|---|---|
| Template verification | Atomic receipts, hashes, local paths, completion validation | No content operation | Local source inspected 2026-10-13 | Extend |
| functools cache | Process-local reuse | No durable identity or evidence | Python stdlib | Reject |
| Independent application cache | Can store hashes | Duplicates template authority | Existing adapter contract | Reject |
## Decisions
The template API captures exact input/worker bytes, hashes dependency closure and Python,
runs with isolated controlled imports, and uses existing receipt validation and atomic writes.
Each content key has its own lock. Missing or invalid proof executes; failures never fallback.
Shard completion rechecks proof and records executed/reused lineage in bound outcomes.
Keep Draft202012 defaults and Lark(start="start"); keep two independent sequential builds.
Buffer compact JSON with the same settings/newline; deque preserves BFS repeated-node order.
Only combine name lookups in fixes that mutate flags/is_leaf, at unchanged registry positions.
## Risks
Cold inputs remain slower than three minutes. Memory increases by roughly 201 MiB in research.
Dependency identity is conservative; optional package changes can trigger fresh validation.
Evidence trusts the existing local store, not arbitrary imported receipts.
