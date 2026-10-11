## Purpose

A value written inside free text -- an address in a URL or a description, a URL's user and
password, an AS number in a name, a group named in an `apply-path` -- is the value of the rule that
claims it, as it is where it stands alone. Anonymization replaces it by that rule, never rewrites
what another rule wrote, and revert restores it exactly.

## ADDED Requirements

### Requirement: A value inside free text goes to the rule that owns its shape

WHEN the anonymize walker meets a string value that no rule replacing whole values takes (the
password, SSH-key, community, identity, group, description and AS-number rules by their places)
THEN it SHALL rewrite, rule by rule in the walker's order, each part of it a rule recognises by its
shape: an address or prefix (the IP rule, under `ips`), a URL's password and user in
`scheme://user[:password]@` (the password rule, under `passwords`; the identity rule, under
`identities`, with the pseudonym a login user of that name takes), a word that is a password hash, a
sensitive word or pattern, and a configured AS number between non-digits and outside an address
(the AS-number rule, under `as_numbers_in_strings`). It SHALL do so alike for a placed value and
for content the walk cannot place, and SHALL never offer text one rule wrote to another rule. A
part that is the whole value SHALL be replaced only where its rule takes the value, so a value that
is one address on a leaf whose type holds none (`snmp view V oid 1.3.6.1`, `from area 0.0.0.0`)
stays, unless `ips_in_strings` is on, which takes an address that is a whole value on any leaf. A
value of the leaf's own enum stays, and `include`/`exclude` apply. No pass after the walk SHALL
rewrite a value. This is the interim rule of specification challenge S1 (owner decision pending).
Tests: `tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_each_value_inside_it_is_replaced`, `tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_an_address_that_is_the_whole_value_answers_by_the_type`, `tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_text_one_rule_wrote_is_never_rewritten`, `tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_an_address_is_no_as_number`, `tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_the_url_user_takes_the_login_users_pseudonym`, `tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_the_filters_apply_inside_free_text`, `tests/unit/anonymize/test_ip_rule.py::TestIpAnonymizeIntegration::test_an_address_inside_free_text_is_replaced`, `tests/unit/anonymize/test_identity_rule.py::TestAUrlUserIsAnIdentity::test_it_takes_the_login_users_pseudonym`, `tests/unit/anonymize/test_password_rule.py::TestAUrlPasswordIsASecret::test_it_is_replaced`

#### Scenario: A URL and prose under every door

- **WHEN** `archive-sites "scp://operator:secret99@203.0.114.5/path"` beside login user `operator`,
  and `description "uplink to 203.0.114.6 port 3"`, arrive as set or curly text, one-line or
  across lines, beside comments holding `;`, `{`, `}` and quotes, and are anonymized by
  `convert_config` or `junoscfg convert` with `--anonymize-ips`, `--anonymize-identities` and
  `--anonymize-passwords`
- **THEN** neither address, nor `operator`, nor `secret99` survives; the URL's user takes the login
  user's pseudonym; `scp://`, `uplink to` and `port 3` stay; and the dumped mapping restores the
  original

#### Scenario: Address-form values, syntax, and another rule's text

- **WHEN** `10.255.0.1:100`, `target:203.0.114.65:100`, `host:203.0.114.9`, `lo_203.0.114.9`,
  `oid 1.3.6.1` and `from area 0.0.0.0` are anonymized with `--anonymize-ips`, and
  `description "via 10.100.0.1 AS100"` with `--anonymize-as-numbers 100` and its in-strings option
- **THEN** each address inside a word is replaced and its text stays; the OID and the area stay
  (with `--anonymize-ips-in-strings` the OID is rewritten: NEW-R17, change 18); `AS100` is
  replaced and `10.100.0.1` stays whole (NEW-R16); a URL under an excluded path stays as written

### Requirement: An apply-path names configuration

WHEN the walker meets the value of an `apply-path` THEN it SHALL read it against the schema tree
from the configuration root: a word the tree names at that point is a keyword and SHALL stay; the
word after a list's keyword is the value of that list's key field and SHALL be offered to the rules
as that key field's value at that path, so a name renamed elsewhere takes the same pseudonym and an
address the same replacement; a wildcard there SHALL be treated as a wildcard name is
(`anonymization/wildcard-names`): `<*>` passes, an address pattern of whole octets takes its
prefix's replacement, and one whose selection changes is reported by the `apply-path`'s schema
path. A path the tree cannot read to its end SHALL be content the walk cannot place: its words are
rewritten by their shapes and its schema path is named in `AnonymizeResult.unplaced`.
Tests: `tests/unit/anonymize/test_walker.py::TestAnApplyPathNamesConfiguration::test_a_name_in_it_takes_the_names_pseudonym`, `tests/unit/anonymize/test_walker.py::TestAnApplyPathNamesConfiguration::test_its_keywords_stay`, `tests/unit/anonymize/test_walker.py::TestAnApplyPathNamesConfiguration::test_a_wildcard_in_it_is_a_pattern`, `tests/unit/anonymize/test_walker.py::TestAnApplyPathNamesConfiguration::test_a_path_the_tree_cannot_read_is_named`, `tests/unit/anonymize/test_walker.py::TestAnApplyPathNamesConfiguration::test_the_mapping_restores_it`

#### Scenario: A renamed BGP group, a keyword, the device example

- **WHEN** `apply-path "protocols bgp group EBGP neighbor <*>"` beside `protocols bgp group EBGP`
  is anonymized with `--anonymize-groups`, or with `--anonymize-sensitive-words bgp`
- **THEN** the path names the group's pseudonym, `<*>` and `protocols bgp group` stay, and the
  prefix list still selects the group's neighbours (NEW-A-N7); the device example's
  `"protocols bgp group <*> neighbor <*>"` (vMX 23.2R2-S7.5, QFX5120 25.2R2-S1.5) is unchanged

### Requirement: Revert undoes each replacement once

WHEN `apply_revert` restores a value or a key THEN it SHALL first take a whole value the mapping
records, then undo every other replacement the mapping records in one pass over the text, the
longest first, a number only between non-digits and never inside an address, and every address
last; a replacement SHALL never be undone twice nor depend on the mapping's order. A sensitive
word's pseudonym SHALL be keyed by its spelling, so two spellings of one word get two pseudonyms and
each reverts to its own; matching stays case-insensitive.
Tests: `tests/unit/anonymize/test_revert.py::TestRevertUndoesEachReplacementOnce::test_a_number_is_restored_only_between_non_digits`, `tests/unit/anonymize/test_revert.py::TestRevertUndoesEachReplacementOnce::test_the_order_of_the_mapping_does_not_matter`, `tests/unit/anonymize/test_revert.py::TestRevertUndoesEachReplacementOnce::test_a_number_inside_an_address_is_no_number`, `tests/unit/anonymize/test_revert.py::TestRevertUndoesEachReplacementOnce::test_a_replacement_inside_a_word_is_restored`, `tests/unit/anonymize/test_sensitive_word_rule.py::TestEachSpellingHasItsPseudonym::test_two_spellings_get_two_pseudonyms`, `tests/unit/anonymize/test_sensitive_word_rule.py::TestEachSpellingHasItsPseudonym::test_a_value_in_two_cases_reverts_to_each`, `tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_the_mapping_restores_each_row`

#### Scenario: AS numbers

- **WHEN** the mapping holds `64496` to `64497` and `64497` to `64498`, and the text holds
  `AS64497`, `AS6449712` and `64498`
- **THEN** revert gives `AS64496`, `AS6449712` and `64497`, whatever the mapping's order (NEW-A-N5)

#### Scenario: Two cases of one word

- **WHEN** `protocols bgp group EBGP description ebgp` and `description EBGP` are anonymized with
  `--anonymize-sensitive-words ebgp` and reverted
- **THEN** each value comes back in its own case (NEW-R13)
