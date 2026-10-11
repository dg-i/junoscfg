## MODIFIED Requirements

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

## ADDED Requirements

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
