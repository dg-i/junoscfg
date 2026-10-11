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
| Context expansion: src/junoscfg/convert/__init__.py | `pipeline_result`, the one caller of `from_dict` in `src/`, and its `wrap=False` door |
| Context expansion: tests/support/shapes.py, tools/check_test_doors.py | the catalogue the read-IR law runs over; why the law cannot sit in `tests/contract/` |
| Context expansion: src/junoscfg/anonymize/__init__.py, src/junoscfg/anonymize/revert.py | Reviewer caller check: does anonymize or revert mutate the caller's IR (F2) |
| Context expansion: src/junoscfg/edityaml/__init__.py, src/junoscfg/audit/__init__.py | Reviewer caller check: edityaml and audit purity |
| Context expansion: .venv agent_ready_checks lane.py, codemap.py | Reviewer: the C5 lane rule; whether the CONTRACT reflow is required (F3) |
| Context expansion: tests/data/device/{jvd,synthetic} captures | Reviewer: the ARCH-C15 citations |
| JSON output time, largest device JSON capture (`services-leaf1_qfx5130-48c.json.gz`) | 5.7 ms with the copy; the copy alone 1.5 ms |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
