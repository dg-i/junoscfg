| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 27, "binary_files": 0, "files": 3, "removed": 4} |
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
| Full checkpoint at a2edf23 | every check passed; application tests 7,559 passed, 37 skipped, 18 xfailed in 112 s; whole check 2 min 43 s; coverage 92.95 % |
| Before/after comparison over `tests/data/device/` | 0 of 96 conversions differ; base stderr carries the `field_validator.py:206` FutureWarning once, head stderr has none |
| Shipped patterns | 263; 2 respelled (#49, #83); 0 compiled programs differ; 0 warn at head |
| Review | lightweight fresh-agent review, APPROVE; findings F1 and F2 applied as records only, F3 deferred to follow-up T5 |
| Retries, regenerations, stalls | 1 test rework: the first version raised the warning as an error, which `agent-ready lane` does not count as a failure at the merge base (a2edf23); no regeneration, no stall |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
