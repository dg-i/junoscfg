## ADDED Requirements

### Requirement: yaml validation refuses what the yaml reader refuses

WHEN a document is validated as `yaml` through `validate_config(format="yaml")`,
`JunosValidator.validate_yaml` or `junoscfg convert -v -i yaml` and holds a mapping key that
is not a string, a cycle, or a value nested deeper than 64 levels, anywhere but in the value
of an `_ansible*` or `_meta_*` key, THEN the system SHALL give an invalid result naming its
kind and path, as the `yaml` reader refuses it (conversion/junos-json-yaml) and as yaml-new
validation reports it ("YAML int key has no JSON spelling"), never an exception and never the
key's value; CLI exit 1. Every other document gets the verdict the YAML schema gives, as
before; a value under an `_ansible*` or `_meta_*` key is not walked, as the schema admits it
unread.
Tests: `tests/unit/validate/test_json_yaml_validator.py::TestYamlValidation::test_a_key_that_is_not_a_string_is_invalid`, `tests/unit/validate/test_json_yaml_validator.py::TestYamlValidation::test_a_cycle_or_a_value_past_64_levels_is_invalid`, `tests/unit/validate/test_json_yaml_validator.py::TestYamlValidation::test_a_meta_key_value_is_not_walked`, `tests/unit/cli/test_cli_validate.py::TestCliValidation::test_a_yaml_key_that_is_not_a_string_exits_one`

#### Scenario: A number as a key

- **WHEN** `configuration: {system: {host-name: r1}, 64496: x}` is validated as `yaml`
- **THEN** the result is invalid with "YAML int key has no JSON spelling" at `configuration`, where validation raised `TypeError` inside jsonschema
