| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 32, "binary_files": 0, "files": 3, "removed": 0} |
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
| generated lifecycle evidence | {"archived": false, "base": "6a956c1dbf31e7c6f32b7d2bb214a629f9db3951", "carry": {}, "change": "xml-status-and-todo", "checks": [{"checkpoint": "bc6993e3c0cebe89e487f0cc9e33bc2f98ab3f23dc7b26a94fafb34a7e773e74", "duration_ms": 8503.194083052222, "evidence": ".agent-ready/verification/d79f6add65c6407a97a5971e03967e86.json", "exit_status": 1, "reused": false, "tier": "full"}, {"checkpoint": "2ecbb7ef1d20c75513c7b6318fe3863ae8231e3ffae5cd30b51cd163d377358e", "duration_ms": 8542.686166008934, "evidence": ".agent-ready/verification/3c2b579466a047ad8a57c6d8f9a781f1.json", "exit_status": 0, "reused": false, "tier": "full"}], "head": "adfa8d8719504327d85509ff1a159cce616ebc0a", "ledger_sha256": "f9a69920dbb60b146d219384e0ac023455a4b5d97ccc6301ec7558cf328c5b31", "observations": {"active_agent_minutes": {"reason": "UNMEASURED", "value": null}, "cache_tokens": {"reason": "UNMEASURED", "value": null}, "escaped_regressions": {"reason": "UNMEASURED", "value": null}, "expensive_runs": {"reason": "UNMEASURED", "value": null}, "full_runs": {"events": ["ca4b97410e4cf273395dbe2fa38f9e975e818e8a5fe4fa5d56a04fe4eb124cfe", "e836e14da2ff8342b93852c5c52fa3ec5ca7aab557b19c83c776c8a0ebac406b"], "value": 2}, "intent_to_archive_minutes": {"reason": "UNMEASURED", "value": null}, "output_tokens": {"reason": "UNMEASURED", "value": null}, "post_review_code_churn": {"reason": "UNMEASURED", "value": null}, "review_findings": {"reason": "UNMEASURED", "value": null}}, "progress": [{"completed": 8, "total": 12}, {"completed": 8, "total": 12}], "roles": [], "schema": "lifecycle-summary/1"} |

Machine evidence and per-field provenance: [metrics.json](metrics.json).

Capture provenance: immutable base `6a956c1dbf31e7c6f32b7d2bb214a629f9db3951`, reviewed-docs/QA/root-report commit `adfa8d8719504327d85509ff1a159cce616ebc0a`. Three document paths only; no runtime or dependency change. Native lifecycle report retains the initial failed and later successful checkpoint events with their native durations; the separately retained root full-wrapper receipt records9.841091s at source proof3b507d195413ba18d7aa8005f2c040a8ff3899a6. These are distinct measured sources, not substituted durations or new runs. No independent review, usage, human-effort, efficiency, XML correctness/qualification or archive completion is inferred. Missing observations remain UNMEASURED. XML functional work is deferred. Actual merge/archive/version/tag/cleanup remains pending root only.
