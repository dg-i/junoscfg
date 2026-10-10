# validation/raw-set-input Specification

## Purpose
Define how raw Junos set validation reports the intentionally unsupported
bracket shorthand without turning a validation result into an exception.

## Requirements

### Requirement: Set validation returns bracket errors per offending line

WHEN `SetValidator`, `validate_set`, or set-format `validate_config` receives a
raw set command containing an unquoted `[` or `]` THEN the system SHALL return
`ValidationResult(valid=False)` without throwing and SHALL add a line-specific
`ValidationError` whose message is `Unsupported bracket syntax in set input on
line N:\n<complete original offending line>`.
Tests: `tests/unit/validate/test_set_validator.py::TestSetBracketSyntaxRejection::test_validation_doors_return_line_errors_without_throwing`, `tests/unit/validate/test_set_validator.py::TestSetBracketSyntaxRejection::test_validation_collects_each_offending_line`

#### Scenario: One offending line

- **WHEN** any supported raw set command type contains an unquoted opening or
  closing square bracket
- **THEN** every validation door returns an invalid result carrying the exact
  two-line diagnostic for that complete line

#### Scenario: Several offending lines

- **WHEN** several raw set lines contain unquoted brackets
- **THEN** validation collects bracket errors with its normal per-line behavior

#### Scenario: Quoted content and comments

- **WHEN** brackets occur only in a quoted value or an ignored comment
- **THEN** the bracket detector adds no validation error for them

### Requirement: CLI validation distinguishes invalid input from conversion failure

WHEN validation-only CLI mode `-v -i set` receives raw set input containing an
unquoted bracket THEN the system SHALL print the same line-specific diagnostic
and exit 1 rather than raising or using the conversion exit code.
Tests: `tests/unit/cli/test_cli_validate.py::TestSetBracketSyntaxRejection::test_validation_only_exits_one_with_complete_diagnostic`

#### Scenario: Validation-only bracket input

- **WHEN** validation-only mode receives `set system apply-groups [ foo bar ]`
- **THEN** it exits 1 and shows the complete two-line diagnostic

### Requirement: The corpus distinguishes intentional exclusion from malformed input

WHEN the exact set corpus classifies validator rejections THEN the system SHALL
record device-valid bracket shorthand under `INTENTIONALLY_UNSUPPORTED`, SHALL
not count it as malformed or accidental over-rejection, and SHALL classify
`set policy-options community FOO members` as correctly rejected because the
leaf-list has no value.
Tests: `tests/corpus/test_set_corpus.py::TestShippedGrammarAgainstTheCorpus::test_rejections_are_exactly_the_recorded_ones`, `tests/corpus/test_set_corpus.py::TestShippedGrammarAgainstTheCorpus::test_the_recorded_rejections_are_still_in_the_corpus`

#### Scenario: Bracket shorthand classification

- **WHEN** the corpus contains device-valid raw set bracket shorthand
- **THEN** its exact rejection belongs to `INTENTIONALLY_UNSUPPORTED`

#### Scenario: Bare community members leaf-list

- **WHEN** the corpus contains `set policy-options community FOO members`
- **THEN** its rejection belongs to the correctly rejected category with a
  leaf-list-with-no-value reason
