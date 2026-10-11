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
Tests: `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`, `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_an_entry_keeps_its_declared_key_order`, `tests/contract/test_format_matrix.py::TestEveryWriterKeepsTheIr::test_the_output_reads_back_as_the_ir`, `tests/unit/display/test_to_yaml.py::TestLoneEntryFollowsTheTree::test_a_lone_keyed_entry_is_a_list`, `tests/unit/display/test_to_yaml.py::TestLoneEntryFollowsTheTree::test_an_element_outside_the_tree_keeps_the_name_heuristic`, `tests/unit/display/test_to_yaml.py::TestLazyXmlImport::test_importing_the_package_loads_no_lxml`, `tests/corpus/test_device_truth.py::test_every_door_gives_the_device_ir`, `tests/contract/test_format_matrix.py::TestASecondWriterKeepsTheIr::test_every_second_writer`, `tests/contract/test_format_matrix.py::TestSetOutputIsTheDeviceLines::test_the_set_lines`, `tests/unit/display/test_to_yaml.py::TestLoneEntryFollowsTheTree::test_a_lone_attributes_match_is_a_list`, `tests/corpus/test_device_truth.py::test_device_attributes_leave_the_keys_alone`, `tests/unit/convert/test_set_input.py::TestKeyValuesOfEveryShape::test_each_key_value_is_one_token`, `tests/unit/convert/test_set_input.py::TestMetaCommandsOnAKeyedEntry::test_the_attribute_lands_on_the_entry`, `tests/unit/convert/test_set_input.py::TestAKeyKeywordBeforeTheValues::test_a_match_type_before_the_address`, `tests/corpus/test_device_truth.py::test_route_filter_entries_are_keyed_by_address_and_match_type`, `tests/corpus/test_device_truth.py::test_a_match_type_before_the_address_is_accepted`, `tests/unit/convert/test_set_input.py::TestKeyFieldsGivenByKeyword::test_declared_order`, `tests/unit/convert/test_set_input.py::TestKeyFieldsGivenByKeyword::test_the_reversed_order_gives_the_same_ir`, `tests/unit/convert/test_set_input.py::TestKeyFieldsGivenByKeyword::test_device_json_keeps_the_keywords`, `tests/unit/convert/test_set_input.py::TestKeyFieldsGivenByKeyword::test_other_keyword_keys`, `tests/unit/convert/test_set_input.py::TestANonListNodeNeverReplacesAnEntry::test_three_forwarding_classes_stay_three`, `tests/unit/convert/test_set_input.py::TestANonListNodeNeverReplacesAnEntry::test_two_entries_stay_two`

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
node carries `o`. The device's structured static route and `attributes-match`
SHALL be pinned beside today's. Correctness is the device's display set
(`tests/corpus/test_device_renderings.py`), not byte identity with an earlier
release.
Tests: `tests/corpus/test_device_renderings.py::TestJunoscfgWritesTheDevicesSet::test_only_the_recorded_lines_differ`, `tests/contract/test_format_matrix.py::TestSetOutputIsTheDeviceLines::test_the_set_lines`, `tests/contract/test_format_matrix.py::TestEveryWriterKeepsTheIr::test_the_output_reads_back_as_the_ir`, `tests/corpus/test_device_truth.py::test_name_keyed_set_lines_match_the_device`, `tests/corpus/test_device_truth.py::test_unexplained_structured_shapes_are_pinned`

#### Scenario: Device JSON and XML to set and structured

- **WHEN** the device-shaped AS-list, community, route-filter, source-address-filter
  and `attributes-match` entries are converted
- **THEN** each is one set line as the device displays it, and structured output
  writes `route-filter 198.51.100.0/24 exact accept;` and `community add COMM-A;`

#### Scenario: Name-keyed lists, as the device splits them

- **WHEN** static `route`, NTP `server` and `flag` entries with two children are set
- **THEN** each child is a line of its own (device probe, vMX 23.2R2-S7.5)

### Requirement: A statement the reader cannot complete is kept whole

WHEN a set or structured statement holds an entry whose key values run out, a key field without its keyword, a token after a terminal entry, `apply-groups` bare or with two names, `apply-macro` with a fourth value, a second, different value for a nokeyword leaf of a node that is no list, or a leaf without its value, THEN the reader SHALL create, replace and apply nothing from it, SHALL keep it whole from its keyword in the record its parent holds under the reserved key `junoscfg:unplaced` (`junoscfg.display.UNPLACED_STATEMENTS`), spelled as its original tokens joined by one space, quotes included, and field validation SHALL report it `UNPLACED`; an unknown token after a complete key of an entry with children stays in-entry. A kept statement SHALL never replace, join or hide a node the reader placed: a statement placed before or after it at the same level is placed and reports nothing. Every writer SHALL write a kept statement's text unchanged at its parent's path. A leaf without its value that arrives as JSON or YAML (`null`, `[null]`, `true`, `[]`) SHALL be reported `UNPLACED` and written as it stands; an empty XML element of a leaf the tree says takes a value SHALL read as the empty value `""`, as the device writes it, and field validation SHALL check `""` like any other value, so `""` on an enum, an integer type or a pattern it fails is reported and a string leaf takes it. A record whose text is not one line of words (a line break, a tab, a stray space, an unbalanced or inner quote, an unquoted `;`, `{`, `}`, `[` or `]`, a comment), that is empty, that holds a tag naming no meta command a writer writes, or whose shape is no record SHALL be refused with `ValueError` where JSON or YAML input is read, by the set and structured writers, and by the set reader for a statement it would keep so; field validation SHALL report such a record once; none of these messages SHALL name the statement. `junoscfg.anonymize.anonymize()` SHALL refuse an IR whose record holds a statement (any other key its walk cannot place is NEW-R5, change 5), and the conversion's refusal SHALL withhold the statement's text. Path wildcards in `edityaml` SHALL pass the record by.
The same applies to `deactivate`, `activate`, `protect` and `delete`: a partial or surplus keyed-list key and an unknown path SHALL apply no attribute to the nearest valid parent or entry; the command SHALL be kept, with its original tokens, as `@<statement>` in the same record. A meta attribute addressed to an entire list SHALL survive set output at that list path. A meta attribute on a positional value the reader placed is written back and reports nothing.
Tests: `tests/unit/convert/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_partial_key_creates_no_entry`, `tests/unit/convert/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_surplus_after_a_terminal_entry_keeps_the_line_whole`, `tests/unit/convert/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_an_unknown_token_in_an_entry_with_children_is_unchanged`, `tests/unit/convert/test_set_input.py::TestApplyGroups::test_two_names_apply_no_group[set-apply-groups]`, `tests/unit/convert/test_field_validator.py::TestAnUnmodelledStatementIsReported::test_an_incomplete_statement_is_unplaced`, `tests/unit/convert/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_bare_list_keyword_creates_no_entry`, `tests/unit/convert/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_partial_attributes_match_creates_no_entry`, `tests/unit/convert/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_surplus_after_attributes_match_keeps_the_line_whole`, `tests/unit/convert/test_set_input.py::TestApplyGroups::test_one_name_inside_a_policy`, `tests/unit/convert/test_set_input.py::TestApplyGroups::test_two_names_apply_no_group`, `tests/unit/convert/test_field_validator.py::TestAnIncompleteStatementIsUnplaced::test_each_door_reports_it`, `tests/unit/convert/test_set_input.py::TestKeyFieldsGivenByKeyword::test_an_incomplete_key_is_kept_whole_and_reported`, `tests/unit/convert/test_set_input.py::TestApplyMacroTakesAtMostThreeValues::test_one_to_three_values`, `tests/unit/convert/test_set_input.py::TestApplyMacroTakesAtMostThreeValues::test_a_fourth_value_is_kept_whole_and_reported`, `tests/unit/convert/test_set_input.py::TestApplyGroups::test_a_bare_keyword_is_kept_whole_and_reported`, `tests/unit/convert/test_set_input.py::TestApplyGroups::test_a_group_after_a_bare_one_is_placed`, `tests/unit/convert/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_keyed_entry_after_a_bare_keyword_is_placed`, `tests/unit/convert/test_set_input.py::TestANonListNodeNeverReplacesAnEntry::test_a_second_value_of_a_nokeyword_leaf_is_kept_whole`, `tests/unit/convert/test_set_input.py::TestANonListNodeNeverReplacesAnEntry::test_the_same_value_again_is_one_statement`, `tests/unit/convert/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied::test_a_partial_or_surplus_key_is_kept_whole`, `tests/unit/convert/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied::test_an_unknown_path_does_not_annotate_its_valid_parent`, `tests/unit/convert/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied::test_meta_on_an_existing_unknown_prefix_reuses_its_unplaced_report`, `tests/unit/convert/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied::test_meta_on_an_existing_positional_value_is_kept_whole`, `tests/unit/convert/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied::test_a_meta_attribute_on_a_whole_list_is_written`, `tests/unit/convert/test_set_input.py::TestAKeptStatementHasARecordOfItsOwn::test_a_bare_keyword_never_meets_its_placed_node`, `tests/unit/convert/test_set_input.py::TestAKeptStatementHasARecordOfItsOwn::test_a_leaf_without_its_value_never_replaces_it`, `tests/unit/convert/test_set_input.py::TestAKeptStatementHasARecordOfItsOwn::test_a_kept_statement_keeps_its_quotes`, `tests/unit/convert/test_set_input.py::TestAKeptStatementHasARecordOfItsOwn::test_a_kept_meta_command_keeps_its_quotes`, `tests/unit/convert/test_set_input.py::TestAKeptStatementHasARecordOfItsOwn::test_a_lone_leaf_without_its_value_is_kept_and_reported`, `tests/unit/convert/test_set_input.py::TestAKeptStatementHasARecordOfItsOwn::test_a_structured_leaf_without_its_value_never_replaces_it`, `tests/unit/convert/test_field_validator.py::TestALeafWithoutItsValueIsUnplaced::test_each_door_reports_it`, `tests/unit/convert/test_field_validator.py::TestALeafWithoutItsValueIsUnplaced::test_strict_refuses_it_and_an_anonymized_run_converts_it`, `tests/unit/convert/test_field_validator.py::TestALeafWithoutItsValueIsUnplaced::test_a_leaf_with_a_value_is_clean`, `tests/unit/convert/test_field_validator.py::TestALeafWithoutItsValueIsUnplaced::test_an_empty_xml_leaf_is_the_empty_value`, `tests/unit/convert/test_set_input.py::TestAKeptStatementHasARecordOfItsOwn::test_a_kept_sibling_leaves_the_placed_node_alone`, `tests/unit/convert/test_set_input.py::TestAKeptStatementHasARecordOfItsOwn::test_each_kept_statement_is_reported`, `tests/unit/convert/test_set_input.py::TestAKeptStatementHasARecordOfItsOwn::test_the_record_name_in_the_input_forges_nothing`, `tests/unit/convert/test_set_input.py::TestAKeptStatementHasARecordOfItsOwn::test_a_statement_no_writer_can_print_is_refused`, `tests/unit/convert/test_convert_api.py::TestARecordOfKeptStatementsIsInput::test_text_no_writer_can_print_is_refused_on_read`, `tests/unit/convert/test_convert_api.py::TestARecordOfKeptStatementsIsInput::test_a_record_of_the_wrong_shape_is_refused_on_read`, `tests/unit/convert/test_convert_api.py::TestARecordOfKeptStatementsIsInput::test_a_writer_refuses_a_record_it_cannot_print`, `tests/unit/convert/test_convert_api.py::TestARecordOfKeptStatementsIsInput::test_validation_reports_a_malformed_record_once`, `tests/unit/convert/test_convert_api.py::TestARecordOfKeptStatementsIsInput::test_set_output_writes_one_line_per_statement`, `tests/unit/anonymize/test_integration.py::TestContentTheWalkCannotPlace::test_its_addresses_are_replaced`, `tests/unit/anonymize/test_integration.py::TestContentTheWalkCannotPlace::test_its_schema_path_is_named`, `tests/unit/anonymize/test_integration.py::TestEveryDoorGivesOneAnswer::test_no_message_carries_an_original_value`, `tests/unit/anonymize/test_integration.py::TestContentTheWalkCannotPlace::test_the_mapping_restores_it`, `tests/unit/convert/test_field_validator.py::TestAnEmptyValueIsCheckedLikeAnyOther::test_an_empty_value_the_type_refuses_is_reported`, `tests/unit/convert/test_field_validator.py::TestAnEmptyValueIsCheckedLikeAnyOther::test_an_empty_description_is_clean`, `tests/unit/anonymize/test_revert.py::TestRevertRestoresKeys::test_an_address_in_a_key_is_restored`, `tests/unit/edityaml/test_path_walker.py::TestAWildcardSkipsTheRecordOfKeptStatements::test_the_record_is_not_selected`, `tests/unit/edityaml/test_path_walker.py::TestAWildcardSkipsTheRecordOfKeptStatements::test_a_static_rule_over_a_wildcard_leaves_the_record_alone`, `tests/unit/audit/test_walker.py::TestARecordOfKeptStatements::test_the_placed_group_is_found_beside_a_bare_one`, `tests/unit/cli/test_cli.py::TestAKeptStatementOnTheCommandLine::test_json_output_holds_the_record_and_stderr_the_report`, `tests/unit/cli/test_cli.py::TestAKeptStatementOnTheCommandLine::test_anonymizing_warns_without_the_statement`, `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`, `tests/contract/test_format_matrix.py::TestEveryWriterKeepsTheIr::test_the_output_reads_back_as_the_ir`, `tests/contract/test_format_matrix.py::TestSetOutputIsTheDeviceLines::test_the_set_lines`, `tests/contract/test_format_matrix.py::TestASecondWriterKeepsTheIr::test_every_second_writer`, `tests/contract/test_round_trip_validates.py::TestTheConverterOutputValidates::test_a_row_that_is_not_valid_junos_is_rejected`

#### Scenario: Statements the device rejects

- **WHEN** `... as-path-neighbors as-list`, `... route-filter 198.51.100.0/24 next-policy`, `... as-list AS-LIST-A EXTRA`, `set apply-groups G1 G2`, bare `set apply-groups`, `virtual-link neighbor-id 10.255.255.3`, `virtual-link 10.255.255.4 0.0.0.2` or `apply-macro 12345 "KADJBF KU!H" balks XXXXX` is read
- **THEN** the parent's `junoscfg:unplaced` record holds it, set output reproduces it (device probe, vMX 23.2R2-S7.5, rejects each)

#### Scenario: A bare keyword beside the node it names

- **WHEN** `set apply-groups G1` and a bare `set apply-groups` are read, in either order, or a keyed entry and its list's bare keyword
- **THEN** the placed node keeps its value, the record holds the bare statement, only the bare one is reported `UNPLACED`, and set output writes both lines (OPEN-2)
- **WHEN** `apply-macro M1 a` and `apply-macro M1 a b c d`, or `apply-groups G0` and `apply-groups G1 G2`, are read
- **THEN** the placed node is unchanged and the kept sibling is the one report

#### Scenario: A leaf without its value

- **WHEN** `set system host-name router1` and a bare `set system host-name` are read in either order, `host-name;` stands in structured text, or `members` has no value
- **THEN** the leaf keeps its value, the record holds the bare statement, it is reported `UNPLACED`, strict conversion raises and anonymization refuses (NEW-C1; corpus `CORRECTLY_REJECTED`)
- **WHEN** `"host-name"` arrives as JSON or YAML holding `null`, `[null]`, `true` or `[]`
- **THEN** it is reported `UNPLACED` and written as it stands; `description ""` and a presence leaf (`no-redirects`) in any spelling report nothing
- **WHEN** `<description></description>` or `<description/>` arrives as XML
- **THEN** it is `description ""`, as the device writes it in set and `""` in JSON (`tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.{set,json,xml}.gz`), it reports nothing, and strict conversion and anonymization pass (DEV-16)
- **WHEN** `<host-name/>`, a family `<mtu/>` or `<root-login/>` arrives as XML, or `""` for them as JSON or set
- **THEN** it is reported as an invalid value (pattern, integer, enum) and strict conversion raises

#### Scenario: A record is input like any other

- **WHEN** JSON or YAML carries a record whose text holds a line break, `; } snmp {` or an unquoted `]`, or a record that is empty, a string, a list, a statement with a value or a tag naming no meta command, or a set line would keep `a;b`
- **THEN** reading refuses it with `ValueError` naming no statement, a writer handed one by hand refuses it, and validation reports it once
- **WHEN** `anonymize()` is called on an IR whose record holds a statement, read from set or JSON
- **THEN** it raises `ValueError` naming no statement; the conversion's refusal withholds the statement too

#### Scenario: A kept statement keeps its quotes

- **WHEN** `set groups G1 apply-macro 12345 "KADJBF KU!H" balks XXXXX` or a meta command on a quoted unknown statement is read
- **THEN** set, structured, JSON and YAML output write the quoted token with its quotes, and the output reads back as the same record (OPEN-3)
- **WHEN** a kept meta command names no statement the record holds whole (alone, or a prefix of a kept statement)
- **THEN** set, JSON and YAML output carry it; structured output, which can tag only a statement it writes, leaves it out with a note

#### Scenario: Meta commands never fall back to a valid prefix

- **WHEN** any of the four meta commands addresses a partial or surplus `as-path-neighbors` key, or `deactivate system bogus-thing` is read
- **THEN** the command is kept whole and reported `UNPLACED`, and no parent or keyed entry receives its attribute

#### Scenario: A whole list carries a meta attribute

- **WHEN** a meta command addresses all of `from as-path-neighbors` or all of `system login user`
- **THEN** set output writes that same meta command at the list path while its entries remain unchanged
