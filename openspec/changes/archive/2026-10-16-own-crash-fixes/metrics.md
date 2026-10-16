| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 875, "binary_files": 0, "files": 25, "removed": 129} |
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
| generated lifecycle evidence | {"archived": false, "base": "4dc114ee7dfb959e29a89d24897fce9443e18549", "carry": {}, "change": "own-crash-fixes", "checks": [{"checkpoint": "e3d13bda77d4c8a4de4b7574150092625dc0d44f6ede100b485b5c8e7cb5a842", "duration_ms": 228452.48012500815, "evidence": ".agent-ready/verification/8750b3baa4e144b6bf9ec18510e932f7.json", "exit_status": 1, "reused": false, "tier": "expensive"}, {"checkpoint": "798ad4783693e1c903d2682684e5ee0d63afa1f848deaa02e78a67b6c2fa0a2e", "duration_ms": 220560.6537499698, "evidence": ".agent-ready/verification/265236952d2a44aca65dd4bb657cd78c.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "86ac98d76d9be58c0a466a8ffb21e73de934f480d46364214a5fb2673161145e", "duration_ms": 16312.125624972396, "evidence": ".agent-ready/verification/0b4d6c43f5184af4863b35012c25b944.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "e5ea2be7d460159a42058a2057b2e05311582f4bd56910122d26a9b933692df8", "duration_ms": 263233.4153340198, "evidence": ".agent-ready/verification/0fb668c8add243c08ef9a656a6f85e49.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "ef1bb7af7806760300b083b41c1e8e8cf56867ff599f1665386299200775e017", "duration_ms": 49285.67583300173, "evidence": ".agent-ready/verification/7b3405e1a92549eb8b1b7093e5a5f8e2.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "10916ff6df575672bacef85ad51ef1170178340228ef064074776c073907cf4f", "duration_ms": 342348.44279207755, "evidence": ".agent-ready/verification/54c477fe4b984297ae872a2eaabc9f43.json", "exit_status": 0, "reused": false, "tier": "full"}], "head": "0cc36491ea3b6c1fdcd74b5b6454a4a4edf707bc", "ledger_sha256": "a4c43015f5212d5a15577e1313f3a798af06dfdb94448e5c18a146c6bafa0bbc", "observations": {"active_agent_minutes": {"reason": "UNMEASURED", "value": null}, "cache_tokens": {"reason": "UNMEASURED", "value": null}, "escaped_regressions": {"reason": "UNMEASURED", "value": null}, "expensive_runs": {"events": ["4defebbd5201c9ab661c32e5630813a0ae1a45a77d4301d2605c9615ae0545cf", "bdca16e3321f0ae16c80312b2cae78cd8b4ae5cc7cbb1fc52b2628bb2b68de9e", "611559ebfb46f62a10eeb1ddb0416d506ac706dac29adccc77de411528d3aa0b", "70fce957c86af91edecc8ed9485f34f517e07081187f74f055f86d2488134dda", "2962ec4bc085944d866bca8ab5646c9f7fcc2cb63baa2c898bf21eaf0287fa34"], "value": 5}, "full_runs": {"events": ["97f8989e299c9d360b2f8711b07d03fc02b6ee1127a2cadbbcc4427a320fe2d7"], "value": 1}, "intent_to_archive_minutes": {"reason": "UNMEASURED", "value": null}, "output_tokens": {"reason": "UNMEASURED", "value": null}, "post_review_code_churn": {"reason": "UNMEASURED", "value": null}, "review_findings": {"reason": "UNMEASURED", "value": null}}, "progress": [{"completed": 4, "total": 11}, {"completed": 4, "total": 11}, {"completed": 4, "total": 11}, {"completed": 7, "total": 10}, {"completed": 7, "total": 10}, {"completed": 7, "total": 10}], "roles": [], "schema": "lifecycle-summary/1"} |
| selections base vs head (probe_selections.py, device JSON captures, 2,875 selections x 5 writers x absolute/relative) | 25 absolute outputs differ, each adding exactly the last key's sibling annotation (21 object outputs verified, verify_tag_only.py); 2 relative set outputs differ (SC1, the `l3vpn` flag); all others identical |
| depth matrix base vs head (depth.py, xml-list-depth) | base: JSON RecursionError from 450 (yaml) / 600 (set, structured) / 1,600 (every writer), repeated XML from 164 XML levels (yaml); head: JSON and XML refused with ValueError past 64 levels in every writer, no RecursionError |
| reader cost on the largest capture (perf.txt, 220 KB) | JSON to_dict 2.8 to 4.2 ms, json to set 9.3 to 10.5 ms; XML to_dict 16 to 18 ms |
| canonical full checkpoint | 85df3e9: every check passed, exit 0, 347 s; suite 13,703 passed / 22 xfailed / 37 skipped (10 workers, 91 s); schema-25.2 qualification and generation exit 0. After review fixes (records and message-door rows, 0cc3649): affected tests 308 passed, `agent-ready check --set fast` passed (247 s) |
| red runs | tests at 5c513a9 against base: 120 failed for their defects (tc/red-full.txt); final tests against base: 183 failed (red-run-2.txt); Reviewer: 175 of 316 selected head tests fail at base, all pass at head |
| review findings | Test/Challenge: 7 binding + 3 advisory, 4 spec challenges (SC2, SC3 resolved in the change; SC1 pending owner; SC4 already backlogged); fresh Reviewer: Merge after fixes, 1 binding (records) + 6 advisory; pending owner decisions: SC1, A1, A2, A3, C3, SC3, TC7 observation |
| Context expansion: src/junoscfg/input.py | the kernel boundary `find_non_json_value` (key rule, reader label, `META_KEY_PREFIXES`) |
| Context expansion: src/junoscfg/display/path_filter.py | `filter_dict_by_path` rebuilds an absolute selection (kernel zone) |
| Context expansion: src/junoscfg/validate/json_yaml_validator.py | yaml and JSON validation report what their readers refuse (schema zone) |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
