## MODIFIED Requirements

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
