## ADDED Requirements

### Requirement: Set validation shares unsupported command classification
WHEN SetValidator, validate_set or set-format validate_config receives visible unsupported command lines THEN the system SHALL return an invalid ValidationResult, collecting one line-specific error per offending line with the shared value-free message `Unsupported command in set input on line N`. Existing bracket refusal retains precedence; supported path grammar and existing validation behavior for metadata commands SHALL NOT be broadened.
Tests: `tests/unit/convert/test_set_commands.py::test_validation_doors_collect_value_free_command_errors`, `tests/unit/convert/test_set_commands.py::test_cli_validation_refuses_without_conversion`

#### Scenario: Multiple physical lines
- **WHEN** annotate and insert follow blank or ignored comment lines
- **THEN** every validation door reports the original line numbers without exposing supplied values.

#### Scenario: Validation-only CLI
- **WHEN** validation-only CLI receives unsupported commands
- **THEN** it exits 1 and reports line-specific errors; an anonymized run withholds the configuration.
