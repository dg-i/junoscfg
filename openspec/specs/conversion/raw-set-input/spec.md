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
line as `Unsupported bracket syntax in set input on line N:\n<line>`. In a
conversion that anonymizes, the `ValueError` SHALL withhold the line and say
that the input could not be read (spec anonymization/placed-values, NEW-R4).
Tests: `tests/unit/convert/test_set_input.py::TestTheReaderRejectsBracketSyntax::test_every_command_and_bracket_form_is_rejected`, `tests/unit/convert/test_convert_api.py::TestSetBracketSyntaxRejection::test_public_conversion_doors_reject_without_validation`, `tests/unit/cli/test_cli.py::TestUsageErrorsExitTwo::test_set_bracket_syntax_is_refused_with_the_whole_line`, `tests/contract/test_every_message.py::TestAnAnonymizedRunQuotesNothingOfTheConfiguration::test_no_message_holds_a_word_of_it`

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

#### Scenario: An anonymized conversion

- **WHEN** `set system name-server [ 203.0.114.9 ]` is converted with an
  anonymizing rule, through the library or `junoscfg convert --anonymize-ips`
- **THEN** it is refused with `ValueError` (exit 2) whose text holds neither the
  line nor the address

### Requirement: Quoted content and ignored comments remain accepted

WHEN square brackets occur only inside a quoted raw set value or on an ignored
comment line THEN the system SHALL treat them as content rather than unsupported
bracket syntax.
Tests: `tests/unit/convert/test_set_input.py::TestTheReaderRejectsBracketSyntax::test_quoted_brackets_and_comments_remain_ordinary_content`

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
Tests: `tests/unit/display/test_set_converter.py::TestStructuredBracketLists::test_structured_bracket_list_emits_repeated_set_commands`

#### Scenario: VLAN members list

- **WHEN** structured input contains `vlan { members [ v10 v20 ]; }`
- **THEN** structured-to-set conversion succeeds and emits one `members v10`
  command and one `members v20` command

### Requirement: Raw set conversion refuses unsupported command lines
WHEN a visible physical raw set line is outside the existing nonempty `set `, `deactivate `, `protect `, `delete ` or `activate ` command dispatch THEN the system SHALL refuse the complete input before constructing or rendering a partial configuration, with InputError (a ValueError) carrying its original physical line number and a value-free message `Unsupported command in set input on line N`. Existing unquoted bracket refusal retains precedence. Validation or strictness options SHALL NOT bypass this refusal.
Tests: `tests/unit/convert/test_set_commands.py::test_unsupported_commands_are_refused`, `tests/unit/convert/test_set_commands.py::test_conversion_doors_refuse_before_rendering`, `tests/unit/convert/test_set_commands.py::test_cli_refusal_has_no_partial_output`, `tests/unit/convert/test_set_commands.py::test_anonymized_refusal_withholds_source`, `tests/unit/convert/test_set_commands.py::test_audit_rejects_before_emitting_findings`

#### Scenario: Interactive commands and bare commands
- **WHEN** input includes annotate, insert, replace (including pattern), rename, copy, edit, top, up, wildcard, unprotect, load, commit, status, show, arbitrary unknown commands, or a supported verb with no path
- **THEN** conversion refuses rather than silently omit that line.

#### Scenario: Original line numbering
- **WHEN** an unsupported command follows blank or comment lines or a closing leading block comment
- **THEN** the refusal names that original physical line and includes no source values.

#### Scenario: Public conversion and CLI doors
- **WHEN** to_dict, pipeline, pipeline_result, convert_config, convert_config_result or CLI conversion/audit reads an unsupported line
- **THEN** it refuses independently of validation and strictness; CLI conversion exits 2 and has no partial output; anonymization withholds source and preserves the physical line.

### Requirement: Existing supported raw set content remains intact
WHEN raw set input contains only existing supported command dispatch forms or blank/comment lines THEN the system SHALL preserve its existing IR and metadata behavior. Command-like words within a quoted value SHALL remain content. Set path grammar, unplaced-statement policy and bracket handling SHALL remain unchanged.
Tests: `tests/unit/convert/test_set_commands.py::test_supported_commands_keep_their_metadata`, `tests/unit/convert/test_set_commands.py::test_comments_and_command_words_in_values_remain_content`, `tests/unit/convert/test_set_commands.py::test_bracket_refusal_keeps_precedence`

#### Scenario: Metadata commands
- **WHEN** set, deactivate, protect, delete or activate appears with a previously supported path
- **THEN** host-name and its existing inactive/protect/operation/active metadata are preserved.

#### Scenario: Ignored comments and quoted values
- **WHEN** command words occur only in comments or a quoted description
- **THEN** they do not cause unsupported-command rejection.
