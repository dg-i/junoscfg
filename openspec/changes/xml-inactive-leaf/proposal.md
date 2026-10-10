## Why

XML input nests an inactive leaf's value under its own name:
`<vlan-id inactive="inactive">751</vlan-id>` becomes
`{"vlan-id": {"@": …, "vlan-id": ["751"]}}` and the set output
`set … unit 751 vlan-id vlan-id 751`, a line the device rejects, without a
diagnostic. Set and structured input already give the IR Junos JSON uses:
`"vlan-id": "751"` with a sibling `"@vlan-id": {"inactive": true}`. Device
evidence: `private_test_data/deactivate2.txt` (23.2R2-S7.5).

## What Changes

- `display/to_yaml.py` writes an inactive leaf as its plain value plus the
  sibling `@<name>` marker, for a single leaf and for a leaf-list.
- A leaf-list where only some values carry `inactive` is refused loudly:
  `private_test_data/deactivate5.txt` shows the CLI rejects `deactivate … members
  64496:2`, so Junos has no per-value tag and the IR gets no per-value marker.
- Patch bump.

## Capabilities

### New Capabilities

- `conversion/meta-tags`: an inactive leaf reaches one IR from XML, set and
  structured input.

### Modified Capabilities

- None.

## Non-goals

- Where a tag lands on a one-line curly statement, the curly writer, the
  schema's print flags, and tags on `homogeneous` containers: change B.
- Set input accepting `deactivate … members <value>` and widening it to the
  whole leaf-list: the device rejects the statement (`deactivate5.txt`), but
  that is set input, raised in change B's preflight.
- A per-value inactive marker format.

## Impact

One module, `src/junoscfg/display/to_yaml.py` (zone `kernel`); no named-surface
change. Reproduce: `junoscfg convert -i xml -e set` on the
`deactivate2.txt` shape with test-data values.
