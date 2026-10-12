## Why
One schema qualification repeats the complete assertion suite for artifact stability and runs a separate sentinel. The owner requests lower latency while retaining executed coverage and fail-closed evidence.

## What Changes
- Run schema assertions once; use a separate public-generation tier with template-owned double-pass stability and shipped comparison.
- Remove the redundant full assertion pass and separately scheduled sentinel; retain explicit sentinel use.
- Automatically select the shipped 25.2 release for generator/schema changes; older releases remain explicit compatibility qualification.
- Capture per-test phase durations and public-build elapsed time without changing outcomes.
- Exercise conversion parity against bundled artifacts before costly qualification.
- Search: schema_verification, stability-manifest, sentinel-command, schema_dump and real_artifacts identify the adapter, policy, pytest hooks, corpus fixtures, declarations, and two workflow guides; no new environment/resource override.

## Capabilities
### Modified Capabilities
- `schema-pipeline/verification-evidence`: economical qualification and timing evidence with template-owned integrity reuse.

## Non-goals
No public API, schema acceptance, shipped artifact, dependency or installed template changes. No new cache framework. Parser/output deduplication waits for timings and preserves distinct grammar paths.

## Impact
Application tooling, tests, declarations and guides change. Consumer and CLI surfaces are unchanged. Qualification uses three builds instead of an unproven two-build optimization because the installed wrapper binds output hashing to its stability pass. Independent challenge and review precede coordinated expensive qualification.
