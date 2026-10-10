## Why

The curly reader in `display/set_converter.py` reads lines, not tokens. A block
on one line (`system { host-name router1; }`) converts to nothing and validates
as empty, silently (OPEN-1); `a; b;` on one line becomes one value; `} x {`
drops a block; a trailing `## a; b` joins the value (NEW-B6); the device's
`{ /* OMITTED */ }` placeholder is written as a set line (DEV-18). Validation
reads curly through the schema-free `SetConverter.to_set()`: the device's
`hold-time up 2000 down 0;` is rejected (NEW-B5), and `to_set()` tags a
one-line statement's last node (OPEN-10, three strict xfails).

## What Changes

- One token lexer reads structured text; `statements()` keeps its shape.
  Malformed text (unbalanced braces or brackets, a statement without `;`, an
  open quote or comment) raises `ValueError`.
- The `/* OMITTED */` placeholder and an empty block are reported as warnings
  (conversion diagnostics, the CLI, `junoscfg audit`, `validate_structured`),
  never written. `to_dict()` and `structured_to_dict()` take an optional
  `diagnostic_sink`, as `from_dict()` and `anonymize()` already do.
- Structured validation checks the input's own tokens, one set statement per
  statement the conversion walk reads (new `junoscfg.convert.structured_set_lines()`),
  composed at the surface because `validate` may not import `convert`. The walk
  runs inside the existing `display.artifacts_dir()` scope; `resolve_artifacts_dir()`
  and `load_schema_tree()` are the only readers of that directory.
- Deprecated until the next minor, behaviour kept: `SetConverter.to_set()`,
  `StructuredValidator`, `JunosValidator.validate_structured()`.
- `omitted-block-emitted` leaves `known-differences.json` through the tool. Patch bump.

## Capabilities

### New Capabilities

- `conversion/structured-input`: the curly lexer, what it refuses and what it reports.
- `validation/structured-validation`: curly validated as conversion reads it, on every door.

### Modified Capabilities

- None.

## Non-goals

- Comment round trip and `annotate` (change 24); chained siblings on one set
  line (no device evidence); removing the deprecated doors (next minor); writer
  defects such as `overload timeout` (change 10).

## Impact

`display/set_converter.py` (zone kernel), `convert/input/`, `convert/__init__.py`,
`validate/structured_validator.py`, `validate/validator.py`, `__init__.py`,
`cli.py`, `tach.toml`, the device-law record. Reproduce with the deltas' tests
and `uv run python tools/device_differences.py` over `tests/data/device/`.
