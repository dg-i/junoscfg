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
or one the device prints no warning for and refuses at `commit check` where it applies:
`hold-time` with only `down` on an interface, which the QFX5120 25.2R2-S1.5 refuses with
"Missing mandatory statement: 'up'", probe D1; the recorded one sits in an unapplied group);
strict mode SHALL raise exactly when a recorded finding is an error;
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

#### Scenario: A hold-time with only down

- **WHEN** the JVD capture `mdr1_acx7509` is field-validated
- **THEN** its `hold-time` without `up` is the one warning, recorded in the class of a
  mandatory statement the device refuses at commit where it applies

### Requirement: Statements the device prints undocumented are modelled

WHEN a committed capture or the committed record of a device probe
(`tests/data/device/probes/`) holds a statement the device's XML wraps in `<undocumented>` and
Juniper's XSD omits THEN the schema model SHALL declare it as the device's XML and JSON shape
it, wherever its parent's XSD type occurs, so every reader places it and every validator
accepts it: `system login user <u> shell <value>`, `system services extension-service
request-response grpc clear-text address <a>` and `port <n>`, and `grpc skip-authentication`,
`system ddos-protection protocols autoconf aggregate bandwidth|burst <n>`, `family inet6
labeled-unicast per-prefix-label` under BGP, `dhcp-local-server stale-timer <n>` and
`no-stale-timer-refresh`, and the flags `system debugger-on-break`, `system debugger-on-panic`,
`chassis dump-on-panic` (`<x/>`) and `system dump-on-panic` (an open and a close tag with
nothing inside, which every reader takes as `[null]`; QFX5120 25.2R2-S1.5, probe D4 and P4).
Every reader SHALL give each one IR (set, curly, JSON, yaml-new, XML). A sibling no device
showed (`chassis debugger-on-panic`) stays refused.
Tests: `tests/unit/validate/test_xsd_fixes.py::TestUndocumentedStatementsAreModelled::test_the_statement_is_declared_where_its_parent_type_occurs`, `tests/contract/test_round_trip_validates.py::TestTheSchemaStillRejects::test_the_bundled_schema_rejects`, `tests/corpus/test_device_renderings.py::TestTheValidatorsTakeWhatTheDevicePrinted::test_only_the_recorded_findings_are_reported`, `tests/corpus/test_device_probes.py::TestEveryProbedLineValidatesAsTheDeviceTookIt::test_the_line`, `tests/corpus/test_device_probes.py::TestEveryProbedRenderingReadsAsItsSet::test_the_rendering`, `tests/corpus/test_set_corpus.py::TestTheGrammarTakesWhatDevicesPrint::test_the_false_rejections_are_exactly_the_recorded_ones`, `tests/corpus/test_shipped_artifacts.py::TestTheShippedGrammarKeepsRejecting::test_rejected`, `tests/corpus/test_device_probes.py::TestEveryAcceptedLineReadsAsOneIrInEveryFormat::test_the_line`

#### Scenario: A login shell

- **WHEN** `set system login user operator shell csh` is validated and converted from set,
  curly, JSON and XML
- **THEN** it is valid, placed, and written back as the device printed it

#### Scenario: The gRPC clear-text address

- **WHEN** the probe's JSON `"clear-text": {"address": "127.0.0.1", "port": 32767}` and its XML
  `<grpc><undocumented><clear-text>...` are read
- **THEN** both validate and give the device's two display set lines

#### Scenario: Chassis dump-on-panic

- **WHEN** `set chassis dump-on-panic` is validated
- **THEN** it is valid, and the grammar corpus records no rejection of it

### Requirement: A Junos variable is not checked as a value

WHEN field validation meets a leaf whose value is a `$junos-` dynamic-profile variable THEN it
SHALL check neither enum, pattern nor type: the device substitutes the value at login.
Tests: `tests/unit/convert/test_field_validator.py::TestAJunosVariableIsNotAValue::test_a_junos_variable_passes_a_pattern`, `tests/unit/convert/test_field_validator.py::TestAJunosVariableIsNotAValue::test_the_device_line_validates`

#### Scenario: An interface variable

- **WHEN** `dynamic-profiles P interfaces interface-set S interface $junos-interface-ifd-name`
  is field-validated
- **THEN** no finding is reported

### Requirement: A device probe is recorded sanitized

WHEN the owner runs a device probe THEN its committed record under
`tests/data/device/probes/<device>/` SHALL hold only the probe's own synthetic statements, the
device's responses and its renderings, with the platform family and the release, and SHALL
hold no host name, user name, prompt or timestamp (`junos:changed-*`), and every value SHALL
be one of the synthetic values of `AGENTS.md`; the raw session stays in `private_test_data/`.
The corpus tests read every record under `probes/` as device evidence.
Tests: `tests/corpus/test_device_probes.py::TestTheProbeRecordIsSanitized::test_no_prompt_or_timestamp`, `tests/corpus/test_device_probes.py::TestTheProbeRecordIsSanitized::test_every_value_is_synthetic`, `tests/corpus/test_device_probes.py::TestTheProbeRecordIsSanitized::test_the_leak_shapes_catch_what_they_name`, `tests/corpus/test_device_probes.py::TestTheProbeRecordIsSanitized::test_the_raw_session_names_nothing_in_the_repository`

#### Scenario: The 2026-10-16 QFX5120 probe

- **WHEN** `tests/data/device/probes/qfx5120-25.2R2-S1.5/2026-10-16.json` is read
- **THEN** it holds no CLI prompt, banner, change or commit attribute, time of day or home
  path, and every value is a synthetic one; where the raw session is on the machine, neither
  name of its prompt occurs under `tests/data/`
