## Why

`_BOOL_FLAG_KEYS` in `artifact_builder.py` carried the comment "Flags the
structure tree stores as a plain boolean key, **in both directions**". Only
`_deserialize_node` read it; `_serialize_node` was a hand-written if/elif
chain, so adding a flag took two edits that looked nothing alike and the one
test guarding the pair walks a fixed sample tree.

`accepts-bracket` is what that asymmetry produced. `_fix_members_bracket` sets
it on 74 `members` nodes, `_serialize_node` has no key for it, so it reaches
no artefact and no runtime can see it. `tests/test_xsd_fixes.py` asserted it
on the in-memory tree, so a correction that cannot ship looked green.

## What Changes

- `_serialize_node` drives off the same two tables `_deserialize_node` reads —
  `_BOOL_FLAG_KEYS` for the plain booleans and a new `_VALUE_FLAG_KEYS` for the
  two that carry a payload (`t`, `fe`). Adding a flag is now one table entry.
  The writer's one guard, on `o`, is declared as `_GUARDED_BOOL_KEYS` beside
  the table rather than buried in the chain.
- `accepts-bracket` deleted, with its test. It reaches no artefact, nothing
  reads it, and it models the wrong thing: `[ a b c ]` is how Junos writes any
  value list, on every leaf-list in the schema, not a property of `members`.
  `set policy-options community FOO members` is still over-rejected under the
  `brackets` code in `test_set_corpus.py`; a grammar fix, not a flag. What
  `_fix_members_bracket` really does — `members` is a leaf — stays, and its
  test asserts that instead.
- `_fix_policy_algebra` deleted. It searched element *names*, and
  `policy-algebra` is only ever a type reference: zero matches in 21.4R0,
  23.2R2, 23.4R2 and 25.2R2 alike, against 186 to 253 uses as a type. It
  returned `True` regardless, so it counted as applied and its deadness never
  showed; with `accepts-bracket` gone its body is a no-op over an empty list.
  Registered fixes 41 → 40; Group G 6 → 5.
- Three new round-trip assertions, driven off the tables themselves.

## Capabilities

### New Capabilities

Nothing new; this makes an existing pair honest.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Making the grammar accept `[ a b c ]`: the `brackets` limitation in
  `docs/guide/validation.md`, still open.
- Serializing the flags the XSD carries verbatim (`oneliner-plus`, …), which
  nothing reads either. A separate question.

## Impact

`artifact_builder.py`, `xsd_fixes.py`, their tests, and the fix counts in
`docs/architecture/`. No bundled artefact changes: the deleted flag was never
written and the deleted fix matched nothing. Verified by re-serializing the
shipped 13 MB tree through the new writer — 427,978 nodes, identical as data.
All four measurements unchanged: 21 rejections over 7,097 real set lines, 106
of 116 on the corpus, the ten recorded rejections intact, load 4.12s.
