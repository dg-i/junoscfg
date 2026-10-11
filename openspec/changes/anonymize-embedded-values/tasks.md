## 1. Verification

- [x] 1.1 Acceptance tests (fail on the merge base `50b0a10` by design, pins named in `evidence-freeze.md`): `tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText` (the synthetic adversarial catalogue `_FREE_TEXT`) and `::TestAnApplyPathNamesConfiguration`, `test_revert.py::TestRevertUndoesEachReplacementOnce`, `test_sensitive_word_rule.py::TestEachSpellingHasItsPseudonym`, `test_as_number_rule.py::TestAWildcardUnderAsNumbersInStrings`, `test_identity_rule.py::TestAUrlUserIsAnIdentity`, `test_password_rule.py::TestAUrlPasswordIsASecret`, `test_ip_rule.py::TestIpAnonymizeIntegration::test_an_address_inside_free_text_is_replaced` (replaces `test_ips_in_strings_disabled_by_default`, which asserted ANON-P5).
- [x] 1.2 Independent Test/Challenge on these tests (high risk floor): `test-challenge.md`; T1-T12 ruled by the orchestrator, all accepted; S3-S7 recorded; the rulings' tests committed.

## 2. Change

- [x] 2.1 `anonymize/rules`: `Rule.spans` and `Rule.rewrite` (where a rule recognises a value by its shape, and its replacement); the IP rule's addresses, the identity rule's URL user, the password rule's hash words and URL password, the sensitive-word rule's words keyed by spelling, the AS rule's numbers outside addresses under `as_numbers_in_strings` and its wildcard report (NEW-R14).
- [x] 2.2 `anonymize/walker.py`: one chain for a value no whole-value rule takes, placed or not, that never offers a rule's text to another; a whole-value shape only where its rule takes the value; `apply-path` read against the tree.
- [x] 2.3 `anonymize/__init__.py`: the strings passes go; `anonymize/revert.py`: one pass, longest first, numbers between non-digits and outside addresses, addresses last.
- [ ] 2.4 After #8 merges and this branch is rebased (orchestrator ruling): the three `test_integration.py` edits named in the freeze.
- [x] 2.5 Contract (`anonymize/CONTRACT.md`), config docstring, CLI help of the in-strings options and the generated reference, CLI guide, developer guide, changelog fragment; before/after comparison with `--anonymize`; timing record.

## 3. Review and evidence

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
