## Why

Synced dumps are named `<release>.xsd`, which does not say which box each came
from. The obvious fix is to read the platform out of the dump. It is not there.

A NETCONF XSD is release-wide: it describes everything a Junos release supports
across the product line. All three synced dumps name ACX, EX, MX, PTX, QFX, SRX
and vMX alike, as enum values for hardware-specific configuration rather than
as a statement of what the device is. Feature depth says the same —
`unified-edge` is 1,771 nodes in both a confirmed vMX's 23.2R2 dump and the
bundled 24.4R0, and `virtual-chassis` is 63 in every one. What varies between
dumps is the release.

This matters beyond tidiness: validating `bordergw0206` against the dump pulled
from `bordergw0206` leaves 1 rejected line of 3,369, against 12 for the bundled
24.4R0. Knowing which dump belongs to which role is what makes that reachable.

## What Changes

- `promote_staged` takes a `platform`, else reads `new.platform` beside the
  staged dump, and names the file `<release>-<platform>.xsd`. Without either it
  keeps the release alone, rather than guessing.
- `read_platform` reads the marker, taking the last word so that
  `show version`'s `Model: vmx` can be piped straight in.
- The marker is consumed on promotion, so it cannot be applied to the next dump.
- `23.2R2-S7.5.xsd` becomes `23.2R2-S7.5-vmx.xsd`: `show version` on
  bordergw0206 reported `Model: vmx`. The other two keep release-only names
  because nobody recorded where they came from.

## Capabilities

### New Capabilities

None; this is test-data bookkeeping.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Inferring the platform from feature depth. The evidence above says it cannot
  be done; a heuristic would be a guess wearing a measurement's clothes.
- Renaming the 23.4R2 and 25.2R2 dumps. Their origin is not recorded and I will
  not invent one.

## Impact

`tests/schema_data.py`, its README and the capture script. Four tests, none
needing a dump, in a new `tests/test_schema_naming.py` so they are not stranded
behind `--schema`.
