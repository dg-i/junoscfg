## 1. Tests

- [x] 1.1 `TestStructureTreeRoundTrip`: the grammar is identical across a
  round trip, every carried field survives, and the three dropped ones are
  pinned so the tree is not mistaken for a faithful copy.
- [x] 1.2 `TestBundledGrammarIsReproducible`: the shipped artefact equals what
  the generator makes from the shipped structure tree.
- [x] 1.3 Drop the `xfail` from `TestBundledGrammarCompiles`.
- [x] 1.5 `TestFreeformNokeywordKeepsItsKeyword`, with a control showing a
  plain `nokeyword` leaf still suppresses its keyword.
- [x] 1.4 Record the one-continuation trade in
  `TestListEntryTakesSiblingsOnOneLine`, and drop the `xfail` from
  `TestUnknownTokensInsideANamedList`, which the same change closes.

## 2. Implementation

- [x] 2.1 `read_structure_tree` and `_deserialize_node`.
- [x] 2.2 A named list emits `VALUE (alts)?` rather than `VALUE (alts)*`.
- [x] 2.3 A `freeform-nk` leaf keeps its keyword.
- [x] 2.4 A nokeyword *presence* node emits its entry name rather than its
  keyword. 204 such nodes; `prefix-list-item` among them, which is why
  junoscfg's own set output for a prefix-list failed its own validator.
- [x] 2.5 `ArtifactBuilder` builds the grammar from the structure tree it has
  just written, so `--regen-schema` cannot disagree with the reproducibility
  test. Verified on a 23.4R2 dump: the two are identical.
- [x] 2.6 Rebuild `src/junoscfg/validate/data/junos-set.lark`.

## 3. Verification

- [x] 3.1 Round trip on a real 25.2R2 tree, 424,436 nodes: the loader-built
  grammar differs from the XSD-built one in one token, `groups`, and in
  nothing else.
- [x] 3.2 Timed at 61, 244 and 976 lines: `(alts)*` 30.3s compile and 228 ms a
  line; `(alts)?` 4.7s and 4 ms. Lark's `~0..n` did not finish compiling, and
  `cache=` is LALR-only so there is nothing to precompile.
- [x] 3.3 `junoscfg -v` on set and structured input: `set system
  bogus-element value` is rejected with its line number and exit 1.
- [x] 3.4 The corpus is committed as `tests/data/set_corpus.txt` with its
  derivation, after two reviewers could not reproduce figures taken from a
  scratch file. 116 commands, 100 accepted; `tests/test_set_corpus.py` records
  every one of the 16 rejections and which 3 are correct.
- [x] 3.5 `examples/router1.set` and `router1.conf` both validate clean, after
  the `freeform-nk` fix; the `vlan-id` line was the only failure.
- [x] 3.6 The Ansible collection's 33 tests pass and its four filters produce
  byte-identical output; it constructs no `SetValidator`.
