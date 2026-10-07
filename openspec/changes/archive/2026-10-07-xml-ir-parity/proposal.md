## Why

The same configuration produced two different IRs depending on which format it
arrived in. Measured on `examples/router1.*`, which are three renderings of one
configuration: **15 divergences**, 11 of them `str` versus `int` and 4 from an
unresolved key alias.

- `KEY_ALIASES` was consulted only in `convert/input/set_input.py`, so the XML
  path kept `ieee-802.3ad` where the structured path gave `802.3ad`.
- `_coerce_value` turned numeric-looking XML text into `int`, "for cleaner YAML
  output". The structured and set paths never did, and Junos JSON is
  string-valued, so `"uid": 2000` and `"uid": "2000"` were both reachable.

Set-side rendering hid both — XML and structured produced byte-identical `.set`
output — which is why it survived to be found by onboarding phase 3.

`ARCHITECTURE.md` section 8 says there is one interchange format. Two spellings
of the same leaf is that rule broken.

## What Changes

- Resolve key aliases on the XML path, as the set path already did.
- `_coerce_value` returns the text. Leaf values are strings in the IR,
  whichever format they came from.
- Rewrite the characterization class that pinned the divergence; it now pins
  the parity, including that the two IRs are equal for the whole fixture.
- Record the rule in `ARCHITECTURE.md` section 8 and in the convert contract,
  so it is enforced rather than remembered.

## Capabilities

### New Capabilities

None; this makes one existing capability behave the same on every input.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Changing set or structured output. Both already agreed and still do.

## Impact

`src/junoscfg/display/to_yaml.py` (kernel zone). JSON and YAML output from XML
input changes: `mtu: 9216` becomes `mtu: '9216'`, and `ieee-802.3ad` becomes
`802.3ad`. That is the point — the structured path already produced both — but
anyone diffing XML-derived JSON across this version sees it.
