| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 640, "binary_files": 0, "files": 15, "removed": 35} |
| dependency count | UNMEASURED |
| residue-arm firings, and additions a fixer made beyond the proposal | none; the diff matches the proposal's Impact list |
| requirement-to-test reconcile result | pass; no requirements exist (skip_specs) |
| pre-commit wall-clock, total and per hook | 5.42s total, all five hooks |
| direct declared runtime dependencies | {"base": 6, "delta": 0, "head": 6} |
| total root-lock packages | {"base": 58, "delta": 1, "head": 59} |
| runtime tokens | UNMEASURED |
| runtime files read | UNMEASURED |
| runtime retries | UNMEASURED |
| runtime phase span | UNMEASURED |

Machine evidence and per-field provenance: [metrics.json](metrics.json).

## Notes on provenance

`lines added and removed` (640/35 over 15 files) counts the change artefacts and
the regression tests, not just the fix. The behavioural change in
`anonymize/rules/password.py` is **+13 / -16**: a sixteen-line `crypt` branch
replaced by one return statement and a docstring explaining why.

`total root-lock packages` moved 58 -> 59 because restoring `requires-python =
">=3.10"` widens the resolution space, so uv locks one additional
version-conditional distribution. No direct dependency was added.

### Cross-version verification

The evidence that matters for this change is not in the table. Full suite, five
interpreters:

| Python | Result |
|---|---|
| 3.10 | 1397 passed, 1 skipped |
| 3.11 | 1397 passed, 1 skipped |
| 3.12 | 1397 passed, 1 skipped |
| 3.13 | 1397 passed, 1 skipped |
| 3.14 | 1397 passed, 1 skipped |

Before the fix, 3.10 through 3.12 were 6 failed / 1388 passed and 0.6.0 refused
to install there at all. The anonymizer's output for a three-password fixture
hashes identically on all five, which is the determinism property the change
exists to establish.

The session-log fields stay UNMEASURED rather than estimated, as phase 7
requires.
