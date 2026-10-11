## 1. Verification

- [x] 1.1 Acceptance tests (fail on the merge base `b8e6fc1` by design, pins named in `evidence-freeze.md`): `tests/contract/test_every_message.py` (the door law: 32 doors anonymized, 31 without anonymization, the debug level, audit), `tests/unit/anonymize/test_integration.py::TestAnonymizeLeavesItsInputAlone` and `TestContentTheWalkCannotPlace::test_the_warning_names_each_shape_it_replaces`, `tests/unit/anonymize/test_as_number_rule.py::TestAsNumberConflictDetection::test_no_warning_pairs_an_original_with_its_replacement`, `tests/unit/anonymize/test_ip_rule.py::TestAPassThroughCollision`, the pin `TestTheLeafsTypeAnswers::test_an_address_on_an_enum_only_leaf_is_replaced`.
- [ ] 1.2 Independent Test/Challenge on these tests (high risk floor): `test-challenge.md`.

## 2. Change

- [ ] 2.1 `convert/field_validator.py`: `FieldValidator(withhold_values=True)`: one helper writes each value-quoting message; `UNPLACED` texts withheld there. `convert/__init__.py`: `_withhold_unplaced` goes; a refusal to read the input in an anonymized run is raised without its text; the `anonymize:` warning's wording.
- [ ] 2.2 `convert/output/{__init__,structured_output}.py`: `from_dict(..., withhold_values=...)`; the dropped-tag note gives its count.
- [ ] 2.3 `anonymize/__init__.py`: copy on entry. `rules/as_number.py`: no warning pairs an original with its replacement. `rules/ip.py`: a pass-through collision is raised without the addresses.
- [ ] 2.4 `cli.py`: `-v` in an anonymized run prints each error's line, its text and path withheld; `--anonymize-log-level` help names what debug prints.
- [ ] 2.5 Contracts, docs (CLI guide, getting-started/README unchanged in substance, generated CLI reference), changelog, minor 0.20.0.
- [ ] 2.6 Timing of the copy on entry: the largest configuration and a synthetic list, base and head.

## 3. Review and evidence

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
