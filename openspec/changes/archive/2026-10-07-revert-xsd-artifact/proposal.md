## Why

`openspec/changes/archive/2026-10-07-validate-xml-promise` made
`schema generate` write `junos-validated.xsd`, claiming it closed the gap
between what the documentation promised and what the command produced. It was
verified against a 516-byte toy XSD, which compiled.

A real dump proves it wrong. On a 163 MB NETCONF dump at Junos 23.2R2, the
extracted XSD does not compile:

```text
Element 'xsd:element', attribute 'name': 'openconfig-lldp:lldp' is not a
valid value of the atomic type 'xs:NCName'
```

85 element names carry OpenConfig prefixes containing a colon, and that is only
the first error lxml reports. The filename was the clue: a *validated* XSD is a
cleaned one, and extraction does not clean.

Two consequences, both bad:

- `validate_xml` still fails, now after loading a 156 MB file instead of
  reporting a missing one.
- `--regen-schema` writes into `src/junoscfg/validate/data/`, so that 156 MB
  would land in the wheel — taking the bundled artifacts from 36 MB to 193 MB,
  and directly contradicting the non-goal the same proposal declared.

## What Changes

- Revert the XSD write from both build paths.
- Restore the characterization pin to the honest form, now carrying the
  measured reason rather than a guess.
- Correct `docs/guide/validation.md`: it told readers that `schema generate`
  produces what XML validation needs. It does not, and cannot without a
  cleaning step nobody has written.

## Capabilities

### New Capabilities

None; this removes an artifact that did not work.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Writing the cleaning step. Renaming or dropping the 85 prefixed names is
  tractable but lxml reports one error at a time, so the true depth is unknown.
  It is a feature with its own design and its own review, not a patch on this.

## Impact

`src/junoscfg/validate/artifact_builder.py`, two tests, the contract and the
validation guide. `schema generate` writes five artifacts again, as it did
before v0.6.4.
