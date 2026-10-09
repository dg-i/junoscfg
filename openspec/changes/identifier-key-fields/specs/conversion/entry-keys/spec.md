## Purpose

Every reader and writer keys a list entry by the tree's fields, in order: four
input formats give one IR, output writes it as the device does, no token lost.

## ADDED Requirements

### Requirement: Four readers give the device's IR for a keyed entry

WHEN an entry keyed by fields other than `name` arrives as set, structured,
JSON or XML THEN `to_dict` and `convert_config` SHALL key it by the tree's
fields, one set token per field in key order, so the four IRs are equal and
match the device's `| display json`; a list keyed `name` SHALL read as before.
The identity is device-shaped IR to set and back to IR.
Tests: `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_as_list_references_give_one_ir`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_attributes_match_gives_its_three_fields`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_one_key_other_than_name`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_device_shaped_ir_round_trips_through_set`, `tests/test_device_truth.py::test_junoscfg_renders_what_the_device_renders`

#### Scenario: AS-list references

- **WHEN** `from as-path-neighbors as-list AS-LIST-A`, and the same under
  `as-path-origins` and `as-path-transits`, arrives in each of the four
  formats, at term and policy level, at the root, in a logical system, in a
  group and in a grouped logical system
- **THEN** each IR entry is `{"list-type": "as-list", "list-name": "AS-LIST-A"}`

#### Scenario: attributes-match

- **WHEN** `attributes-match ping.test-owner matches "^uptime$"` is read
- **THEN** the entry carries `from-event-attribute`, `condition` and
  `to-event-attribute-value`, and no `name`, `_v0` or `_v1`

#### Scenario: One key other than name

- **WHEN** `from source-address-filter 198.51.100.0/24 exact` is read
- **THEN** the entry is keyed `address`, not `name`

### Requirement: Writers write the key values in order on one line

WHEN set or structured output renders a keyed entry read from any of the four
formats THEN the writer SHALL write its key values unlabelled, in key order,
at the position the tree gives, as one statement.
Tests: `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_json_and_xml_write_one_set_line`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_structured_output_writes_the_keys_in_order`, `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_a_community_action_gives_one_ir_and_one_line`

#### Scenario: Device JSON and XML to set and structured

- **WHEN** the device-shaped JSON or XML AS-list entry is converted
- **THEN** set output is the one line `... from as-path-neighbors as-list
  AS-LIST-A`, never a `list-type` and a `list-name` line, and structured
  output is `as-path-neighbors as-list AS-LIST-A;`

#### Scenario: Community action, key last

- **WHEN** `then community add COMM-A` arrives as set, as XML with
  `<community-name>`, or as JSON with `community-name`
- **THEN** each IR is `{"community-name": "COMM-A", "add": [null]}` and the set
  writer renders the one line `... then community add COMM-A` from each

### Requirement: An entry with tokens left over is kept whole

WHEN a set line names a list entry and tokens remain after its key values that
the entry's declared children cannot place THEN the set reader SHALL keep every
remaining token in the IR as one unplaced statement, field validation SHALL
report it with `expected` `UNPLACED`, and the set writer SHALL reproduce the
line; the reader SHALL NOT return with a token unread.
Tests: `tests/test_set_input.py::TestAnEntryWithTokensLeftIsKeptWhole::test_a_terminal_entry_keeps_the_trailing_token`, `tests/test_set_input.py::TestAnEntryWithTokensLeftIsKeptWhole::test_an_as_list_reference_keeps_the_trailing_token`, `tests/test_field_validator.py::TestAnUnmodelledStatementIsReported::test_a_trailing_token_after_an_entry_is_unplaced`

#### Scenario: A terminal entry with one token more

- **WHEN** a list whose entries hold only their key, or the AS-list reference,
  is followed by one more token `EXTRA`
- **THEN** `EXTRA` is in the IR, field validation reports one unplaced
  statement, and set output reproduces the input line

### Requirement: apply-groups with a trailing token is kept whole

WHEN `apply-groups` or `apply-groups-except` is followed by more than one
token THEN the set reader SHALL keep the statement whole as unplaced instead
of reading the first token and dropping the rest; one token SHALL read as a
group name as before.
Tests: `tests/test_set_input.py::TestApplyGroups::test_a_trailing_token_is_kept_whole`, `tests/test_set_input.py::TestApplyGroups::test_apply_groups_except_keeps_a_trailing_token`

#### Scenario: Two tokens after apply-groups

- **WHEN** `set system apply-groups G1 EXTRA` is read
- **THEN** `G1` and `EXTRA` are in the IR, field validation reports one
  unplaced statement, and `G1` is not read as an applied group

### Requirement: Anonymization keeps a keyed reference

WHEN a configuration holding an AS-list reference inside a group is converted
through `convert_config` or CLI `convert` with `--anonymize-all`, or with
`--anonymize-as-numbers 64496` THEN the output SHALL keep `list-type` and
`list-name` unchanged, and under `--anonymize-all` SHALL anonymize the group
name.
Tests: `tests/test_anonymize/test_integration.py::TestPipelineIntegration::test_an_as_list_reference_survives_anonymize_all`, `tests/test_anonymize/test_integration.py::TestPipelineIntegration::test_as_numbers_leave_the_as_list_name`, `tests/test_cli.py::TestAnonymizeKeepsKeyedEntries::test_anonymize_all_keeps_the_as_list_reference`

#### Scenario: Structured input, every rule on

- **WHEN** the structured form is converted to set with `--anonymize-all`
- **THEN** the line ends `as-path-neighbors as-list AS-LIST-A`
