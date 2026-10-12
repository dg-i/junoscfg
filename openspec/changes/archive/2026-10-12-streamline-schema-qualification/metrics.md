| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 707, "binary_files": 0, "files": 18, "removed": 116} |
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
| generated lifecycle evidence | {"archived": false, "base": "9bdd15dac7fd6997474c1979c92bb1c001c7e362", "carry": {}, "change": "streamline-schema-qualification", "checks": [{"checkpoint": "2af384c262e3dbbc450aba8dc2a6e75432d5cac4a06923c84823be1bef8ae95d", "duration_ms": 416483.460834017, "evidence": ".agent-ready/verification/f4feb69465f645f89e5ee5ac288026c5.json", "exit_status": 0, "reused": false, "tier": "full"}, {"checkpoint": "fe730c29be27db9c15e0c9a1ad244b3147193086a34336a558eab40dad724a7b", "duration_ms": 463.72316603083163, "evidence": ".agent-ready/verification/02f5fb04ecce40968aa8466cf12cdbe8.json", "exit_status": 1, "reused": false, "tier": "expensive"}, {"checkpoint": "a5e4c3c5d6cca80a8171410d8c21223a0fdc548589144b6c8d84ae9e624d1385", "duration_ms": 827289.2483750475, "evidence": ".agent-ready/verification/7170e0c7bfa4413db6c9d1ce45b574c7.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "90e36b11eaa7f3c84252e0402f10f724c37f92ddc1f01f4b83aa67a8c989ad4d", "duration_ms": 434390.34770801663, "evidence": ".agent-ready/verification/513895c247f749e4ac3a7def81392f03.json", "exit_status": 0, "reused": false, "tier": "expensive"}], "head": "779b322217dadd2a01a92dc3a5db7959c801a29e", "ledger_sha256": "de9832a4c79ecae71743caefa0685e437c29ee7937e77eb1fbe2fb136f2a3a6a", "observations": {"active_agent_minutes": {"reason": "UNMEASURED", "value": null}, "cache_tokens": {"reason": "UNMEASURED", "value": null}, "escaped_regressions": {"reason": "UNMEASURED", "value": null}, "expensive_runs": {"events": ["3a0ddca6c8a3cb096a2f1624af92727420a5a6ba18d82b26d3dac69698ac1043", "da83d359f25dc58e087ba80ae47f7331e6934a4dafade69ceefcda4271e630d4", "3c315892851d44f313c9e299b92e239a28b9a459ed78de282877dce23b2f9b2a"], "value": 3}, "full_runs": {"events": ["63e8b1b680e8522ed635acd20c3ed8602bb43905c2abe777abfe9281852ac2f4"], "value": 1}, "intent_to_archive_minutes": {"reason": "UNMEASURED", "value": null}, "output_tokens": {"reason": "UNMEASURED", "value": null}, "post_review_code_churn": {"reason": "UNMEASURED", "value": null}, "review_findings": {"reason": "UNMEASURED", "value": null}}, "progress": [{"completed": 7, "total": 11}, {"completed": 7, "total": 11}, {"completed": 7, "total": 11}, {"completed": 7, "total": 11}, {"completed": 11, "total": 11}], "roles": [{"referent": "779b322217dadd2a01a92dc3a5db7959c801a29e", "role": "Reviewer", "verdict": "APPROVE"}], "schema": "lifecycle-summary/1"} |
| Context expansion: src/junoscfg/display/constants.py | Artifact compression/key helpers are direct generator dependencies; retain their trigger coverage |
| Context expansion: src/junoscfg/display/__init__.py | Generator package door exports these helpers; include it in schema qualification triggers |
| Qualification performance observation | Assertion native command: 827.289248 seconds; generation double-pass native command: 434.390348 seconds; sum: 1261.679596 seconds. Qualification receipt span: 1262.804176 seconds. Current Python 3.13.15; historical 1897.69 seconds used Python 3.14.7. Observational comparison only; no causal percentage speedup claimed. Sources: native verification receipts 7170e0c7bfa4413db6c9d1ce45b574c7 and 513895c247f749e4ac3a7def81392f03; independently reviewed in review.md. |
| Executed work and build timings | Exactly 12 assertions passed, 36 measured pytest phases; two public builds measured 215.74688150000293 and 215.88739716698183 seconds. One assertion pass plus two public generation builds replaces two assertion passes plus a separately scheduled sentinel; the assertion fixture also generates artifacts. Sources: review.md and its hash-verified native logs. |
| Prerequisite refusals versus schema execution | Two admission refusals for uncommitted events.jsonl occurred before native execution; retained logs: private_test_data/schema-qualification-validation/qualify-admission-first.log and qualify-admission-second.log. One native runtime-mismatch refusal took 0.46372316603083163 seconds and ran no schema work (receipt 02f5fb04ecce40968aa8466cf12cdbe8). The generated lifecycle expensive_runs=3 counts this refusal plus the two successful schema commands, not three costly qualifications. |
| Timing interpretation | Pytest setup/call/teardown timings are observed phases, not isolated parser or generator stage profiles. First fixture setup includes parsing and fixes; JSON-schema validity includes writing and check_schema. No further benchmark reruns or generator changes were made. |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
