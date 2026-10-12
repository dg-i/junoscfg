| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 152, "binary_files": 0, "files": 7, "removed": 17} |
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
| generated lifecycle evidence | {"archived": false, "base": "a7da186460b5d5991c27a7301fb61e421bd22ece", "carry": {}, "change": "test-selection-completeness", "checks": [{"checkpoint": "71e4f7b3c2d7eb38eb623cce3a986ed8f6ebc65d217961d3ebf9b9ea177d0525", "duration_ms": 359524.5197920012, "evidence": ".agent-ready/verification/0778e04d6e0546719af395202b7246eb.json", "exit_status": 1, "reused": false, "tier": "full"}, {"checkpoint": "63f8af247b00f8339e5026e78593452c1c2cf3d09348ddae553170fdfc517fbb", "duration_ms": 355331.73575002, "evidence": ".agent-ready/verification/1bdfdc654a73419b910f22811cd4bece.json", "exit_status": 0, "reused": false, "tier": "full"}], "head": "68114279f23c6cef592a6d17f913a64abe806176", "ledger_sha256": "19cd5ccce1f1c4d6330b254c031606fbfebc00324e6e585187fcd5b7b2526312", "observations": {"active_agent_minutes": {"reason": "UNMEASURED", "value": null}, "cache_tokens": {"reason": "UNMEASURED", "value": null}, "escaped_regressions": {"reason": "UNMEASURED", "value": null}, "expensive_runs": {"reason": "UNMEASURED", "value": null}, "full_runs": {"events": ["a0dff601c5717747b7e1e16b430c0f73f4b83794f7093cbb489054a04b0375be", "c46325d4f1a6fa89572563cefcc33036e081e5f23ff21dbaf6c038ad00d8c282"], "value": 2}, "intent_to_archive_minutes": {"reason": "UNMEASURED", "value": null}, "output_tokens": {"reason": "UNMEASURED", "value": null}, "post_review_code_churn": {"reason": "UNMEASURED", "value": null}, "review_findings": {"reason": "UNMEASURED", "value": null}}, "progress": [{"completed": 2, "total": 6}, {"completed": 2, "total": 6}], "roles": [{"referent": "51e91f69d9ef5f3fe25527bb904a77cf0c4bd1eb", "role": "Reviewer", "verdict": "APPROVE"}], "schema": "lifecycle-summary/1"} |
| Context expansion: tools/affected_tests.py | Tooling owner outside generated runtime-only slice; no module contract exists |
| Context expansion: .pre-commit-config.yaml | Selector invocation and deleted-file filtering |
| Context expansion: tests/CONTRACT.md | Authoritative layer and selection rules |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
