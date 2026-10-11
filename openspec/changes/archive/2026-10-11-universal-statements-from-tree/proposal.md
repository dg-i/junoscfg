## Why

The structure tree declares the four statements Junos takes at every level
(`apply-groups`, `apply-groups-except`, `apply-flags`, `apply-macro`) once, on the
root, flagged `u`, and only the grammar generator reads that. Every other layer
keeps its own names, so below the root a reader or writer meets them without
their node (ARCH-C06), and the Group-H helpers fall back to six name tables;
every "lost context" they cover is a nested universal statement or unplaced
content, and where they fire they drop a keyword (ARCH-C08). `apply-flags` is
also modelled as a leaf where the device writes a container holding `omit`, so
set and curly `apply-flags omit` is `UNPLACED` below the root and another IR at
it (DEV-V2).

## What Changes

- One kernel helper, `junoscfg.display.schema_child(node, key, root)`, resolves a
  key absent from a node's children against the root's universal statements
  (`universal_statements(root)`); every tree walker of the set, curly, XML and
  normalization readers, the set, structured and JSON writers, field validation
  and the JSON-schema generator uses it, and the anonymizer can (change 5).
- The tree is authoritative. A tree that declares none (artifacts before 0.8.0)
  gets the floor `UNIVERSAL_STATEMENTS`, retired when the loader refuses such
  trees; a tripwire fails if the bundled artifacts ever run on it.
- The Group-H helpers read the node only; their six name tables go.
- **BREAKING** (`consumer`, `cli`): `apply-flags` is the device's container of
  presence flags (`omit`, and `replace`, which the grammar accepts today), read
  as `{"apply-flags": {"omit": [null]}}` from every door at every level; any
  other word under it is reported and rejected. Artifacts regenerated.
- The floor's resource is the structure tree; searched: every
  `load_schema_tree`/`read_structure_tree` caller in `src/` (`set_input`,
  `to_yaml`, `normalization`, `json_output`, `dict_walker`, `structured_output`,
  `field_validator`, `anonymize/walker`, `audit/engine`, `artifact_builder`,
  `__init__`); all but the last four take the helper.

## Capabilities

### New Capabilities

- `schema-pipeline/universal-statements`: declared by the tree, resolved by one helper, the floor, `apply-flags`, flag helpers without name fallbacks.

### Modified Capabilities

- None.

## Non-goals

- The anonymizer's traversal and `_replace_apply_groups` (change 5); the audit
  walker's group references; name-wide Group-H matchers (NEW-A-S1, change 10);
  JSON scalar leaf-lists (ARCH-C10) and `KEY_ALIASES` (ARCH-C09), change 13.

## Impact

`display/` (kernel), `convert/` readers, writers and field validation,
`validate/xsd_fixes.py`, `schema_generator.py`, regenerated `validate/data/*`,
version files. Reproduce: `private_test_data/makeover-work/universal-statements-from-tree/repro.py`;
outputs: `outputs.py` (device captures, `--jvd`).
