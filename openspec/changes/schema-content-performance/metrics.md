<!-- Capture before merge/archive with explicit base and code-head SHAs. Evidence and per-field sources live in adjacent metrics.json. A field without evidence stays UNMEASURED. -->

| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | UNMEASURED |
| dependency count | UNMEASURED |
| direct declared runtime dependencies | UNMEASURED |
| total root-lock packages | UNMEASURED |
| runtime tokens | UNMEASURED |
| runtime files read | UNMEASURED |
| runtime retries | UNMEASURED |
| runtime phase span | UNMEASURED |
| workflow telemetry by phase and model | UNMEASURED |
| residue-arm firings, and additions a fixer made beyond the proposal | UNMEASURED |
| requirement-to-test reconcile result | UNMEASURED |
| pre-commit wall-clock, total and per hook | UNMEASURED |
| Context expansion: agent-ready-python/checks/src/agent_ready_checks/verification_content.py | Dependency trust boundary review |
| Context expansion: agent-ready-python/checks/src/agent_ready_checks/verification.py | Preservation of two-pass execution |

| Complete final full checkpoint | 597.57 s; 10,448 passed, 37 skipped, 20 xfailed; verification.md and final-full log |
| Cold full checkpoint / schema portions | 794.74 s / 318.009 s; verification.md |
| Warm native shipped-release qualification | 112.638111417, 111.743011875, 112.506422750 s; mean 112.296 s; three exit-zero runs; verification.md |
| Explicit older-release native qualification | 21.4: 287.039505959 s; 23.2: 307.921749459 s; both exit zero; verification.md |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
