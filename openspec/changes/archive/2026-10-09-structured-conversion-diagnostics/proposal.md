## Why

Conversion currently writes validation, anonymization, and rendering messages
directly to process stderr, so in-process callers cannot reliably capture,
route, or suppress them.

## What Changes

- Add immutable conversion-result and diagnostic value objects.
- Add opt-in `convert_config_result()` and `pipeline_result()` package-door APIs
  while keeping `convert_config()` and `pipeline()` string returns unchanged.
- **BREAKING API BEHAVIOR:** stop all conversion-path library stderr writes;
  legacy string APIs discard diagnostics and structured-result callers receive
  them explicitly.
- Make the CLI call the structured-result API and render the same warning,
  debug, and note text to stderr with unchanged exit behavior.
- Thread a diagnostic sink through anonymization and structured rendering
  rather than introducing global capture state.

## Capabilities

### New Capabilities

- `conversion/diagnostics`: Structured conversion results and caller-owned
  diagnostic rendering.

### Modified Capabilities

- None.

## Non-goals

- Do not change validation strictness, diagnostic wording, or CLI exit codes.
- Do not convert Python `warnings.warn()` calls outside the conversion path.
- Do not change the return type of either existing package-door function.

## Impact

Top-level and conversion APIs, anonymization walking, output dispatch,
structured rendering, the CLI, interface declarations, docs, and tests change.
No dependency, override, fallback, or environment lookup is added.
