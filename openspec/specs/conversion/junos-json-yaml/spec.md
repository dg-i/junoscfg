# conversion/junos-json-yaml Specification

## Purpose

The format `yaml-new` is the Junos JSON object written and read as YAML: the object the
JSON writer builds and the JSON reader takes, with only the text syntax changed. It sits
beside the IR-dump format `yaml`, which it is planned to replace under that name.

## Requirements

### Requirement: yaml-new output is the Junos JSON object

WHEN any reader's IR is written as `yaml-new`, wrapped or as a relative selection, THEN the
system SHALL write YAML whose loaded value equals the parsed JSON output for the same IR and
options, mapping keys in the same order, holds no YAML anchor or alias, and escapes the
line breaks YAML alone reads as breaks (NEL, LINE and PARAGRAPH SEPARATOR); WHEN that IR
holds a value JSON cannot hold, a cycle, or a shared object written out past the bound THEN
the writer SHALL raise `ValueError` naming its kind and path, never its value, before it
builds the object.
Tests: `tests/contract/test_format_matrix.py::TestJunosYamlIsTheJsonObject::test_the_output_is_the_json_object`, `tests/corpus/test_device_renderings.py::TestJunosYamlIsTheDevicesJson::test_every_rendering_writes_the_json_object`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_shared_object_is_written_out_each_time`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_any_json_object_survives_junos_yaml`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_the_device_spellings_are_written_as_json_writes_them`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_value_json_cannot_hold_is_refused_on_write`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_cycle_or_an_alias_bomb_is_refused_on_write`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_shared_object_is_spelled_in_each_of_its_contexts`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_yaml_only_line_break_reads_back_as_written`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_selection_is_the_bare_subtree`

#### Scenario: An empty container the device wrote as {}

- **WHEN** the QFX5120 25.2R2-S1.5 capture's `system services netconf ssh {}` is written as yaml-new
- **THEN** the output holds `ssh: [null]` spelled as a YAML sequence, as JSON output holds `"ssh": [null]`

#### Scenario: Groups and a one-element scalar leaf

- **WHEN** an IR with `groups: {group: [...]}` and `class: [super-user]` is written as yaml-new
- **THEN** `groups` is the list of entries and `class` the scalar, as in JSON output

### Requirement: yaml-new input reads as the JSON object it spells

WHEN a YAML document is read as `yaml-new` THEN the system SHALL load it with PyYAML's
`safe_load` (YAML 1.1 implicit types, as `yaml` loads it) and give the IR the JSON reader
gives for the loaded object: `_ansible_*` and `_meta_*` keys are kept, a scalar leaf-list
stays scalar, no schema artifact is loaded, and annotation spellings and record refusals
are handled as for every reader.
Tests: `tests/contract/test_format_matrix.py::TestJunosYamlIsTheJsonObject::test_the_yaml_spelling_of_json_reads_as_json`, `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`, `tests/corpus/test_device_renderings.py::TestJunosYamlIsTheDevicesJson::test_the_devices_json_in_yaml_reads_as_the_json`, `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_meta_keys_are_kept_as_json_keeps_them`, `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_a_scalar_leaf_list_stays_scalar_without_loading_schema`, `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_unquoted_words_are_read_as_pyyaml_reads_them`

#### Scenario: An Ansible meta key

- **WHEN** `configuration: {system: {host-name: r1, _meta_x: y}}` is read as yaml-new and as yaml
- **THEN** the yaml-new IR keeps `_meta_x`, as JSON input does, and the yaml IR drops it

#### Scenario: An unquoted on

- **WHEN** `location: on` is read as yaml-new
- **THEN** the value is the boolean `true`, as PyYAML reads it; `location: 'on'` is the string

### Requirement: A YAML value JSON cannot hold is refused

WHEN anywhere in a `yaml-new` document, wrappers and siblings of `configuration` included,
a value is not a mapping with string keys, a list, a string, a number, a boolean or null
(a timestamp, a key of another type, binary data, a set, an ordered map's pairs) THEN the
system SHALL raise `ValueError` naming the value's kind and path, never the value or key;
an anonymizing conversion withholds the path as it does for every refusal to read. A
mapping or list reached through an alias is not such a value: it is read written out, and
only a cycle or an expansion past the bound is refused (requirement "A block shared through
an alias is written out, a cycle and an alias bomb are refused").
Tests: `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_a_value_json_cannot_hold_is_refused`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_the_first_value_json_cannot_hold`, `tests/unit/cli/test_audit_command.py::TestInputFormats::test_a_value_json_cannot_hold_is_refused`, `tests/contract/test_every_message.py::TestAnAnonymizedRunQuotesNothingOfTheConfiguration::test_no_message_holds_a_word_of_it`

#### Scenario: An unquoted date

- **WHEN** `host-name: 2026-10-15` is read as yaml-new
- **THEN** `ValueError` says a YAML date at `configuration.system.host-name` has no JSON spelling

### Requirement: Each format name selects its implementation through one table

WHEN a format name reaches `convert_config`, `validate_config`, `junoscfg.convert.to_dict`,
`from_dict`, or the CLI's convert and audit commands THEN the system SHALL select the
implementation `junoscfg.convert.FORMAT_IMPLEMENTATIONS` names for it; the values of
`junoscfg.Format` SHALL be exactly the table's names; `yaml` SHALL keep its reader and
writer unchanged, and YAML that the CLI detects SHALL still read as `yaml`.
Tests: `tests/unit/convert/test_convert_api.py::TestFormatEnum::test_every_format_has_one_implementation`, `tests/unit/convert/test_convert_api.py::TestFormatEnum::test_an_unknown_name_is_refused`, `tests/unit/cli/test_cli.py::TestConvertReadsAndWrites::test_every_import_and_export_format_reaches_the_library`, `tests/unit/cli/test_audit_command.py::TestInputFormats::test_junos_yaml_is_audited_as_json`, `tests/unit/convert/test_convert_api.py::TestFormatEnum::test_the_rename_is_a_change_to_the_table`, `tests/unit/convert/test_convert_api.py::TestTheYamlWriterDumpsTheIr::test_the_output_is_the_ir_as_read`

#### Scenario: Every door offers yaml-new

- **WHEN** `-i yaml-new` or `-e yaml-new` is given to `junoscfg convert`, or `-i yaml-new` to `junoscfg audit`
- **THEN** the command reads or writes yaml-new, as `convert_config` does for `Format.YAML_NEW`

#### Scenario: The rename rehearsed

- **WHEN** the table's `yaml` and `yaml-new` rows are swapped
- **THEN** every door reads, writes and validates `yaml` as the Junos JSON object and `yaml-new` as the IR dump

### Requirement: An existing YAML file migrates to yaml-new

WHEN a configuration read as `yaml` is written as `yaml-new` THEN reading the result as
`yaml-new` SHALL give the IR the `yaml` source gave, with the yaml reader's metadata
cleanup and leaf-list promotion applied once, and `junoscfg convert -i yaml -e yaml-new`
SHALL write the same text; a value the `yaml` file holds that JSON cannot hold (an unquoted
date) SHALL stop the migration with its kind and path, CLI exit 2.
Tests: `tests/contract/test_format_matrix.py::TestIrYamlMigratesToJunosYaml::test_the_converted_file_reads_as_the_yaml_did`, `tests/unit/cli/test_cli.py::TestConvertReadsAndWrites::test_an_ir_yaml_file_migrates_to_junos_yaml`, `tests/unit/cli/test_cli.py::TestConvertReadsAndWrites::test_a_value_json_cannot_hold_stops_the_migration`

#### Scenario: A legacy file with meta keys

- **WHEN** a yaml file holding `_ansible_host` is converted with `-i yaml -e yaml-new`
- **THEN** the output holds no `_ansible_host` and reads as yaml-new to the IR the yaml file read as

### Requirement: A block shared through an alias is written out, a cycle and an alias bomb are refused

WHEN a `yaml-new` document, or an IR handed to the `yaml-new` writer, reaches a mapping or
list more than once (a YAML alias, a merge key's container value, or a caller sharing one
object) THEN the system SHALL treat each place as its own copy, as JSON spells it: the
reader gives the IR of the document written out, holding no mapping or list twice, and the
writer writes each copy. WHEN such a mapping or list is reached inside itself (a cycle) THEN
the system SHALL refuse it as kind `cycle` at the path where it is reached again. WHEN the
document written out would hold more than twice the values the parsed document holds
(mappings, lists and scalars, each scalar per place; a mapping or list reached again counted
once), or would nest deeper than the parsed document's deepest value (an alias counted as a
leaf, as in the text) THEN the system SHALL refuse the outermost alias being written out
when that bound is passed, as kind `alias` at its path, so that the check stops within twice
the parsed values and the parsed depth and no later stage expands more. The bounds count
written-out values, not aliases: every document that reaches each value at most twice and
nests no deeper than written SHALL pass; a document without aliases never reaches them.
Each refusal names its kind, path and reason (`has no JSON spelling`, `expands the document
past twice its size`, `nests the document deeper than it is written`) and never the
offending value or key: reader and writer raise `ValueError`, validation gives an invalid
result. Both bounds are interim (SC-2, SC-A, pending the owner). Scalar aliases and merge
keys are expanded by PyYAML while loading, before the check, and are not bounded here
(SC-B).
Tests: `tests/unit/input/test_input.py::TestFindNonJsonValue::test_a_shared_block_is_walked_where_it_is_reached`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_a_value_in_a_shared_block_is_found_where_first_reached`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_a_cycle_is_refused_where_it_is_reached_again`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_an_alias_bomb_is_refused_in_linear_time`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_a_block_reached_three_times_through_nested_anchors_is_refused`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_a_block_aliased_deeper_than_anything_written_is_refused`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_the_bound_is_twice_the_parsed_document`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_the_refusal_names_an_alias_when_the_copies_end_early`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_one_value_past_twice_is_refused`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_scalars_count_toward_the_bound`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_an_alias_free_document_of_repeated_scalars_passes`, `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_a_shared_block_is_read_written_out`, `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_a_shared_block_converts_as_written_out`, `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_the_ir_of_a_shared_block_shares_nothing`, `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_a_cycle_or_an_alias_bomb_is_refused`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_cycle_or_an_alias_bomb_is_refused_on_write`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_shared_object_is_written_out_each_time`, `tests/unit/cli/test_cli.py::TestConvertReadsAndWrites::test_a_yaml_new_alias_bomb_exits_two`, `tests/unit/cli/test_cli.py::TestConvertReadsAndWrites::test_a_yaml_new_shared_block_converts_as_written_out`, `tests/unit/cli/test_audit_command.py::TestInputFormats::test_a_yaml_new_shared_block_and_alias_bomb`, `tests/contract/test_every_message.py::TestAnAnonymizedRunQuotesNothingOfTheConfiguration::test_no_message_holds_a_word_of_it`

#### Scenario: Two syslog hosts sharing one contents block

- **WHEN** host `198.51.100.9` anchors `contents: &c [...]` and host `198.51.100.10` gives `contents: *c`, read as yaml-new
- **THEN** the IR holds two equal, separate `contents` lists, as the same document written out reads

#### Scenario: A self-referencing alias

- **WHEN** `configuration: &a {system: {x: *a}}` is read as yaml-new
- **THEN** `ValueError` says a YAML cycle at `configuration.system.x` has no JSON spelling

#### Scenario: Billion laughs

- **WHEN** nine levels of ten aliases each (10^9 values written out) are read as yaml-new
- **THEN** `ValueError` says a YAML alias at `lol1.2` expands the document past twice its size, within milliseconds

#### Scenario: An alias chain deeper than the recursion limit

- **WHEN** four flow lists 300 deep, each innermost an alias of the one before, are read as yaml-new
- **THEN** `ValueError` says the alias nests the document deeper than it is written, never a `RecursionError`
