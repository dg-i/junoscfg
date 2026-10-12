## Context
The installed template couples repeated execution to hashed output validation. A new upstream API is outside this bounded application change.

## Reuse ladder

| Candidate | Coverage | Gap | Maintenance signal, lookup date | Verdict |
|---|---|---|---|---|
| Existing wrapper plus app adapter and public ArtifactBuilder | Identity, locking, coverage, double-pass hashes and public generation | Requires three builds rather than two | Current checked-in and installed code, 2026-10-12 | Reuse |
| time.perf_counter and pytest report.duration | Elapsed timing | No intra-generator stage breakdown | Python and pytest existing dependencies, 2026-10-12 | Reuse |

## Decisions
Keep assertion and generation tiers separate; generation requires successful assertion completion, but executes its own fresh public build. The wrapper alone compares generation exports across two passes and validates hashes on reuse. Add distinct generation required/result manifests. Preserve assertion artifact exports as diagnostics, not integrity-authoritative outputs. Keep explicit older-release commands and narrow automatic triggers. Do not add caching or change generator APIs.

## Risks
Three builds cost more than the speculative two-build design but preserve the installed template contract. Timing setup includes shared fixture work and is attributed to the triggering test; avoid claiming isolated stage costs. Existing semantic metadata tests plus independent challenge guard failure handling and reuse.
