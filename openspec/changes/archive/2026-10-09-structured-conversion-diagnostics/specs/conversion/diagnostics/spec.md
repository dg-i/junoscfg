## Purpose

Let in-process conversion callers receive diagnostics as data while leaving
terminal rendering to the CLI.

## ADDED Requirements

### Requirement: Offer structured results without changing legacy return types

WHEN a caller opts into `convert_config_result()` or `pipeline_result()` THEN
the system SHALL return converted output plus immutable structured diagnostics,
while `convert_config()` and `pipeline()` continue to return only strings.

Tests: `tests/test_conversion_diagnostics.py::TestStructuredConversionResult::test_opt_in_result_preserves_legacy_return_contracts`

#### Scenario: Top-level package door

- **WHEN** the caller uses `convert_config_result()`
- **THEN** it receives a conversion result with output and diagnostics

#### Scenario: Conversion package door

- **WHEN** the caller uses `pipeline_result()`
- **THEN** it receives the same structured result shape

#### Scenario: Existing package doors

- **WHEN** the caller uses `convert_config()` or `pipeline()`
- **THEN** the return value remains a string

### Requirement: The caller owns diagnostic rendering

WHEN conversion produces field-validation messages, anonymization debug logs,
or structured-output loss notes THEN the system SHALL carry them as diagnostics
without writing from library code, and the CLI SHALL render their existing text
to stderr with unchanged exit behavior.

Tests: `tests/test_conversion_diagnostics.py::TestDiagnosticRouting::test_cli_is_only_stderr_renderer`

#### Scenario: Library call

- **WHEN** an in-process caller converts input that produces diagnostics
- **THEN** process stderr stays empty and the structured result contains them

#### Scenario: CLI call

- **WHEN** the CLI performs the same conversion
- **THEN** it writes the same diagnostic wording to stderr
