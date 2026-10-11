## ADDED Requirements

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
