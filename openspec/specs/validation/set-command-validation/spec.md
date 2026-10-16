# validation/set-command-validation Specification

## Purpose

Define which Junos display-set commands the generated and shipped grammar
accepts, while keeping structural validation bounded and useful on real
configurations.

## Requirements

### Requirement: Equivalent compact sibling forms validate

WHEN Junos permits a flattened hierarchy to carry multiple keyworded sibling
settings after its entry or positional value THEN the system SHALL accept both
the compact command and the equivalent expanded commands through the generated
grammar, `SetValidator.validate`, `JunosValidator.validate_set`, the public
`validate_set` and `validate_config` functions, and CLI `-v -i set` validation.
Tests: `tests/unit/validate/test_grammar_generator.py::TestListEntryTakesSiblingsOnOneLine::test_two_siblings_after_the_entry_name`, `tests/unit/validate/test_grammar_generator.py::TestFlatPositionalContainerTakesSiblingsOnOneLine::test_two_siblings_after_the_positional_value`, `tests/contract/test_every_door.py::TestSiblingsShareOneLine::test_every_door_agrees`, `tests/unit/validate/test_grammar_generator.py::TestEveryValidatorTakesTheGeneratedSiblings::test_compact_and_expanded_forms_validate`, `tests/corpus/test_set_corpus.py::TestTheGrammarRefusesWhatIsNotJunos::test_malformed_junos_is_rejected`

#### Scenario: Oneliner named-list siblings

- **WHEN** an NTP server command carries `version`, `prefer`, and
  `routing-instance` after the server address
- **THEN** the compact command and three commands that repeat the server path
  each validate

#### Scenario: Flat positional-container siblings

- **WHEN** a maximum-prefixes command carries its positional limit followed by
  `threshold` and `log-interval`
- **THEN** the compact command and three commands that repeat the
  maximum-prefixes path each validate

### Requirement: Sibling support remains structurally narrow

WHEN sibling repetition is generated for a flattened hierarchy THEN the system
SHALL repeat only keyworded sibling alternatives after consuming the entry's
key values, one per key field, or the positional value, once, and SHALL
continue to reject unknown trailing tokens and unmarked hierarchies that do
not permit compact siblings.
Tests: `tests/unit/validate/test_grammar_generator.py::TestUnknownTokensInsideANamedList::test_unknown_element_is_rejected`, `tests/unit/validate/test_grammar_generator.py::TestListEntryTakesSiblingsOnOneLine::test_unmarked_list_does_not_repeat_siblings`, `tests/unit/validate/test_grammar_generator.py::TestFlatPositionalContainerTakesSiblingsOnOneLine::test_unmarked_same_named_container_does_not_repeat_siblings`, `tests/contract/test_every_door.py::TestSiblingsShareOneLine::test_every_door_agrees`, `tests/unit/validate/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_an_unknown_sibling_after_two_keys_is_rejected`

#### Scenario: Unknown named-list sibling

- **WHEN** a named-list entry is followed by an unknown keyword and value
- **THEN** set validation reports the command invalid

#### Scenario: Unknown positional-container sibling

- **WHEN** a positional container is followed by an unknown keyword and value
- **THEN** set validation reports the command invalid

#### Scenario: Unmarked list entry

- **WHEN** a list without flattening metadata is followed by two child settings
  on one line
- **THEN** the generated grammar rejects that compact command

#### Scenario: Unknown sibling after a two-field key

- **WHEN** an entry keyed by two fields is followed by both key values and an
  unknown keyword and value
- **THEN** the generated grammar rejects that command

### Requirement: Sibling validation has bounded parse cost

WHEN the shipped validator checks a representative multi-line configuration
containing compact sibling commands THEN the system SHALL complete within a
five-second bound for 100 commands, keeping the performance promise executable
from committed repository state.
Tests: `tests/corpus/test_shipped_artifacts.py::TestCompactSiblingsParseInPracticalTime::test_compact_siblings_keep_practical_parse_time`

#### Scenario: Representative repeated commands

- **WHEN** the validator checks 100 compact NTP and maximum-prefixes commands
- **THEN** validation succeeds within five seconds on the test runner

### Requirement: A keyed entry takes exactly its key values

WHEN the generated grammar renders a list keyed by anything but the single
`name` THEN it SHALL take one value per key field in key order, a field whose
leaf is not `nokeyword` as `keyword value` (such fields in any order among
themselves), a key choice as one of its keywords with its value, then only the
entry's declared children; SHALL reject a missing or further value; SHALL NOT
offer a nokeyword key element's name as a keyword; and SHALL take a key choice
before or after the other key values and no child before the keys. A
`flat-dict` list (`apply-macro`) takes its key, then optionally its child
list's key and that entry's leaf values, at most three values for
`apply-macro`; another `flat-dict` keeps `keyword value+`; the grammar of
`name`-keyed lists SHALL stay byte-identical but for `apply-macro`. This holds through `SetValidator.validate`, the public
`validate_set` and `validate_config`, and CLI `-v -i set`; phase 5 SHALL stop
and report any device-captured set line under `tests/data/device/` it newly
rejects: the covering lines of `grammar-corpus.json` by default, every line with
`--device-grammar`.
Tests: `tests/unit/validate/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_two_keys_are_taken_in_order`, `tests/unit/validate/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_a_missing_or_further_value_is_rejected`, `tests/unit/validate/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_a_key_name_is_not_a_keyword`, `tests/unit/validate/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_a_key_keyword_goes_either_side`, `tests/unit/validate/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_name_keyed_grammar_is_byte_identical`, `tests/contract/test_every_door.py::TestAKeyedEntryTakesExactlyItsKeys::test_every_door_agrees`, `tests/corpus/test_set_corpus.py::TestTheGrammarRefusesWhatIsNotJunos::test_malformed_junos_is_rejected`, `tests/corpus/test_set_corpus.py::TestTheGrammarTakesWhatDevicesPrint::test_every_covering_line_is_accepted`, `tests/unit/validate/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_a_numeric_list_type_is_rejected`

#### Scenario: The device probe's lines

- **WHEN** the lines the device accepted are validated through each door:
  `as-path-neighbors as-list AS-LIST-A`, `as-path-origins as-list-group
  ASG-A`, `route-filter 198.51.100.0/24 exact accept`, `route-filter
  198.51.100.0/24 orlonger`, `source-address-filter 198.51.100.0/24 exact
  accept`, `then community add COMM-A`, `then community COMM-A add`, and
  `attributes-match ping.test-owner matches "^uptime$"`; and from round 5
  `virtual-link neighbor-id 10.255.255.1 transit-area 0.0.0.2`, the same
  reversed, `apply-macro ABCDE`, `apply-macro ABCDE DEFGH` and `apply-macro
  12345 "KADJBF KU!H" balks`
- **THEN** each is valid (device probe, vMX 23.2R2-S7.5)

#### Scenario: Lines the device rejected

- **WHEN** `as-path-neighbors as-list`, bare `as-path-neighbors`,
  `as-path-neighbors AS-LIST-A`, `as-path-neighbors as-list AS-LIST-A EXTRA`,
  `route-filter 198.51.100.0/24 next-policy`, `route-filter 198.51.100.0/24
  exact EXTRA`, the `attributes-match` line with a trailing `EXTRA`,
  `virtual-link neighbor-id 10.255.255.3`, `virtual-link 10.255.255.4
  0.0.0.2`, `apply-macro 12345 "KADJBF KU!H" balks XXXXX`, `apply-macro 12345
  XXX XXXX XXX` and `system location dc-a` are validated
- **THEN** each is invalid, as on the device

#### Scenario: A key choice after the first key

- **WHEN** the grammar is generated for a list keyed `(address, (exact,
  orlonger))` with `accept` as a child
- **THEN** `exact` or `orlonger` is required on either side of the address
  and before `accept`, and no rule offers `"address"` as a keyword

#### Scenario: Lines a device printed

- **WHEN** the covering set lines of `tests/data/device/grammar-corpus.json`,
  each printed by a device, are validated
- **THEN** each is valid

### Requirement: A quoted value takes an escaped quote

WHEN a set line holds a quoted value with `\"` inside it (`set interfaces ge-0/0/0 description
"uplink to sw1 \"core\""`, which vMX 23.2R2-S7.5 and QFX5120 25.2R2-S1.5 print in
`junoscfg-oracle.set.gz`) THEN set validation SHALL read it as one value, as the set and curly
readers do (`\` and the character after it belong to the value), and accept the line; a value
whose inner quotes are bare (`"uplink to sw1 "core""`) SHALL stay rejected. A quoted value ending
in a lone backslash (`"abc\"`, `"a b\"`), which the set reader reads as ending in `\` and
junoscfg's set writer writes so, SHALL stay accepted: the set reader, the set writer and the
shipped grammar agree, and every line junoscfg writes validates; how the device writes one is open
(specification challenge SC2, interim; probe P11) (DEV-V1, escape half; NEW-C6).
Tests: `tests/unit/validate/test_grammar_generator.py::TestAnyLeafValueMayBeQuoted::test_an_escaped_quote_is_part_of_the_value`, `tests/unit/validate/test_grammar_generator.py::TestAnyLeafValueMayBeQuoted::test_bare_inner_quotes_are_not_one_value`, `tests/unit/validate/test_grammar_generator.py::TestAnyLeafValueMayBeQuoted::test_a_quoted_value_ending_in_a_backslash_parses`, `tests/unit/validate/test_grammar_generator.py::TestAnyLeafValueMayBeQuoted::test_an_escaped_backslash_ends_before_the_quote`, `tests/corpus/test_shipped_artifacts.py::TestJunoscfgsOwnSetOutputValidates::test_the_written_line_validates`, `tests/corpus/test_shipped_artifacts.py::TestTheShippedGrammarKeepsRejecting::test_accepted`, `tests/corpus/test_shipped_artifacts.py::TestTheShippedGrammarKeepsRejecting::test_rejected`, `tests/corpus/test_set_corpus.py::TestTheGrammarTakesWhatDevicesPrint::test_the_false_rejections_are_exactly_the_recorded_ones`

#### Scenario: The device's escaped quote

- **WHEN** `set interfaces ge-0/0/0 description "uplink to sw1 \"core\""` is validated with the shipped grammar
- **THEN** it is valid, and the device grammar corpus no longer records it as a false rejection

#### Scenario: Bare inner quotes

- **WHEN** `set interfaces ge-0/0/0 description "uplink to sw1 "core""` is validated
- **THEN** it is rejected

#### Scenario: A trailing backslash

- **WHEN** `set system host-name "abc\"` or `set interfaces ge-0/0/0 description "a b\"` is validated, or junoscfg writes the value `a b\` as a set line
- **THEN** each validates, as on the base

### Requirement: Set validation reads every verb conversion reads

WHEN set input carries a `protect`, `activate`, `delete` or `deactivate` line THEN set
validation SHALL validate the statement path after the verb as `set` validates it, except
that the path may stop where one value would follow (the device prints `deactivate ...
max-hello-size`): such a line is valid when the grammar takes it with one value more, so a
path that stops inside an entry's key, before a keyword the key still needs, is invalid
(`deactivate ... route-filter 10.0.0.0/8` without its match type), through `SetValidator.validate`, `JunosValidator.validate_set`,
`validate_set`, `validate_config`, `validate_structured` and CLI `-v -i set|structured`; a
`set` line SHALL still give a leaf its value, and a line starting with any other word SHALL
be rejected; an error message SHALL carry the whole line, never a cut one.
Tests: `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_verb_line_is_validated_as_its_path`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_an_invalid_path_after_a_verb_is_reported`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_set_gives_a_leaf_its_value`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_another_verb_is_no_command`, `tests/unit/validate/test_set_validator.py::TestEveryVerbIsValidated::test_a_long_line_is_reported_whole`, `tests/contract/test_every_door.py::TestEveryVerbNamesAStatementPath::test_every_door_agrees`

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
