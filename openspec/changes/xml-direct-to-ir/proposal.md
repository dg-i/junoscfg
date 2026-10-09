## Why

XML input already constructs the dict IR, serializes it as YAML, and immediately
parses that YAML back into the same IR. The round trip costs work and obscures
the single-IR architecture.

## What Changes

- Extract the existing XML walker result as one private shared display helper.
- Make `xml_to_yaml()` serialize that dict result.
- Make conversion XML input consume the dict result directly.
- Preserve XML parsing, errors, normalization, and public output exactly.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- None; this is a behavior-preserving refactor, so specs are skipped.

## Non-goals

- Changing accepted XML syntax, XML output, or the dict IR schema.
- Moving XML parsing across the established display-layer boundary.

## Impact

The XML input adapter and existing XML/YAML renderer share one private helper;
no public API, CLI, dependency, or configuration reader changes.
