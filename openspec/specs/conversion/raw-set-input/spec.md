# conversion/raw-set-input Specification

## Purpose
Define the accepted lexical boundary for raw Junos set input and prevent
unsupported spellings from entering the configuration IR.

## Requirements

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

### Requirement: Quoted content and ignored comments remain accepted

WHEN square brackets occur only inside a quoted raw set value or on an ignored
comment line THEN the system SHALL treat them as content rather than unsupported
bracket syntax.
Tests: `tests/test_set_input.py::TestSetBracketSyntaxRejection::test_quoted_brackets_and_comments_remain_ordinary_content`

#### Scenario: Quoted regular-expression value

- **WHEN** raw set input contains `set policy-options community FOO members
  "64498:[2-6]....$"`
- **THEN** conversion accepts the brackets as part of the quoted value

#### Scenario: Ignored comment

- **WHEN** an otherwise ignored comment line contains `[` or `]`
- **THEN** the comment does not trigger bracket rejection

### Requirement: Structured bracket lists retain canonical conversion

WHEN structured Junos input contains a bracket list THEN the system SHALL keep
accepting that structured syntax and SHALL render canonical set output as one
repeated command per list value; raw set users migrating from bracket shorthand
SHALL be able to supply those repeated commands instead.
Tests: `tests/test_set_converter.py::TestStructuredBracketLists::test_structured_bracket_list_emits_repeated_set_commands`

#### Scenario: VLAN members list

- **WHEN** structured input contains `vlan { members [ v10 v20 ]; }`
- **THEN** structured-to-set conversion succeeds and emits one `members v10`
  command and one `members v20` command
