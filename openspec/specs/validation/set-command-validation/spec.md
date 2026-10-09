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
Tests: `tests/test_grammar_generator.py::TestListEntryTakesSiblingsOnOneLine::test_two_siblings_after_the_entry_name`, `tests/test_grammar_generator.py::TestFlatPositionalContainerTakesSiblingsOnOneLine::test_two_siblings_after_the_positional_value`, `tests/test_set_validator.py::TestTheShippedGrammarAcceptsMultipleSiblings::test_compact_and_expanded_forms_validate`, `tests/test_cli_validate.py::TestCliValidation::test_validate_set_with_multiple_siblings`, `tests/test_set_corpus.py::TestShippedGrammarAgainstTheCorpus::test_rejections_are_exactly_the_recorded_ones`

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
Tests: `tests/test_grammar_generator.py::TestUnknownTokensInsideANamedList::test_unknown_element_is_rejected`, `tests/test_grammar_generator.py::TestListEntryTakesSiblingsOnOneLine::test_unmarked_list_does_not_repeat_siblings`, `tests/test_grammar_generator.py::TestFlatPositionalContainerTakesSiblingsOnOneLine::test_unmarked_same_named_container_does_not_repeat_siblings`, `tests/test_set_validator.py::TestTheShippedGrammarAcceptsMultipleSiblings::test_unknown_sibling_is_rejected`, `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_an_unknown_sibling_after_two_keys_is_rejected`

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
Tests: `tests/test_set_validator.py::TestTheShippedGrammarAcceptsMultipleSiblings::test_compact_siblings_keep_practical_parse_time`

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
and report any corpus or `--jvd` line it newly rejects.
Tests: `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_two_keys_are_taken_in_order`, `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_a_missing_or_further_value_is_rejected`, `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_a_key_name_is_not_a_keyword`, `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_a_key_keyword_goes_either_side`, `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_name_keyed_grammar_is_byte_identical`, `tests/test_set_validator.py::TestTheShippedGrammarTakesKeyedEntries::test_device_probe_lines`, `tests/test_cli_validate.py::TestCliValidation::test_validate_set_with_an_as_list_reference`, `tests/test_set_corpus.py::TestShippedGrammarAgainstTheCorpus::test_rejections_are_exactly_the_recorded_ones`, `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_a_numeric_list_type_is_rejected`, `tests/test_set_validator.py::TestTheShippedGrammarTakesKeyedEntries::test_a_numeric_list_type_is_rejected`, `tests/test_set_validator.py::TestTheShippedGrammarTakesKeyedEntries::test_the_bare_keyed_list_keyword_is_rejected`, `tests/test_set_validator.py::TestTheShippedGrammarTakesKeyedEntries::test_round_5_accepted_lines`, `tests/test_set_validator.py::TestTheShippedGrammarTakesKeyedEntries::test_round_5_rejected_lines`

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
