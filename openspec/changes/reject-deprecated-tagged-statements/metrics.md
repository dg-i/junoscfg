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

| Context expansion: src/junoscfg/validate/structured_validator.py | Direct deprecated caller and exception boundary; validation requirement records invalid result. |
| Context expansion: src/junoscfg/validate/CONTRACT.md | Caller layering and lazy-loading invariants. |
| Context expansion: openspec/specs/validation/structured-validation/spec.md | Freeze and proposed clarification of affected deprecated validation guarantee. |
| Context expansion: tests/contract/test_every_door.py | Existing deprecated validator exclusions and richer public door coverage. |

| Context expansion: src/junoscfg/display/set_converter.py | Owning shared kernel excluded from domain-ranked slice; necessary lexical guard responsibility. |
| Context expansion: src/junoscfg/display/CONTRACT.md | Owning shared-kernel contract and deprecated boundary. |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
