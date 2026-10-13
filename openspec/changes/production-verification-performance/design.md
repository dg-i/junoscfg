## Context
Adopt measured scheduling improvements in native verification, preserving admission
and content-bound success. The application keeps full ordinary test obligations.
## Reuse ladder
| Candidate | Coverage | Gap | Maintenance signal, lookup date | Verdict |
|---|---|---|---|---|
| Existing native engine and schema adapters | Admission, identity, manifests, capacity | Engine binding and scheduling need extension | Local source 2026-10-13 | Extend at owner |
| Python subprocess/concurrent.futures with pytest hooks and coverage combine | Complete isolated execution and aggregation | Small application scheduling/report adapter | Installed runtime 2026-10-13 | Reuse measured adapter |
| Independent application evidence cache | Can record outcomes | Duplicates native authority | Existing contract 2026-10-13 | Reject |
## Decisions
Native opt-in bounded readers finish after pre-commit and before suite/tier overlap.
Only full-suite execution suppresses the redundant affected-test hook. All failures
remain fatal; selected schema tiers preserve order and two generation passes.
Application worker collection is authoritative; module locality and cost hints
only place tests. Coverage combines once and enforces the configured floor.
Native selection-command consumes exact boolean JSON and falls back conservatively.
Application selection preserves workflow-only and version-only exceptions while
unknown changes select. Runtime preparation is input identity, never proof.
Native declared runtime-command probes the actual project interpreter; engine and
meaningful environment bytes bind proof. No app-owned cache or evidence waiver.
## Risks
Parallel CPU/memory pressure and fixture state require negative controls and review.
Shared native API changes are tested upstream before immutable dependency adoption.
No-schema45 remains open; production results, not scratch timings, update baseline.
