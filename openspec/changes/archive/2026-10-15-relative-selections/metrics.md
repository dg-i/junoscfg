| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 984, "binary_files": 0, "files": 17, "removed": 74} |
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
| generated lifecycle evidence | {"archived": false, "base": "d3ed6278e285261f784b7ef319e9db591fb1fa7f", "carry": {}, "change": "relative-selections", "checks": [{"checkpoint": "a1fafd304ed1ae7cd6fd71c86901dbc048af545643f60ed7dc43ec427ebbd820", "duration_ms": 259317.26300006267, "evidence": ".agent-ready/verification/116bbbc50f7a44d8b688483ee4d7fd20.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "5486c0f879d6916f2f20072d2148380d412d0b7e04cd6d626be7e97c5ff00fd8", "duration_ms": 50087.535790982656, "evidence": ".agent-ready/verification/3cc569098f734420b7f7c05f974b1af4.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "10360762862e3f3c591ece7ac15df86499c72a8ec863f6a877e8b01b4b5ba0c4", "duration_ms": 346186.30929198116, "evidence": ".agent-ready/verification/59f65811d5a64e0c8736b9d43bec131c.json", "exit_status": 0, "reused": false, "tier": "full"}, {"checkpoint": "032f659c1a2a9e4ca215064e4b623c91597d10d60d22676e05ebe851b53cb098", "duration_ms": 72384.58374992479, "evidence": ".agent-ready/verification/e78b3cfcdc64461494a6428a44c278f8.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "eb01b9bb56f86886ce1da26e3134bc532c66ca0e30a0932b737fd25e40f864bb", "duration_ms": 50688.175291987136, "evidence": ".agent-ready/verification/824bd8c1a56d4847845d0cb6020e9a9b.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "4b702c1233178c69dd654490cc9582d198c0d70f3e97c6ecd7af230a32519dbc", "duration_ms": 161086.45599999, "evidence": ".agent-ready/verification/6254e419d1bf4b07b31ea5ae0efcce4a.json", "exit_status": 0, "reused": false, "tier": "full"}], "head": "9d00c00b541760d83b2af97bc02292ffb7e6edc6", "ledger_sha256": "9a54101629c7e3a300423d09abf3bf11cfcd9fb9d39e12736ef6b03bfb028e5b", "observations": {"active_agent_minutes": {"reason": "UNMEASURED", "value": null}, "cache_tokens": {"reason": "UNMEASURED", "value": null}, "escaped_regressions": {"reason": "UNMEASURED", "value": null}, "expensive_runs": {"events": ["39185f7a2eab4cf1bfbf9be0576e4507fdc3573fb787d384c906603f00fab2f8", "6542ca3b9c0f3d9350de0fc36791a8004ff1ccaec84c76077b7f4d3e28068b21", "ab34c052c4365d35f76c39413aea52573539fcef567c0009b4043f63c1861f1c", "40e9890c9e90c12984688586aa5e2efb3982bdc76d17046ba908a98f6e608fc1"], "value": 4}, "full_runs": {"events": ["c1c1217a23f177986a2b7e323a8a9f82d0c1c3db12bae3a9feddc8a1bcffdfa5", "bc80f44eb386811b9eb8f4cdd89e6722012f3b141c306b8635e8094b3a04a13e"], "value": 2}, "intent_to_archive_minutes": {"reason": "UNMEASURED", "value": null}, "output_tokens": {"reason": "UNMEASURED", "value": null}, "post_review_code_churn": {"reason": "UNMEASURED", "value": null}, "review_findings": {"reason": "UNMEASURED", "value": null}}, "progress": [{"completed": 5, "total": 8}, {"completed": 5, "total": 8}, {"completed": 5, "total": 8}, {"completed": 6, "total": 9}, {"completed": 6, "total": 9}, {"completed": 6, "total": 9}], "roles": [], "schema": "lifecycle-summary/1"} |
| relative selections vs absolute output, device corpus base d3ed627 vs head (probe_all.py; 2,875 selections x writers) | json and yaml-new: 2 annotation differences at base, 0 at head (yaml 0); set and structured: the corpus law (TestRelativeSelections) holds at depth 5, 575 selections, 0 problems (law5-head.txt); base wrote `set interface ...` for 64 set and 110 structured mapping selections, a Python repr or nothing for 234 / 139 list selections |
| absolute output base vs head (tools/compare_device_outputs.py; catalogue) | device corpus 0 of 96; catalogue 0 of 2,435 |
| mutations of the final code (mutations.txt) | 17 of 17 caught; Test/Challenge 10 of 19 on the first tests, all survivors closed |
| canonical full checkpoint | ab46c51: every check passed, 350 s, 13,492 passed / 22 xfailed / 37 skipped, coverage 93.11 %, schema-25.2 tiers exit 0; follow-up f677934: every check passed, 166 s, 13,496 passed, coverage 93.17 %; after the correction review (tests only, 9d00c00): focused 2,196 passed, fast set passed |
| review findings | Test/Challenge 8 binding + 3 advisory, 5 spec challenges; Reviewer 2 binding + 5 advisory, then 3 advisory; all resolved; pending owner decisions: break call (patch), absolute leaf tag dropped by --path (pre-existing), display text filters' path rule |
| Context expansion: src/junoscfg/display/CONTRACT.md | display's text filters keep their own path rule (kernel zone, records only) |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
