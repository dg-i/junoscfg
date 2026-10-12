## ADDED Requirements

### Requirement: Raw set conversion refuses unsupported command lines
WHEN a visible physical raw set line is outside the existing nonempty `set `, `deactivate `, `protect `, `delete ` or `activate ` command dispatch THEN the system SHALL refuse the complete input before constructing or rendering a partial configuration, with InputError (a ValueError) carrying its original physical line number and a value-free message `Unsupported command in set input on line N`. Existing unquoted bracket refusal retains precedence. Validation or strictness options SHALL NOT bypass this refusal.
Tests: `tests/unit/convert/test_set_commands.py::test_unsupported_commands_are_refused`, `tests/unit/convert/test_set_commands.py::test_conversion_doors_refuse_before_rendering`, `tests/unit/convert/test_set_commands.py::test_cli_refusal_has_no_partial_output`, `tests/unit/convert/test_set_commands.py::test_anonymized_refusal_withholds_source`

#### Scenario: Interactive commands and bare commands
- **WHEN** input includes annotate, insert, replace (including pattern), rename, copy, edit, top, up, wildcard, unprotect, load, commit, status, show, arbitrary unknown commands, or a supported verb with no path
- **THEN** conversion refuses rather than silently omit that line.

#### Scenario: Original line numbering
- **WHEN** an unsupported command follows blank or comment lines or a closing leading block comment
- **THEN** the refusal names that original physical line and includes no source values.

#### Scenario: Public conversion and CLI doors
- **WHEN** to_dict, pipeline, pipeline_result, convert_config, convert_config_result or CLI conversion/import reads an unsupported line
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
