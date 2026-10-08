## Why

The generated JSON Schema lets every container's type admit an array, so a
bare statement rendered as `[null]` passes, but gives the array no `items`
constraint. `properties` and `additionalProperties: false` bind only objects,
so the entries of every named list, always written as arrays, go unchecked:
`-v` passes an interface entry holding `mtuu` and `[42]` as an interface list,
where the field validator and the set grammar reject both. Found at the v0.7.0
review, whose tightening was dropped for rejecting valid Junos, and again by
the split-brain audit of 2026-10-08. Step 6 of the schema replacement plan.

## What Changes

- `_container_schema` gives the array form an `items` constraint: `null` for a
  bare statement, `string` for a leaf-list value, the child's entry schema on
  a transparent container; `string` leaves the container type. The plan's six
  probes reject and its four shapes validate. **BREAKING** on `api` and `cli`:
  `validate_json`, `validate_yaml` and `-v` report invalid where they passed.
- `required` leaves the schema. Its 8,782 arrays were inert; live, they reject
  every fragment (`user admin uid 2000` for want of `class`), which is what
  broke the first attempt. Mandatory stays a field-validator warning.
- `@` attribute keys are named in `patternProperties`; the schema has to
  accept junoscfg's own output. Both schema artifacts are regenerated.

## Capabilities

### New Capabilities

None; the schema enforces what it has claimed to since 0.5.0.

### Modified Capabilities

None at spec level; `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Audit finding 3, aliases on JSON input: `ieee-802.3ad` now fails `-v` as it
  fails `--strict`. One defect, one change, after this.
- Statements the schema does not model: they fail `-v` as they fail `--strict`.
- Enum, pattern or type checks in the JSON Schema; it stays structural.

## Impact

Examples: all three validate before and after. jvd, 150 of 1,535 sampled under
an in-memory patch: 25 files invalid before, 42 after, `required` kept or
dropped alike; every new rejection is an unmodelled statement field validation
already reports. `validate/schema_generator.py`, both artifacts, two test
files. Minor bump to 0.11.0 (0.10.0 went to step 4); the Ansible collection calls
`validate_config`.
