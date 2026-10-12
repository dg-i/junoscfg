| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 174, "binary_files": 0, "files": 4, "removed": 6} |
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
| generated lifecycle evidence | {"archived": false, "base": "630a5c958b28354787a58dfe416af2fe165d0a09", "carry": {}, "change": "synthetic-schema-check", "checks": [{"checkpoint": "ce8e32866390eb7cad39b9c4073de55483aee2bdc66438cae84c22f0f4a5382f", "duration_ms": 265213.2666250109, "evidence": ".agent-ready/verification/16412f316dae4d59bb5eedb48764cf1a.json", "exit_status": 1, "reused": false, "tier": "full"}, {"checkpoint": "502013aac1a9b4a7983ee2505f806d742437d38fb1cdc804fc99d3b3da134210", "duration_ms": 266007.8606249881, "evidence": ".agent-ready/verification/1e4657a989e2466f962b427235fe1293.json", "exit_status": 0, "reused": false, "tier": "full"}], "head": "d4311345d62d53474cbcaae9d6a8f78df4a0d46e", "ledger_sha256": "45efc6bde5f8478989d39ad408a819f75393feaac8a659f74fb35cf65f672d81", "observations": {"active_agent_minutes": {"reason": "UNMEASURED", "value": null}, "cache_tokens": {"reason": "UNMEASURED", "value": null}, "escaped_regressions": {"reason": "UNMEASURED", "value": null}, "expensive_runs": {"reason": "UNMEASURED", "value": null}, "full_runs": {"events": ["b01ad4eb81694da6642a29826249cd8756f6af61c94f0a28fafe05ff4694f0d0", "197da14b1e8e5942448f53df39a37095b31fd740d30cf450137b31e775cbc279"], "value": 2}, "intent_to_archive_minutes": {"reason": "UNMEASURED", "value": null}, "output_tokens": {"reason": "UNMEASURED", "value": null}, "post_review_code_churn": {"reason": "UNMEASURED", "value": null}, "review_findings": {"reason": "UNMEASURED", "value": null}}, "progress": [{"completed": 4, "total": 6}, {"completed": 4, "total": 6}, {"completed": 6, "total": 6}], "roles": [{"referent": "d4311345d62d53474cbcaae9d6a8f78df4a0d46e", "role": "Reviewer", "verdict": "APPROVE"}], "schema": "lifecycle-summary/1"} |
| Focused synthetic pipeline measurement | Builder pytest total 0.11s, call 0.03s; independent Reviewer pytest total 0.09s, call 0.03s, tool-reported command wall 0.143s. These observed runs support the target on this machine, not a five-second guarantee or timing assertion. Sources: tasks.md and exact Reviewer report review.md. |
| Successful ordinary full checkpoint | 266.007860625 seconds native duration; 10427 passed, 13 skipped, 20 xfailed in 236.68 seconds pytest duration. Receipt .agent-ready/verification/1e4657a989e2466f962b427235fe1293.json, independently inspected by Reviewer. No real-schema tiers selected or claimed qualified; synthetic coverage does not replace them. |
| Failed full versus admission refusal | Prior full receipt 16412f316dae4d59bb5eedb48764cf1a recorded exit 1 after 265.213266625 seconds: ordinary tests passed but towncrier required a misc fragment. The fragment repaired that requirement before the successful full. Initial parked-readiness refusal ran no tests. The lifecycle records two actual full attempts and no expensive schema attempts. |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
