## Why

The suite grew by stacking: five layout schemes at once, one fix pinned in up
to 18 files, copy-pasted per-rule checks, a quarter of the tests past the
public doors, and 25 tests taking 99 % of the runtime because nothing cached
the compiled grammar or the loaded schemas. Review and owner interview:
`private_test_data/test-suite-review-2026-10-10.md` (owner, 2026-10-10).

## What Changes

- Product: `display.build_from_artifact` builds an artifact once per process
  while the file is unchanged; the set grammar and the JSON/YAML schemas go
  through it. `display.forget_loaded_artifacts` drops the caches for
  `--regen-schema`. Small public doors where a test needed an internal.
- Tests: `tests/unit/<package>/`, `tests/contract/` (laws over catalogues:
  format matrix, every reader, every anonymize rule, every validation door),
  `tests/corpus/` (evidence, ordered like the evidence hierarchy),
  `tests/tooling/`, `tests/support/` (helpers and catalogues). Bug-, phase-
  and change-named classes fold into the behaviour they guard; every case is
  kept, proven by `ledger-before.txt` → `ledger.md`.
- Workflow: affected tests on commit (pre-commit, so the fast set), the full
  set with branch coverage and a ratchet floor, CI from a locked test group
  with the coverage gate, a nightly `--jvd` job, publish after green CI, and
  a door check over `tests/`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- None: test ids named by specs move with their tests; no requirement changes.

## Non-goals

- A disk cache of the compiled grammar; a single CLI run still compiles once.
- Mutation testing.

## Impact

Tests throughout; `src/junoscfg/display/constants.py`,
`src/junoscfg/validate/{set_validator,json_yaml_validator}.py`; pyproject,
pre-commit, CI, developer guide. Patch bump. Timing: `pytest --durations=0`
before and after.
