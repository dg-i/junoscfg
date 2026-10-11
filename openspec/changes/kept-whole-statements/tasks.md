## 1. Verification

- [x] 1.1 Acceptance tests (fail on the merge base `f0bb6aa` by design): `tests/unit/convert/test_set_input.py::TestAKeptStatementHasARecordOfItsOwn` (OPEN-2 both orders for five bare keywords, NEW-C1 for `host-name` and `members` both orders, alone and in curly, OPEN-3 for statements and meta commands through every writer, the display door's constant); `tests/unit/convert/test_field_validator.py::TestALeafWithoutItsValueIsUnplaced` (five doors, strict and anonymization, six negative guards that pass on both sides); catalogue rows `a-bare-keyword-beside-the-node-it-names`, `a-leaf-without-its-value-beside-its-value`, `a-kept-statement-keeps-its-quotes` in `tests/support/shapes.py`. The tests that pinned the old key spelling, the quote loss or the false `UNPLACED` move to the record (C5); `TestApplyGroups::test_a_group_after_a_bare_one_is_placed` and `TestTokensTheReaderCannotPlaceAreKept::test_a_keyed_entry_after_a_bare_keyword_is_placed` replace the two `..._kept_too` tests.
- [x] 1.2 Independent Test/Challenge on these tests (high risk floor): `test-challenge.md`; F1–F8 accepted, dispositions in `review.md` (DEV-16 folded in, `anonymize()` refusal, malformed-record refusal, `edityaml` wildcards, stronger and wider cases, C5 challenge).

## 2. Change

- [x] 2.1 `src/junoscfg/display/constants.py` and its door: `UNPLACED_STATEMENTS`, `unplaced_record_problem()` on the lexer's `reads_as_one_statement()`. `src/junoscfg/convert/input/set_input.py`: `_keep_whole` and `_keep_meta_whole` write the record with the original tokens; a leaf without its value is kept whole. `convert/input/__init__.py` refuses a malformed record on read; `display/to_yaml.py` reads an empty XML leaf as `""` (DEV-16).
- [x] 2.2 `src/junoscfg/convert/output/dict_walker.py` (and the structured writer's note): every writer writes the record verbatim, after the level's placed nodes, and refuses a malformed one. `src/junoscfg/convert/field_validator.py`: each kept statement and each value-less leaf is `UNPLACED`. `anonymize()` refuses a record; the pipeline refusal withholds the text; `edityaml` wildcards skip it; `tools/device_differences.py` drops `xml-empty-value-lost` and the record is regenerated.
- [x] 2.3 Contracts and docs (and `src/junoscfg/anonymize/CONTRACT.md`): `src/junoscfg/convert/CONTRACT.md`, `docs/guide/validation.md`, `docs/architecture/conversion-bugfix-guide.md`; changelog fragment; minor bump 0.17.0 in `pyproject.toml`, `src/junoscfg/__init__.py`, `uv.lock`.

## 3. Review and evidence

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
