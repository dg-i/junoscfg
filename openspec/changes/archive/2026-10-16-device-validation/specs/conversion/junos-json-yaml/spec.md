## MODIFIED Requirements

### Requirement: yaml-new input reads as the JSON object it spells

WHEN a YAML document is read as `yaml-new` THEN the system SHALL load it with PyYAML's
`safe_load` (YAML 1.1 implicit types, as `yaml` loads it) and give the IR the JSON reader
gives for the loaded object: `_ansible_*` and `_meta_*` keys are kept, a scalar leaf-list
stays scalar, and annotation spellings and record refusals are handled as for every
reader. Like every reader it keys the IR by the structure tree (an element name a fix
renamed is read as its CLI keyword: spec schema-pipeline/conversion-hints), so it loads
the structure tree as the JSON reader does.
Tests: `tests/contract/test_format_matrix.py::TestJunosYamlIsTheJsonObject::test_the_yaml_spelling_of_json_reads_as_json`, `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`, `tests/corpus/test_device_renderings.py::TestJunosYamlIsTheDevicesJson::test_the_devices_json_in_yaml_reads_as_the_json`, `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_meta_keys_are_kept_as_json_keeps_them`, `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_a_scalar_leaf_list_stays_scalar`, `tests/unit/convert/test_convert_api.py::TestJunosYamlReader::test_unquoted_words_are_read_as_pyyaml_reads_them`

#### Scenario: An Ansible meta key

- **WHEN** `configuration: {system: {host-name: r1, _meta_x: y}}` is read as yaml-new and as yaml
- **THEN** the yaml-new IR keeps `_meta_x`, as JSON input does, and the yaml IR drops it

#### Scenario: An unquoted on

- **WHEN** `location: on` is read as yaml-new
- **THEN** the value is the boolean `true`, as PyYAML reads it; `location: 'on'` is the string
