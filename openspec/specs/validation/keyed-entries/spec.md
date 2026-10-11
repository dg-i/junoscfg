# validation/keyed-entries Specification

## Purpose
Field validation and the JSON and YAML schemas accept a list entry in the
shape the device keys it, by the fields the structure tree names, and refuse
the `name` spelling the readers used to put in their place.

## Requirements

### Requirement: Field validation checks each key field as a leaf

WHEN `validate_ir`, or a conversion that validates, checks an IR whose list
entries carry the fields `entry_keys()` names THEN field validation SHALL
validate each key value against its own leaf in the tree, a key choice's
chosen element, enum and pattern included, an enum closed for a field the tree
names in `k` and open, as a fragment, for a `name` key (owner decision,
challenge C); SHALL report no unplaced error for a key field, and SHALL report
`name`, `_v0` or `_v1` under a list keyed otherwise as unplaced; no key SHALL
be exempted by spelling.
Tests: `tests/unit/convert/test_field_validator.py::TestKeyedEntries::test_a_device_keyed_as_list_reference_is_clean`, `tests/unit/convert/test_field_validator.py::TestANameKeyIsOpen::test_a_classifier_name_is_clean`, `tests/unit/convert/test_field_validator.py::TestKeyedEntries::test_a_key_value_is_checked_against_its_leaf`, `tests/unit/convert/test_field_validator.py::TestKeyedEntries::test_name_under_a_list_keyed_otherwise_is_unplaced`, `tests/unit/convert/test_field_validator.py::TestKeyedEntries::test_attributes_match_takes_its_three_fields`, `tests/unit/convert/test_field_validator.py::TestKeyedEntries::test_a_route_filter_action_is_clean`

#### Scenario: AS-list reference

- **WHEN** the IR holds `{"list-type": "as-list", "list-name": "AS-LIST-A"}`
  under `from as-path-neighbors`
- **THEN** field validation reports no error

#### Scenario: A list-type outside its enum

- **WHEN** `list-type` holds `1`, which the device rejects at `set` with
  `as-path-neighbors 1 AS-LIST-A` (device probe, vMX 23.2R2-S7.5)
- **THEN** field validation reports an error naming `list-type`

#### Scenario: A name key outside its enum

- **WHEN** `class-of-service interfaces ge-0/0/0 unit 0 classifiers dscp
  SAMPLE-DSCP` is validated; `dscp` is keyed `name`, whose enum is `[default]`
- **THEN** field validation reports no error

#### Scenario: The retired spelling

- **WHEN** the entry under `as-path-neighbors` is `{"name": "as-list"}`, or an
  `attributes-match` entry carries `_v0`
- **THEN** field validation reports the key as unplaced

#### Scenario: A route-filter action

- **WHEN** a `route-filter` entry holds its `address`, `"exact": [null]` and
  `"accept": [null]`
- **THEN** field validation reports no error

### Requirement: An entry without a key field is unplaced

WHEN an entry from JSON, YAML or XML lacks one of the fields `entry_keys()`
names THEN field validation SHALL report it with the unplaced message
(`'<list>' entry without its key field '<field>' could not be placed in the
schema: kept as written, not validated`), so `--strict` refuses it, as it
refuses a set statement the reader could not complete. An anonymized run SHALL
walk the entry's fields like any entry's, so no rule misses a value in it, and
SHALL withhold the message's text (owner answer 5, spec anonymization/placed-values).
Tests: `tests/unit/convert/test_field_validator.py::TestAnEntryWithoutItsKeyIsUnplaced::test_validation_reports_it`, `tests/unit/convert/test_field_validator.py::TestAnEntryWithoutItsKeyIsUnplaced::test_each_structured_door_reports_it`, `tests/unit/convert/test_field_validator.py::TestAnEntryWithoutItsKeyIsUnplaced::test_a_complete_entry_is_clean`, `tests/unit/convert/test_field_validator.py::TestAnEntryWithoutItsKeyIsUnplaced::test_an_anonymized_run_replaces_its_addresses`

#### Scenario: An AS-list reference without its list-type

- **WHEN** `{"as-path-neighbors": [{"list-name": "X"}]}` arrives as JSON, YAML
  or XML, or a `route-filter` entry without its `address`
- **THEN** field validation reports it unplaced, where it was written as a line
  the device rejects with no diagnostic (phase-6 review, finding 5)

#### Scenario: Anonymized

- **WHEN** a BGP `neighbor` entry without its `name` holds `local-address
  203.0.114.9` and is converted with `--anonymize-ips`
- **THEN** the address is replaced, the run converts, and the `UNPLACED`
  message names its schema path only

### Requirement: The JSON and YAML schemas name the key fields

WHEN the JSON and YAML schemas are generated THEN a list entry's properties
SHALL hold its key fields from `entry_keys()`, and `name` only where `name` is
the key, with no `required` added; `validate_json`, `validate_yaml`,
`validate_config` and CLI `-v` on JSON or YAML SHALL accept the device-shaped
entry and reject one keyed `name` under a list keyed otherwise.
Tests: `tests/unit/validate/test_schema_generator.py::TestEntryKeysAreTheTreesFields::test_entry_properties_are_the_key_fields`, `tests/unit/validate/test_schema_generator.py::TestEntryKeysAreTheTreesFields::test_name_keyed_lists_keep_name`, `tests/unit/validate/test_schema_generator.py::TestEntryKeysAreTheTreesFields::test_no_required_is_added`, `tests/contract/test_every_door.py::TestAKeyedEntryTakesExactlyItsKeys::test_every_door_agrees`

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
- **THEN** it validates as before, and its schema is byte-identical

### Requirement: Field validation walks a transparent container's other children

WHEN field validation meets a transparent container (`interfaces`, `groups`,
`routing-instances`, `vlans`) THEN it SHALL validate the transparent child's
entries against the child's node and every other child (`interface-range`,
`interface-set`, `traceoptions`) against the container's own node, and SHALL
validate each entry of a list held by a container that is no list (NEW-A-S2).
Tests: `tests/unit/convert/test_field_validator.py::TestATransparentContainersOtherChildren::test_a_sibling_alone_is_placed`, `tests/unit/convert/test_field_validator.py::TestATransparentContainersOtherChildren::test_an_unknown_key_among_them_is_reported`, `tests/unit/convert/test_field_validator.py::TestATransparentContainersOtherChildren::test_each_entry_of_a_list_a_container_holds_is_validated`

#### Scenario: A sibling alone

- **WHEN** `set interfaces interface-range R1 member-range xe-0/0/0 to
  xe-0/0/3` or `set interfaces traceoptions file f1` is converted with no
  `interface` entry, `--strict` on
- **THEN** it converts; it was reported `could not be placed` and strict raised

#### Scenario: An unknown key beside the transparent child

- **WHEN** JSON holds `interface` entries beside an `interface-range` entry
  carrying `bogus-key`, or `traceoptions` carrying `bogus-trace`
- **THEN** each is reported `UNPLACED`, where it passed without a word
