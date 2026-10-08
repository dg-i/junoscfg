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
SHALL repeat only keyworded sibling alternatives after consuming the entry or
positional value once, and SHALL continue to reject unknown trailing tokens and
unmarked hierarchies that do not permit compact siblings.
Tests: `tests/test_grammar_generator.py::TestUnknownTokensInsideANamedList::test_unknown_element_is_rejected`, `tests/test_grammar_generator.py::TestListEntryTakesSiblingsOnOneLine::test_unmarked_list_does_not_repeat_siblings`, `tests/test_grammar_generator.py::TestFlatPositionalContainerTakesSiblingsOnOneLine::test_unmarked_same_named_container_does_not_repeat_siblings`, `tests/test_set_validator.py::TestTheShippedGrammarAcceptsMultipleSiblings::test_unknown_sibling_is_rejected`

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

### Requirement: Sibling validation has bounded parse cost

WHEN the shipped validator checks a representative multi-line configuration
containing compact sibling commands THEN the system SHALL complete within a
five-second bound for 100 commands, keeping the performance promise executable
from committed repository state.
Tests: `tests/test_set_validator.py::TestTheShippedGrammarAcceptsMultipleSiblings::test_compact_siblings_keep_practical_parse_time`

#### Scenario: Representative repeated commands

- **WHEN** the validator checks 100 compact NTP and maximum-prefixes commands
- **THEN** validation succeeds within five seconds on the test runner
