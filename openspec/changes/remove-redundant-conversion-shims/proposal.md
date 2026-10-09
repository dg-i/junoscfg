## Why

Two conversion helpers duplicate behavior already owned by the dict-IR pipeline:
an unused direct JSON-to-YAML renderer and an XML-output module that only raises.

## What Changes

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

The change removes two internal implementations and their stale documentation;
it removes no named API or CLI surface and adds no dependency.
