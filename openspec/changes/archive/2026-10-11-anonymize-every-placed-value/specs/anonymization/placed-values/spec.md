## Purpose

Anonymization never claims success while a value it could replace survives
unannounced. The walker reaches every value the structure tree places and offers
it to the rules; content it cannot place is handled by one rule, the same at the
library door and in the conversion, and is named in a warning that carries no
original value.

## ADDED Requirements

### Requirement: The walker reaches every value the schema places

WHEN the anonymize walker meets a key THEN it SHALL resolve it through
`junoscfg.display.schema_child`, so a universal statement below the root
(`apply-groups`, `apply-groups-except`, `apply-macro`) is walked against the
root's node; for a transparent container it SHALL walk the transparent child's
entries against the child's node and every other child against the container's
own node; for a container that is no list holding a list it SHALL walk each
entry; and a list's key field the tree holds no leaf for SHALL reach the rules
as a leaf of no type.
Tests: `tests/unit/anonymize/test_walker.py::TestTheWalkerReachesEveryPlacedValue::test_a_universal_statement_below_the_root`, `tests/unit/anonymize/test_walker.py::TestTheWalkerReachesEveryPlacedValue::test_a_transparent_containers_other_children`, `tests/unit/anonymize/test_walker.py::TestTheWalkerReachesEveryPlacedValue::test_each_entry_of_a_list_a_container_holds`, `tests/unit/anonymize/test_walker.py::TestTheWalkerReachesEveryPlacedValue::test_a_key_field_the_tree_holds_no_leaf_for`, `tests/contract/test_every_rule.py::TestEveryRule::test_a_value_is_replaced_alike_everywhere`, `tests/corpus/test_device_anonymization.py::TestEveryCaptureAnonymizes::test_no_address_of_the_capture_survives`

#### Scenario: The device example and nested statements

- **WHEN** `interface-range` descriptions sit beside `interface`, JSON holds the
  port-mirroring `routing-instance` as a list of one, or `system apply-macro M2
  peer 203.0.114.8` stands below the root
- **THEN** every rule sees their values, as at the root (ANON-P2, NEW-C11)

### Requirement: The IP rule answers by the leaf's type

WHEN the IP rule is offered a value THEN it SHALL take it only if the value
starts with an IPv4 or IPv6 address or prefix and the leaf's type is an address
type, a host type (`host`, `hostname`), `ipprefix-only`, or none at all; a key
of one of the lists the tree types only as free text or `areaid`
(`syslog host`, `ospf area`, ...) answers by its list's name; `ipv6-router-id`,
`cluster`, a route distinguisher, a VRF target, community `members` by their
own, the address anywhere in the value (S4, S5, R1); no other free text is one. Text beside the address in the same word
(`/rack-4`, `,`, `:8080`, `/33`, `%ge-0/0/0.0`, a trailing `/`) SHALL stay as text and
never fail the run; no value without an address SHALL reach the address
anonymizer.
Tests: `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_an_address_on_these_types_is_replaced`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_a_name_on_a_host_type_is_not`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_no_other_type_takes_an_address`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_an_interface_name_never_reaches_the_address_anonymizer`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_every_address_the_device_writes_there_is_replaced`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_syntax_shaped_like_an_address_is_unchanged`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_a_malformed_value_never_crashes`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_an_address_inside_a_route_distinguisher_or_target_is_replaced`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_a_policy_community_matches_its_renamed_target`

#### Scenario: Syntax shaped like an address

- **WHEN** `snmp view V oid 1.3.6.1`, `from area 0.0.0.0` or an integer BGP
  `cluster` is anonymized, `--anonymize-ignore-reserved` on
- **THEN** it is unchanged; `protocols ospf area 0.0.0.0` is still rewritten
  there through the list name, as before (specification challenge S3), and an
  address in `cluster` or `ipv6-router-id` is replaced like the router ID (S4)

#### Scenario: An interface where an address may stand

- **WHEN** `from interface ge-0/0/0.0` or `next-hop ge-0/0/0.0` is anonymized
- **THEN** it passes unchanged; the run used to crash (NEW-R8)

### Requirement: A group reference goes to the group rule once

WHEN `apply-groups` or `apply-groups-except` stands at any level THEN the group
rule SHALL claim its values in the walk, so a group and every reference to it
get one replacement whichever other rules are on, and no second pass SHALL
rewrite a reference again. A name Junos reserves (`re0`, `re1`, `node0`,
`node1`, `member<N>`, a `$` variable such as `${node}`) SHALL pass unchanged as a
group and as a reference.
Tests: `tests/unit/anonymize/test_group_rule.py::TestApplyGroupsIsAReference::test_the_rule_claims_both_statements`, `tests/unit/anonymize/test_integration.py::TestGroupReferencesResolve::test_every_reference_names_the_renamed_group`, `tests/contract/test_every_rule.py::TestRulesDoNotOverlap::test_a_value_goes_to_the_first_rule_that_takes_it`, `tests/contract/test_every_rule.py::TestEveryRuleTogether::test_every_rule_together_reverts`, `tests/corpus/test_device_anonymization.py::TestEveryCaptureAnonymizes::test_every_group_reference_resolves`, `tests/unit/anonymize/test_integration.py::TestAGroupJunosReservesKeepsItsName::test_the_reserved_names_pass`

#### Scenario: Groups and sensitive words together

- **WHEN** `groups acme-base` is applied at the root, in `system` and under
  `interfaces`, with the group rule and `--anonymize-sensitive-words acme` on
- **THEN** every reference names the group's one pseudonym and revert restores
  all of them (ANON-P1)

### Requirement: Content the walk cannot place is named, its addresses replaced

WHEN `anonymize()` or an anonymizing conversion meets content its walk cannot
place (a key the schema does not name, a value of a shape its node does not
take, or a statement kept whole in `junoscfg:unplaced`) THEN it SHALL rewrite
each word of its keys and values that a rule recognises by its shape alone --
an address or prefix, a password hash (`$9$`, `$1$`, `$5$`, `$6$`...), a
sensitive word -- as that rule does, in turn on the same word, never a keyword,
and a tag (`@<key>`) SHALL follow its renamed key; an address inside a word
(`http://203.0.114.9:8080/x`, `lo_203.0.114.9`) is replaced as well. It SHALL leave every other word as written and
name the place, once per piece, by its schema path (the parent of an unknown
key, the key of a misshapen value) in `AnonymizeResult.unplaced` and in one
`anonymize` warning per path that names only the shapes the active rules
replace, withholding the key, every entry name and every value. Neither door SHALL refuse it. In an anonymized run, the text of every
`UNPLACED` field-validation message, returned or raised, SHALL be withheld.
Revert SHALL restore the replaced words of a key (owner answer 5; the
password and sensitive-word half is specification challenge S2).
Tests: `tests/unit/anonymize/test_integration.py::TestContentTheWalkCannotPlace::test_its_addresses_are_replaced`, `tests/unit/anonymize/test_integration.py::TestContentTheWalkCannotPlace::test_its_schema_path_is_named`, `tests/unit/anonymize/test_integration.py::TestContentTheWalkCannotPlace::test_every_other_word_is_left_as_written`, `tests/unit/anonymize/test_integration.py::TestContentTheWalkCannotPlace::test_the_mapping_restores_it`, `tests/unit/anonymize/test_integration.py::TestContentTheWalkCannotPlace::test_without_the_ip_rule_it_is_still_named`, `tests/unit/anonymize/test_integration.py::TestContentTheWalkCannotPlace::test_without_a_rule_nothing_changes`, `tests/unit/anonymize/test_integration.py::TestContentTheWalkCannotPlace::test_a_password_hash_and_a_sensitive_word_are_replaced_by_shape`, `tests/unit/anonymize/test_integration.py::TestContentTheWalkCannotPlace::test_every_shape_in_one_word_is_replaced`, `tests/unit/anonymize/test_revert.py::TestRevertRestoresKeys::test_an_address_inside_a_word_of_a_key_is_restored`, `tests/unit/anonymize/test_integration.py::TestEveryDoorGivesOneAnswer::test_no_address_passes_and_a_warning_names_the_path`, `tests/unit/anonymize/test_integration.py::TestEveryDoorGivesOneAnswer::test_no_message_carries_an_original_value`, `tests/unit/anonymize/test_revert.py::TestRevertRestoresKeys::test_an_address_in_a_key_is_restored`, `tests/unit/cli/test_cli.py::TestAKeptStatementOnTheCommandLine::test_anonymizing_warns_without_the_statement`, `tests/unit/convert/test_field_validator.py::TestThePipelineAppliesFieldValidation::test_anonymization_replaces_the_addresses_it_cannot_place`, `tests/corpus/test_device_anonymization.py::TestEveryCaptureAnonymizes::test_the_mapping_restores_the_canonical_ir`

#### Scenario: Every door

- **WHEN** `unknown-knob 203.0.114.9` under a BGP group arrives as set, curly,
  JSON, YAML or XML, or a 0.16.1 joined key `bogus 203.0.114.9 G-SECRET` as JSON,
  and is anonymized by `anonymize()`, `convert_config` or `junoscfg convert`
- **THEN** `203.0.114.9` is replaced, `unknown-knob`, `bogus` and `G-SECRET`
  stay, `protocols.bgp.group` (or `system`) is named, and no message, `--strict`
  included, carries `203.0.114.9`, `G-SECRET` or the group's name
