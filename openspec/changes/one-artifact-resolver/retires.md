## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired.

## Symbols

`validate.validator._default_artifacts_dir` is removed; `resolve_artifacts_dir`
replaces it for every caller. `display.artifacts_dir` and
`display.resolve_artifacts_dir` are added and exposed. The module-level
`_schema_tree` singleton becomes `_schema_trees`, keyed on directory.

## Dependencies

No dependency is added or released by this change.

## Requirements

No requirement is retired; this change sets `skip_specs: true`.

## Tests and fixtures

No test is retired. `tests/test_artifact_resolution.py` adds ten: the four
precedence steps, that conversion honours the environment, that a missing
directory is None rather than a crash, that two directories keep separate
trees, that the override is restored on exit and on an exception, and that the
validator resolves identically.

## Docs

None yet. `docs/guide/cli.md` describes `--artifacts` as "path to validation
artifacts directory", which is now too narrow; the gzip change that follows
touches the same documentation and will correct it.
