## 1. Verification

- [x] 1.1 Acceptance tests (fail on the merge base `b8e6fc1` by design, pins named in `evidence-freeze.md`): `tests/contract/test_every_message.py` (the door law: 38 doors anonymized, 35 without anonymization, a failure no handler expects, the debug level, audit), `tests/unit/anonymize/test_integration.py::TestAnonymizeLeavesItsInputAlone` and `TestContentTheWalkCannotPlace::test_the_warning_names_each_shape_it_replaces`, `tests/unit/anonymize/test_as_number_rule.py::TestAsNumberConflictDetection::test_no_warning_pairs_an_original_with_its_replacement`, `tests/unit/anonymize/test_ip_rule.py::TestAPassThroughCollision`, the pin `TestTheLeafsTypeAnswers::test_an_address_on_an_enum_only_leaf_is_replaced`.
- [x] 1.2 Independent Test/Challenge on these tests (high risk floor): `test-challenge.md`; findings F1–F5 ruled by the orchestrator, all accepted and applied.

## 2. Change

- [x] 2.1 `convert/field_validator.py`: `FieldValidator(withhold_values=True)`: one helper writes each value-quoting message; `UNPLACED` texts withheld there. `convert/__init__.py`: `_withhold_unplaced` goes; a refusal to read the input in an anonymized run is raised without its text; the `anonymize:` warning's wording.
- [x] 2.2 `convert/output/{__init__,structured_output}.py`: `from_dict(..., withhold_values=...)`; the dropped-tag note gives its count.
- [x] 2.3 `anonymize/__init__.py`: copy on entry. `rules/as_number.py`: no warning pairs an original with its replacement. `rules/ip.py`: a pass-through collision is raised without the addresses.
- [x] 2.4 `cli.py`: `-v` in an anonymized run prints each error's line, its text and path withheld; `--anonymize-log-level` help names what debug prints; in an anonymized run a failure no handler expects prints its class only (ruling F2).
- [x] 2.5 Contracts, docs (CLI guide, getting-started/README unchanged in substance, generated CLI reference), changelog, minor 0.20.0.
- [x] 2.6 Timing of the copy on entry: the largest configuration and a synthetic list, base and head.

## 3. Review and evidence

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it: fresh Reviewer (`review.md`), CHANGES REQUIRED at 8860818, APPROVE at 5b8e22e, R7 fixed at e85e3b8.
- [x] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head: base b8e6fc1, code head e85e3b8.
- [x] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits: main specs applied before merge from a disposable worktree (20db29d); run by the Builder under the owner's unattended-run brief, no product edit.
