## Why
Schema qualification repeatedly traverses large trees, streams tiny JSON writes,
and repeats pure checks even when their exact inputs and checker implementations match.
The owner approved the measured design and approximately 201 MiB additional peak memory.

## What Changes
Use deque traversal, batch four flag-only searches, and buffer two artifact writers.
Use template-owned exact-content proof for Draft202012 schema checks and Lark compilation.
Bind proof lineage in shard outcomes; preserve fresh generation and two serial builds.
Search of verification STORE, schema workers, corpus checks and qualification found
readers in tools/schema_verification.py, tests/conftest.py and test_schema_data.py.

## Capabilities
### Modified Capabilities
- `schema-pipeline/verification-evidence`: explicit pure-operation success reuse.

## Non-goals
No change to accepted Junos configurations, schema dialect, artifacts or public CLI.
No cross-machine cache transfer, app-owned cache, or weakening of whole-run identity.

## Impact
Generator internals, schema test adapter, and the agent-ready-checks dependency.
Research baseline was approximately 1262 seconds; combined scratch run was 104 seconds.
Native reproduction: `python -m tools.schema_verification qualify schema-25.2`.

## Completion
Warm native qualification <=180 seconds on this machine in three runs; measure cold separately.
Exact compressed products agree; metadata excludes only generated_at. Corruption,
changed inputs/engine and failures must never reuse invalid success. Independent tests
and fresh review required. Owner approved implementation and required records on 2026-10-13.
