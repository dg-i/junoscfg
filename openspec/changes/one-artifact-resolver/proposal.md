## Why

Conversion and validation each answered "where do the artifacts live?", and
had diverged. `JunosValidator` took an argument, then `JUNOSCFG_ARTIFACTS`,
then the bundle, and documented it. `display/constants.py` hardcoded the
bundled path and cached the tree in a process-wide singleton. So
`JUNOSCFG_ARTIFACTS` switched validation and was **silently ignored** by
conversion — the larger feature, reached by ten call sites across `convert`,
`anonymize`, `audit` and `field_validator`, and the one the downstream Ansible
collection renders through.

`--artifacts` had the same split at the CLI: it was passed to validation only,
so a user pointing at a schema they had generated got it for `-v` and the
bundled one for the conversion in the same command.

A documented option that works for half a tool is worse than one that does not
exist, because the documentation is true and nobody checks the other half.

## What Changes

- `display.resolve_artifacts_dir` is the one rule: explicit argument, then an
  invocation override, then `JUNOSCFG_ARTIFACTS`, then the bundle.
  `JunosValidator` delegates to it; its own `if/elif` and
  `_default_artifacts_dir` go.
- `load_schema_tree(artifacts_dir=None)` resolves the same way and caches per
  directory, so two schemas can coexist in one process. The singleton could
  not: an Ansible play touching two device roles got whichever tree loaded
  first.
- `display.artifacts_dir` is a **context manager**, not a setter, and the CLI
  closes it on the click context.

## Capabilities

### New Capabilities

None; this makes an existing one reach the whole package.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- `convert_config(artifacts_dir=...)`. Threading it to ten call sites inside
  `set_input` and `dict_walker` is real churn for a value that never varies
  within a call; the environment variable and the CLI flag already cover it.
- Moving the artifacts out of `validate/data/`. The kernel still reads a
  sibling layer's directory by path, which is the remaining smell, but moving
  35 MB is a packaging change and the gzip work lands next.

## Impact

`display/constants.py`, `validate/validator.py`, `cli.py`, `tach.toml`. Ten
tests. `JUNOSCFG_ARTIFACTS` and `--artifacts` now switch conversion as well as
validation; the Ansible collection's 33 tests pass with byte-identical output.
