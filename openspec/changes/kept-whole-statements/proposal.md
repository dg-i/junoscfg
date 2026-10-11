## Why

The set reader keeps a statement it cannot place as one key, its tokens joined,
at its parent's level. A bare keyword kept so has the key of the node it names:
after `set apply-groups G1`, a bare `set apply-groups` vanishes silently, and in
the other order the valid `G1` is kept and reported too (OPEN-2). A leaf with no
value is not kept at all: a bare `set system host-name` replaces `router1` with
`null` and is written back device-invalid, without a word (NEW-C1). The joined
key drops each token's quotes, so `apply-macro 12345 "KADJBF KU!H" balks XXXXX`
is written as five words (OPEN-3).

## What Changes

- **BREAKING** (`consumer`, `cli`): a statement the reader cannot place is kept
  under one reserved key at its level, `junoscfg:unplaced`, as its original
  tokens (quotes kept) mapped to `true`; a tag or a meta command on it sits
  beside it as `@<statement>`. It never replaces, joins or hides a placed node.
  JSON and YAML output show the new key where they showed `"<statement>": [null]`.
- A leaf with no value (`host-name;`, `members`) is kept whole and reported
  `UNPLACED`; a value-less leaf from JSON, YAML or XML is reported too.
- A valid statement after a bare keyword is placed; only the bare one is kept.
- Every writer prints a kept statement verbatim; field validation reports each
  one `UNPLACED`; anonymization still refuses it.
- `junoscfg.display.UNPLACED_STATEMENTS` names the key; minor bump to 0.17.0.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `conversion/entry-keys`: "A statement the reader cannot complete is kept whole": where the record lives, a value-less leaf, and the placed statement after a bare one.

## Non-goals

- The meta walk itself (change 14), XML empty text (DEV-16, change 9), a
  reader-wide `true`/`[null]` spelling (change 13), anonymizing inside a kept
  statement (change 5), unsupported set verbs (change 15).

## Impact

`convert/input/set_input.py`, `convert/output/dict_walker.py`,
`convert/field_validator.py` (zone conversion), `display/constants.py` and its
door (kernel), version files, docs. Reproduce: `private_test_data/makeover-work/kept-whole-statements/repro.py`.
