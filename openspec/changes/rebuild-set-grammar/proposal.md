## Why

`junoscfg -v` has validated nothing for set or structured input since the 24.4
migration: the bundled `junos-set.lark` carries two `start:` rules and fails to
load, so both report "Error loading validation artifacts" on a valid and an
invalid configuration alike. The generator was repaired in the two preceding
changes; the artefact was not, and rebuilding it needs the 24.4R0 dump it came
from, which is not in the repository.

## What Changes

- `read_structure_tree`, the inverse of `write_structure_tree`, so the grammar
  can be rebuilt from `junos-structure-tree.json`. It restores every field the
  format carries; the three it cannot are pinned and documented.
- The bundled `junos-set.lark` is rebuilt, so set and structured validation
  work: `set system bogus-element value` is reported with its line number and
  exit 1 where both formats previously validated nothing at all.
- A named list takes one continuation, `VALUE (alts)?`, not a repetition.
  Measured on the bundled tree at 61, 244 and 976 lines, `(alts)*` costs 228 ms
  a line against 4 ms — 19 minutes for a 5,000-line configuration against 18
  seconds — because the repetition is ambiguous and lets a bare `VALUE` absorb
  any run of tokens. Lark's `~0..n` range is not a middle way: it expands
  combinatorially and does not finish compiling.
- A `freeform-nk` leaf keeps its keyword. The flag marks a node carrying
  `nokeyword` only so its value is validated as freeform — `vlan-id` and
  `vlan-name` — which `_fix_freeform_nk_keys` says is "treated as a normal
  keyword in conversion". Reading the bare `nokeyword` rejected every
  VLAN-bearing configuration, `examples/router1.set` among them.
- `TestBundledGrammarIsReproducible` holds the shipped artefact to the command
  that builds it, which is what `ARCHITECTURE.md` section 8 needs to be
  checkable. `TestBundledGrammarCompiles` loses its `xfail`.

## Capabilities

### New Capabilities

None; this repairs an existing one.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- The over-rejection that remains. Of 113 set commands taken from this
  repository's tests, 97 are accepted and two of the rest should be rejected,
  leaving 14 the one-continuation rule and `set groups` explain. Documented in
  `docs/guide/validation.md`, not fixed.
- Regenerating the other four artefacts. Only the grammar is rebuilt; the
  schema version and every conversion artefact are untouched.

## Impact

`src/junoscfg/validate/` and `data/junos-set.lark`, which grows 734 KB to 761
KB. `junoscfg -v -i set` goes from exit 3 and no validation to a 4.3s run that
reports real errors, and `examples/router1.set` validates clean. Nothing on the conversion path changes, and the Ansible
collection never constructs a `SetValidator`.
