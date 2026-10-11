## ADDED Requirements

### Requirement: No message of an anonymized run quotes the configuration

WHEN a conversion anonymizes (`convert_config`, `convert_config_result`, `pipeline`,
`pipeline_result` with an `anon_config` that enables a rule, or `junoscfg convert --anonymize-*`)
THEN no message it returns, raises or prints SHALL quote a word of the configuration, original or
replaced: a field-validation report, in the diagnostics and in `FieldValidationError`, SHALL keep
its schema path, its reason and what was expected and withhold its value (`FieldError.value` is
`""`); a refusal to read the input SHALL be raised as `ValueError` (`yaml.YAMLError` for a YAML
parse error) saying the input could not be read and naming its line (`(line N)`: each reader sets
`lineno` on its refusal, PyYAML marks it); any other failure SHALL be raised as `RuntimeError`
naming only its class, with no cause, context or notes; the
structured writer's note on dropped tags SHALL give their count without their paths; `-v` and
validate-only SHALL print each error's line, never its text or document path; a warning or error
of a rule SHALL name neither an original value nor its replacement (the AS-number rule's warnings,
`ipanon`'s pass-through collision); on the command line a failure no handler expects SHALL print
the library's withheld failure or
`Error: the conversion failed (<class>); details withheld: the run anonymizes` and exit 1, with no
traceback. A message SHALL still say what it exists to say: its path, reason, line or count. Messages that already name only schema names, counts and
lines (the `anonymize:` warnings, the read notes, a missing artifact's `SchemaLoadError`) stay as
they are. A run that does not anonymize, revert included, SHALL keep every message as it was.
Only `log_level="debug"` prints each original beside its replacement, by design and documented.
`junoscfg audit` has no anonymized run (lesson #1 of the makeover run; NEW-R1, NEW-R4, NEW-R9,
NEW-R10).
Tests: `tests/contract/test_every_message.py::TestAnAnonymizedRunQuotesNothingOfTheConfiguration::test_no_message_holds_a_word_of_it`, `tests/contract/test_every_message.py::TestARunThatDoesNotAnonymizeKeepsItsMessages::test_the_message_quotes_the_configuration`, `tests/contract/test_every_message.py::TestAFailureNoHandlerExpectsNamesOnlyItsClass::test_the_details_are_withheld`, `tests/contract/test_every_message.py::TestTheLibraryRaisesAFailureByItsClassOnly::test_nothing_of_the_original_travels_with_it`, `tests/contract/test_every_message.py::TestTheLibraryRaisesAFailureByItsClassOnly::test_a_refusal_to_read_carries_nothing_either`, `tests/contract/test_every_message.py::TestTheLibraryRaisesAFailureByItsClassOnly::test_without_anonymization_the_original_is_raised`, `tests/contract/test_every_message.py::TestOnlyTheDebugLevelPrintsOriginals::test_debug_pairs_each_original_with_its_replacement`, `tests/contract/test_every_message.py::TestOnlyTheDebugLevelPrintsOriginals::test_no_other_level_does`, `tests/contract/test_every_message.py::TestTheAuditHasNoAnonymizedRun::test_it_takes_no_anonymize_option`, `tests/unit/anonymize/test_as_number_rule.py::TestAsNumberConflictDetection::test_no_warning_pairs_an_original_with_its_replacement`, `tests/unit/anonymize/test_ip_rule.py::TestAPassThroughCollision::test_the_error_names_no_address`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_an_address_on_an_enum_only_leaf_is_replaced`, `tests/unit/anonymize/test_integration.py::TestContentTheWalkCannotPlace::test_the_warning_names_each_shape_it_replaces`

#### Scenario: A value no rule replaces

- **WHEN** `set system services ssh protocol-version v9-acme` is converted with `--anonymize-ips`
- **THEN** the field-validation message names `system.services.ssh.protocol-version` and `must be
  one of [v2]`, and neither it nor `--strict`'s error holds `v9-acme`

#### Scenario: A refusal to read

- **WHEN** `set system name-server [ 203.0.114.9 ]`, a curly statement without its `;`, a broken
  YAML or XML document is converted with an anonymizing rule
- **THEN** the error says the input could not be read, names its line (`(line 1)`, `(line 2)`)
  and holds no word of it; without anonymization it is the reader's own message, the line included

#### Scenario: A failure the library does not expect

- **WHEN** `configuration: {system: {x-acme: 2026-10-11}}` (a YAML date) is converted to JSON with
  an anonymizing rule
- **THEN** `RuntimeError("the conversion failed (TypeError) ...")` is raised with no cause, context
  or notes, where the writer's `TypeError` noted `x-acme`

#### Scenario: A failure no handler expects

- **WHEN** an anonymized `junoscfg convert` fails with an exception no handler expects (a
  pass-through collision, a crash whose chain holds `203.0.114.9`)
- **THEN** it prints only the exception's class and exits 1; without anonymization the
  traceback stays

#### Scenario: Validation on the command line

- **WHEN** `junoscfg convert -v --anonymize-ips` (with or without `-e`) validates
  `set system bogus-statement 203.0.114.9`
- **THEN** it exits 1 printing `Validation: FAILED (1 error(s))` and the error's line, never
  `bogus-statement` or the address

### Requirement: anonymize() leaves its input alone

WHEN `junoscfg.anonymize.anonymize(ir, config)` runs THEN it SHALL copy *ir* once on entry, rewrite
only the copy and return it as `AnonymizeResult.ir`, so the caller's IR is unchanged and shares no
mutable part with the result; a generated salt is still written back into *config*, so a reused
config keeps one salt. `apply_revert` and `walk` SHALL keep rewriting the IR they are given in
place, as they document (NEW-R3; a documented in-place contract stays, an undocumented side effect
goes).
Tests: `tests/unit/anonymize/test_integration.py::TestAnonymizeLeavesItsInputAlone::test_the_callers_ir_is_unchanged`, `tests/unit/anonymize/test_integration.py::TestAnonymizeLeavesItsInputAlone::test_the_result_shares_nothing_with_it`, `tests/unit/anonymize/test_integration.py::TestAnonymizeLeavesItsInputAlone::test_revert_still_rewrites_in_place`

#### Scenario: The caller keeps its IR

- **WHEN** a caller anonymizes `{"configuration": {"system": {"name-server": [{"name": "203.0.114.9"}]}}}`
- **THEN** its dict still holds `203.0.114.9`, `result.ir` holds the pseudonym, and changing
  `result.ir` changes nothing the caller holds
