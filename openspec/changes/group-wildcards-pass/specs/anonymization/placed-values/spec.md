## ADDED Requirements

### Requirement: A wildcard name is a pattern, not a name

WHEN the anonymize walker meets an entry's key field whose value is a Junos wildcard, the whole
value in angle brackets (`<*>`, `<ge-*>`, `<[gx]e-*>`, `<VRF-*>`), THEN a pattern of `*` alone
SHALL pass every rule unchanged, because it selects every name; any other wildcard SHALL keep its
brackets while the text inside them is offered to the rules as a value of that key field, so text
that spells a name is replaced as that name is (`<EBGP>` as BGP group `EBGP`, `<203.0.114.7>` as
neighbour `203.0.114.7`). WHEN the anonymized wildcard selects, among the names the configuration
holds at that key field inside and outside `groups`, other names than the original selected
(Junos wildcard characters `*`, `?`, `[...]`, `[!...]`), or a rule claims its text and leaves it
as written, THEN its place SHALL be named by schema path in `AnonymizeResult.patterns`, once per
wildcard, and in one `anonymize` warning per path that names the path and a count and withholds
every value. Revert SHALL restore every wildcard exactly. A value that is no key field (a
description written `<...>`) is data and SHALL be replaced as before. This is the interim rule of
specification challenge S1 (owner decision pending: pseudonyms that keep a wildcard's literal
text selecting the same names).
Tests: `tests/unit/anonymize/test_integration.py::TestKeyedEntriesSurvive::test_a_wildcard_group_name_passes_the_group_rule`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_a_match_all_wildcard_passes_every_rule`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_the_text_of_a_wildcard_is_replaced_as_the_name_it_spells`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_a_wildcard_that_selects_other_names_is_reported`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_a_wildcard_that_selects_the_same_names_is_not_reported`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_the_mapping_restores_every_wildcard`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_a_description_written_as_a_wildcard_is_data`, `tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_the_warning_names_the_path_and_no_value`, `tests/contract/test_every_rule.py::TestEveryRule::test_a_match_all_wildcard_name_passes`, `tests/contract/test_every_message.py::TestAnAnonymizedRunQuotesNothingOfTheConfiguration::test_no_message_holds_a_word_of_it`, `tests/corpus/test_device_anonymization.py::TestEveryCaptureAnonymizes::test_every_wildcard_name_passes`

#### Scenario: The device example's BGP wildcard

- **WHEN** `groups GR-BGP protocols bgp group <*>` (vMX 23.2R2-S7.5 and QFX5120 25.2R2-S1.5
  `junoscfg-oracle` captures) is anonymized with every rule on
- **THEN** it stays `<*>`, the group selects every BGP group as before, the mapping holds no
  wildcard, and nothing is reported

#### Scenario: A wildcard that spells one name

- **WHEN** `groups GR-BGP protocols bgp group <EBGP>` and `protocols bgp group EBGP` are
  anonymized with `--anonymize-groups`
- **THEN** the wildcard becomes `<` + the group's pseudonym + `>`, selects the renamed group, and
  nothing is reported

#### Scenario: A wildcard with literal text under a renaming rule

- **WHEN** `groups GR-BGP protocols bgp group <EBGP-*>` and `protocols bgp group EBGP-A` are
  anonymized with `--anonymize-groups`
- **THEN** the wildcard is `<group_…>`, no `EBGP` survives, `groups.protocols.bgp.group` is
  reported, and revert restores `<EBGP-*>`

#### Scenario: A sensitive word inside a wildcard

- **WHEN** the same configuration is anonymized with `--anonymize-sensitive-words ebgp`
- **THEN** the wildcard is `<word_…-*>`, it selects the renamed `word_…-A`, and nothing is reported;
  `"<[A-E]BGP*>"`, which no longer selects `word_…`, is reported

#### Scenario: An address pattern

- **WHEN** `groups GR-BGP protocols bgp group IBGP neighbor <203.0.114.*>` and a neighbour
  `203.0.114.7` are anonymized with `--anonymize-ips`
- **THEN** the wildcard is left as written and its path is reported
