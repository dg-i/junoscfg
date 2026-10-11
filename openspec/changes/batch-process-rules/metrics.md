| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | 16 from the fresh Reviewer (3 major, 10 minor, 3 nit): 15 accepted and fixed, 1 kept with rationale; 0 new on re-review; no human review (owner away, unattended run) |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 337, "binary_files": 0, "files": 7, "removed": 15} |
| dependency count | UNMEASURED |
| residue-arm firings, and additions a fixer made beyond the proposal | UNMEASURED |
| requirement-to-test reconcile result | UNMEASURED |
| pre-commit wall-clock, total and per hook | UNMEASURED |
| direct declared runtime dependencies | {"base": 6, "delta": 0, "head": 6} |
| total root-lock packages | {"base": 63, "delta": 0, "head": 63} |
| runtime tokens | UNMEASURED |
| runtime files read | UNMEASURED |
| runtime retries | UNMEASURED |
| runtime phase span | UNMEASURED |
| workflow telemetry by phase and model | UNMEASURED |
| Batch id | process-rules-2026-10-11 |
| Batch review mode | per-change |
| Batch check executions | full checkpoint 2 (the first failed only on the missing untracked `.claude/skills` mirror), schema tier 1 (scratch worktree), device-evidence focus run 1 |
| Batch integration-only findings | UNMEASURED |
| Batch escaped regressions | UNMEASURED |
| Per-change corpus evidence, measured | device-evidence check files 17.6 s (3,664 passed, 5 xfailed); before/after comparison 3.4 s for 96 conversions, about 40 s for 1,152 with every anonymize rule; versus the owner's 45–90 minutes for `--jvd` |
| Schema tier, measured | `--regen-schema` with the suite 272 s per run; `--schema` 2,021 s over three dumps (34 passed, 2 skipped) |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
