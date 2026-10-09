## Why

`from as-path-neighbors as-list AS_LIST_NAME` loses `AS_LIST_NAME` on set and
structured input (`private_test_data/bugreport.txt`).
`_build_from_complex_type` keeps a sequence's first `xsd:choice` and drops the
rest: identifiers (2,800 types keyed `name`, right by accident; 171 by one
other element; 64 by two to four, `list-type` and `list-name` among them) and a
second choice (seven types, route-filter's `accept` among them). 38 list
definitions also key on a choice marked `<identifier/>`, such as route-filter's
match type. `fe`, `values-only`, `_v<n>`, `ENTRY_KEY_OVERRIDES`, the
`community-name` branches and `_takes_either_order` each patch part of the loss.

## What Changes

- The parser keeps every element a sequence declares, in declared order. Every
  list node carries its key fields (`k`, omitted for `("name",)`): each
  identifier element, and each all-identifier choice as one field.
- One kernel helper, `entry_keys()`, answers the fields at every site. Identity
  is the key tuple. Set output writes the key values in declared order, then a
  line per other child: every device set shape, no flag. Structured output keeps
  today's `o`. A key choice goes either side of the positional values, as on
  the device. XML input takes list shape from the tree, loaded lazily.
- One unplaced rule replaces the reader's silent branches: a statement the
  reader cannot complete (a partial key, a surplus after a terminal entry,
  `apply-groups` with a surplus) is kept whole, from its keyword, at its
  parent, and validation reports it `UNPLACED`.
- Retired: `fe`, `values-only`, `_v<n>`, `_takes_either_order`,
  `_fix_attributes_match_oneliner`, the `flat-entry` half of
  `_fix_flat_entry_keys`, `FLAT_ENTRY_ELEMENTS`, the `community-name` branches;
  `ENTRY_KEY_OVERRIDES` and `get_flat_entry_config`, removed and banned.
- **BREAKING** on `consumer` and `cli` under decision 2026-10-09: the IR keys
  the 171 + 64 lists by their declared fields and holds route-filter actions as
  the device does. The four imports keep their signatures; the collection's
  test suite, run in phase 5, is the proof. No override or fallback is added.

## Capabilities

### New Capabilities

- `schema-pipeline/entry-key-fields`: the tree keeps every declared child and the keys.
- `conversion/entry-keys`: keys from the tree; one IR from every input; nothing lost.
- `validation/keyed-entries`: field and schema validation accept device-keyed entries.
- `audit/keyed-references`: the named key field is the reference, not `list-type`.
- `anonymization/keyed-entries`: key fields are leaves the tree declares.

### Modified Capabilities

- `validation/set-command-validation`: a keyed entry takes exactly its key values.

## Non-goals

- IR, grammar and output of `name`-keyed lists stay byte-identical (test and
  corpus); structured `oneliner-plus` and `homogeneous` shapes; key types from
  `simpleContent` bases; numeric JSON normalization; lost values elsewhere.

## Impact

25.2R2-S1.5 dump via `extract_xsd`: 3,035 sequences hold identifiers. Device
probe, vMX 23.2R2-S7.5. Five domains, the kernel, one fixture, three docs, one
decision record; minor bump.
