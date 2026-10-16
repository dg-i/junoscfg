# validation/device-captures Specification

## Purpose
A device capture is configuration a Junos device loaded and printed; every statement in it is
valid Junos. Validating any of its renderings therefore reports nothing but findings recorded
with a reason, so a validator that starts rejecting what the device printed fails a test.

## Requirements

### Requirement: A device capture validates with only its recorded findings

WHEN a committed capture under `tests/data/device/` is read in each of its renderings (curly,
set, JSON, XML) through `convert_config_result` with field validation, in default and in
strict mode, WHEN its JSON rendering is validated through `validate_config(format="json")`,
and WHEN junoscfg's JSON output of each rendering is validated the same way THEN the system
SHALL report exactly the findings `tests/data/device/expected-findings.json` records for that
rendering and door, each with a reason (a mandatory statement the device itself warns about,
an open device question); strict mode SHALL raise exactly when a recorded finding is an error;
a finding not recorded SHALL fail, and so SHALL a recorded one that no longer appears. Set
`-v` of device lines runs where the grammar is compiled (`tests/corpus/test_set_corpus.py`):
the covering `set` lines of the grammar corpus and every line of every capture with another
verb; curly `-v` checks the set lines the conversion walk reads, those the device's own set
holds through those and the rest directly; every line of every capture runs under
`--device-grammar`.
Tests: `tests/corpus/test_device_renderings.py::TestTheValidatorsTakeWhatTheDevicePrinted::test_only_the_recorded_findings_are_reported`, `tests/corpus/test_device_renderings.py::TestTheValidatorsTakeWhatTheDevicePrinted::test_strict_mode_raises_only_on_a_recorded_error`, `tests/corpus/test_set_corpus.py::TestEveryCaptureValidatesAsSet::test_the_curly_rendering_validates_as_its_set_lines`, `tests/corpus/test_set_corpus.py::TestEveryCaptureValidatesAsSet::test_every_verb_line_of_the_capture_validates`, `tests/corpus/test_set_corpus.py::TestEveryCaptureValidatesAsSet::test_the_captures_hold_verb_lines`, `tests/corpus/test_device_renderings.py::TestTheValidatorsTakeWhatTheDevicePrinted::test_every_recorded_finding_has_a_reason`, `tests/corpus/test_set_corpus.py::TestTheGrammarTakesWhatDevicesPrint::test_the_false_rejections_are_exactly_the_recorded_ones`, `tests/corpus/test_set_corpus.py::TestEveryDeviceLine::test_only_the_recorded_lines_are_rejected`

#### Scenario: The QFX5120 capture

- **WHEN** `synthetic/qfx5120-25.2R2-S1.5/junoscfg-oracle` is validated in all four renderings
- **THEN** the only findings are the mandatory `secret` of `access profile ... radius-server`,
  which the device's own curly rendering warns about

#### Scenario: A new false rejection

- **WHEN** the shipped artifacts stop placing a statement a capture holds
- **THEN** the law fails, naming the capture, rendering, door and finding

### Requirement: Statements the device prints undocumented are modelled

WHEN a committed capture holds a statement the device's XML wraps in `<undocumented>` and
Juniper's XSD omits THEN the schema model SHALL declare it as the capture's XML and JSON shape
it, wherever its parent's XSD type occurs, so every reader places it and every validator
accepts it: `system login user <u> shell <value>`, `system services extension-service
request-response grpc clear-text port <n>` and `grpc skip-authentication`, `system
ddos-protection protocols autoconf aggregate bandwidth|burst <n>`, `family inet6
labeled-unicast per-prefix-label` under BGP, and `dhcp-local-server stale-timer <n>` and
`no-stale-timer-refresh`.
Tests: `tests/unit/validate/test_xsd_fixes.py::TestUndocumentedStatementsAreModelled::test_the_statement_is_declared_where_its_parent_type_occurs`, `tests/contract/test_round_trip_validates.py::TestTheSchemaStillRejects::test_the_bundled_schema_rejects`, `tests/corpus/test_device_renderings.py::TestTheValidatorsTakeWhatTheDevicePrinted::test_only_the_recorded_findings_are_reported`

#### Scenario: A login shell

- **WHEN** `set system login user operator shell csh` is validated and converted from set,
  curly, JSON and XML
- **THEN** it is valid, placed, and written back as the device printed it

### Requirement: A Junos variable is not checked as a value

WHEN field validation meets a leaf whose value is a `$junos-` dynamic-profile variable THEN it
SHALL check neither enum, pattern nor type: the device substitutes the value at login.
Tests: `tests/unit/convert/test_field_validator.py::TestAJunosVariableIsNotAValue::test_a_junos_variable_passes_a_pattern`, `tests/unit/convert/test_field_validator.py::TestAJunosVariableIsNotAValue::test_the_device_line_validates`

#### Scenario: An interface variable

- **WHEN** `dynamic-profiles P interfaces interface-set S interface $junos-interface-ifd-name`
  is field-validated
- **THEN** no finding is reported
