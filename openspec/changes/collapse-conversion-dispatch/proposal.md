## Why

`convert_config()` routes every supported pair through twenty private wrappers
that only repeat arguments already known to the caller. This duplicates the
unified pipeline's dispatch surface and makes adding or auditing formats harder.

## What Changes

- Route supported non-XML-output pairs directly through `_pipeline_convert()`.
- Replace the string-valued converter table with an explicit supported-pair set.
- Remove the twenty private format-pair wrappers.
- Preserve normalization, validation, strict mode, anonymization, path filtering,
  exceptions, and the public `convert_config()` signature.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- None; this is a behavior-preserving refactor, so specs are skipped.

## Non-goals

- Changing supported input or output formats.
- Centralizing format detection or moving path filtering to the IR boundary.
- Changing either public conversion package door.

## Impact

The change is confined to `src/junoscfg/__init__.py`, its contract and developer
guide, and focused conversion tests. It removes no public API and adds no
dependency or configuration reader.
