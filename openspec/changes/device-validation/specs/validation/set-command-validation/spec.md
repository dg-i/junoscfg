## ADDED Requirements

### Requirement: Set validation reads every verb conversion reads

WHEN set input carries a `protect`, `activate`, `delete` or `deactivate` line THEN set
validation SHALL validate the statement path after the verb, as for `set`, through
`SetValidator.validate`, `validate_set`, `validate_config` and CLI `-v -i set`, and SHALL
reject a line with any other verb; an error message SHALL carry the whole line, never a cut
one.
Tests: `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_verb_line_is_validated_as_its_path`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_an_invalid_path_after_a_verb_is_reported`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_long_line_is_reported_whole`, `tests/unit/validate/test_set_validator.py::TestSetValidator::test_no_set_prefix_error`

#### Scenario: A protected group

- **WHEN** `protect groups GR-PROTECTED` follows the group's `set` lines
- **THEN** the input is valid

#### Scenario: A long invalid line

- **WHEN** a line longer than 80 characters is invalid
- **THEN** the error quotes it whole
