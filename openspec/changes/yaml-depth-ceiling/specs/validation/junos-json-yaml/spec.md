## MODIFIED Requirements

### Requirement: yaml-new validates as the JSON object it spells

WHEN a `yaml-new` document is validated through `validate_config(format="yaml-new")`,
`JunosValidator.validate_yaml_as_json` or `junoscfg convert -v -i yaml-new` THEN the system
SHALL give the verdict and errors the JSON schema gives for the loaded object, written out
where it shares a mapping or list through an alias, an `_ansible_*` or `_meta_*` key
included; a YAML parse error SHALL be an invalid result naming its line, and a value JSON
cannot hold, a cycle, or a value nested deeper than 64 levels (conversion/junos-json-yaml)
an invalid result naming its kind and path, never an exception.
Tests: `tests/contract/test_every_door.py::TestAKeyedEntryTakesExactlyItsKeys::test_every_door_agrees`, `tests/contract/test_round_trip_validates.py::TestTheConverterOutputValidates::test_the_rendering_validates`, `tests/unit/validate/test_json_yaml_validator.py::TestYamlAsJsonValidation::test_a_meta_key_is_rejected_as_json_rejects_it`, `tests/unit/validate/test_json_yaml_validator.py::TestYamlAsJsonValidation::test_a_parse_error_names_its_line`, `tests/unit/convert/test_convert_api.py::TestValidateConfig::test_junos_yaml_is_judged_by_the_json_schema`, `tests/unit/validate/test_validator.py::TestJunosValidator::test_validate_yaml_as_json_uses_the_json_schema`, `tests/unit/validate/test_json_yaml_validator.py::TestYamlAsJsonValidation::test_a_value_json_cannot_hold_is_invalid`, `tests/unit/validate/test_json_yaml_validator.py::TestYamlAsJsonValidation::test_a_shared_block_validates_written_out`, `tests/unit/validate/test_json_yaml_validator.py::TestYamlAsJsonValidation::test_a_value_past_64_levels_is_invalid`, `tests/unit/cli/test_cli_validate.py::TestCliValidation::test_a_yaml_new_value_json_cannot_hold_exits_one`, `tests/unit/cli/test_cli_validate.py::TestCliValidation::test_a_yaml_new_cycle_exits_one`, `tests/unit/cli/test_cli_validate.py::TestCliValidation::test_a_yaml_new_value_past_64_levels_exits_one`, `tests/unit/convert/test_convert_api.py::TestValidateConfig::test_a_yaml_new_shared_block_and_deep_document`

#### Scenario: A meta key

- **WHEN** `configuration: {system: {host-name: r1, _ansible_host: x}}` is validated as yaml-new
- **THEN** it is invalid, as the same object in JSON is, while `yaml` validation accepts it

#### Scenario: junoscfg's own output

- **WHEN** a valid catalogue configuration is converted to yaml-new and validated as yaml-new
- **THEN** the verdict is valid, as for its JSON rendering

#### Scenario: A key PyYAML reads as a boolean

- **WHEN** `configuration: {system: {on: x}}` is validated as yaml-new
- **THEN** the result is invalid with "YAML bool key has no JSON spelling" at `configuration.system`

#### Scenario: A shared block

- **WHEN** a yaml-new document whose two syslog hosts share `contents` through an alias is validated
- **THEN** the verdict is the one the JSON schema gives the document written out

#### Scenario: A document 65 levels deep

- **WHEN** a yaml-new document holding a value 65 path steps below its root is validated
- **THEN** the result is invalid with "YAML value is nested deeper than 64 levels" at that value's path
