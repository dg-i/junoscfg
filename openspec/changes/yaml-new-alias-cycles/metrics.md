| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 953, "binary_files": 0, "files": 28, "removed": 132} |
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
| generated lifecycle evidence | {"archived": false, "base": "87e14cd79eb4e0bd9b69d9990f882fe1beacfa77", "carry": {}, "change": "yaml-new-alias-cycles", "checks": [{"checkpoint": "d43d808bddefc36af616af35d22e46390f870f9a57fc3beaeba39184aabc7402", "duration_ms": 256864.40754204523, "evidence": ".agent-ready/verification/aaaa957da45b4eae925f07261d0cbbed.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "eed4dd32658d84873385c35404dcbdf2188ee1140f214278a56d1f9dedca9543", "duration_ms": 50162.07850002684, "evidence": ".agent-ready/verification/166e2944a0e74ce389fbe382f01e5d22.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "75a1244945d88cce42a0142f5570d5fce27ebefd8dd637f6c11e0ae8cddb7358", "duration_ms": 345416.78545903414, "evidence": ".agent-ready/verification/7f8fed4a05984d2f95e680dc22c92902.json", "exit_status": 0, "reused": false, "tier": "full"}, {"checkpoint": "a80824c4158b8f91210b2286801980f33178f0094d56387de19fd179dc3214fc", "duration_ms": 71321.39754097443, "evidence": ".agent-ready/verification/678dba1ab12f4d12850f6dcdc0022b9b.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "6d728ae34edcc1dc5dfc8e9ddd128eb1dca4396249a9dc364ebe4b74374a0082", "duration_ms": 50727.14149998501, "evidence": ".agent-ready/verification/228bd48bdc25437fb8bba06e945421f1.json", "exit_status": 0, "reused": false, "tier": "expensive"}, {"checkpoint": "518462ee431ed8210604a26c0e499b42f3ab180a3eda4aabe8827c0afbe2fa28", "duration_ms": 162027.4926670827, "evidence": ".agent-ready/verification/2233e92b260f46bb8801884ffe2c6cd2.json", "exit_status": 0, "reused": false, "tier": "full"}], "head": "084e1de376fc390b8dfd94411364726b43569492", "ledger_sha256": "325e3d192bcdc7240ab355d30d0ce9335a8746dc25e14f11723d0122ea702d99", "observations": {"active_agent_minutes": {"reason": "UNMEASURED", "value": null}, "cache_tokens": {"reason": "UNMEASURED", "value": null}, "escaped_regressions": {"reason": "UNMEASURED", "value": null}, "expensive_runs": {"events": ["833cc166e71af2162e027d0af504b76efc70fa16c247a549dbc505127606337a", "a2d519148d928de57142d2c47c094efdae95dd65d05899dcbbd8bfcd2d90c3a1", "438da157eacf9bf3727a904058b1ac2a771d0fa6ca71b46bbdf87caaa559c55e", "d9c5980bae029b37002e6973eb7b361cc9c5a9781a2053d2a890908c880d0655"], "value": 4}, "full_runs": {"events": ["ca34fb875ea3317eafa084d3c85dbd88c122f4af57bf57ea2984c056e0ccda70", "96c6ecb8587ea21ba22f3ef0e15fd9e8fac1fcf4edc38ee62dc9ac033f0aa6fc"], "value": 2}, "intent_to_archive_minutes": {"reason": "UNMEASURED", "value": null}, "output_tokens": {"reason": "UNMEASURED", "value": null}, "post_review_code_churn": {"reason": "UNMEASURED", "value": null}, "review_findings": {"reason": "UNMEASURED", "value": null}}, "progress": [{"completed": 5, "total": 8}, {"completed": 5, "total": 8}, {"completed": 5, "total": 8}, {"completed": 6, "total": 9}, {"completed": 6, "total": 9}, {"completed": 6, "total": 9}], "roles": [], "schema": "lifecycle-summary/1"} |
| alias refusals, door probe base 87e14cd vs head (po2.py) | shared block: refused at every yaml-new door at base, read written out at head; cycle: `alias` at base, `cycle` at head; 10^4 and 10^5 bombs refused at `l1.2` in about 1 ms; legacy `yaml` unchanged |
| device corpus base vs head (tools/compare_device_outputs.py; set, structured, json, yaml) | 0 of 96 conversions differ |
| canonical full checkpoint | 8fecbdd: every check passed, 349 s, 13,380 passed / 22 xfailed / 37 skipped, coverage 93.15 %, schema-25.2 tiers exit 0; follow-up b30dcd2: every check passed, 167 s, 13,382 passed, coverage 93.15 % |
| review findings | Test/Challenge 4 binding + 6 advisory, 3 spec challenges (SC-A to SC-C); Builder consequences 3; Reviewer 1 binding (code) + 5 advisory (records); all resolved; pending owner decisions SC-2, SC-A, SC-B, SC-C, C5, C8 |
| Context expansion: src/junoscfg/validate/json_yaml_validator.py | the validation door shares the kernel check (validation domain) |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
