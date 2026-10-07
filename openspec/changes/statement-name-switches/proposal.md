## Why

`protocols { ospf { disable; } }` converted to JSON as
`{"enable-disable": "disable"}`. A device renders it `{"disable": [null]}`, and
there is no `enable-disable` statement in Junos — so junoscfg emitted JSON and
YAML that no device would accept, on the path the downstream Ansible
collection renders through.

The schema folds an on/off switch into one nokeyword leaf whose name joins both
spellings, carrying the enum `['disable']`, so the token in a configuration is
the statement itself rather than a value beneath it. `set_to_dict` keyed the
dict on the schema node.

Nothing caught it. It is not a validation failure — the set form is correct and
parses — only the JSON and YAML output is wrong, silently. It was found by
round-tripping a device's own `| display json` and diffing against the input:
of the differences, 147 were this.

## What Changes

- A nokeyword leaf whose enum values are all words of its own name keys on the
  token. In 24.4R0 that is 4,238 nodes and every one is `enable-disable`; the
  26,386 positional nokeyword leaves and the 352 marked `freeform-nk` keep the
  node name.

## Capabilities

### New Capabilities

None; this repairs an existing one.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- The other three classes the same diff found: Junos emits numbers as JSON
  integers where junoscfg emits strings (285), `as-path-neighbors` list lengths
  differ (5), and `forwarding-options.analyzer` comes back a dict where the
  device has a list (1). The numeric one is a property of the string-valued IR
  and a larger decision than a defect.
- `protocols { ospf disable; }` rendering as a oneliner beside a second `ospf`
  block in structured output. Pre-existing and unchanged by this; verified
  against the parent commit.

## Impact

`src/junoscfg/convert/input/set_input.py`. JSON and YAML output for any
configuration carrying `disable` becomes what a device accepts;
`{"disable": [null]}` now round-trips to itself. Four tests, one of them seen
to fail with the fix reverted.
