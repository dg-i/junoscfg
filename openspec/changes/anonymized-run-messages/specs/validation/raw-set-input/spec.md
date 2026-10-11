## MODIFIED Requirements

### Requirement: CLI validation distinguishes invalid input from conversion failure

WHEN validation-only CLI mode `-v -i set` receives raw set input containing an
unquoted bracket THEN the system SHALL print the same line-specific diagnostic
and exit 1 rather than raising or using the conversion exit code. WHEN the same
command also anonymizes (`--anonymize-*`) THEN it SHALL exit 1 and print each
error's line with its text and document path withheld (spec
anonymization/placed-values, NEW-R1).
Tests: `tests/contract/test_every_door.py::TestBracketShorthandIsRejected::test_every_door_agrees`, `tests/contract/test_every_message.py::TestAnAnonymizedRunQuotesNothingOfTheConfiguration::test_no_message_holds_a_word_of_it`

#### Scenario: Validation-only bracket input

- **WHEN** validation-only mode receives `set system apply-groups [ foo bar ]`
- **THEN** it exits 1 and shows the complete two-line diagnostic

#### Scenario: Validation-only bracket input in an anonymized run

- **WHEN** `junoscfg convert -v -i set --anonymize-ips` receives
  `set system name-server [ 203.0.114.9 ]`
- **THEN** it exits 1 and prints `line 1` with neither the line nor the address
