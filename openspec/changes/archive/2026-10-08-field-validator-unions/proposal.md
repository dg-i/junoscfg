## Why

Converting Juniper's own Validated Designs corpus — `github.com/Juniper/jvd`,
1,535 configurations and 4.9M lines — raised **53,326 field-validation
warnings**. Nearly all were wrong. Two causes:

- 9,903 in the first 200 files alone were
  `class-of-service ... classifiers ieee-802.1 classifier-name: Invalid value
  '8021P': must be one of [default]`. The node is a `nokeyword` leaf: its value
  stands where the element name would, and the XSD models it as a union of an
  enum with a freeform type, of which extraction keeps only the enum. 4,448
  leaves are shaped like this, `vlan-id` among them — it carries
  `['none', 'vlan-id']` and takes any VLAN number.
- 215 were `policy-options policy-statement <p> term <t> from interface lo0.0`
  reported as "not a valid IP address". The XSD type is literally
  `ipaddr-or-interface`, and `_IP_ANY_TYPES` sent it to an IP-only check.

`field_validator.py` already carried three escapes for this family — a pattern
or type fallback, bare numerics, and union placeholder names. Neither of these
shapes was covered.

## What Changes

- A `nokeyword` leaf's enum is advisory: a value outside it is accepted.
- `ipaddr-or-interface` leaves its IP-only set; both forms are valid, so there
  is nothing to check.

## Capabilities

### New Capabilities

None; this repairs an existing one.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Correcting the extraction. The right home is `xsd_fixes.py`, so that the
  enum carries its freeform half, but that changes the structure tree and the
  bundled tree cannot be rebuilt without a 24.4R0 dump.
- The 217 warnings that remain, of which 199 name a `$VARIABLE`: jvd ships
  templates, so those values are placeholders rather than configuration.

## Impact

`src/junoscfg/convert/field_validator.py`. Across the jvd corpus field warnings
fall from 53,326 to 217 with conversion unchanged at 1,500 of 1,535 files, and
the three real device configurations tested this session go from warnings to
none. It does weaken checking: 4,448 enum-bearing leaves no longer have their
enum enforced. That is the right trade only because the enum is known to be a
fragment of the real type, which the 53,326 warnings demonstrate.
