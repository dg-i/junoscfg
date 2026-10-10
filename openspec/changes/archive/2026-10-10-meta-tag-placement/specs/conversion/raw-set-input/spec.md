## MODIFIED Requirements

### Requirement: Raw set conversion rejects unquoted square brackets

WHEN any line of raw set input, whatever its command (`set`, `delete`,
`deactivate`, `activate`, `protect` or another), contains an unquoted `[` or
`]` THEN the system
SHALL reject the input before constructing an IR with `ValueError`, independent
of validation and strictness, and SHALL report the complete original offending
line as `Unsupported bracket syntax in set input on line N:\n<line>`.
Tests: `tests/test_set_input.py::TestSetBracketSyntaxRejection::test_every_command_and_bracket_form_is_rejected`, `tests/test_convert_api.py::TestSetBracketSyntaxRejection::test_public_conversion_doors_reject_without_validation`, `tests/test_cli.py::TestSetBracketSyntaxRejection::test_conversion_exits_two_with_complete_diagnostic`

#### Scenario: Bracket-form matrix

- **WHEN** a raw set command contains `[ foo bar ]`, `[foo bar]`, `[]`, `[ ]`,
  a lone opening bracket, a lone closing bracket, a scalar bracket value, or an
  `apply-groups` bracket value
- **THEN** conversion rejects the first offending line with the specified
  two-line diagnostic and preserves that line without truncation

#### Scenario: Validation bypass does not bypass the boundary

- **WHEN** `convert_config(..., from_format=Format.SET, validate=False)` receives
  raw set input containing an unquoted bracket
- **THEN** it raises the same `ValueError` as `set_to_dict` and `to_dict`

#### Scenario: CLI conversion

- **WHEN** CLI conversion or import receives raw set input containing an
  unquoted bracket
- **THEN** it prints the specified diagnostic and exits 2
