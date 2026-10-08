## Removed

- The array escape in `_container_schema`: a container's type union admitted
  `array` with no `items` constraint. `properties` and `additionalProperties`
  are object-only keywords, so the moment a value was wrapped in an array
  neither bound anything — every `additionalProperties: false` node in the
  shipped 25.2R2 schema, 52,219 of them, enforced nothing behind one, and
  `{"configuration": "garbage"}` validated. The array form now carries `null`
  and `string`, or on `groups` alone its child's entries, and nothing else.
- `string` from the container type union. A bare string is a leaf's rendering,
  not a container's.
- `required` from the generated schema, all 8,782 arrays. They were inert
  behind the escape; live, they rejected every fragment that omits a field the
  XSD marks mandatory for a whole configuration — `set system login user admin
  uid 2000` for want of `class`. Mandatory stays a field-validator warning —
  which the API reports and the CLI prints only beside an error, so a `-v` or
  `--strict` user sees nothing for it; that is unchanged from before.

## Added

- `^@` in every container's `patternProperties`, both variants. A device puts
  its attributes there (`junos:commit-seconds` and friends), junoscfg's
  converters round-trip them, and `field_validator` already skips the prefix;
  the schema had never named it, which the escape hid.
- `tests/test_round_trip_validates.py::TestTheSchemaStillRejects` — seven
  probes against the shipped artifact and two positive guards.
- `tests/test_round_trip_validates.py::TestFragmentsWithoutMandatoryFieldsStayValid`.
- Five tests in `tests/test_schema_generator.py::TestGenerateJsonSchema`.
- `changelog.d/+validate-list-entries.bugfix.md`.

## Changed, not removed

- `tests/test_schema_generator.py::test_mandatory_in_required` becomes
  `test_mandatory_is_a_warning_not_a_schema_requirement`, asserting the
  inverse. It pinned a requirement the proposal removes; under beta the break is
  declared in `.openspec.yaml`, so the test is inverted with its reason rather
  than weakened or deleted.
- `test_the_yaml_variant_keeps_its_own_patterns` adds `^@` to the expected set.
- Both JSON-schema artifacts regenerated from the bundled 25.2R2 structure tree.
  The grammar, the tree and the metadata are untouched.

## Cost recorded

- The artifacts grow: `junos-json-schema.json.gz` 652 KB → ~960 KB,
  `junos-yaml-schema.json.gz` likewise, `Draft7Validator` load 0.17 s → ~0.3 s.
  `properties["group"]` is inlined into `groups`' `items.anyOf`, which
  serialises the whole `group` entry schema a second time. A `$ref` to a def
  would avoid it; left for a follow-up because it is a size cost, not a
  correctness one.
- The error a user sees for the new rejection names the enclosing *list* and
  prints it — jsonschema reports a list matching neither `anyOf` branch as one
  error — not the offending key. Pre-existing formatting in
  `json_yaml_validator._validate_data`; this change makes it the first thing a
  `-v` user meets on a device config. Follow-up: descend the error's context.

## Not retired

- The branch `child_name == "groups" and depth > 0` in `_container_schema`,
  typed `["object", "array", "null"]` with no `items`. It was written for
  groups inside groups, which Junos does not have; in the shipped artifact it
  serves three unrelated statements named `groups` (`ietf-netconf-acm:nacm`,
  `openconfig-platform-port:breakout-mode`, `igmp-snooping … source`). Left as
  it was; recorded here under its real description.
- The unwrapped-root `groups` escape in `generate_json_schema`, for a document
  given without the `configuration` wrapper. Left.
- What the array form still admits, by design: a list position takes nested
  arrays and strings; presence flags (123,636 nodes) take any object or array;
  leaves take anything; `_MAX_DEPTH = 12` accepts anything below it. The schema
  is structural; `additionalProperties: false` binds inside list entries,
  behind arrays and inside `groups` entries, on non-presence containers, to
  depth 12 — and that is the claim, not more.
- Enum, pattern and type checks. The field validator owns values.
