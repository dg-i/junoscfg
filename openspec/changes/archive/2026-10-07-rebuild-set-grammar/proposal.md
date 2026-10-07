## Why

`junoscfg -v` validated nothing for set or structured input since the 24.4
migration: the bundled `junos-set.lark` carries two `start:` rules, fails to
load, and both formats exit 3 on a valid and an invalid configuration alike.
The generator was repaired in the two preceding changes; the artefact was not,
and rebuilding it needs the 24.4R0 dump it came from, which is not here.

## What Changes

- `read_structure_tree`, the inverse of `write_structure_tree`, so the grammar
  rebuilds from `junos-structure-tree.json`. What the format drops is pinned.
- The bundled `junos-set.lark` is rebuilt, so set and structured validation
  work: `set system bogus-element value` is reported with its line and exit 1.
- A named list takes one continuation, `VALUE (alts)?`, not a repetition.
  Measured at 61, 244 and 976 lines, `(alts)*` costs 228 ms a line against
  4 ms — 19 minutes for a 5,000-line configuration against 18 seconds. Lark's
  `~0..n` expands combinatorially and does not finish compiling.
- Two more flags the generator read wrongly. A `freeform-nk` leaf keeps its
  keyword: it marks `vlan-id` and `vlan-name`, which carry `nokeyword` only
  for freeform value validation. And a nokeyword *presence* node emits its
  entry name — the presence branch ran first, so 204 nodes kept a keyword no
  set command writes, `prefix-list-item` among them. That is why junoscfg's
  own `set policy-options prefix-list PL-A 10.0.0.0/8` failed its own
  validator.
- `ArtifactBuilder` builds the grammar from the structure tree it just wrote,
  not from the XSD tree. Otherwise `--regen-schema`, which `AGENTS.md`
  mandates, emits a grammar differing on `groups` and turns the
  reproducibility test red on a correct regeneration.
- `TestBundledGrammarIsReproducible` holds the artefact to the command that
  builds it. The corpus behind the accept-rate figures is committed as
  `tests/data/set_corpus.txt`, with every rejection recorded.

## Capabilities

### New Capabilities

None; this repairs an existing one.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- The over-rejection that remains: 100 of 116 corpus commands accepted, 3 of
  the 16 rejections correct, the other 13 listed with a cause in
  `tests/test_set_corpus.py`. `xsd_fixes` already carries an `accepts-bracket`
  flag the generator ignores.
- Regenerating the other four artefacts; the schema version is untouched.

## Impact

`src/junoscfg/validate/` and `data/junos-set.lark`, 734 KB to 761 KB.
`junoscfg -v -i set` goes from exit 3 and no validation to a 4s run that
reports real errors. It also reports false ones: on a configuration using
groups or bracket lists it goes from always-exit-3 to exit 1 with confident
wrong errors, which a CI consumer should know before turning it on.
