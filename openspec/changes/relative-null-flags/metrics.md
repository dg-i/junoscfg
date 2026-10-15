| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 208, "binary_files": 0, "files": 7, "removed": 15} |
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
| generated lifecycle evidence | {"archived": false, "base": "ea18fab544a055935abaab09f6b550b1d889c049", "carry": {}, "change": "relative-null-flags", "checks": [{"checkpoint": "04ee583263e365c70ef94b9a80db479980198a1641cd7c89153aaa207c295cf4", "duration_ms": 76486.69945891015, "evidence": ".agent-ready/verification/ce511c198da5417982cd567c8f3369f6.json", "exit_status": 1, "reused": false, "tier": "full"}, {"checkpoint": "da9e197d359022ede79e2cee1003cbcb6f168fd63fa5e1ea5a328412f3b6464c", "duration_ms": 259710.13200003654, "evidence": ".agent-ready/verification/02992bae406e4ed1b50fba1f3cb57a1c.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "66c2db3419f40adf708c77011bbbbb43d0322ef19f9cd86f67a314f66199279d", "duration_ms": 50357.92787501123, "evidence": ".agent-ready/verification/fe17fb2d6a184469a1d66641f877318c.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "04ee583263e365c70ef94b9a80db479980198a1641cd7c89153aaa207c295cf4", "duration_ms": 348240.09420897346, "evidence": ".agent-ready/verification/d08cf61babb84c93af88096badf13c40.json", "exit_status": 0, "reused": false, "tier": "full"}], "head": "d9deb10169aa90db6662659bb1423eddf554c6ec", "ledger_sha256": "4f8dab931909152a3d6204bd059f12e903b0aaf2799d546a1ff80468c1766a76", "observations": {"active_agent_minutes": {"reason": "UNMEASURED", "value": null}, "cache_tokens": {"reason": "UNMEASURED", "value": null}, "escaped_regressions": {"reason": "UNMEASURED", "value": null}, "expensive_runs": {"events": ["6661b0e8216164ad9c02972e1b04f3e4ec15239754a48abadb78fd3e64b2cbe9", "05c5b2b29d7d95345917393f980726ec62beb864b6d6f6958a5a03a1bc3991e9"], "value": 2}, "full_runs": {"events": ["07d8f4eb076b4db0c303f5917b82f30e853f5d35933117366a3be138d0c4ee02", "c69d75fcc5fc4a5b1bb3eae2d79a084b257a10aa37ae36a1ddd8b672a962fa0f"], "value": 2}, "intent_to_archive_minutes": {"reason": "UNMEASURED", "value": null}, "output_tokens": {"reason": "UNMEASURED", "value": null}, "post_review_code_churn": {"reason": "UNMEASURED", "value": null}, "review_findings": {"reason": "UNMEASURED", "value": null}}, "progress": [{"completed": 4, "total": 7}, {"completed": 4, "total": 7}, {"completed": 4, "total": 7}, {"completed": 4, "total": 7}], "roles": [], "schema": "lifecycle-summary/1"} |
| relative selections vs absolute output, device JSON captures (probe_relative.py) | base ea18fab: 20 of 1,002 differ (QFX5120 25.2R2-S1.5 `{}` spellings); head: 0 of 1,002 |
| device corpus base vs head (tools/compare_device_outputs.py) | 0 of 96 conversions differ |
| canonical full checkpoint | 10a53b2: every check passed, 352 s, 13,323 passed / 22 xfailed / 37 skipped, coverage 93.12 %, schema-25.2 tiers exit 0; c929c31: failed only the schema tiers (runtime identity not prepared) |
| review findings | Test/Challenge 2 binding + 11 advisory, 4 spec challenges on the draft delta; Reviewer 1 binding + 4 advisory, all records; all resolved; pending owner decisions C5, TC8, TC12, R1, R5, C8 |
| Context expansion: src/junoscfg/display/path_filter.py | display kernel's `filter_dict_by_path` decides what a relative selection hands the writer |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
