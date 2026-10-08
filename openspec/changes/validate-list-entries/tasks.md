## 1. Tests

- [x] 1.1 `tests/test_schema_generator.py`: four generator-level tests — the
  array form carries `items` of `null | string` and the container type loses
  `string`; a transparent container's `items` admits its child's entry schema;
  `^@` is named in `patternProperties`; `required` is absent. The existing
  `test_mandatory_in_required` asserted the opposite of the delta and is
  rewritten as `test_mandatory_is_a_warning_not_a_schema_requirement`, with the
  reason in its docstring — the proposal declares the break, so the test is
  inverted rather than weakened or deleted.
- [x] 1.2 `tests/test_round_trip_validates.py`: `TestTheSchemaStillRejects`,
  the plan's six probes against the shipped schema, plus the two positive
  guards (a transparent container keeps its child; `@` attributes validate).
- [x] 1.3 `TestFragmentsWithoutMandatoryFieldsStayValid`: the three lines the
  first attempt broke, each omitting a mandatory field, each must validate.
- [x] 1.4 Seen to fail before implementation: 12 failed, 34 passed — the five
  generator tests and the seven artifact probes fail, every guard passes.

## 2. Implementation

- [x] 2.1 `_container_schema`: type `["object", "null", "array"]`; `items`
  of `null | string`, or `anyOf` with the transparent child's schema;
  `^@` in `patternProperties` for both variants; no `required`.
- [x] 2.2 Regenerate `junos-json-schema.json.gz` and `junos-yaml-schema.json.gz`
  from the bundled 25.2R2 structure tree with `write_json_schema`; assert each
  artifact's hash changed before trusting any test result. Both changed; the
  grammar, tree and metadata did not; a second write is byte-identical.
- [x] 2.3 Full suite green: 1,576 passed, 72 skipped, 2 xfailed; the twelve
  phase-4 tests pass. Mutated in turn with the artifacts regenerated under
  each and their hashes confirmed changed: `items` dropped → 7 failed;
  transparent branch dropped → 2; `^@` dropped → 3; `string` back in the
  container type → 2. Restored; both hashes back at the new base.
- [x] 2.4 Device-truth fixtures: 4 of 4 pairs pass, none skipped — the
  synthetic pair and the three real ones (both bordergw subtrees,
  uplink-failure-detection). Examples: all validate, via
  `test_the_example_configuration_round_trips` in both formats.
- [x] 2.5 Version 0.11.0 in `pyproject.toml`, `src/junoscfg/__init__.py` and
  `tests/test_cli.py`; `retires.md`, `checklist.md`,
  `changelog.d/+validate-list-entries.bugfix.md`; `agent-ready codemap slice`
  re-cut (12 modules listed).
- [x] 2.6 `pre-commit run --all-files`: all five hooks pass. `openspec
  validate validate-list-entries --strict`: valid. `agent-ready check`: every
  gate passes except `stage griffe` and `lane`, both structural and unchanged
  by this change — the branch carries eight live changes and griffe compares
  against `master`; both clear at the archive. Committed and tagged `v0.11.0`.
