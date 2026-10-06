## Why

`junoscfg schema makedoc` has never worked. `cli.py:726` imports
`junoscfg.validate.schema_doc`, a module that does not exist in the tree or
anywhere in git history, so every invocation ends in `ModuleNotFoundError`.
`docs/guide/cli.md` documents it with worked examples, and `tests/test_cli.py`
asserts only that its name appears in `--help`, which is why nothing caught it.

## What Changes

- **BREAKING**: remove the `schema makedoc` command, its options and its
  documentation. Declared under `declared-break` as a `cli` surface removal
  raising the minor component.
- Replace the characterization test that pinned the crash with one that pins
  the command's absence.
- Remove `makedoc` from the help-text assertion in `tests/test_cli.py`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None; `skip_specs: true`. No requirement exists for a command that has never
run, and phase 6 recorded that this repository backfills no specs.

## Non-goals

- Writing `schema_doc.py`. A documentation generator for the schema tree may be
  worth having, but it is a feature, not this bug fix.
- Touching `schema generate` or `schema info`, which work.

## Impact

`src/junoscfg/cli.py`, `docs/guide/cli.md`, `tests/test_characterization.py`,
`tests/test_cli.py`. No library code, no dependencies. The Ansible collection
drives `convert`, `edityaml rename-root` and `edityaml ansibilize`, none of
which this touches.
