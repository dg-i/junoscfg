## Purpose

Readers and writers key a list entry by the tree's fields in declared order:
each input gives the device's IR, output writes it as the device does, and no
token is dropped.

## ADDED Requirements

### Requirement: Every reader gives the device's IR for a keyed entry

WHEN a list entry arrives as set, structured, JSON, YAML or XML through
`to_dict` or `convert_config` THEN each reader SHALL key it by the fields
`entry_keys()` names; the set reader SHALL take one value per field in order,
a key choice as its keyword and value before or after the positional values
(device probe, vMX 23.2R2-S7.5), and merge equal key tuples into one entry.
The XML walker in `display/to_yaml.py` SHALL take a lone element's list shape
from the tree, loaded lazily by `load_schema_tree()`, and the `name`-child
heuristic only where the tree does not reach. Identity: device IR to set to IR.
Tests: `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_as_list_references_give_one_ir`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_attributes_match_gives_its_three_fields`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_route_filter_holds_its_action`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_a_community_action_reads_in_either_order`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_identity_is_the_key_tuple`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_device_ir_round_trips_through_set`, `tests/test_to_yaml.py::TestLoneEntryFollowsTheTree::test_a_lone_keyed_entry_is_a_list`, `tests/test_to_yaml.py::TestLoneEntryFollowsTheTree::test_an_element_outside_the_tree_keeps_the_name_heuristic`, `tests/test_to_yaml.py::TestLazyXmlImport::test_to_yaml_module_level_has_no_lxml`, `tests/test_device_truth.py::test_every_door_gives_the_device_ir`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_every_writer_reads_back_the_device_ir`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_an_attribute_on_a_keyed_entry_agrees_across_readers`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_an_empty_list_writes_nothing`, `tests/test_to_yaml.py::TestLoneEntryFollowsTheTree::test_a_lone_attributes_match_is_a_list`, `tests/test_device_truth.py::test_device_attributes_leave_the_keys_alone`, `tests/test_set_input.py::TestKeyValuesOfEveryShape::test_each_key_value_is_one_token`, `tests/test_set_input.py::TestMetaCommandsOnAKeyedEntry::test_the_attribute_lands_on_the_entry`, `tests/test_set_input.py::TestAKeyKeywordBeforeTheValues::test_a_match_type_before_the_address`, `tests/test_device_truth.py::test_route_filter_entries_are_keyed_by_address_and_match_type`, `tests/test_device_truth.py::test_a_match_type_before_the_address_is_accepted`

#### Scenario: AS-list references

- **WHEN** `from as-path-neighbors as-list AS-LIST-A`, and the same under
  `as-path-origins` and `as-path-transits`, arrives in each format, at term and
  policy level, at the root, in a logical system, a group and a grouped one,
  XML holding one entry included
- **THEN** each IR is a one-entry list `{"list-type": "as-list", "list-name":
  "AS-LIST-A"}` (device probe, vMX 23.2R2-S7.5)

#### Scenario: Three key fields, and a key choice with an action

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
  name, then `as-list AS-LIST-B`; or `route-filter 198.51.100.0/24 exact`,
  then `orlonger`, on one address
- **THEN** the first list holds three entries and the second two, in order

#### Scenario: Device-truth captures

- **WHEN** `tests/data/captures/keyed-entries-*` (set, structured, JSON, XML),
  built from the probe with prompts, hostnames and `junos:changed-*` stripped
- **THEN** every door's IR equals the capture's JSON

### Requirement: Writers follow the declared order

WHEN set or structured output renders a list entry THEN set output SHALL write
the keyword, the key values in declared order, a key choice as its keyword and
value, then each other child on a line of its own; structured output SHALL put
an entry on one line exactly where the node carries `o`. The output of
`name`-keyed lists SHALL stay byte-identical, the device's structured shapes
for a static route with leaf children only and for `attributes-match` SHALL be
pinned beside today's in the device-truth fixture, and phase 5 SHALL stop and
report any other slot whose rendering moves.
Tests: `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_json_and_xml_write_the_device_set_lines`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_structured_output_writes_the_keys_in_order`, `tests/test_characterization.py::TestNameKeyedListsAreUnchanged::test_corpus_output_is_byte_identical`, `tests/test_device_truth.py::test_name_keyed_set_lines_match_the_device`, `tests/test_device_truth.py::test_unexplained_structured_shapes_are_pinned`

#### Scenario: Device JSON and XML to set and structured

- **WHEN** the device-shaped AS-list, community, route-filter,
  source-address-filter and `attributes-match` entries are converted
- **THEN** each is one set line as the device displays it, e.g. `...
  source-address-filter 198.51.100.0/24 exact accept`, and structured output
  writes `route-filter 198.51.100.0/24 exact accept;` and `community add COMM-A;`

#### Scenario: Name-keyed lists, as the device splits them

- **WHEN** static `route`, NTP `server` and BGP traceoptions `flag` entries
  with two children each are written as set
- **THEN** each child is a line of its own (device probe, vMX 23.2R2-S7.5)

### Requirement: A statement the reader cannot complete is kept whole

WHEN a set line holds a list entry whose key values run out, or a further
token after a terminal entry or after `apply-groups` and its one value, THEN
the reader SHALL create no entry and apply no group from it, SHALL keep the
whole statement, from its keyword, as one unplaced statement at its parent,
and field validation SHALL report it `UNPLACED`; an unknown token after a
complete key of an entry with other children stays on today's in-entry path.
Tests: `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_partial_key_creates_no_entry`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_surplus_after_a_terminal_entry_keeps_the_line_whole`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_an_unknown_token_in_an_entry_with_children_is_unchanged`, `tests/test_set_input.py::TestApplyGroups::test_a_second_group_token_keeps_the_line_whole`, `tests/test_field_validator.py::TestAnUnmodelledStatementIsReported::test_an_incomplete_statement_is_unplaced`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_bare_list_keyword_creates_no_entry`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_partial_attributes_match_creates_no_entry`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_surplus_after_attributes_match_keeps_the_line_whole`, `tests/test_set_input.py::TestApplyGroupsAndKeyedEntries::test_one_name_inside_a_policy`, `tests/test_set_input.py::TestApplyGroupsAndKeyedEntries::test_two_names_apply_no_group`, `tests/test_field_validator.py::TestAnIncompleteStatementIsUnplaced::test_each_door_reports_it`

#### Scenario: Statements the device rejects

- **WHEN** `... from as-path-neighbors as-list`, `... from route-filter
  198.51.100.0/24 next-policy` (no match type), `... from as-path-neighbors
  as-list AS-LIST-A EXTRA`, or `set apply-groups G1 G2` is read
- **THEN** no entry or group results, the parent holds the statement from its
  keyword unplaced, and set output reproduces the line (device probe, vMX
  23.2R2-S7.5, rejects each)
