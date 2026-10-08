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
- [x] 2.3 Full suite green: 1,578 passed, 72 skipped, 2 xfailed — eleven
  new phase-4 tests plus one rewritten, and two more from the review (2.7).
  Mutated in turn with the artifacts regenerated under each and their hashes
  confirmed changed: `items` dropped → 9 failed; transparent branch dropped
  → 2; the `groups`-only condition dropped → 2; `^@` dropped → 3; `string`
  back in the container type → 2. Restored; both hashes back at the new base.
  (First run, before 2.7: 1,576 passed and 7 / 2 / 3 / 2.)
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

## 3. Review (phase 6, fresh session) — applied

- [x] 3.1 Finding 1: the transparent-items branch fired on all 187
  `transparent:` nodes; only `groups` drops its wrapper in JSON. Conditioned
  on `node.name == "groups"`; one generator test and one shipped-artifact
  probe added; artifacts regenerated (JSON 983,770 → 960,792 bytes), hashes
  verified, second write byte-identical.
- [x] 3.2 Finding 2: `.openspec.yaml` migration text now says the error names
  the enclosing list, not the key; the formatter fix is a recorded follow-up.
- [x] 3.3 Findings 4, 5, 9: `retires.md` describes the `groups` escape's real
  target; 43,331 (a 24.4R0 figure) replaced by the re-taken 52,219 → 83,825 in
  source comment, test docstring and `retires.md`; checklist and test counts
  made precise. Findings 3, 6, 7 recorded in `retires.md`; 8 owner-approved.
- [x] 3.4 `review.md` written; patch bump to 0.11.1; commit; tag `v0.11.1`.
