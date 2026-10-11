| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 2065, "binary_files": 0, "files": 32, "removed": 565} |
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
| Every-rule anonymization over the device captures and examples (`combos.py`, 363 runs) | base: 297 refused; head: 0 refused, 0 surviving addresses (whole words and inside words), 0 revert failures, 0 dangling group references |
| Deterministic-mapping pin | 92 entries to 95, none dropped or altered (`pin-diff.txt`) |
| Context expansion: `git archive 3a0607f src` (base `rules/ip.py`, pipeline) | Reviewer: base comparison, finding 1 and S4 |
| Context expansion: `src/junoscfg/anonymize/rules/sensitive_word.py`, `password.py` (full) | Reviewer: `lexical` semantics and rule order, finding 5 |
| Context expansion: `tests/support/devices.py`, `pin_map.py` | Reviewer: pin recomputation |
| Context expansion: `private_test_data/jvd/**/*.conf` (grep) | Reviewer: blast radius of R1 |
| Context expansion: `blast_s4.py`, `blast_s4.out` | Reviewer: the extension's figures |
| Context expansion: `src/junoscfg/audit/walker.py` | Builder: change-4 carry-forward (`schema_child`) |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
