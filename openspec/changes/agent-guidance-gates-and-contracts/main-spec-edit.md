<!-- The reviewed main-spec edit for openspec/specs/conversion/entry-keys/spec.md. OpenSpec 1.13.0 refuses a delta under specs/ beside skip_specs, which the docs lane sets, so the edit travels here, is read by the fresh Reviewer in phase 6, and is applied verbatim by the Finalizer in phase 7 (C4). Traceability only: no behaviour changes. -->

## MODIFIED Requirements

### Requirement: A statement the reader cannot complete is kept whole

WHEN a set line holds an entry whose key values run out, a key field without
its keyword, a token after a terminal entry, `apply-groups` bare or with two
names, `apply-macro` with a fourth value, or a second, different value for a
nokeyword leaf of a node that is no list, THEN the reader
SHALL create, replace and apply nothing from it, SHALL keep it whole from its
keyword at its parent, and field validation SHALL report it `UNPLACED`; an
unknown token after a complete key of an entry with children stays in-entry.
WHEN a `deactivate`, `activate`, `protect` or `delete` line names such a path,
or a path the configuration does not hold, THEN the reader SHALL follow the
same rule: it SHALL attach the attribute to no shorter valid path, SHALL keep
the malformed path whole at its parent carrying the attribute, set output
SHALL reproduce the line, and field validation SHALL report it `UNPLACED` once,
sharing the report of a `set` line already kept whole at that path; an
attribute on a whole list, or on a positional value the reader placed, is
written back and reports nothing.
Tests: `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_partial_key_creates_no_entry`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_surplus_after_a_terminal_entry_keeps_the_line_whole`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_an_unknown_token_in_an_entry_with_children_is_unchanged`, `tests/test_set_input.py::TestApplyGroups::test_a_second_group_token_keeps_the_line_whole`, `tests/test_field_validator.py::TestAnUnmodelledStatementIsReported::test_an_incomplete_statement_is_unplaced`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_bare_list_keyword_creates_no_entry`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_partial_attributes_match_creates_no_entry`, `tests/test_set_input.py::TestTokensTheReaderCannotPlaceAreKept::test_a_surplus_after_attributes_match_keeps_the_line_whole`, `tests/test_set_input.py::TestApplyGroupsAndKeyedEntries::test_one_name_inside_a_policy`, `tests/test_set_input.py::TestApplyGroupsAndKeyedEntries::test_two_names_apply_no_group`, `tests/test_field_validator.py::TestAnIncompleteStatementIsUnplaced::test_each_door_reports_it`, `tests/test_set_input.py::TestKeyFieldsGivenByKeyword::test_an_incomplete_key_is_kept_whole_and_reported`, `tests/test_set_input.py::TestApplyMacroTakesAtMostThreeValues::test_one_to_three_values`, `tests/test_set_input.py::TestApplyMacroTakesAtMostThreeValues::test_a_fourth_value_is_kept_whole_and_reported`, `tests/test_set_input.py::TestABareApplyGroups::test_it_is_reported`, `tests/test_set_input.py::TestABareApplyGroups::test_a_group_after_a_bare_one_is_kept_too`, `tests/test_set_input.py::TestABareApplyGroups::test_a_keyed_entry_after_a_bare_keyword_is_kept_too`, `tests/test_set_input.py::TestANonListNodeNeverReplacesAnEntry::test_a_second_value_of_a_nokeyword_leaf_is_kept_whole`, `tests/test_set_input.py::TestANonListNodeNeverReplacesAnEntry::test_the_same_value_again_is_one_statement`, `tests/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied::test_a_partial_or_surplus_key_is_kept_whole`, `tests/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied::test_an_unknown_path_does_not_annotate_its_valid_parent`, `tests/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied::test_meta_on_an_existing_unknown_prefix_reuses_its_unplaced_report`, `tests/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied::test_meta_on_an_existing_positional_value_is_kept_whole`, `tests/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied::test_a_meta_attribute_on_a_whole_list_is_written`

#### Scenario: Statements the device rejects

- **WHEN** `... as-path-neighbors as-list`, `... route-filter 198.51.100.0/24
  next-policy`, `... as-list AS-LIST-A EXTRA`, `set apply-groups G1 G2`, bare
  `set apply-groups`, `virtual-link neighbor-id 10.255.255.3`, `virtual-link
  10.255.255.4 0.0.0.2` or `apply-macro 12345 "KADJBF KU!H" balks XXXXX` is read
- **THEN** the parent holds it unplaced, set output reproduces it (device probe,
  vMX 23.2R2-S7.5, rejects each)

#### Scenario: Metadata verbs on a malformed path

- **WHEN** `deactivate`, `activate`, `protect` or `delete` names `... from
  as-path-neighbors as-list` (a key value missing), `... as-list SAMPLE-AS-LIST
  extra` (a surplus token) or `system bogus-thing` (unmodelled), after the
  matching `set` lines
- **THEN** neither the parent nor the complete entry gains an attribute, the
  malformed path holds it whole, set output reproduces the line, and validation
  reports one `UNPLACED` per kept-whole path, none extra for a path a `set`
  line already reported

#### Scenario: Metadata on a whole list or a placed value

- **WHEN** `deactivate ... from as-path-neighbors`, `protect system login user`,
  or `deactivate protocols isis SAMPLE-UNKNOWN` after `set protocols isis
  SAMPLE-UNKNOWN` is read
- **THEN** set output writes the line back, and the placed value reports nothing
