## Removed

- The array escape in `_container_schema`: a container's type union admitted
  `array` with no `items` constraint. `properties` and `additionalProperties`
  are object-only keywords, so the moment a value was wrapped in an array
  neither bound anything — 43,331 `additionalProperties: false` nodes in the
  shipped schema enforced nothing behind one, and `{"configuration": "garbage"}`
  validated. The array form now carries `null` and `string`, or a transparent
  container's child entries, and nothing else.
- `string` from the container type union. A bare string is a leaf's rendering,
  not a container's.
- `required` from the generated schema, all 8,782 arrays. They were inert
  behind the escape; live, they rejected every fragment that omits a field the
  XSD marks mandatory for a whole configuration — `set system login user admin
  uid 2000` for want of `class`. Mandatory stays a field-validator warning,
  which is where a device-side rule on a partial document belongs.

## Added

- `^@` in every container's `patternProperties`, both variants. A device puts
  its attributes there (`junos:commit-seconds` and friends), junoscfg's
  converters round-trip them, and `field_validator` already skips the prefix;
  the schema had never named it, which the escape hid.
- `tests/test_round_trip_validates.py::TestTheSchemaStillRejects` — six
  probes against the shipped artifact and two positive guards.
- `tests/test_round_trip_validates.py::TestFragmentsWithoutMandatoryFieldsStayValid`.
- Four tests in `tests/test_schema_generator.py::TestGenerateJsonSchema`.
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

## Not retired

- The unwrapped-root `groups` escape in `generate_json_schema` and the nested
  `groups` escape in `_container_schema` (`{"type": ["object", "array",
  "null"]}`, no `items`), both for a document given without the `configuration`
  wrapper or with groups inside groups. Recursive, out of this change's
  statement, left as they were.
- Enum, pattern and type checks. The schema stays structural; the field
  validator owns values.
