## Why

`apply-groups`, `apply-groups-except`, `apply-flags` and `apply-macro` are
valid at every hierarchy level and appear in **no** NETCONF XSD — not as
element, ref or substring, in 21.4R0, 23.2R2, 23.4R2 or 25.2R2. Six modules
each compensate separately: `set_validator.py` (three regexes, a quote-aware
guard, an early return), `set_input.py`, `structured_output.py`,
`dict_walker.py`, `anonymize/` and `audit/`. JSON and YAML validation reject
them outright — every container carries `additionalProperties: false`.

## What Changes

- `xsd_fixes._fix_apply_statements` (Group D) declares the four on the root,
  each flagged `universal`: two leaf-lists, a leaf, and a named list carrying
  `flat-dict` because `apply-macro m1 key1 val1` writes a run.
- `artifact_builder` carries the flag as `u`, one entry in `_BOOL_FLAG_KEYS`.
- `grammar_generator` emits one `universal_statement` rule and references it
  from every rule. `schema_generator` names them as one `patternProperties`
  entry per container.
- Declared once, not copied under each of 123,769 containers: +242 bytes
  against +24 MB on the structure tree.

## Nothing ships yet, and that is the point

A fix in `xsd_fixes.py` reaches a user only through regenerated artifacts. The
bundled ones are 24.4R0 from a dump not in this repository, and regenerating
from the 23.2R2-S7.5 dump that is here was measured and rejected: Juniper's
Validated Designs go from 217 field warnings to 3,254, over the budget
`test_jvd_corpus.py` enforces, because 23.2R2's `evpn ip-prefix-routes
encapsulation` enum lacks `srv6` and that corpus writes it 22,304 times.
Numbers in `tasks.md`.

Mutating the structure tree to ship it anyway was rejected: section 8 forbids
hand-editing a generated artefact, and a tree carrying nodes no XSD produced
would leave the grammar and the JSON schemas disagreeing. So the compensation
stays, **labelled**: `set_validator.py`'s docstring names it a temporary
bridge and says what retires it, and two tests assert it is load-bearing.

## Capabilities

### New Capabilities

Nothing reaches a user until the artifacts are regenerated.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Regenerating the bundled artifacts. Measured and rejected above.
- Removing the other five modules' special cases. Only the grammar and
  JSON-schema generators read `universal`; the converters, the anonymizer and
  the audit walker would each need to.

## Impact

`xsd_fixes.py`, `artifact_builder.py`, `grammar_generator.py`,
`schema_generator.py`, three docstrings, two fix counts. Fifteen tests, eight
seen to fail. All four measurements unchanged, because nothing shipped.
