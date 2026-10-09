---
status: accepted
scope: ["src/junoscfg/display/constants.py", "src/junoscfg/validate/xsd_parser.py"]
enforced-by: tests
review-by: 2027-04-09
bans:
  - junoscfg.display.ENTRY_KEY_OVERRIDES
  - junoscfg.display.get_flat_entry_config
---

# Key list entries by the identifiers the XSD declares

## Context

The XSD parser kept a sequence's first choice and dropped the elements the
sequence declares beside it: the identifiers that key a list's entries, and any
second choice. Every list therefore read as keyed `name`, and each site that
met a list keyed otherwise kept its own patch: the `fe` flag and its
`flat-entry:<key>:<position>` fix, `values-only` and the `_v<n>` keys for
`attributes-match`, `ENTRY_KEY_OVERRIDES` for `then community`, and
`get_flat_entry_config` to read the flag. `from as-path-neighbors as-list
<name>` lost its list name on set and structured input
(`openspec/changes/identifier-key-fields/`).

## Decision

The parser keeps every element a sequence declares and records an entry's key
fields on the list node: each identifier element, and each choice whose every
element is an identifier as one field. The structure tree carries them as `k`,
omitted where the one key is `name`, and `junoscfg.display.entry_keys()` is
the one answer every reader, writer and validator asks.
`ENTRY_KEY_OVERRIDES` and `get_flat_entry_config` leave the secondary
`junoscfg.display` door without prior deprecation, as decision
2026-10-09-scope-compatibility-to-production-consumer permits for a secondary
door; the production collection imports neither.

## Consequences

- A list keyed by anything but `name` needs no flag, fix or table: the tree
  carries its keys.
- The two retired names are banned, so neither returns as a second answer.
- The IR spelling of the lists keyed otherwise changes, a declared break on
  `consumer` and `cli` with a minor bump.
