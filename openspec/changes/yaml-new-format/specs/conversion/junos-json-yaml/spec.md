## Purpose

The format `yaml-new` is the Junos JSON object written and read as YAML: the object the
JSON writer builds and the JSON reader takes, with only the text syntax changed. It sits
beside the IR-dump format `yaml`, which it is planned to replace under that name.

## ADDED Requirements

### Requirement: yaml-new output is the Junos JSON object

WHEN any reader's IR is written as `yaml-new`, wrapped or as a relative selection, THEN the
system SHALL write YAML whose loaded value equals the parsed JSON output for the same IR and
options, mapping keys in the same order, and that holds no YAML anchor or alias.
Tests: `tests/contract/test_format_matrix.py::TestYamlNewSpellsTheJsonObject::test_the_output_is_the_json_object`, `tests/corpus/test_device_renderings.py::TestYamlNewIsTheDevicesJsonInYaml::test_every_rendering_writes_the_json_object`, `tests/unit/convert/test_convert_api.py::TestYamlNewWriter::test_a_shared_object_is_written_out_each_time`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_selection_is_the_bare_subtree`

#### Scenario: An empty container the device wrote as {}

- **WHEN** the QFX5120 25.2R2-S1.5 capture's `system services netconf ssh {}` is written as yaml-new
- **THEN** the output holds `ssh: [null]` spelled as a YAML sequence, as JSON output holds `"ssh": [null]`

#### Scenario: Groups and a one-element scalar leaf

- **WHEN** an IR with `groups: {group: [...]}` and `class: [super-user]` is written as yaml-new
- **THEN** `groups` is the list of entries and `class` the scalar, as in JSON output

### Requirement: yaml-new input reads as the JSON object it spells

WHEN a YAML document is read as `yaml-new` THEN the system SHALL give the IR the JSON reader
gives for the same object: `_ansible_*` and `_meta_*` keys are kept, a scalar leaf-list stays
scalar, no schema artifact is loaded, and annotation spellings and record refusals are
handled as for every reader.
Tests: `tests/contract/test_format_matrix.py::TestYamlNewSpellsTheJsonObject::test_the_yaml_spelling_of_json_reads_as_json`, `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`, `tests/corpus/test_device_renderings.py::TestYamlNewIsTheDevicesJsonInYaml::test_the_devices_json_in_yaml_reads_as_the_json`, `tests/unit/convert/test_convert_api.py::TestYamlNewReader::test_meta_keys_are_kept_as_json_keeps_them`, `tests/unit/convert/test_convert_api.py::TestYamlNewReader::test_a_scalar_leaf_list_stays_scalar_without_loading_schema`

#### Scenario: An Ansible meta key

- **WHEN** `configuration: {system: {host-name: r1, _meta_x: y}}` is read as yaml-new and as yaml
- **THEN** the yaml-new IR keeps `_meta_x`, as JSON input does, and the yaml IR drops it

### Requirement: A YAML value JSON cannot hold is refused

WHEN `yaml-new` input holds a value no JSON document can hold (a timestamp, a mapping key
that is not a string, binary data, a set) THEN the system SHALL raise `ValueError` naming
the value's kind and path, not its value; an anonymizing conversion withholds the path as
it does for every refusal to read.
Tests: `tests/unit/convert/test_convert_api.py::TestYamlNewReader::test_a_value_json_cannot_hold_is_refused`, `tests/contract/test_every_message.py::TestAnAnonymizedRunQuotesNothingOfTheConfiguration::test_no_message_holds_a_word_of_it`

#### Scenario: An unquoted date

- **WHEN** `host-name: 2026-10-15` is read as yaml-new
- **THEN** `ValueError` says a timestamp at `system.host-name` has no JSON spelling

### Requirement: Each format name selects its implementation through one table

WHEN a format name reaches `convert_config`, `validate_config`, `junoscfg.convert.to_dict`,
`from_dict`, or the CLI's convert and audit commands THEN the system SHALL select the
implementation `junoscfg.convert.FORMAT_IMPLEMENTATIONS` names for it; the values of
`junoscfg.Format` SHALL be exactly the table's names; `yaml` SHALL keep its reader and
writer unchanged, and YAML that the CLI detects SHALL still read as `yaml`.
Tests: `tests/unit/convert/test_convert_api.py::TestFormatEnum::test_every_format_has_one_implementation`, `tests/unit/convert/test_convert_api.py::TestFormatEnum::test_an_unknown_name_is_refused`, `tests/unit/cli/test_cli.py::TestConvertReadsAndWrites::test_every_import_and_export_format_reaches_the_library`, `tests/unit/cli/test_audit_command.py::TestAuditReadsYamlNew::test_yaml_new_input_is_audited_as_json`

#### Scenario: Every door offers yaml-new

- **WHEN** `-i yaml-new` or `-e yaml-new` is given to `junoscfg convert`, or `-i yaml-new` to `junoscfg audit`
- **THEN** the command reads or writes yaml-new, as `convert_config` does for `Format.YAML_NEW`

### Requirement: An existing YAML file migrates to yaml-new

WHEN a configuration read as `yaml` is written as `yaml-new` THEN reading the result as
`yaml-new` SHALL give the IR the `yaml` source gave, with the yaml reader's metadata
cleanup and leaf-list promotion applied once, and `junoscfg convert -i yaml -e yaml-new`
SHALL write the same text.
Tests: `tests/contract/test_format_matrix.py::TestYamlMigratesToYamlNew::test_the_converted_file_reads_as_the_yaml_did`, `tests/unit/cli/test_cli.py::TestConvertReadsAndWrites::test_a_yaml_file_converts_to_yaml_new`

#### Scenario: A legacy file with meta keys

- **WHEN** a yaml file holding `_ansible_host` is converted with `-i yaml -e yaml-new`
- **THEN** the output holds no `_ansible_host` and reads as yaml-new to the IR the yaml file read as
