## 1. Verification

- [x] 1.1 Acceptance tests (fail on the merge base `3a0607f` by design, guards named in `evidence-freeze.md`): `tests/unit/anonymize/test_walker.py::TestTheWalkerReachesEveryPlacedValue`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers` (and the qualified-next-hop rows given the tree's leaf), `tests/unit/anonymize/test_group_rule.py::TestApplyGroupsIsAReference`, `tests/unit/anonymize/test_revert.py::TestRevertRestoresKeys`, `tests/unit/anonymize/test_integration.py::{TestGroupReferencesResolve,TestContentTheWalkCannotPlace,TestEveryDoorGivesOneAnswer}` and `TestKeyedEntriesSurvive::test_what_a_rule_once_missed_is_replaced` (strict xfail removed, `MISSED` gone), `tests/unit/convert/test_field_validator.py::TestATransparentContainersOtherChildren` and the three changed refusal tests (C4, C5), `tests/unit/cli/test_cli.py::TestAKeptStatementOnTheCommandLine::test_anonymizing_warns_without_the_statement`, `tests/contract/test_every_rule.py` (`_APPLY_GROUPS_DEFECT` removed, nested references in the catalogue), `tests/tooling/test_universal_statement_names.py` (names only in the group rule and the audit walker), `tests/corpus/test_device_anonymization.py`.
- [x] 1.2 Independent Test/Challenge on these tests (high risk floor): `test-challenge.md`; findings 1–9 ruled by the orchestrator and applied (S2, S3 in `review.md`, NEW-R9 carried to change 5b).

## 2. Change

- [x] 2.1 `anonymize/walker.py`: `schema_child`, transparent siblings, lists under containers, untyped key fields, content it cannot place (address words through the IP rule, schema paths returned).
- [x] 2.2 `anonymize/rules/ip.py`: type families (address, host, `ipprefix-only`, untyped), a value that starts with an address, text beside it kept, the list-name answer only for keys typed free text or `areaid`; `Rule.lexical` on the IP, password and sensitive-word rules. `rules/group.py`: claims `apply-groups[-except]`, Junos-reserved names pass, docstring.
- [x] 2.3 `anonymize/__init__.py`: `AnonymizeResult.unplaced`, the record refusal and `_replace_apply_groups` gone. `revert.py`: key words.
- [x] 2.4 `convert/__init__.py`: no refusal, `anonymize` warnings, `UNPLACED` messages withheld in an anonymized run. `convert/field_validator.py`: transparent siblings, lists under containers. `audit/walker.py`: `schema_child`.
- [x] 2.5 The pin re-pinned with each added entry explained; contracts, docs, changelog, minor 0.19.0.
- [x] 2.6 Measurement: every rule combination over the device captures and the examples (`combos.py`), base and head; timing.

## 3. Review and evidence

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it: fresh Reviewer (`review.md`), CHANGES REQUIRED at ab13794 and 7173e75, APPROVE at bb0c86a.
- [x] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head: base 3a0607f, code head bb0c86a.
- [x] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits: main specs applied before merge from a disposable worktree; run by the Builder under the owner's unattended-run brief, no product edit.
