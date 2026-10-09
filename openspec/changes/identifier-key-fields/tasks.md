## 1. Verification

- [x] 1.1 Phase-4 acceptance tests written and failing before the change (177 failed at 6f8018f).
- [x] 1.2 Owner-approved rewrites (phase-4 question 1): the attributes-match, flat-entry and `fe` tests rewritten to the keyed form, intent kept.
- [x] 1.3 Owner question 3: the `o` digest pin replaced by a test of the rule (`o` where the dump flags `oneliner`, and on the filter lists the fix names).
- [x] 1.4 Owner question 4: `test_name_keyed_lists_keep_name` compares the generated schema by dict equality.
- [x] 1.5 Owner question 8: the grammar rejects a numeric `list-type`; seen failing before the grammar change.
- [x] 1.6 The proposal's identifier counts reproduced by a test on the dump.
- [x] 1.7 Device round 4 (owner-approved): R, S and T in `tests/data/captures/keyed-entries-route-filter.*` and the T tests; a key keyword goes either side of the positional values.

## 2. Change

- [x] 2.1 Parser keeps every element a sequence declares and records the key fields.
- [x] 2.2 Structure tree carries `k`; `fe`, `values-only`, `_v<n>` and `_fix_attributes_match_oneliner` retired; fix counts in the docs.
- [x] 2.3 Kernel `entry_keys()` (and `entry_key_names()`); `ENTRY_KEY_OVERRIDES`, `get_flat_entry_config`, `FLAT_ENTRY_ELEMENTS` removed and banned.
- [x] 2.4 Set reader, set and structured writer, field validator, schema generator, grammar generator, audit walker and fixture, anonymize walker, XML reader read `entry_keys()`.
- [x] 2.5 Artifacts regenerated with `--regen-schema`, committed separately.
- [x] 2.6 Docs: keyed-entries convention, validation guide, API page.
- [x] 2.7 Version 0.15.0 and the towncrier fragment.
- [x] 2.8 Full check, declared-break measurement, collection test suite.
  - Full check at 4305435: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full` exit 0, "every check passed" (1838 passed, 93 skipped, 1 xfailed).
  - Declared break: 2,558 of 10,792 list-entry objects in the regenerated JSON schema carry no `name` property (0.14.0: 0 of 8,394).
  - Collection 347715a against this checkout: 33 passed.

## 3. Review and evidence

- [ ] 3.1 Complete the fresh-session review and write `review.md`.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
