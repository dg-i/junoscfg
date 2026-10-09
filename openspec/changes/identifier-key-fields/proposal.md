## Why

`from as-path-neighbors as-list AS_LIST_NAME` loses `AS_LIST_NAME` on set and
structured input, before anonymization (`private_test_data/bugreport.txt`).
`_build_from_complex_type` keeps a sequence's first `xsd:choice` and drops the
rest: identifiers (2,800 types keyed `name`, right by accident; 171 by one
other element; 64 by two to four, `list-type` and `list-name` among them) and a
second choice (seven types, route-filter's `accept` among them). `fe`,
`values-only`, `_v<n>`, `ENTRY_KEY_OVERRIDES`, the `community-name` branches and
`_takes_either_order` each re-supply part of what the parser dropped.

## What Changes

- The parser keeps every element a sequence declares, in declared order:
  identifiers, `name` included, and every choice. Every list node carries its
  key tuple (`k`, omitted for `("name",)`); `c`'s order places the keys.
- One kernel helper, `entry_keys()`, answers the tuple at every site. Identity
  is the key tuple; key children are positional, never keywords. Writers put
  pre-key children, the keys in order, then the rest; reader and grammar take
  pre-key keywords on either side, as the device does, and exactly the key
  values. XML input takes list shape from the tree; one-line rendering follows
  `oneliner` and `oneliner-plus`; anonymization treats keys as leaves.
- One unplaced rule replaces the reader's silent branches: an entry exists once
  all its key values are read; tokens from the first unplaceable one on are kept
  at the deepest node fully placed, and validation reports them `UNPLACED`.
- Retired: `fe`, `values-only`, `_v<n>`, `_takes_either_order`, the fixes
  `_fix_flat_entry_keys` and `_fix_attributes_match_oneliner`, `FLAT_ENTRY_ELEMENTS`,
  the `community-name` branches; `ENTRY_KEY_OVERRIDES` and
  `get_flat_entry_config` are removed and banned in a decision record.
- **BREAKING** on `consumer` and `cli` under decision 2026-10-09: the IR keys
  the 171 + 64 lists by their declared fields and holds route-filter actions as
  the device does. The collection's four imports keep their signatures; its
  test suite, run in phase 5, is the proof. No override or fallback is added.

## Capabilities

### New Capabilities

- `schema-pipeline/entry-key-fields`: the tree keeps every declared child and the keys.
- `conversion/entry-keys`: keys from the tree; one IR from every input; nothing lost.
- `validation/keyed-entries`: field and schema validation accept device-keyed entries.
- `audit/keyed-references`: the named key field is the reference, not `list-type`.
- `anonymization/keyed-entries`: key fields are leaves of their declared type.

### Modified Capabilities

- `validation/set-command-validation`: a keyed entry takes exactly its key values.

## Non-goals

- IR, grammar and output of `name`-keyed lists stay byte-identical, pinned by a
  test and the corpus; numeric JSON normalization; lost values elsewhere.

## Impact

Over `private_test_data/schemas/25.2R2-S1.5_qfx5120.xsd` via `extract_xsd`,
3,035 sequences hold identifiers; 3,011 declare them first, 4 types (24 slots)
a choice first; 23.2R2-S7.5: 3,079, 3,059, 3 types (20 slots). Device probe,
vMX 23.2R2-S7.5, backs every shape. Five domains and the kernel, five
artifacts, tests, one fixture, three docs, one decision record; minor bump.
