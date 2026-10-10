## Why

Junos meta tags (`inactive:`, `protect:`, `replace:`, `delete:`) land on the wrong
node. Curly input deactivates the last token of a one-line statement:
`inactive: route 0.0.0.0/0 apply-groups [ G_LOC G_DEF ];` marks `apply-groups`,
not the route. Curly output writes `family inactive: inet {`, which the device
rejects. `deactivate … family` and `<family inactive="inactive">` pass without a
diagnostic, though the device rejects that tag. XML input drops `protect`.
Evidence: `private_test_data/deactivate{,2,3,4,6}.txt`; layout is cosmetic
(`ARCHITECTURE.md` §1), so only meaning-changing layout is in scope.

## What Changes

- Schema: the structure tree carries the XSD's `homogeneous` flag (`h`).
- Curly input: the lexer hands the set reader's schema walk each statement's
  levels and their tags; a tag marks the node its statement starts (a list
  entry ends after its key, a leaf's value is no node, an unkeyed `homogeneous`
  container passes it to its child). The `replace <path>` pseudo command and
  `SetConverter(emit_replace=…)` are removed.
- Curly output: a tag leads its line; no line joins past a tagged node;
  `homogeneous` replaces `ConfigStore.COMPOUND_KEYWORDS`.
- Validation: a tag on an unkeyed `homogeneous` container is `UNPLACED` on every
  input; structured output drops it with a note. XML input reads `protect`.
- Patch bump.

## Capabilities

### New Capabilities

- `conversion/curly-meta-tags`: where a tag lands reading and writing curly
  configuration.
- `conversion/tag-acceptance`: XML keeps `protect`; a tag on `family` is
  reported from every input.

### Modified Capabilities

- `conversion/raw-set-input`: the bracket requirement no longer names the
  internal `replace` form.

## Non-goals

- Device layout: defect 4, `oneliner`/`oneliner-plus` in the tree,
  `_fix_flat_entry_keys`, `_emit_oneliner` (cosmetic follow-up).
- `SetConverter.to_set()` keeps its output; its limit goes in the contract.
- Keyed `homogeneous` containers, `deactivate … members <value>`, unknown set
  commands, `_apply_meta`'s schema walk: follow-ups.
