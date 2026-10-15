## Purpose

Validating a `yaml-new` document gives the verdict the JSON schema gives the same object,
so a file validates the same whether it is spelled in JSON or in yaml-new.

## ADDED Requirements

### Requirement: yaml-new validates as the JSON object it spells

WHEN a `yaml-new` document is validated through `validate_config(format="yaml-new")`,
`JunosValidator.validate_yaml_as_json` or `junoscfg convert -v -i yaml-new` THEN the system
SHALL give the verdict and errors the JSON schema gives for the loaded object, an
`_ansible_*` or `_meta_*` key included, and a YAML parse error SHALL be an invalid result
naming its line.
Tests: `tests/contract/test_every_door.py::TestAKeyedEntryTakesExactlyItsKeys::test_every_door_agrees`, `tests/contract/test_round_trip_validates.py::TestTheConverterOutputValidates::test_the_rendering_validates`, `tests/unit/validate/test_json_yaml_validator.py::TestYamlAsJsonValidation::test_a_meta_key_is_rejected_as_json_rejects_it`, `tests/unit/validate/test_json_yaml_validator.py::TestYamlAsJsonValidation::test_a_parse_error_names_its_line`

#### Scenario: A meta key

- **WHEN** `configuration: {system: {host-name: r1, _ansible_host: x}}` is validated as yaml-new
- **THEN** it is invalid, as the same object in JSON is, while `yaml` validation accepts it

#### Scenario: junoscfg's own output

- **WHEN** a valid catalogue configuration is converted to yaml-new and validated as yaml-new
- **THEN** the verdict is valid, as for its JSON rendering
