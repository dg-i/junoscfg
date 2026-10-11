| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 1105, "binary_files": 0, "files": 18, "removed": 59} |
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
| Wildcard names on the device captures (`test_every_wildcard_name_passes`, 12 renderings) | base: the BGP `group <*>` of both `junoscfg-oracle` captures renamed (8 renderings fail); head: every wildcard name kept, none reported |
| Acceptance tests on base product code | 54 failed, 18 passed (named pins) at phase 5; review rows fail there on the missing `patterns` |
| Timing, `anonymize()` with six rules, largest held configuration (296,365 lines) | base 2.059 s, head 2.321 s (names recorded for the selection check); device example 7.3 ms and 7.9 ms; a record, not a gate |
| Context expansion: `src/junoscfg/anonymize/walker.py` | Builder: below the code-map cut; the owning module of the wildcard rule |
| Context expansion: `src/junoscfg/anonymize/rules/{group,identity,sensitive_word,__init__}.py` | Builder: which rules claim an entry name, and the lexical chain |
| Context expansion: `tests/contract/test_every_rule.py`, `tests/contract/test_every_message.py`, `tests/corpus/test_device_anonymization.py` | Builder: where the law, the door row and the capture row belong |
| Context expansion: `src/junoscfg/anonymize/rules/as_number.py` | Reviewer R3 (AS strings pass) |
| Context expansion: `src/junoscfg/anonymize/__init__.py` second passes | Reviewer R2 |
| Context expansion: `src/junoscfg/cli.py` `--strict` | Reviewer point 5 (version) |
| Context expansion: `.venv/.../ipanon/{anonymizer,ranges}.py` | Builder, R5: which blocks the address anonymizer keeps or treats apart |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
