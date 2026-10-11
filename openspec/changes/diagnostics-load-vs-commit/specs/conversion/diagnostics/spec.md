## MODIFIED Requirements

### Requirement: The caller owns diagnostic rendering

WHEN conversion produces field-validation messages, anonymization debug logs,
or structured-output loss notes THEN the system SHALL carry them as diagnostics
without writing from library code, and the CLI SHALL render their existing text
to stderr with unchanged exit behavior. WHEN field validation finds a warning
THEN the system SHALL carry it as a diagnostic whether or not the validation
also found errors, and WHEN `strict` is set THEN only errors SHALL raise
`FieldValidationError`; a configuration with warnings and no errors SHALL
convert with its warnings carried.

Tests: `tests/unit/convert/test_conversion_diagnostics.py::TestDiagnosticRouting::test_cli_is_only_stderr_renderer`, `tests/unit/convert/test_conversion_diagnostics.py::TestAFieldWarningNeedsNoError::test_every_door_reports_it`, `tests/unit/convert/test_conversion_diagnostics.py::TestAFieldWarningNeedsNoError::test_an_error_beside_it_changes_nothing`, `tests/unit/convert/test_conversion_diagnostics.py::TestAFieldWarningNeedsNoError::test_the_cli_prints_it`

#### Scenario: Library call

- **WHEN** an in-process caller converts input that produces diagnostics
- **THEN** process stderr stays empty and the structured result contains them

#### Scenario: CLI call

- **WHEN** the CLI performs the same conversion
- **THEN** it writes the same diagnostic wording to stderr

#### Scenario: A warning without an error

- **WHEN** a configuration whose only field-validation finding is a warning
  (`set access radius-server 192.168.50.10`, no `secret`, as the vMX
  23.2R2-S7.5 loaded it in
  `tests/data/device/synthetic/vmx-23.2R2-S7.5/synthetic-probes.set.gz`) is
  converted from set, structured, JSON, YAML or XML, with or without `strict`
- **THEN** the result carries the warning as a `field-validate` diagnostic at
  `access.radius-server.secret`, nothing is raised, and `junoscfg
  convert` (with or without `--strict`) prints it on stderr and exits 0

#### Scenario: A warning beside an error

- **WHEN** the same configuration also holds a statement field validation
  reports as an error and `strict` is not set
- **THEN** the result carries the same warning as without the error, beside
  the error

## ADDED Requirements

### Requirement: A missing mandatory statement is reported as a commit-time warning

WHEN a configuration lacks a statement the schema marks mandatory THEN field
validation SHALL report a warning, never an error, whose message names the
statement and says that Junos requires it at commit and loads the
configuration without it; `strict` SHALL NOT raise on it. Device evidence: the
vMX (23.2R2-S7.5) and the QFX5120 (25.2R2-S1.5) loaded `access profile PROF-1
radius-server 192.168.50.10 timeout 10` without `secret`
(`tests/data/device/synthetic/*/junoscfg-oracle.set.gz`); the commit half is
the schema model's `mandatory` flag, as no capture is committed.

Tests: `tests/unit/convert/test_field_validator.py::TestMandatoryValidation::test_the_message_names_the_commit_boundary`, `tests/unit/convert/test_field_validator.py::TestTheExampleConfigurationValidates::test_every_statement_the_schema_places_validates`

#### Scenario: The radius-server secret

- **WHEN** `access profile PROF-1 radius-server 192.168.50.10` carries no
  `secret`
- **THEN** the warning at `access.profile.radius-server.secret` reads
  `Missing mandatory field 'secret': required at commit; the configuration
  loads without it`, and the validation result is valid
