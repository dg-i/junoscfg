## Purpose

Readers and writers key a list entry by the tree's fields in declared order:
each input gives the device's IR, output writes it as the device does, and no
token is dropped.

## ADDED Requirements

### Requirement: Every reader gives the device's IR for a keyed entry

WHEN a list entry arrives as set, structured, JSON, YAML or XML through
`to_dict` or `convert_config` THEN each reader SHALL key it by the fields
`entry_keys()` names; the set reader SHALL take one token per key in key
order, the node's pre-key keywords before or after the keys, and merge lines
with equal key tuples into one entry, keeping entry order; the XML reader
SHALL wrap a lone entry of a tree list in an array. The identity is device IR
to set and back to IR.
Tests: `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_as_list_references_give_one_ir`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_attributes_match_gives_its_three_fields`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_route_filter_holds_its_action`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_a_community_action_reads_in_either_order`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_identity_is_the_key_tuple`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_device_ir_round_trips_through_set`, `tests/test_device_truth.py::test_every_door_gives_the_device_ir`

#### Scenario: AS-list references

- **WHEN** `from as-path-neighbors as-list AS-LIST-A`, and the same under
  `as-path-origins` and `as-path-transits`, arrives in each format, at term and
  policy level, at the root, in a logical system, a group and a grouped one
- **THEN** each IR entry is `{"list-type": "as-list", "list-name": "AS-LIST-A"}`
  (device probe, vMX 23.2R2-S7.5)

#### Scenario: Three key fields, and a key with an action

- **WHEN** `attributes-match ping.test-owner matches "^uptime$"` and `from
  route-filter 198.51.100.0/24 exact accept` are read
- **THEN** the first carries `from-event-attribute`, `condition`,
  `to-event-attribute-value` and no `name`, `_v0` or `_v1`; the second is
  `{"address": "198.51.100.0/24", "exact": [null], "accept": [null]}`

#### Scenario: Community action in either order

- **WHEN** `then community add COMM-A` or `then community COMM-A add` arrives as
  set, or the device's XML or JSON of it arrives
- **THEN** each IR is `{"add": [null], "community-name": "COMM-A"}`

#### Scenario: Identity

- **WHEN** one AS-list line is read twice, then `as-list-group` with the same
  name, then `as-list AS-LIST-B`
- **THEN** the list holds three entries in that order

#### Scenario: Device-truth captures

- **WHEN** `tests/data/captures/keyed-entries-*` (set, structured, JSON, XML),
  built from the probe with prompts, hostnames and `junos:changed-*` stripped
- **THEN** every door's IR equals the capture's JSON

### Requirement: Writers follow the declared order

WHEN set or structured output renders a list entry THEN the writer SHALL
write the children declared before the keys, then the key values unlabelled
in key order, then the other children, in the statements the device displays,
one set line for each probed entry below; IR, set and structured output of
`name`-keyed lists SHALL stay byte-identical, and phase 5 SHALL stop and
report any other slot whose rendering moves.
Tests: `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_json_and_xml_write_one_set_line`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_structured_output_writes_the_keys_in_order`, `tests/test_characterization.py::TestNameKeyedListsAreUnchanged::test_corpus_output_is_byte_identical`

#### Scenario: Device JSON and XML to set and structured

- **WHEN** the device-shaped JSON or XML AS-list, community, route-filter and
  `attributes-match` entries are converted
- **THEN** set output is `... as-path-neighbors as-list AS-LIST-A`, `... then
  community add COMM-A`, `... route-filter 198.51.100.0/24 exact accept` and
  the one `attributes-match` line, and structured output
  `as-path-neighbors as-list AS-LIST-A;`

### Requirement: Tokens the reader cannot place are kept

WHEN a set line holds a token the tree cannot place THEN the reader SHALL place
the tokens before it, create an entry only once all its key values are read,
and keep the rest of the line, from that token on, as one unplaced statement at
the deepest node it fully placed; field validation SHALL report it `UNPLACED`.
No branch SHALL return with a token unread.
Tests: `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_partial_key_creates_no_entry`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_surplus_token_after_the_key_is_kept`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_an_unknown_token_path_is_unchanged`, `tests/test_set_input.py::TestApplyGroups::test_a_second_group_token_is_kept`, `tests/test_field_validator.py::TestAnUnmodelledStatementIsReported::test_a_partial_key_and_a_surplus_are_unplaced`

#### Scenario: A partial key

- **WHEN** `... from as-path-neighbors as-list` is read, which the device
  rejects at `set`
- **THEN** no entry exists, `from` holds `as-path-neighbors as-list` unplaced,
  and set output reproduces the line

#### Scenario: A surplus after a complete key

- **WHEN** `... from as-path-neighbors as-list AS-LIST-A EXTRA` is read
- **THEN** the entry exists, holds `EXTRA` unplaced, and set output reproduces
  the line

#### Scenario: apply-groups with a second token

- **WHEN** `set apply-groups G1 G2` is read, which the device rejects at the
  second token
- **THEN** `G1` is an applied group, `G2` is kept unplaced at the root, and
  field validation reports it
