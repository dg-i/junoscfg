## REMOVED Requirements

### Requirement: A block shared through an alias is written out, a cycle and an alias bomb are refused

**Reason**: Owner rulings 2026-10-15 (SC-2, SC-A): alias bombs are YAML's and PyYAML's, not junoscfg's; one ceiling.
**Migration**: None for valid documents; a caller handling untrusted YAML bounds it before calling junoscfg.

## ADDED Requirements

### Requirement: A block shared through an alias is written out, a cycle and nesting past 64 levels are refused

WHEN a `yaml-new` document, or an IR handed to the `yaml-new` writer, reaches a mapping or
list more than once (an alias, a merge key's container value, a caller sharing one object)
THEN the system SHALL read and write each place as its own copy, as JSON spells it, however
often it is reused; the reader's IR holds no mapping or list twice. WHEN one is reached
inside itself THEN the system SHALL refuse kind `cycle` at the path where it is reached
again. WHEN a value sits more than 64 path steps below the root of the document written out
(the loaded document; for the writer, the IR and the object it writes, wrapped or bare) THEN
the system SHALL refuse the first such value as kind `value` at its path (a key that is not
a string named by its kind), before a later stage walks it. The `yaml` reader
SHALL refuse both the same way before its meta-key cleanup, in what that cleanup walks: every
place but the `_ansible_*` and `_meta_*` keys it drops unwalked. Refusals name kind, path and
reason, never a value or key: `ValueError` from readers and writer (an anonymizing
conversion withholds it), an invalid result from validation. junoscfg assumes its YAML input
is not hostile: alias bombs, scalar aliases and merge keys are expanded, and text PyYAML
cannot load (past about 490 levels) fails in PyYAML as at base; bound untrusted YAML first.
Tests: `tests/unit/input/test_input.py::TestFindNonJsonValue::test_a_shared_block_is_walked_where_it_is_reached`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_a_value_in_a_shared_block_is_found_where_first_reached`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_a_cycle_is_refused_where_it_is_reached_again`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_a_block_reused_any_number_of_times_is_walked_written_out`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_a_document_64_levels_deep_passes`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_a_value_past_64_levels_is_refused_at_its_path`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_without_scalars_only_a_cycle_or_depth_is_refused`, `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_a_shared_block_is_read_written_out`, `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_a_shared_block_converts_as_written_out`, `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_the_ir_of_a_shared_block_shares_nothing`, `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_a_block_the_old_bounds_refused_is_read_written_out`, `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_a_cycle_or_a_value_past_64_levels_is_refused`, `tests/unit/convert/test_convert_api.py::TestIrYamlReader::test_a_cycle_or_a_value_past_64_levels_is_refused`, `tests/unit/convert/test_convert_api.py::TestIrYamlReader::test_a_shared_block_and_a_date_read_as_before`, `tests/unit/convert/test_convert_api.py::TestIrYamlReader::test_a_meta_key_subtree_is_not_walked`, `tests/unit/convert/test_convert_api.py::TestIrYamlReader::test_a_deep_sibling_of_the_configuration_is_refused`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_a_cycle_closing_at_step_65_is_a_cycle`, `tests/unit/cli/test_cli.py::TestConvertReadsAndWrites::test_detected_yaml_refuses_a_cycle`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_cycle_or_a_value_past_64_levels_is_refused_on_write`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_an_ir_64_levels_deep_and_any_reuse_is_written`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_json_input_past_64_levels_is_refused_as_yaml_new`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_flag_at_step_64_is_refused_where_its_null_would_sit`, `tests/unit/convert/test_convert_api.py::TestIrYamlReader::test_a_key_that_is_not_a_string_is_named_by_its_kind`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_shared_object_is_written_out_each_time`, `tests/unit/cli/test_cli.py::TestConvertReadsAndWrites::test_a_cycle_or_a_value_past_64_levels_exits_two`, `tests/unit/cli/test_cli.py::TestConvertReadsAndWrites::test_a_yaml_new_shared_block_converts_as_written_out`, `tests/unit/cli/test_audit_command.py::TestInputFormats::test_a_shared_block_cycle_and_deep_document`, `tests/contract/test_every_message.py::TestAnAnonymizedRunQuotesNothingOfTheConfiguration::test_no_message_holds_a_word_of_it`

#### Scenario: A block anchored beside the configuration

- **WHEN** `x-contents: &c [...]` sits beside `configuration` and a syslog host gives `contents: *c`, read as yaml-new
- **THEN** the IR holds the block at the host, as the document written out reads

#### Scenario: A self-referencing alias

- **WHEN** `configuration: &a {system: {x: *a}}` is read as yaml-new or as yaml
- **THEN** `ValueError` says a YAML cycle at `configuration.system.x` has no JSON spelling

#### Scenario: A document 65 levels deep

- **WHEN** `x` under `configuration.system` holds 62 nested lists around one value, read as yaml-new or as yaml
- **THEN** `ValueError` says a YAML value at `configuration.system.x` and 62 `.0` steps is nested deeper than 64 levels; with 61 lists it reads

## MODIFIED Requirements

### Requirement: yaml-new output is the Junos JSON object

WHEN any reader's IR is written as `yaml-new`, wrapped or as a relative selection, THEN the
system SHALL write YAML whose loaded value equals the parsed JSON output for the same IR and
options, mapping keys in the same order, holds no YAML anchor or alias, and escapes the
line breaks YAML alone reads as breaks (NEL, LINE and PARAGRAPH SEPARATOR); WHEN that IR
holds a value JSON cannot hold, a cycle, or a value nested deeper than 64 levels THEN the
writer SHALL raise `ValueError` naming its kind and path, never its value, before it
builds the object.
Tests: `tests/contract/test_format_matrix.py::TestJunosYamlIsTheJsonObject::test_the_output_is_the_json_object`, `tests/corpus/test_device_renderings.py::TestJunosYamlIsTheDevicesJson::test_every_rendering_writes_the_json_object`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_shared_object_is_written_out_each_time`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_any_json_object_survives_junos_yaml`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_the_device_spellings_are_written_as_json_writes_them`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_value_json_cannot_hold_is_refused_on_write`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_cycle_or_a_value_past_64_levels_is_refused_on_write`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_an_ir_64_levels_deep_and_any_reuse_is_written`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_json_input_past_64_levels_is_refused_as_yaml_new`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_shared_object_is_spelled_in_each_of_its_contexts`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_yaml_only_line_break_reads_back_as_written`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_selection_is_the_bare_subtree`

#### Scenario: An empty container the device wrote as {}

- **WHEN** the QFX5120 25.2R2-S1.5 capture's `system services netconf ssh {}` is written as yaml-new
- **THEN** the output holds `ssh: [null]` spelled as a YAML sequence, as JSON output holds `"ssh": [null]`

#### Scenario: Groups and a one-element scalar leaf

- **WHEN** an IR with `groups: {group: [...]}` and `class: [super-user]` is written as yaml-new
- **THEN** `groups` is the list of entries and `class` the scalar, as in JSON output

### Requirement: A YAML value JSON cannot hold is refused

WHEN anywhere in a `yaml-new` document, wrappers and siblings of `configuration` included,
a value is not a mapping with string keys, a list, a string, a number, a boolean or null
(a timestamp, a key of another type, binary data, a set, an ordered map's pairs) THEN the
system SHALL raise `ValueError` naming the value's kind and path, never the value or key;
an anonymizing conversion withholds the path as it does for every refusal to read. A
mapping or list reached through an alias is not such a value: it is read written out, and
only a cycle or a value nested deeper than 64 levels is refused.
Tests: `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_a_value_json_cannot_hold_is_refused`, `tests/unit/input/test_input.py::TestFindNonJsonValue::test_the_first_value_json_cannot_hold`, `tests/unit/cli/test_audit_command.py::TestInputFormats::test_a_value_json_cannot_hold_is_refused`, `tests/contract/test_every_message.py::TestAnAnonymizedRunQuotesNothingOfTheConfiguration::test_no_message_holds_a_word_of_it`

#### Scenario: An unquoted date

- **WHEN** `host-name: 2026-10-15` is read as yaml-new
- **THEN** `ValueError` says a YAML date at `configuration.system.host-name` has no JSON spelling

### Requirement: Each format name selects its implementation through one table

WHEN a format name reaches `convert_config`, `validate_config`, `junoscfg.convert.to_dict`,
`from_dict`, or the CLI's convert and audit commands THEN the system SHALL select the
implementation `junoscfg.convert.FORMAT_IMPLEMENTATIONS` names for it; the values of
`junoscfg.Format` SHALL be exactly the table's names; `yaml` SHALL keep its reader (but for
its cycle and depth refusal) and writer, and YAML the CLI detects SHALL still read as `yaml`.
Tests: `tests/unit/convert/test_convert_api.py::TestFormatEnum::test_every_format_has_one_implementation`, `tests/unit/convert/test_convert_api.py::TestFormatEnum::test_an_unknown_name_is_refused`, `tests/unit/cli/test_cli.py::TestConvertReadsAndWrites::test_every_import_and_export_format_reaches_the_library`, `tests/unit/cli/test_audit_command.py::TestInputFormats::test_junos_yaml_is_audited_as_json`, `tests/unit/convert/test_convert_api.py::TestFormatEnum::test_the_rename_is_a_change_to_the_table`, `tests/unit/convert/test_convert_api.py::TestTheYamlWriterDumpsTheIr::test_the_output_is_the_ir_as_read`, `tests/unit/convert/test_convert_api.py::TestIrYamlReader::test_a_shared_block_and_a_date_read_as_before`

#### Scenario: Every door offers yaml-new

- **WHEN** `-i yaml-new` or `-e yaml-new` is given to `junoscfg convert`, or `-i yaml-new` to `junoscfg audit`
- **THEN** the command reads or writes yaml-new, as `convert_config` does for `Format.YAML_NEW`

#### Scenario: The rename rehearsed

- **WHEN** the table's `yaml` and `yaml-new` rows are swapped
- **THEN** every door reads, writes and validates `yaml` as the Junos JSON object and `yaml-new` as the IR dump
