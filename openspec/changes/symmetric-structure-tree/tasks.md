## 1. Tests

- [x] 1.1 Every key of `_BOOL_FLAG_KEYS` and `_VALUE_FLAG_KEYS` survives a
  round trip, with the tree built from the tables rather than a fixed sample.
- [x] 1.2 A value-flag key with no sample payload fails its own coverage test.
- [x] 1.3 The shipped 13 MB tree re-serializes to itself exactly.
- [x] 1.4 `_fix_members_bracket` makes `members` a leaf and adds no flag.
- [x] 1.5 All four seen to fail — writer made to skip `frnk`, a table key added
  with no sample, the flag put back on `members`; tree restored and green.

## 2. Implementation

- [x] 2.1 `_VALUE_FLAG_KEYS` and `_ValueFlag`, the encode/decode pair for `t`
  and `fe`, read by both directions.
- [x] 2.2 `_GUARDED_BOOL_KEYS`, the writer's one guard, declared beside the
  table it guards.
- [x] 2.3 `_serialize_node`'s if/elif chain replaced by two loops over those
  tables.
- [x] 2.4 `_deserialize_node`'s `t`/`fe` branch replaced by the same loop.
- [x] 2.5 `accepts-bracket` removed from `_fix_members_bracket`, which keeps
  `is_leaf`; `read_structure_tree`'s docstring no longer names the flag.
- [x] 2.6 `_fix_policy_algebra` and its `policy-algebra-any` registration
  removed; counts updated in `developer-guide.md` and `schema-internals.md`.

## 3. Verification

- [x] 3.1 No bundled artefact changes: `write_structure_tree(read_structure_tree
  (shipped))` equals the shipped file as data, 427,978 nodes.
- [x] 3.2 `policy-algebra` appears as an element name 0 times and as a type
  reference 186 / 196 / 201 / 253 times in the 21.4R0, 23.2R2, 23.4R2 and
  25.2R2 dumps. The fix could never have matched.
- [x] 3.3 Real configurations 21 rejected of 7,097; corpus 106 of 116; ten
  recorded rejections unchanged; grammar load 4.12s. All as before.
- [x] 3.4 `uv run pytest tests/ -q`, `pre-commit run --all-files`,
  `agent-ready check`.
