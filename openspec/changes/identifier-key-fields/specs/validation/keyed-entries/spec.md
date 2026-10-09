## Purpose

Field validation and the JSON and YAML schemas accept a list entry in the
shape the device keys it, by the fields the structure tree names, and refuse
the `name` spelling the readers used to put in their place.

## ADDED Requirements

### Requirement: Field validation accepts device-keyed entries

WHEN `validate_ir`, or a conversion that validates, checks an IR whose list
entries carry the fields the tree names THEN field validation SHALL report no
unplaced error for a key field, SHALL validate each key value against its own
leaf, and SHALL report `name`, `_v0` or `_v1` under a list keyed otherwise as
unplaced.
Tests: `tests/test_field_validator.py::TestKeyedEntries::test_a_device_keyed_as_list_reference_is_clean`, `tests/test_field_validator.py::TestKeyedEntries::test_a_key_value_is_checked_against_its_leaf`, `tests/test_field_validator.py::TestKeyedEntries::test_name_under_a_list_keyed_otherwise_is_unplaced`, `tests/test_field_validator.py::TestKeyedEntries::test_attributes_match_takes_its_three_fields`

#### Scenario: AS-list reference

- **WHEN** the IR holds `{"list-type": "as-list", "list-name": "AS-LIST-A"}`
  under `from as-path-neighbors`
- **THEN** field validation reports no error

#### Scenario: A key value outside its leaf

- **WHEN** `list-type` holds a value its enum does not list
- **THEN** field validation reports an error naming `list-type`

#### Scenario: The retired spelling

- **WHEN** the entry under `as-path-neighbors` is `{"name": "as-list"}`, or an
  `attributes-match` entry carries `_v0`
- **THEN** field validation reports the key as unplaced

### Requirement: The JSON and YAML schemas name the key fields

WHEN the JSON and YAML schemas are generated THEN a list entry's properties
SHALL hold its key fields from `entry_keys()`, and `name` only where that is
the key; `validate_json`, `validate_yaml`, `validate_config` and CLI `-v` on
JSON or YAML SHALL accept the device-shaped entry and reject one keyed `name`
under a list keyed otherwise.
Tests: `tests/test_schema_generator.py::TestEntryKeysAreTheTreesFields::test_entry_properties_are_the_key_fields`, `tests/test_schema_generator.py::TestEntryKeysAreTheTreesFields::test_name_keyed_lists_keep_name`, `tests/test_json_yaml_validator.py::TestKeyedEntries::test_the_device_shaped_as_list_reference_validates`, `tests/test_json_yaml_validator.py::TestKeyedEntries::test_name_under_an_as_list_reference_is_rejected`, `tests/test_cli_validate.py::TestCliValidation::test_validate_json_with_an_as_list_reference`

#### Scenario: Device-shaped JSON

- **WHEN** JSON holding the device-shaped AS-list entry is validated through
  each door
- **THEN** it is valid, and the same in YAML is valid

#### Scenario: Name in its place

- **WHEN** the entry under `as-path-neighbors` is `{"name": "as-list"}`, or a
  `source-address-filter` entry is keyed `name`
- **THEN** JSON and YAML validation reject it

#### Scenario: A list keyed name

- **WHEN** a `policy-statement` entry is keyed `name`
- **THEN** it validates as before
