## Findings

A fresh session reviewed this change, the one that ships a 761 KB artefact. It
verified the load-bearing claims independently and two to the digit: the
artefact is byte-identical to what the documented command produces (761,365
bytes, four runs); the reproducibility test fails when the generator or the
artefact is altered; the 25.2R2 round trip over 424,436 nodes differs in
exactly one token, `groups`; and the performance ratio is real, measured
slightly worse than claimed at 245.9 ms a line against 3.4 ms. Six findings;
four acted on, two of them code defects.

1. **The new gate contradicted the mandated workflow.** `--regen-schema`, which
   `AGENTS.md` requires after a schema change, had `ArtifactBuilder` write the
   grammar from the XSD tree, while `TestBundledGrammarIsReproducible` compares
   against a loader-built one. Those differ on `groups`, so a correct
   regeneration turned the test red and the obvious way to clear it was to
   discard the XSD-built grammar. **Fixed**: both build paths now generate the
   grammar from the structure tree they have just written, so the artefacts are
   self-consistent by construction. Verified on a 23.4R2 dump — `schema
   generate` output and the loader rebuild are now identical.
2. **The validator rejected junoscfg's own output.** `convert -i structured -e
   set` emits `set policy-options prefix-list PL-A 10.0.0.0/8`; `convert -v -i
   set` rejected it. Cause: `_child_reference` tested `is_presence` before
   `nokeyword`, so 204 nokeyword presence nodes kept a keyword no set command
   writes. **Fixed**: such a node emits its entry name. The round trip now
   validates clean, and the corpus goes 97 to 100 of 116.
3. **The loader's "three things it cannot carry" was not exhaustive.**
   `accepts-bracket`, raw XSD flags outside the writer's allow-list,
   `oneliner` on a non-list, `is_presence` on a leaf and a bare
   `pattern_negated` are also dropped. None reaches the grammar, so the
   grammar claim stands, but the docstring read as a complete list. **Fixed**,
   with the reason the grammar is unaffected stated explicitly.
4. **The documented causes of over-rejection were incomplete and the figures
   unreproducible.** Bracket value lists, `prefix-list`, merged container rules
   and `apply-macro` were not named, and no corpus existed to audit 97/113.
   **Fixed**: `tests/data/set_corpus.txt` is committed with its derivation,
   `tests/test_set_corpus.py` records all 16 rejections and which 3 are
   correct, and `docs/guide/validation.md` lists every cause. The proposal's
   "reports real errors" now also says it reports false ones.
5. **Record residue from `acd0633`**: tasks.md still said the example "reports
   the `vlan-id` line" four lines above saying it validates clean; retires.md
   undercounted tests; the docs still said 5 seconds. **Fixed.**

## Accepted as-is

- The gate pins `junos-set.lark == f(junos-structure-tree.json)`, not the tree
  against the XSD. One of five artefacts is pinned; the reviewer is right that
  `ARCHITECTURE.md` section 8 wants more. Carried forward.
- `read_structure_tree` raises `json.JSONDecodeError`/`OSError` rather than
  `SchemaLoadError`. Not on the runtime path.
- The reviewer saw one unreproducible run where the rebuild produced
  pre-`0f3f7ef` output, then nine identical runs. It attributes this to stale
  worktree copies in the shared scratch directory. I could not reproduce it
  either; recorded rather than dismissed.

## Specification challenges

No challenge. `skip_specs: true`.

## Verdict

Accepted after correction. Two of the findings were live defects, not record
errors: the reproducibility gate would have fought the documented regeneration
workflow, and the tool rejected configuration it had just emitted. Both are
fixed and verified. Owner acceptance: the owner asked for the open changes to
be archived in this session; they have not reviewed these findings
individually.
