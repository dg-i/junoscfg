## MODIFIED Requirements

### Requirement: Sibling support remains structurally narrow

WHEN sibling repetition is generated for a flattened hierarchy THEN the system
SHALL repeat only keyworded sibling alternatives after consuming the entry's
key values, one per key field, or the positional value, once, and SHALL
continue to reject unknown trailing tokens and unmarked hierarchies that do
not permit compact siblings.
Tests: `tests/test_grammar_generator.py::TestUnknownTokensInsideANamedList::test_unknown_element_is_rejected`, `tests/test_grammar_generator.py::TestListEntryTakesSiblingsOnOneLine::test_unmarked_list_does_not_repeat_siblings`, `tests/test_grammar_generator.py::TestFlatPositionalContainerTakesSiblingsOnOneLine::test_unmarked_same_named_container_does_not_repeat_siblings`, `tests/test_set_validator.py::TestTheShippedGrammarAcceptsMultipleSiblings::test_unknown_sibling_is_rejected`, `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_an_unknown_sibling_after_two_keys_is_rejected`, `tests/test_grammar_generator.py::TestFlattenedRenderingsTakeARunOfValues::test_a_flat_entry_takes_its_values`

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

WHEN the generated grammar renders a list keyed by anything but the single
`name` THEN it SHALL take one value per key field, in key order, then only the
entry's declared children, SHALL reject a missing or further value, SHALL NOT
offer a key field as a keyword, and SHALL take a child declared before the keys
on either side of them and no other child before them; `flat-dict` keeps
`keyword value+`, and the grammar of `name`-keyed lists SHALL stay
byte-identical. This holds through `SetValidator.validate`, the public
`validate_set` and `validate_config`, and CLI `-v -i set`; phase 5 SHALL stop
and report any corpus or `--jvd` line it newly rejects.
Tests: `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_two_keys_are_taken_in_order`, `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_a_missing_or_further_value_is_rejected`, `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_a_key_name_is_not_a_keyword`, `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_a_child_declared_before_the_key_goes_either_side`, `tests/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys::test_name_keyed_grammar_is_byte_identical`, `tests/test_set_validator.py::TestTheShippedGrammarTakesKeyedEntries::test_device_probe_lines`, `tests/test_cli_validate.py::TestCliValidation::test_validate_set_with_an_as_list_reference`, `tests/test_set_corpus.py::TestShippedGrammarAgainstTheCorpus::test_rejections_are_exactly_the_recorded_ones`

#### Scenario: The device probe's lines

- **WHEN** the lines the device accepted are validated through each door:
  `as-path-neighbors as-list AS-LIST-A`, `as-path-origins as-list-group
  ASG-A`, `route-filter 198.51.100.0/24 exact accept`, `then community add
  COMM-A`, `then community COMM-A add`, and `attributes-match
  ping.test-owner matches "^uptime$"`
- **THEN** each is valid (device probe, vMX 23.2R2-S7.5)

#### Scenario: Lines the device rejected

- **WHEN** `as-path-neighbors as-list`, bare `as-path-neighbors`,
  `as-path-neighbors AS-LIST-A`, `as-path-neighbors as-list AS-LIST-A EXTRA`,
  `route-filter 198.51.100.0/24 exact EXTRA` and the `attributes-match` line
  with a trailing `EXTRA` are validated
- **THEN** each is invalid, as on the device

#### Scenario: Key first, no child before it

- **WHEN** the grammar is generated for a list keyed `(address,)` with `exact`
  declared after the key
- **THEN** `exact` is taken only after the key, and no rule offers `"address"`
  as a keyword
