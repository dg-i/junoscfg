| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 1847, "binary_files": 0, "files": 19, "removed": 24} |
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
| generated lifecycle evidence | {"archived": false, "base": "fb84ef7e4027ef49bf474eced30933d097463978", "carry": {}, "change": "schema-verification-evidence", "checks": [{"checkpoint": "3a4007689829893ff9232b157c7d212dc84d8933f055c81ee2e2936cdaac2c6e", "duration_ms": 1251290.236834, "evidence": ".agent-ready/verification/140a368e5ca949fd8876eca25ad279fe.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "3a56cd1b19e30a33c04b55c20f2e5b9ad13020b8b15a7add65231e78ee228cc9", "duration_ms": 1413780.5970420013, "evidence": ".agent-ready/verification/34df9023e50b443eaed2eb2493335f01.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "beda29425e880aae733515ed2b49a577f61d704bced6727aa9983472bb9d55cc", "duration_ms": 216751.64662499446, "evidence": ".agent-ready/verification/459f2983154543ed97f53a076a143519.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "b6baf90f87b4d29f7fc96023a35b26d01be444bb480c296c0073b5d29b1fcdec", "duration_ms": 1517706.9182500127, "evidence": ".agent-ready/verification/5ee47bca072c4e44b587e0d85dfd4819.json", "exit_status": 0, "reused": false, "tier": "expensive"}], "head": "5f0ba1e004514e5596c6cdf4cffaedc835c5c780", "ledger_sha256": "be8776936f3ebfa5fe8eabba87c09af0605d16d1e25a82c4bb236c16ae86578c", "observations": {"active_agent_minutes": {"reason": "UNMEASURED", "value": null}, "cache_tokens": {"reason": "UNMEASURED", "value": null}, "escaped_regressions": {"reason": "UNMEASURED", "value": null}, "expensive_runs": {"events": ["99bc1b428cef989d914722762531f67810ec0de30a7dd1ab4e0b53bbb0973123", "7957e7336494321047d2c2777be99aef21825ddc791d99bed41651a9cd69ae18", "fbe6514b44f624d86a9a5d1ec4649628428688c60d2ebf2bdbddaa87e09be93c", "979b7da95342ce26345f351b7c6aa4bcb3deeb03f1606c9850212de0daca678a"], "value": 4}, "full_runs": {"reason": "UNMEASURED", "value": null}, "intent_to_archive_minutes": {"reason": "UNMEASURED", "value": null}, "output_tokens": {"reason": "UNMEASURED", "value": null}, "post_review_code_churn": {"reason": "UNMEASURED", "value": null}, "review_findings": {"events": ["8d95be3a15b3fcd45da94efcea4e57aee0cdd763bf7af474e56af0b4feb4dc58", "519e86249a957e2fd55b4db17228c5c7f241e29733a281f07471c18f27eafcd3", "1ee898d4a04257be358bce724954b3360dfba0490e1c90c4532a5aa6e3ebbf2e", "b1df3a3cff77ffc1b741d9e5b8248ecad757d8da601dbbb0f7c8a09252499956"], "value": 4}}, "progress": [{"completed": 10, "total": 14}, {"completed": 10, "total": 14}, {"completed": 10, "total": 14}, {"completed": 10, "total": 14}], "roles": [{"referent": "15b87eea8117d692e719c8e3252d996666a6e67b", "role": "reviewer", "verdict": "REQUEST CHANGES"}, {"referent": "5f0ba1e004514e5596c6cdf4cffaedc835c5c780; real schema evidence deferred by explicit owner", "role": "reviewer", "verdict": "APPROVE scoped operational activation and bounded finalization/release handoff"}], "schema": "lifecycle-summary/1"} |
| Context expansion: tests/corpus/test_schema_data.py and tests/conftest.py | Schema execution/reporting crosses into test-fixture ownership; preserve suite assertions |
| Context expansion: tools/ and tests/tooling/ | Application-owned evidence adapter, not product runtime |
| Context expansion: pyproject.toml, .gitignore, mkdocs.yml and docs/how-to/run-a-batch-of-changes.md | Binding, inactive seeds, navigation and executable recipe |

Machine evidence and per-field provenance: [metrics.json](metrics.json).

Efficiency improvement: UNMEASURED. Generated lifecycle checks retain historical observations and do not establish current schema or activated canonical-full proof. Final selected 25.2R2 schema verification is owner-deferred until the whole-makeover checkpoint; see [release handoff](release-handoff.md).
