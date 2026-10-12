# Independent Test/Challenge — ADEQUATE for STOP-T admission

Exact frozen HEAD: `4209679f3e33228b53b9ed25d173b3a9f0facf9c`. Declared base and measured merge-base: `69f072604e0585acd008cb4df3fc043dc515c182`. Fresh isolated TC received frozen intent/test/contracts and no Builder reasoning. This is preparation/test adequacy, not implementation approval or a green product claim.

Read the ten-line proposal, `.openspec.yaml`, instruction-integrity/preflight record, checkpoint, frozen 23-line test; relevant convert/display/test contracts and shared metadata walker/public pipeline/CLI handlers. This fix lane has no tasks.md or separate preflight.md: its frozen preflight is instruction-integrity.md plus checkpoint.md. No missing standard-lane task obligation is inferred.

## Measured evidence

- Public regression: exactly **12 failed**, every failure `DID NOT RAISE ValueError`; pytest **exit 1**, 0.19 s internal summary, 1.467240625 s measured process duration, UTC 2026-10-12T10:35:33.672158+00:00. `initial-regression.log` SHA256 fd36d3d661bde55f576d017befd9925006a914fda322ebf9e2aeb2bdc78fa31e. No skips/errors. This supersedes the earlier unmeasured pytest exit; the Builder wrapper's original exit remains UNMEASURED as historical evidence.
- Existing focused controls: **40 passed**, exit 0, 0.73 s internal summary, 1.566264 s process duration, UTC 2026-10-12T10:35:35.139744+00:00. `initial-controls.log` SHA256 ad7f00d5f2ed25808ab77b9147dcf3b9fc7ff9d26e0cfc24b840f82b9e26ad1c. These cover bare metadata commands, ordering, complete keyed entries, partial/surplus key retention with UNPLACED, whole named lists, set last-node placement, and existing curly/XML/API/CLI partial leaf-list refusals.
- Corrected private supplementary probes: **68 checks: 16 preservation passes and 52 expected future-refusal failures**, actual exit 1, 0.56327225 s, UTC 2026-10-12T10:36:05.377649+00:00. `probes.log` SHA256 e55d09756c2fe06e0f609fa45d2c7f588e69a192b80af47b856ce888932ff8dd. All 16 non-future controls pass: four shared verbs times bare host-name/apply-groups/members and quoted named-entry keys. Forty API failures accept unsupported selectors; twelve normal/strict/anonymizing CLI failures exit 0 instead of required exit 2. Quoted scalar values, quoted parent keys, surplus tails and a synthetic password present elsewhere in input are covered. All checks use package doors.
- Initial private probe mistakenly used nonexistent `--anonymize`, whose usage error generated four false passes. It is preserved as `initial-probes.log`; corrected `--anonymize-passwords` measurements above supersede it. No public test/source edit was needed.

`initial-execution.json` records raw argv, UTC, durations, real subprocess exits, SHA256 of logs and all tracked before/after hashes for regression/controls/initial probes. `execution.json` records the corrected private probe identically. Each measured snapshot has **1,286 tracked files**, unchanged hashes, clean status and unchanged HEAD. Source `_apply_meta` SHA256 is **3571df5ae220ab84d6c4a8895157c73c1b2a25dc6a2474c5d658ed7afb1b0d75** at both HEAD and base. No runtime edits, public edits, schema/ordinary/fast/full/network commands, capture edits or gate modifications occurred. Offline canonical `uv run --offline --locked --group dev` commands used owner-authorized isolated worktree/cache access.

## Challenge assessment

No concrete specification or acceptance correction is required. Frozen parameterization meaningfully catches one shared failure mode at both two-sibling leaf-lists and a scalar surplus target across all four metadata verbs. Bare whole-leaf/list targets and complete quoted/keyed entries remain accepted; malformed named-list keys remain retained whole/UNPLACED. The test docstring and proposal distinguish conversion IR limits from device syntax. Device evidence establishes only per-value deactivate rejection: held device-probe.out P9 line 681 and deactivate5.txt line 8 show syntax errors; no new claims for activate/protect/delete or broad device grammar are needed. The refusal must precede annotation and be value-free, as approved, while migration removes the unsupported command without dropping its selector into a broader operation.

## Implementation follow-through

Rerun the same public regression and focused controls after the admitted minimal repair; expected 12+40 green. Rerun private probes.py unchanged; expected all 68 green, exit 0. The future checks bind consumer to_dict/convert_config/convert_config_result, pipeline/pipeline_result (including strict), anonymizing API, and normal/strict/anonymizing CLI to clear refusal. Non-anonymizing ValueError must identify the scalar-leaf refusal without synthetic configuration markers; anonymizing errors must retain no cause/context/notes; CLI must exit 2 with Error and no traceback or markers. Current red evidence cannot establish post-fix error text/privacy, and this report does not claim it does.

Verdict: **ADEQUATE**, no unresolved correctness challenge. Root may admit the bounded source repair; fresh post-implementation review remains mandatory.

## Root admission

{
  "utc": "2026-10-12T10:38:27.399352+00:00",
  "verdict": "ACCEPT ADEQUATE for bounded phase5",
  "head": "4209679f3e33228b53b9ed25d173b3a9f0facf9c",
  "base": "69f072604e0585acd008cb4df3fc043dc515c182",
  "tracked_verified": 1286,
  "report_sha256": "e9bb128c6afbd4a6b1b5ae30616b3907bcc574ecae54a5676e747ce9f3bec265",
  "red_pytest_actual_exit": 1,
  "preservation_control_actual_exit": 0,
  "private_future_refusal_actual_exit": 1,
  "old_builder_exit_remains": "UNMEASURED",
  "unresolved_challenges": [],
  "permission": "Minimal owning scalar metadata branch refusal, valuefree before annotation; preservebare/keyed controls. No broadrefactor/schema/network. Renewsourcebase/operatorreadiness beforeordinary+fast; freshreview required."
}
