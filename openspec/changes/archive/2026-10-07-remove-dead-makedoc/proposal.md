## Why

`junoscfg schema makedoc` has never worked. `cli.py:726` imports
`junoscfg.validate.schema_doc`, a module that does not exist in the tree or
anywhere in git history, so every invocation ends in `ModuleNotFoundError`.
`docs/guide/cli.md` documents it with worked examples, and `tests/test_cli.py`
asserts only that its name appears in `--help` — and because the import is
function-local, `--help` worked and only execution crashed.

Something did catch it. mypy reports
`cli.py:727: Cannot find implementation or library stub for module named
"junoscfg.validate.schema_doc"` at the merge base, verified in a detached
worktree. It survived seven patch releases not because no tool saw it, but
because mypy was in no dependency group until onboarding phase 2 and is
CI-reported-but-non-blocking by the decision in
`docs/decisions/2026-10-06-adopt-mypy-strict.md`. That is the lesson worth
keeping.

## What Changes

- **BREAKING**: remove the `schema makedoc` command, its options and its
  documentation. Declared under `declared-break` as a `cli` surface removal
  raising the minor component.
- Replace the characterization test that pinned the crash with one that pins
  the command's absence.
- Remove `makedoc` from the help-text assertion in `tests/test_cli.py`.

## Capabilities

### New Capabilities

This change adds no capability; it removes one that never functioned.

### Modified Capabilities

No capability changes, so `.openspec.yaml` sets `skip_specs: true`. No
requirement was ever written for this command, and onboarding phase 6 recorded
that this repository backfills no specs for existing behaviour.

## Non-goals

- Writing `schema_doc.py`. A documentation generator for the schema tree may be
  worth having, but it is a feature, not this bug fix.
- Touching `schema generate` or `schema info`, which work.

## Impact

`src/junoscfg/cli.py`, `docs/guide/cli.md`, `tests/test_characterization.py`,
`tests/test_cli.py`. No library code, no dependencies. The Ansible collection
drives `convert`, `edityaml rename-root` and `edityaml ansibilize`, none of
which this touches.
