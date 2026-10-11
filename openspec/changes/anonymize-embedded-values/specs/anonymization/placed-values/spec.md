## MODIFIED Requirements

### Requirement: The IP rule answers by the leaf's type

WHEN the IP rule is offered a value that is one IPv4 or IPv6 address or prefix THEN it SHALL take
it only if the leaf's type is an address type, a host type (`host`, `hostname`), `ipprefix-only`,
free text (`string`, `key-attribute-string-type`: S4 of change anonymize-embedded-values) but for
an SNMP OID (`snmp view V oid`), or none at all; a key of a list the tree types `areaid`
(`ospf area`) answers by its list's name, and BGP `cluster` by its own (S4); no other type takes
one, unless `ips_in_strings` is on. WHEN an address stands
beside other text in the value (a route distinguisher, a VRF target, community `members`, a URL,
prose) THEN it SHALL be replaced on any leaf (`anonymization/embedded-values`, S1 of change
anonymize-embedded-values). Text beside the address in the same word (`/rack-4`, `,`, `:8080`,
`/33`, `%ge-0/0/0.0`, a trailing `/`) SHALL stay as text and never fail the run; no value without
an address SHALL reach the address anonymizer.
Tests: `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_an_address_on_these_types_is_replaced`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_a_name_on_a_host_type_is_not`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_no_other_type_takes_an_address`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_an_interface_name_never_reaches_the_address_anonymizer`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_every_address_the_device_writes_there_is_replaced`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_syntax_shaped_like_an_address_is_unchanged`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_a_malformed_value_never_crashes`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_an_address_inside_a_route_distinguisher_or_target_is_replaced`, `tests/unit/anonymize/test_ip_rule.py::TestTheLeafsTypeAnswers::test_a_policy_community_matches_its_renamed_target`, `tests/unit/anonymize/test_ip_rule.py::TestIpAnonymizeIntegration::test_an_address_inside_free_text_is_replaced`, `tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_an_address_alone_in_free_text_is_replaced`

#### Scenario: Syntax shaped like an address

- **WHEN** `snmp view V oid 1.3.6.1`, `from area 0.0.0.0` or an integer BGP
  `cluster` is anonymized, `--anonymize-ignore-reserved` on
- **THEN** it is unchanged; `protocols ospf area 0.0.0.0` is still rewritten
  there through the list name, as before (specification challenge S3), and an
  address in `cluster` or `ipv6-router-id` is replaced like the router ID (S4)

#### Scenario: An interface where an address may stand

- **WHEN** `from interface ge-0/0/0.0` or `next-hop ge-0/0/0.0` is anonymized
- **THEN** it passes unchanged; the run used to crash (NEW-R8)

#### Scenario: An address inside free text

- **WHEN** `archive-sites "scp://admin@203.0.114.5/path"` or `description "uplink to 203.0.114.6"`
  is anonymized with `--anonymize-ips` alone
- **THEN** the address is replaced and the text around it stays; it used to survive unless
  `--anonymize-ips-in-strings` was on (ANON-P5)

#### Scenario: An address alone in free text

- **WHEN** `description 203.0.114.9` or `snmp location 203.0.114.9` is anonymized with
  `--anonymize-ips`
- **THEN** the address is replaced; it survived with no word (specification challenge S4)
