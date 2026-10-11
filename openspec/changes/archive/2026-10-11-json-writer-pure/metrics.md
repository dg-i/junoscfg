| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 159, "binary_files": 0, "files": 8, "removed": 11} |
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
| Context expansion: src/junoscfg/convert/__init__.py | `pipeline_result`, the one caller of `from_dict` in `src/`, and its `wrap=False` door |
| Context expansion: tests/support/shapes.py, tools/check_test_doors.py | the catalogue the read-IR law runs over; why the law cannot sit in `tests/contract/` |
| Context expansion: src/junoscfg/anonymize/__init__.py, src/junoscfg/anonymize/revert.py | Reviewer caller check: does anonymize or revert mutate the caller's IR (F2) |
| Context expansion: src/junoscfg/edityaml/__init__.py, src/junoscfg/audit/__init__.py | Reviewer caller check: edityaml and audit purity |
| Context expansion: .venv agent_ready_checks lane.py, codemap.py | Reviewer: the C5 lane rule; whether the CONTRACT reflow is required (F3) |
| Context expansion: tests/data/device/{jvd,synthetic} captures | Reviewer: the ARCH-C15 citations |
| caller IR changed by a writer (`TestNoWriterChangesTheIrItIsGiven`, 384 cases) | base d1e804e: 22 cases changed (every JSON door of nine hand-built spellings, four catalogue sources); head 5f9934f: none |
| JSON output time, largest device JSON capture (`services-leaf1_qfx5130-48c.json.gz`) | 5.7 ms with the copy; the copy alone 1.5 ms |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
