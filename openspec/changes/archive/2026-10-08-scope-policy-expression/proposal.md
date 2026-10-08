## Why

`set policy-options policy-statement P term T from policy
(( A && ! B ) || ( ! C && D ))` was rejected, so a global Lark terminal
`EXPRESSION: /\([^\n]*\)/` was added to `QUOTED_OR_VALUE`. That terminal is not
one slot: the generated grammar writes `QUOTED_OR_VALUE` in **11,853** value
slots, which is every value slot there is. The fix for one shape loosened all
of them, and the result shipped.

Verified against the bundled artefact before this change:

- `set system host-name (anything at all goes here)` — accepted.
- `set interfaces ge-0/0/0 description (not a policy expression)` — accepted.

A hostname holds neither a space nor a parenthesis.

The key is already in the shipped artefact and needed no serialization change:
the XSD type reference `policy-algebra`, on **7,636** nodes of
`junos-structure-tree.json` — `import`, `export`, `prefix-policy`, `policy` —
and on none of the others. Every one is a leaf. It is a *type* reference, not
an element name, which is why `_fix_policy_algebra` in `xsd_fixes.py` finds
nothing: it searches element names through `find_all`.

## What Changes

- `_value_token(node)` in `grammar_generator.py` returns `ALGEBRA_OR_VALUE` for
  a node whose `type_ref` is `policy-algebra` and `QUOTED_OR_VALUE` for every
  other node. `_child_reference` uses it in all three value slots it writes.
- The grammar emits `QUOTED_OR_VALUE: QUOTED | VALUE` and
  `ALGEBRA_OR_VALUE: QUOTED | EXPRESSION | VALUE`. `EXPRESSION` is unchanged.
- `junos-set.lark` regenerated from the bundled structure tree, as
  `ArtifactBuilder` does it.
- Negative tests. `tests/test_set_validator.py` ran entirely against a
  three-rule `MINIMAL_GRAMMAR`, which is why this shipped; it now also runs
  against the artefact we ship, and asserts what must stay rejected.

## Capabilities

### New Capabilities

None; this narrows an existing one back to what it was meant to be.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Validating the *content* of a policy expression. It stays one opaque value,
  which is what the device's own `| display json` carries.
- Narrowing `EXPRESSION` itself. The regex is right; its reach was not.

## Impact

Blast radius, measured: expression-capable value slots fall from 11,853 to
**159** (74.5x), across 93 changed rules of 4,385. Rejections over three real
device configurations (7,097 set lines): 21 before, **21** after. Corpus accept
rate 106/116 before and after, with the same ten recorded rejections. Grammar
load 4.09s before, 4.24s after. `src/junoscfg/validate/grammar_generator.py`,
the bundled `junos-set.lark`, and five new negative tests seen to fail.
