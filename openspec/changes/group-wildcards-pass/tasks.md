## 1. Verification

- [x] 1.1 Acceptance tests (fail on the merge base `1ebeed9` by design, pins named in `evidence-freeze.md`): `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern`, the strict xfail `test_a_wildcard_group_name_passes_the_group_rule` (removed when it passes) and the `<` filters of C6, `tests/contract/test_every_rule.py::TestEveryRule::test_a_match_all_wildcard_name_passes`, door rows in `tests/contract/test_every_message.py`, `tests/corpus/test_device_anonymization.py::TestEveryCaptureAnonymizes::test_every_wildcard_name_passes`.
- [x] 1.2 Independent Test/Challenge on these tests (high risk floor): `test-challenge.md`; findings F1–F9 ruled by the orchestrator, all accepted and applied (S2, S3, probe P10).

## 2. Change

- [x] 2.1 `anonymize/walker.py`: an entry's key field holding a wildcard: `*` alone passes; other text goes to the rules inside its brackets; each name the walk hands the rules is recorded; a wildcard whose selection changes, or whose text a rule claims and leaves, is named by schema path.
- [x] 2.2 `anonymize/revert.py`: a wildcard reverts the text inside its brackets (a whole-octet address pattern through its prefix). `anonymize/__init__.py`: `AnonymizeResult.patterns`. `anonymize/rules`: `Rule.wildcard`, the IP rule's whole-octet patterns (S2), the sensitive-word rule's words behind a class (S3).
- [x] 2.3 `convert/__init__.py`: one `anonymize:` warning per path, path and count only.
- [x] 2.4 Contract (`anonymize/CONTRACT.md`), CLI guide, changelog, patch 0.20.1; timing record.

## 3. Review and evidence

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it: fresh Reviewer (`review.md`), CHANGES REQUIRED at a4eb20e, fixes at 79b44a3, APPROVE at b2bc5d3.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
