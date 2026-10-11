# anonymization/wildcard-names Specification

## Purpose
A Junos wildcard name in a configuration group (`<*>`, `<ge-*>`) is a pattern that selects
names, not a name. Anonymization keeps it selecting the replacements of the names it selected,
or names its place in a report that carries no value, and revert restores it exactly.

## Requirements

### Requirement: A wildcard name is a pattern, not a name

WHEN the anonymize walker meets an entry's key field whose value is a Junos wildcard, the whole
value in angle brackets (`<*>`, `<ge-*>`, `<[gx]e-*>`, `<VRF-*>`), THEN a pattern of `*` alone
SHALL pass every rule unchanged, because it selects every name; any other wildcard SHALL keep its
brackets while the text inside them goes, rule by rule in the walker's order, to a rule that knows
patterns of its values or else is offered as a value of that key field, so text that spells a name
is replaced as that name is (`<EBGP>` as BGP group `EBGP`, `<203.0.114.7>` as neighbour
`203.0.114.7`). Where an address stands, an IPv4 pattern of whole octets (`<203.0.114.*>`,
`<203.0.*>`) SHALL become the pattern of its prefix's replacement (`203.0.114.0/24`), which selects
the replacement of every address it selected, when the prefix is wholly kept or wholly replaced; any
other address pattern, and one whose prefix a preserved prefix or a block the address anonymizer
keeps or treats apart cuts (`203.0.0.0/16` holds `203.0.113.0/24`), SHALL be left as written
(specification challenge S2). Text inside a wildcard is treated as a value's free text is
(`anonymization/embedded-values`): under `ips` a whole-octet pattern of two or more octets inside it
(`<peer-203.0.114.*>`) becomes its prefix's replacement and any other address fragment beside a
wildcard character is left as written; under `as_numbers_in_strings` a configured AS number written
in it is replaced, and one that could be spelled only where a `?` or a class stands, between
non-digits (`<AS6449?-*>` for 64496), leaves the text as written (S4); digits no configured AS
number can match (`<ge-0/0/1?>`) are no such case (NEW-R14). A sensitive word the text holds literally SHALL be replaced as in a
name; a word it can spell only through a class or `?` in either case (`<[Aa]cme-*>`), and any class
or `?` while a sensitive pattern is on, SHALL leave the text as written (S3). WHEN the anonymized
wildcard selects, among the names the configuration holds at that key field in any group and
outside them, a wildcard being no name, other names than the original selected (Python's
`fnmatchcase`: `*`, `?`, `[...]`, `[!...]`), judged on the final values, or its
text was left as written by a rule that claims it (S2-S4), or a rule claims text
holding a wildcard character and leaves it as written, THEN its place SHALL be named by the entry's schema path in `AnonymizeResult.patterns`, once per
wildcard, and in one `anonymize` warning per path that gives the count and withholds every value.
Revert SHALL restore every wildcard exactly; a sensitive word's pseudonym follows its spelling,
so no two cases share one (NEW-R13). A value that is no key field (a description written `<...>`) is data and SHALL be
replaced as before. This is the interim rule of specification challenges S1-S3 (owner decisions
pending; S4 as recorded).
Tests: `tests/unit/anonymize/test_integration.py::TestKeyedEntriesSurvive::test_a_wildcard_group_name_passes_the_group_rule`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_a_match_all_wildcard_passes_every_rule`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_the_text_of_a_wildcard_is_replaced_as_the_name_it_spells`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_a_wildcard_that_selects_other_names_is_reported`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_a_wildcard_that_selects_the_same_names_is_not_reported`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_the_mapping_restores_every_wildcard`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_a_description_written_as_a_wildcard_is_data`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_an_address_pattern_takes_its_prefixs_replacement`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_a_preserved_address_is_not_reported`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_a_sensitive_word_behind_a_class_is_reported`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_the_names_are_those_at_the_same_place`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_each_wildcard_is_counted`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_a_word_in_two_cases_reverts_to_each`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_the_warning_names_the_path_and_no_value`, `tests/contract/test_every_rule.py::TestEveryRule::test_a_match_all_wildcard_name_passes`, `tests/contract/test_every_message.py::TestAnAnonymizedRunQuotesNothingOfTheConfiguration::test_no_message_holds_a_word_of_it`, `tests/corpus/test_device_anonymization.py::TestEveryCaptureAnonymizes::test_every_wildcard_name_passes`, `tests/unit/anonymize/test_as_number_rule.py::TestAWildcardUnderAsNumbersInStrings::test_it_is_reported_only_where_a_configured_number_can_stand`

#### Scenario: The device example's BGP wildcard

- **WHEN** `groups GR-BGP protocols bgp group <*>` (vMX 23.2R2-S7.5 and QFX5120 25.2R2-S1.5
  `junoscfg-oracle` captures) is anonymized with every rule on
- **THEN** it stays `<*>`, the group selects every BGP group as before, the mapping holds no
  wildcard, and nothing is reported

#### Scenario: A renaming rule

- **WHEN** `groups GR-BGP protocols bgp group <EBGP>` and `<EBGP-*>` beside `protocols bgp group
  EBGP` and `EBGP-A` are anonymized with `--anonymize-groups`
- **THEN** `<EBGP>` becomes `<` + the pseudonym of `EBGP` + `>` and is not reported; `<EBGP-*>`
  becomes `<group_…>`, no `EBGP` survives, its path is reported, and revert restores it

#### Scenario: An address pattern

- **WHEN** `groups GR-BGP protocols bgp group IBGP neighbor <203.0.114.*>`, with or without a
  neighbour `203.0.114.7`, is anonymized with `--anonymize-ips`
- **THEN** it becomes `<a.b.c.*>` of the replacement of `203.0.114.0/24`, selects the neighbour's
  replacement, no `203.0.114` survives, and nothing is reported; `<203.0.11*>` and `<3ffe:b00:*>`
  are left as written and reported, and `<198.51.100.*>`, a block kept by design, is unchanged
  and not reported

#### Scenario: Sensitive words

- **WHEN** `<EBGP-*>`, `"<[A-E]BGP*>"` and `<ebgp-*>` beside `EBGP-A` and `EBGP` are anonymized
  with `--anonymize-sensitive-words ebgp`
- **THEN** `<EBGP-*>` becomes `<word_…-*>`, selects `word_…-A` and is not reported; the class,
  which no longer selects `word_…`, is left as written and reported; `<ebgp-*>` takes the
  pseudonym of the spelling `ebgp`, so it selects nothing, as Junos, matching case, selected
  nothing, and is not reported (NEW-R13)

#### Scenario: The strings passes

- **WHEN** `groups GR protocols bgp group <peer-203.0.114.*>` beside `peer-203.0.114.7` is
  anonymized with `--anonymize-ips`, with or without `--anonymize-ips-in-strings`, or `<AS6449?-*>`
  beside `AS64496-A` with `--anonymize-as-numbers 64496 --anonymize-as-numbers-in-strings`
- **THEN** the first becomes `<peer-a.b.c.*>` of `203.0.114.0/24`'s replacement, selects the
  renamed group and is not reported; `<peer-203.0.11*>` and the second are left as written and
  reported; `groups GR interfaces <ge-0/0/1?>` under the same AS options is unchanged and not
  reported (NEW-R14)

#### Scenario: Revert keeps each spelling

- **WHEN** `<ebgp>` beside group `EBGP`, or `<EBGP>` beside a description `ebgp`, is anonymized with
  `--anonymize-sensitive-words ebgp` and reverted
- **THEN** each wildcard comes back in its own case

#### Scenario: Where the names are

- **WHEN** `<EBGP-*>` in group `GR-A` meets `EBGP-B` defined only in group `GR-B`, or
  `routing-instances <*> protocols bgp group <EBGP-*>` meets `routing-instances R1 protocols bgp
  group EBGP-A`, under `--anonymize-groups`
- **THEN** both are reported; a top-level `<EBGP-*>` beside `EBGP-A` only in `R1` is not, and
  another wildcard (`<*BGP*>`) is no name it selects
