## Terms

<!-- agent-ready:retires:begin -->
accepts-bracket
<!-- agent-ready:retires:end -->

`accepts-bracket` is retired. It named a property no artefact carried: the
writer had no key for it, so it existed only between `apply_all_fixes` and the
end of the process. Bracket value lists remain a real gap, tracked as the
`brackets` code in `tests/test_set_corpus.py` and in
`docs/guide/validation.md`, where they belong — in the grammar, not in a flag.

## Symbols

Removed: `_fix_policy_algebra` and the `policy-algebra-any` entry of
`ALL_FIXES`, in `junoscfg.validate.xsd_fixes`. Both private;
`get_fix_count()` goes from 41 to 40.

Added, all private to `junoscfg.validate.artifact_builder`: `_ValueFlag`,
`_VALUE_FLAG_KEYS`, `_GUARDED_BOOL_KEYS`, `_unguarded`.

## Dependencies

No dependency is added or released by this change.

## Requirements

No requirement is retired; this change sets `skip_specs: true`.

## Tests and fixtures

Retired: `TestGroupDMissingElements::test_members_accepts_bracket`. It asserted
a flag on an in-memory tree that no artefact ever carried, so it was green for
a correction that could not ship. `test_members_is_made_a_leaf` replaces it and
asserts what the fix achieves.

Added to `TestStructureTreeRoundTrip`: `test_every_flag_the_tables_name_survives`,
`test_the_value_flag_samples_cover_the_table`, and
`test_the_bundled_tree_survives_a_round_trip_exactly`. The first two are driven
off the tables, so a flag added to one without a writer fails them; the third
checks the pair against the artefact we ship.

## Docs

`docs/architecture/developer-guide.md` and `docs/architecture/schema-internals.md`
carry the fix counts, 41 → 40 and Group G 6 → 5, as the AGENTS.md documentation
checklist requires. `read_structure_tree`'s docstring no longer lists
`accepts-bracket` among the flags the format drops, because the flag is gone.
