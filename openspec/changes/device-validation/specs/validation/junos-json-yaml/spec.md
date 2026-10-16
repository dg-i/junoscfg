## ADDED Requirements

### Requirement: A JSON validation message names the path and the keys

WHEN JSON, yaml-new or yaml validation reports an error THEN the message SHALL name the
deepest failing path and the offending keys or the kind of the failure (an unexpected key, a
wrong type), and SHALL NOT reprint the instance or a subtree of it: a list entry's failure is
reported at the entry, never as the whole list's repr.
Tests: `tests/unit/validate/test_json_yaml_validator.py::TestAMessageNamesThePathAndTheKeys::test_a_failing_entry_is_named_by_its_path_and_key`, `tests/unit/validate/test_json_yaml_validator.py::TestAMessageNamesThePathAndTheKeys::test_no_message_reprints_a_value`, `tests/unit/validate/test_json_yaml_validator.py::TestAMessageNamesThePathAndTheKeys::test_a_failure_deep_in_a_list_is_named_where_it_is`

#### Scenario: An unknown key in a list entry

- **WHEN** an interface entry in a JSON configuration carries an unknown key beside a
  `description`
- **THEN** the one error names `configuration.interfaces.interface.0` and the key, and holds
  no description text

### Requirement: Presence statements validate in both device spellings

WHEN an empty statement is written `[null]` or `{}` in JSON or yaml-new (the vMX 23.2R2
capture writes `[null]` where the QFX5120 25.2R2 capture writes an empty container `{}`)
THEN JSON validation and field validation SHALL accept both.
Tests: `tests/unit/validate/test_json_yaml_validator.py::TestPresenceInBothDeviceSpellings::test_both_spellings_validate`

#### Scenario: BGP flags

- **WHEN** `family inet-vpn unicast`, `multipath` and `bgp-error-tolerance` are written `{}`
- **THEN** the JSON is valid, as with `[null]`
