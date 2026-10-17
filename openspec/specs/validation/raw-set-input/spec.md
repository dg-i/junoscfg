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
Tests: `tests/unit/validate/test_set_validator.py::TestBracketShorthandIsALineError::test_validation_doors_return_line_errors_without_throwing`, `tests/unit/validate/test_set_validator.py::TestBracketShorthandIsALineError::test_validation_collects_each_offending_line`

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

### Requirement: The corpus distinguishes intentional exclusion from malformed input

WHEN the exact set corpus classifies validator rejections THEN the system SHALL
record device-valid bracket shorthand under `INTENTIONALLY_UNSUPPORTED`, SHALL
not count it as malformed or accidental over-rejection, and SHALL classify
`set policy-options community FOO members` as correctly rejected because the
leaf-list has no value.
Tests: `tests/corpus/test_set_corpus.py::TestTheGrammarRefusesWhatIsNotJunos::test_malformed_junos_is_rejected`, `tests/corpus/test_set_corpus.py::TestTheGrammarRefusesWhatIsNotJunos::test_bracket_shorthand_is_refused_with_its_reason`

#### Scenario: Bracket shorthand classification

- **WHEN** the corpus contains device-valid raw set bracket shorthand
- **THEN** its exact rejection belongs to `INTENTIONALLY_UNSUPPORTED`

#### Scenario: Bare community members leaf-list

- **WHEN** the corpus contains `set policy-options community FOO members`
- **THEN** its rejection belongs to the correctly rejected category with a
  leaf-list-with-no-value reason

### Requirement: Set validation shares unsupported command classification
WHEN SetValidator, validate_set or set-format validate_config receives visible unsupported command lines THEN the system SHALL return an invalid ValidationResult, collecting one line-specific error per offending line with the shared value-free message `Unsupported command in set input on line N`. Existing bracket refusal retains precedence; supported path grammar and existing validation behavior for metadata commands SHALL NOT be broadened.
Tests: `tests/unit/convert/test_set_commands.py::test_validation_doors_collect_value_free_command_errors`, `tests/unit/convert/test_set_commands.py::test_cli_validation_refuses_without_conversion`

#### Scenario: Multiple physical lines
- **WHEN** annotate and insert follow blank or ignored comment lines
- **THEN** every validation door reports the original line numbers without exposing supplied values.

#### Scenario: Validation-only CLI
- **WHEN** validation-only CLI receives unsupported commands
- **THEN** it exits 1 and reports line-specific errors; an anonymized run withholds the configuration.

### Requirement: Set validation reads every verb conversion reads

WHEN set input carries a `protect`, `activate`, `delete` or `deactivate` line THEN set
validation SHALL validate the statement path after the verb as `set` validates it, except that
the path may stop where one value would follow, and SHALL take the line only where it names a
statement the device can tag, as the set reader places the tag (one read-only walk,
`junoscfg.display.meta_target`, serves both): a container, a leaf, leaf-list or flag before its
value (the device prints `deactivate ... max-hello-size`), a list entry after its whole key
(`deactivate routing-options static route 198.51.100.0/24`), or a list the XSD marks
`homogeneous` as a whole (the device takes `deactivate forwarding-options port-mirroring family
inet output routing-instance`, deactivate6.txt). A line SHALL be invalid when it stops at
another list's keyword without the entry's name (`protect policy-options policy-statement`; the
QFX5120 25.2R2-S1.5 refuses it, "syntax error, expecting <identifier>"), tags a container Junos
writes merged with each child (`deactivate ... family`, "missing argument"), names a leaf's
value or one value of a leaf-list (`deactivate ... community 64496:2`; the device refuses it,
"syntax error, expecting ';', [Enter], or '|'"), or stops inside an entry's key, before a
keyword the key needs (`route-filter 10.0.0.0/8` without its match type) or before a key value
(`virtual-link neighbor-id 10.255.255.1 transit-area`). This holds through
`SetValidator.validate`, `JunosValidator.validate_set`, `validate_set`, `validate_config`,
`validate_structured` and CLI `-v -i set|structured`, but for a curly whole-list tag, which the
curly doors still take (a strict xfail, BACKLOG WHOLE-LIST-TAGS-001). The set reader refuses
the same lines with `ValueError` (a list's keyword, a value), keeps them unplaced (inside a
key) or places the tag that set and structured output then drop with a note (`family`), for
every verb: the device was asked about `deactivate` and `protect`; `activate` and `delete`
follow the one walk. The validator reads the structure tree beside its grammar for a verb line
and raises `SchemaLoadError` where there is none. A `set` line SHALL still give a leaf its
value, and a line starting with any other word SHALL be rejected; an error message SHALL carry
the whole line, never a cut one. Every verb line of the committed device captures stays valid.
Tests: `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_verb_line_is_validated_as_its_path`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_an_invalid_path_after_a_verb_is_reported`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_set_gives_a_leaf_its_value`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_another_verb_is_no_command`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_long_line_is_reported_whole`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_verb_line_names_no_value`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_verb_line_names_no_list_without_its_entry`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_verb_line_without_a_structure_tree_is_a_load_error`, `tests/unit/display/test_meta_path.py::TestAMetaPathNamesWhatTheReaderTags::test_the_target`, `tests/contract/test_every_door.py::TestEveryVerbNamesAStatementPath::test_every_door_agrees`, `tests/corpus/test_set_corpus.py::TestEveryCaptureValidatesAsSet::test_every_verb_line_of_the_capture_validates`, `tests/corpus/test_device_probes.py::TestEveryProbedLineValidatesAsTheDeviceTookIt::test_the_line`, `tests/unit/convert/test_scalar_meta_targets.py::test_a_list_keyword_without_its_entry_cannot_be_tagged`, `tests/unit/convert/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied::test_a_meta_attribute_on_a_whole_list_is_written`, `tests/unit/convert/test_meta_tags.py::TestATagOnFamilyIsReported::test_set_output_drops_it_with_a_note`

#### Scenario: A protected group
- **WHEN** `protect groups GR-PROTECTED` follows the group's `set` lines
- **THEN** the input is valid through every door

#### Scenario: A deactivated leaf
- **WHEN** `deactivate system host-name` follows `set system host-name router1`
- **THEN** the input is valid, while `set system host-name` alone is not

#### Scenario: A line that stops inside an entry's key
- **WHEN** `deactivate policy-options policy-statement P term T from route-filter 10.0.0.0/8`
  follows the route filter's `set` line with its match type `exact`
- **THEN** the line is invalid through every door, as the set reader cannot place it

#### Scenario: A long invalid line
- **WHEN** a line longer than 80 characters is invalid
- **THEN** the error quotes it whole

#### Scenario: A list's keyword without its entry
- **WHEN** `protect policy-options policy-statement` or `deactivate policy-options
  policy-statement` follows `set policy-options policy-statement JUNOSCFG-PROBE term t1 then
  accept` (probe D5)
- **THEN** the line is invalid through every door, as the device refuses it, and conversion
  refuses it; `deactivate forwarding-options port-mirroring family inet output
  routing-instance` and `deactivate system name-server`, homogeneous lists, stay valid

#### Scenario: A tag on family itself
- **WHEN** `deactivate interfaces ge-0/0/1 unit 0 family` follows the family's `set` line
- **THEN** the line is invalid through every door, and set output drops the tag with a note

#### Scenario: One value of a leaf-list
- **WHEN** `deactivate routing-options static route 198.51.100.0/24 community 64496:2` follows
  the route's `set` lines (probe A2), or `deactivate system host-name router1` follows
  `set system host-name router1`
- **THEN** the line is invalid through every door, where `-v` said OK and conversion failed

#### Scenario: A keyed entry after its whole key
- **WHEN** `deactivate protocols ospf area 0.0.0.0 virtual-link neighbor-id 10.255.255.1
  transit-area 0.0.0.2` follows the entry's `set` line
- **THEN** the line is valid, and the line without its last value is invalid

#### Scenario: No structure tree beside the grammar
- **WHEN** a grammar directory holds no structure tree and a verb line is validated
- **THEN** `SchemaLoadError` names the missing tree; a `set` line still validates

### Requirement: Several statements on one line are named unsupported

WHEN a `set` line the grammar refuses gives a leaf its value and goes on with another
statement of the same level, each of which validates on a line of its own (`set interfaces
ge-0/0/1 hold-time up 0 down 0`) THEN set validation SHALL report "Unsupported in set input,
one statement a line: <line>" instead of "Invalid syntax", and conversion SHALL read it as the
statements one a line. The QFX5120 25.2R2-S1.5 takes the typed form (probe D1), but its
display set writes one statement a line, and set input is what a device exports (decision
2026-10-17-set-input-is-a-device-export). A line whose parts do not each stand alone stays
"Invalid syntax".
Tests: `tests/corpus/test_shipped_artifacts.py::TestTheShippedGrammarKeepsRejecting::test_several_statements_on_one_line_are_named_unsupported`, `tests/corpus/test_shipped_artifacts.py::TestTheShippedGrammarKeepsRejecting::test_what_is_no_statement_stays_invalid`, `tests/corpus/test_device_probes.py::TestEveryProbedLineValidatesAsTheDeviceTookIt::test_the_lines_out_of_scope_still_disagree`

#### Scenario: A one-line hold-time
- **WHEN** `set interfaces ge-0/0/1 hold-time up 0 down 0` is validated and converted
- **THEN** validation names it unsupported, and conversion gives the IR of `hold-time up 0`
  and `hold-time down 0`

#### Scenario: A word that is no statement
- **WHEN** `set interfaces ge-0/0/1 hold-time up 0 bogus 1` is validated
- **THEN** it is "Invalid syntax", as before
