## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: A keyed entry takes exactly its key values

WHEN the generated grammar renders a list keyed by fields other than the
single `name` THEN it SHALL take one value per key field, in key order, then
only the entry's declared children, SHALL reject a further value, and SHALL
NOT offer a key field's element name as a keyword; lists keyed `name` and
`flat-dict` renderings SHALL keep their grammar. This holds through
`SetValidator.validate`, the public `validate_set` and `validate_config`
functions, and CLI `-v -i set`.
Tests: `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_two_keys_are_taken_in_order`, `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_a_further_value_is_rejected`, `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_a_key_name_is_not_a_keyword`, `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_a_name_keyed_list_is_unchanged`, `tests/test_set_validator.py::TestTheShippedGrammarTakesKeyedEntries::test_as_list_references_validate`, `tests/test_set_validator.py::TestTheShippedGrammarTakesKeyedEntries::test_attributes_match_takes_three_values`, `tests/test_cli_validate.py::TestCliValidation::test_validate_set_with_an_as_list_reference`, `tests/test_set_corpus.py::TestShippedGrammarAgainstTheCorpus::test_rejections_are_exactly_the_recorded_ones`

#### Scenario: AS-list references

- **WHEN** `... from as-path-neighbors as-list AS-LIST-A` and `... from
  as-path-transits as-list-group ASG-A` are validated through each door
- **THEN** both are valid, and each with a trailing `EXTRA` is invalid

#### Scenario: attributes-match

- **WHEN** `attributes-match ping.test-owner matches "^uptime$"` is validated,
  and the same with a fourth value
- **THEN** the first is valid and the second invalid

#### Scenario: A key field's name as a keyword

- **WHEN** the grammar is generated for a list keyed `(list-type, list-name)`
- **THEN** no rule offers `"list-type"` or `"list-name"` as a keyword

#### Scenario: The corpus

- **WHEN** the shipped grammar checks the exact set corpus
- **THEN** its rejections are exactly the recorded ones
