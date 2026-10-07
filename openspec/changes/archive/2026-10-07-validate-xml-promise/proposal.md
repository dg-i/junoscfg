## Why

`validate_xml` is in `__all__` on the declared beta `api` surface and raises
`SchemaLoadError` unless the caller supplies a directory containing
`junos-validated.xsd`.

That the XSD is not bundled is deliberate and documented:
`docs/guide/validation.md` warns about it, and the reason is sound — the XSD
comes from a NETCONF dump off a specific device at a specific Junos release,
not from the wheel.

The defect is in the workflow the documentation points at. It says to obtain a
dump and "generate artifacts with `junoscfg schema generate`". That command
wrote five artifacts and never the XSD, so a caller who followed the
instructions exactly still could not use XML validation. Onboarding phase 3
recorded this as a pin on a name that always raises.

## What Changes

- `schema generate` writes `junos-validated.xsd` alongside the five existing
  artifacts, in both build paths (`build_from_netconf_dump` and
  `build_from_xsd`). The text is what `XmlValidator` compiles directly.
- Rewrite the characterization pin: it recorded a name that could never work;
  it now records that the documented workflow produces what the name needs.
- The contract stops calling it a defect and states the real constraint: the
  XSD is per-device, from `schema generate`, not from the wheel.

## Capabilities

### New Capabilities

None. `validate_xml` already existed; this makes the documented route to it
actually produce its input.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Bundling an XSD in the wheel. It is per-device and per-release; shipping one
  would make every user's validation wrong for every other device.
- Serialising the corrected `SchemaNode` tree back to XSD. The fixes in
  `xsd_fixes.py` apply to the tree, not to the XSD text, so the written XSD is
  the extracted one. That is what `XmlValidator` compiled before and compiles
  now.

## Impact

`src/junoscfg/validate/artifact_builder.py`, two tests asserting the artifact
count, and the characterization pin. `schema generate` writes one more file
into the directory the caller names. Nothing else changes.
