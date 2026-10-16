## ADDED Requirements

### Requirement: Set validation reads every verb conversion reads

WHEN set input carries a `protect`, `activate`, `delete` or `deactivate` line THEN set
validation SHALL validate the statement path after the verb as `set` validates it, except
that the path may stop where one value would follow (the device prints `deactivate ...
max-hello-size`): such a line is valid when the grammar takes it with one value more, so a
path that stops inside an entry's key, before a keyword the key still needs, is invalid
(`deactivate ... route-filter 10.0.0.0/8` without its match type), through `SetValidator.validate`, `JunosValidator.validate_set`,
`validate_set`, `validate_config`, `validate_structured` and CLI `-v -i set|structured`; a
`set` line SHALL still give a leaf its value, and a line starting with any other word SHALL
be rejected; an error message SHALL carry the whole line, never a cut one.
Tests: `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_verb_line_is_validated_as_its_path`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_an_invalid_path_after_a_verb_is_reported`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_set_gives_a_leaf_its_value`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_another_verb_is_no_command`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_long_line_is_reported_whole`, `tests/contract/test_every_door.py::TestEveryVerbNamesAStatementPath::test_every_door_agrees`

#### Scenario: A protected group

- **WHEN** `protect groups GR-PROTECTED` follows the group's `set` lines
- **THEN** the input is valid through every door

#### Scenario: A deactivated leaf

- **WHEN** `deactivate system host-name` follows `set system host-name router1`
- **THEN** the input is valid, while `set system host-name` alone is not

#### Scenario: A line that stops inside an entry's key

- **WHEN** `deactivate policy-options policy-statement P term T from route-filter 10.0.0.0/8`
  follows the route filter's `set` line with its match type `exact`
- **THEN** the line is invalid through every door, as the set reader cannot place it

#### Scenario: A long invalid line

- **WHEN** a line longer than 80 characters is invalid
- **THEN** the error quotes it whole
