| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 1457, "binary_files": 0, "files": 34, "removed": 186} |
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
| Context expansion: src/junoscfg/convert/__init__.py | Reviewer: the pipeline refusal door (R1) |
| Context expansion: src/junoscfg/convert/output/json_output.py, src/junoscfg/convert/input/normalization.py | Reviewer: how the record is normalized (R5) |
| Context expansion: src/junoscfg/edityaml/ansibilize.py | Reviewer: wildcard readers |
| Context expansion: src/junoscfg/convert/field_validator.py (`_validate_leaf`) | Reviewer: the `""` skip (R3) |
| Context expansion: tach.toml | Reviewer: which fix the layering allows (R1) |
| Context expansion: tools/device_differences.py | the 928-line regeneration and its rerun |
| Context expansion: src/junoscfg/input.py | the shared bracket rule (R4) |
| Context expansion: src/junoscfg/audit/walker.py, src/junoscfg/anonymize/revert.py | Test/Challenge F7: audit and revert with a record |
| known-differences.json (`tools/device_differences.py`) | base f0bb6aa: 932 lines, 17 classes; head 8561b95: 928 lines, 16 classes (`xml-empty-value-lost`, 4 lines, removed by the DEV-16 fix) |
| reproductions (`private_test_data/makeover-work/kept-whole-statements/repro.py`) | base: OPEN-2 silent loss / false UNPLACED, NEW-C1 value replaced by null with no report, OPEN-3 quotes lost; head: all kept in the record, reported once, written as read |
| value-less leaves in 100 device JSON/XML files (`null_leaves.py`) | base: 12 (all DEV-16 `description`); head: 0 |
| set/curly files the reader now refuses (`refusal_radius.py`, 1,716 device and JVD files) | 0 |
| new empty-value errors (`empty_radius.py`, 1,775 device and JVD files) | 0 |
| acceptance tests failing on the merge base (phase 4 set) | 172 of 4,029 in the four phase-4 files; every later Test/Challenge and review addition fails on the base except the stated guards |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
