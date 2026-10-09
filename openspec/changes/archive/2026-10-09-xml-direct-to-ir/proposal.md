## Why

XML input already constructs the dict IR, serializes it as YAML, and immediately
parses that YAML back into the same IR. The round trip costs work and obscures
the single-IR architecture.

## What Changes

- Expose the existing XML walker result as the supported
  `junoscfg.display.xml_to_dict()` package-door helper.
- Make `xml_to_yaml()` serialize that dict result.
- Make conversion XML input consume the dict result directly.
- Apply schema-backed leaf-list normalization at the common input boundary.
- Preserve XML parsing, errors, normalization, and public output exactly.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- None; this is a behavior-preserving refactor, so specs are skipped.

## Non-goals

- Changing accepted XML syntax, XML output, or the dict IR schema.
- Moving XML parsing across the established display-layer boundary.
- Changing the top-level `junoscfg` names used by the production Ansible
  collection.

## Impact

The XML input adapter and existing XML/YAML renderer share one package-door
helper. This adds a `junoscfg.display` API without changing the CLI or the four
top-level names imported by `dg-i/ansible-collection-junos-config`.
