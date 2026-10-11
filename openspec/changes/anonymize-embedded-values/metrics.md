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
| Acceptance tests on base product code (phase 4) | 36 failed, 17 passed (named pins), `50b0a10` |
| Context expansion: `src/junoscfg/anonymize/` (every module, ≈3,000 lines) | Builder, phase 0: the change's owning package, read in source; the rules' shapes, the walker's chain, revert |
| Context expansion: `tests/unit/anonymize/test_integration.py` (wildcard and unplaced catalogues, the mapping pin) | Builder, phase 0: which existing tests the delta changes |
| Context expansion: `src/junoscfg/convert/__init__.py` (`_unplaced_warnings`, `_pattern_warnings`) | Builder, phase 2: whether the warnings name the new shapes |
| Context expansion: `tests/contract/test_every_rule.py` | Builder, phase 2: the mapping law the sensitive-word rule must keep (whole values) |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
