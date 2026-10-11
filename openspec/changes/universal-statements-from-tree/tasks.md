## 1. Verification

- [x] 1.1 Acceptance tests (fail on the merge base `dd7c8c4` by design, guards named in `evidence-freeze.md`): `tests/unit/display/test_universal_statements.py` (the helper, the floor, the tripwire, an old tree), `tests/tooling/test_universal_statement_names.py` (no module keeps the names or the six tables), `tests/unit/convert/test_set_input.py::TestApplyFlagsIsAContainerOfFlags`, `tests/unit/convert/test_field_validator.py::TestAUniversalStatementIsValidatedWithItsNode`, `tests/unit/convert/test_convert_api.py::TestUnplacedContentKeepsItsKeywords`, `tests/unit/validate/test_schema_generator.py::TestUniversalStatementsReachEveryContainer::test_the_tree_is_authoritative`, `tests/unit/validate/test_xsd_fixes.py::TestGroupDMissingElements::test_apply_flags_is_the_devices_container_of_flags`, `tests/corpus/test_shipped_artifacts.py` (`apply-flags` lines), catalogue rows `apply-flags-omit-as-the-device-writes-it` and `universal-statements-below-the-root` in `tests/support/shapes.py`.
- [x] 1.2 Independent Test/Challenge on these tests (high risk floor): `test-challenge.md`; findings 1–7 ruled by the orchestrator and applied (`review.md`, S1 pending the owner).

## 2. Change

- [x] 2.1 `src/junoscfg/display/constants.py` and its door: `schema_child`, `universal_statements`, `UNIVERSAL_STATEMENTS` as the floor's nodes; the Group-H helpers read the node only, the six tables go.
- [x] 2.2 Readers, writers and validation take the helper: `convert/input/set_input.py` (statements and meta commands), `display/to_yaml.py`, `convert/input/normalization.py`, `convert/output/{dict_walker,structured_output,json_output}.py`, `convert/field_validator.py`, `validate/schema_generator.py`.
- [x] 2.3 `validate/xsd_fixes.py`: `apply-flags` is a container of the presence flags `omit` and `replace`; artifacts regenerated with `junoscfg schema generate`; a second regeneration unchanged.
- [x] 2.4 Contracts and docs, changelog fragment, minor bump 0.18.0 in `pyproject.toml`, `src/junoscfg/__init__.py`, `uv.lock`.
- [x] 2.5 Measurement: head outputs against `base-device.json` and `base-jvd.json`; schema tier, JVD tier, device law.

## 3. Review and evidence

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it: fresh Reviewer (`review.md`), CHANGES REQUIRED at 81ff738, APPROVE at ff380dd.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [x] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits: main spec `schema-pipeline/universal-statements` applied before merge from a disposable worktree; run by the Builder under the owner's unattended-run brief, no product edit.
