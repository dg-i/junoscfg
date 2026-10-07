## Terms

<!-- agent-ready:retires:begin -->
makedoc
<!-- agent-ready:retires:end -->

## Symbols

- `junoscfg.cli.makedoc`

## Dependencies

None. The command imported `junoscfg.validate.schema_doc`, which never existed,
so nothing is released by removing it.

## Requirements

None. `skip_specs: true`; no requirement was ever written for this command.

## Tests and fixtures

- `tests/test_characterization.py::TestSchemaMakedocIsDead` — replaced by
  `TestSchemaMakedocIsGone` rather than deleted, so the removal stays pinned.
- The `makedoc` entries in `tests/test_cli.py`'s help-text assertions.

## Docs

- `docs/guide/cli.md`, the `### schema makedoc` section and its three examples.
