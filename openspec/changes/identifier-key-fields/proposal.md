## Why

`from as-path-neighbors as-list AS_LIST_NAME` loses `AS_LIST_NAME` on set and
structured input, before anonymization: the set reader takes `as-list` as the
entry's `name` and drops the rest of the line in silence (bug report
`private_test_data/bugreport.txt`, device 23.2R2-S7.5). The node is childless
because `_build_from_complex_type` collects only a sequence's trailing
`xsd:choice` and drops the sequence's own elements, the identifiers: right by
accident for 2,800 types keyed `name`, wrong for `control-as-list-type` with
`list-type` and `list-name`, 64 more types with two to four keys, and 171 keyed
by one element that is not `name`. Every hand-kept answer to "what keys this
entry" re-supplies what the parser dropped: `ENTRY_KEY_OVERRIDES`, `fe.k`,
`values-only` with `_v0` and `_v1` for `attributes-match`, five sites alone.

## What Changes

- The parser keeps a list's identifier elements as children in declared order
  and records them on the node as `k`, omitted where the one key is `name`.
  One kernel helper, `entry_keys()`, answers the tuple at every site: set
  reader, set and structured writer, field validator, schema and grammar
  generators, audit walker, anonymize walker, XML reader. An entry's identity
  is its key tuple; the set reader takes one token per key and keeps a line
  whole as unplaced when tokens remain, so the childless-list and `apply-groups`
  branches that dropped a token go; output writes the keys in order.
- Retired: `fe.k`, `values-only` and its `_v*` keys, the hard-coded
  `community-name` branches, the parent-scoped fix of
  `change/entry-keys-from-the-tree`, superseded, its helper's shape kept.
  `ENTRY_KEY_OVERRIDES` stays exported, unread. Artifacts regenerated, docs follow.
- **BREAKING** on `consumer` and `cli`, under decision
  2026-10-09-scope-compatibility-to-production-consumer: the IR keys an entry
  by the element the dump declares, so JSON and YAML output change for the 171
  lists keyed `ip`, `index`, `interface-id`, `address`, `id` or 66 other names
  and for `attributes-match`; device JSON and XML of them give one line, not two.
- No override, fallback, parameter or environment read is added.

## Capabilities

### New Capabilities

- `schema-pipeline/entry-key-fields`: the tree keeps identifiers as ordered keys.
- `conversion/entry-keys`: keys from the tree; one IR from four inputs, one line.
- `validation/keyed-entries`: field and schema validation accept device-keyed entries.
- `audit/keyed-references`: the named key field is the reference, not `list-type`.

### Modified Capabilities

- `validation/set-command-validation`: a keyed entry takes exactly its key values.

## Non-goals

- Lists keyed `name` (2,800); `fe.p`; numeric JSON normalization; lost values; captures.

## Impact

Counted over `private_test_data/schemas/25.2R2-S1.5_qfx5120.xsd` through
`extract_xsd`, complexTypes whose sequence holds a trailing choice: keyed
`name` 2,800, one other key 171, two or more 64; the 23.2R2-S7.5 dump gives
2,851, 163, 65. The token-dropping branches fire 0 times on 1,072,944 jvd lines
and three captures, by an instrumented reader; phase 4 pins both in tests.
Fourteen source files in five zones, five artifacts, tests, three docs; minor bump.
