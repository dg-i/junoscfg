# conversion/entry-keys Specification

## Purpose
Readers and writers key a list entry by the tree's fields in declared order:
each input gives the device's IR, output writes it so, and no token is dropped.

## Requirements

### Requirement: Every reader gives the device's IR for a keyed entry

WHEN a list entry arrives as set, structured, JSON, YAML or XML through
`to_dict` or `convert_config` THEN each reader SHALL key it by the fields
`entry_keys()` names; the set reader SHALL take one value per positional field
in order, a field whose leaf is not `nokeyword` as `keyword value` (such fields
in any order among themselves), a key choice as its keyword and value before or
after the rest (device probe, vMX 23.2R2-S7.5), and merge equal key tuples.
The XML walker in `display/to_yaml.py` SHALL take a lone element's list shape
from the tree, loaded lazily by `load_schema_tree()`, and the `name`-child
heuristic only where the tree does not reach. Identity: device IR to set to IR.
Tests: `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_as_list_references_give_one_ir`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_attributes_match_gives_its_three_fields`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_route_filter_holds_its_action`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_a_community_action_reads_in_either_order`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_identity_is_the_key_tuple`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_device_ir_round_trips_through_set`, `tests/test_to_yaml.py::TestLoneEntryFollowsTheTree::test_a_lone_keyed_entry_is_a_list`, `tests/test_to_yaml.py::TestLoneEntryFollowsTheTree::test_an_element_outside_the_tree_keeps_the_name_heuristic`, `tests/test_to_yaml.py::TestLazyXmlImport::test_to_yaml_module_level_has_no_lxml`, `tests/test_device_truth.py::test_every_door_gives_the_device_ir`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_every_writer_reads_back_the_device_ir`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_an_attribute_on_a_keyed_entry_agrees_across_readers`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_an_empty_list_writes_nothing`, `tests/test_to_yaml.py::TestLoneEntryFollowsTheTree::test_a_lone_attributes_match_is_a_list`, `tests/test_device_truth.py::test_device_attributes_leave_the_keys_alone`, `tests/test_set_input.py::TestKeyValuesOfEveryShape::test_each_key_value_is_one_token`, `tests/test_set_input.py::TestMetaCommandsOnAKeyedEntry::test_the_attribute_lands_on_the_entry`, `tests/test_set_input.py::TestAKeyKeywordBeforeTheValues::test_a_match_type_before_the_address`, `tests/test_device_truth.py::test_route_filter_entries_are_keyed_by_address_and_match_type`, `tests/test_device_truth.py::test_a_match_type_before_the_address_is_accepted`, `tests/test_set_input.py::TestKeyFieldsGivenByKeyword::test_declared_order`, `tests/test_set_input.py::TestKeyFieldsGivenByKeyword::test_the_reversed_order_gives_the_same_ir`, `tests/test_set_input.py::TestKeyFieldsGivenByKeyword::test_device_json_keeps_the_keywords`, `tests/test_set_input.py::TestKeyFieldsGivenByKeyword::test_other_keyword_keys`, `tests/test_set_input.py::TestANonListNodeNeverReplacesAnEntry::test_three_forwarding_classes_stay_three`, `tests/test_set_input.py::TestANonListNodeNeverReplacesAnEntry::test_two_entries_stay_two`

#### Scenario: AS-list references

- **WHEN** `from as-path-neighbors as-list AS-LIST-A`, or `as-path-origins` or
  `as-path-transits`, arrives in each format, at term and policy level, at the
  root, in a logical system, a group and a grouped one, XML of one entry too
- **THEN** each IR is `[{"list-type": "as-list", "list-name": "AS-LIST-A"}]`
  (device probe, vMX 23.2R2-S7.5)

#### Scenario: Three key fields, and a key choice with an action

- **WHEN** `attributes-match ping.test-owner matches "^uptime$"` and `from
  route-filter 198.51.100.0/24 exact accept` are read
- **THEN** the first carries its three fields and no `name`, `_v0` or `_v1`; the
  second is `{"address": "198.51.100.0/24", "exact": [null], "accept": [null]}`

#### Scenario: Key keywords in either order

- **WHEN** `then community COMM-A add`, or `virtual-link transit-area 0.0.0.3
  neighbor-id 10.255.255.2`, or the device's XML or JSON of either, is read
- **THEN** the IR and set output hold the fields in declared order

#### Scenario: Lists the XSD bounds by a number

- **WHEN** `forwarding-classes { class fc0 queue-num 0; class fc1 queue-num 1;
  class mcast-fc queue-num 2; }`, or two `commit peers`, or two `http servers server`
- **THEN** each is a list holding every entry, none replaced (challenge A)

#### Scenario: Identity

- **WHEN** an AS-list line twice, `as-list-group`, `as-list AS-LIST-B`; or
  `route-filter 198.51.100.0/24` `exact`, then `orlonger`, are read
- **THEN** the first list holds three entries and the second two, in order

#### Scenario: Device-truth captures

- **WHEN** each door of `tests/data/captures/keyed-entries-*` is read
- **THEN** its IR equals the capture's JSON

### Requirement: Writers follow the declared order

WHEN set or structured output renders a list entry THEN set output SHALL write
the keyword, the key values in declared order, each not `nokeyword` with its
keyword, a key choice as its keyword and value, then each other child on a line
of its own; structured output SHALL put an entry on one line exactly where the
node carries `o`. `name`-keyed output SHALL stay byte-identical, the device's
structured static route and `attributes-match` SHALL be pinned beside today's,
and phase 5 SHALL stop and report any other slot whose rendering moves.
Tests: `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_json_and_xml_write_the_device_set_lines`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_structured_output_writes_the_keys_in_order`, `tests/test_characterization.py::TestNameKeyedListsAreUnchanged::test_corpus_output_is_byte_identical`, `tests/test_device_truth.py::test_name_keyed_set_lines_match_the_device`, `tests/test_device_truth.py::test_unexplained_structured_shapes_are_pinned`

#### Scenario: Device JSON and XML to set and structured

- **WHEN** the device-shaped AS-list, community, route-filter, source-address-filter
  and `attributes-match` entries are converted
- **THEN** each is one set line as the device displays it, and structured output
  writes `route-filter 198.51.100.0/24 exact accept;` and `community add COMM-A;`

#### Scenario: Name-keyed lists, as the device splits them

- **WHEN** static `route`, NTP `server` and `flag` entries with two children are set
- **THEN** each child is a line of its own (device probe, vMX 23.2R2-S7.5)

### Requirement: A statement the reader cannot complete is kept whole

WHEN a set line holds an entry whose key values run out, a key field without
its keyword, a token after a terminal entry, `apply-groups` bare or with two
names, `apply-macro` with a fourth value, or a second, different value for a
nokeyword leaf of a node that is no list, THEN the reader
SHALL create, replace and apply nothing from it, SHALL keep it whole from its
keyword at its parent, and field validation SHALL report it `UNPLACED`; an
unknown token after a complete key of an entry with children stays in-entry.
Tests: `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_partial_key_creates_no_entry`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_surplus_after_a_terminal_entry_keeps_the_line_whole`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_an_unknown_token_in_an_entry_with_children_is_unchanged`, `tests/test_set_input.py::TestApplyGroups::test_a_second_group_token_keeps_the_line_whole`, `tests/test_field_validator.py::TestAnUnmodelledStatementIsReported::test_an_incomplete_statement_is_unplaced`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_bare_list_keyword_creates_no_entry`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_partial_attributes_match_creates_no_entry`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_surplus_after_attributes_match_keeps_the_line_whole`, `tests/test_set_input.py::TestApplyGroupsAndKeyedEntries::test_one_name_inside_a_policy`, `tests/test_set_input.py::TestApplyGroupsAndKeyedEntries::test_two_names_apply_no_group`, `tests/test_field_validator.py::TestAnIncompleteStatementIsUnplaced::test_each_door_reports_it`, `tests/test_set_input.py::TestKeyFieldsGivenByKeyword::test_an_incomplete_key_is_kept_whole_and_reported`, `tests/test_set_input.py::TestApplyMacroTakesAtMostThreeValues::test_one_to_three_values`, `tests/test_set_input.py::TestApplyMacroTakesAtMostThreeValues::test_a_fourth_value_is_kept_whole_and_reported`, `tests/test_set_input.py::TestABareApplyGroups::test_it_is_reported`, `tests/test_set_input.py::TestABareApplyGroups::test_a_group_after_a_bare_one_is_kept_too`, `tests/test_set_input.py::TestABareApplyGroups::test_a_keyed_entry_after_a_bare_keyword_is_kept_too`, `tests/test_set_input.py::TestANonListNodeNeverReplacesAnEntry::test_a_second_value_of_a_nokeyword_leaf_is_kept_whole`, `tests/test_set_input.py::TestANonListNodeNeverReplacesAnEntry::test_the_same_value_again_is_one_statement`

#### Scenario: Statements the device rejects

- **WHEN** `... as-path-neighbors as-list`, `... route-filter 198.51.100.0/24
  next-policy`, `... as-list AS-LIST-A EXTRA`, `set apply-groups G1 G2`, bare
  `set apply-groups`, `virtual-link neighbor-id 10.255.255.3`, `virtual-link
  10.255.255.4 0.0.0.2` or `apply-macro 12345 "KADJBF KU!H" balks XXXXX` is read
- **THEN** the parent holds it unplaced, set output reproduces it (device probe,
  vMX 23.2R2-S7.5, rejects each)
