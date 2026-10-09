## Why

Two conversion helpers duplicate behavior already owned by the dict-IR pipeline:
an unused direct JSON-to-YAML renderer and an XML-output module that only raises.

## What Changes

- Scope the beta compatibility promise to the `consumer` and `cli` surfaces
  the owner requires: the production collection's top-level imports and its
  documented CLI pipelines.
- Delete `display.to_yaml.json_to_yaml()` and its direct implementation tests.
- Delete `convert.output.xml_output`.
- Raise the same XML-output `NotImplementedError` at the existing
  `junoscfg.convert.from_dict()` package door.
- Preserve `convert_config(..., to_format=XML)` and `from_dict(ir, "xml")`
  exception types and messages.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- None; behavior is preserved, so specs are skipped.

## Non-goals

- Implementing XML output or changing XML input.
- Changing JSON, YAML, or dict-IR rendering behavior.

## Impact

The change removes two secondary package APIs and their stale documentation.
It does not change the newly named `consumer` or `cli` surfaces and adds no
dependency. Direct importers migrate from `json_to_yaml()` to
`convert_config(..., from_format=Format.JSON, to_format=Format.YAML)` and from
the XML-output submodule to `junoscfg.convert.from_dict()`.
