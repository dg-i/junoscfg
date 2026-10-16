# validation/junos-json-yaml Specification

## Purpose

Validating a `yaml-new` document gives the verdict the JSON schema gives the same object,
so a file validates the same whether it is spelled in JSON or in yaml-new.

## Requirements

### Requirement: yaml-new validates as the JSON object it spells

WHEN a `yaml-new` document is validated through `validate_config(format="yaml-new")`,
`JunosValidator.validate_yaml_as_json` or `junoscfg convert -v -i yaml-new` THEN the system
SHALL give the verdict and errors the JSON schema gives for the loaded object, written out
where it shares a mapping or list through an alias, an `_ansible_*` or `_meta_*` key
included; a YAML parse error SHALL be an invalid result naming its line, and a value JSON
cannot hold, a cycle, or a value nested deeper than 64 levels (conversion/junos-json-yaml)
an invalid result naming its kind and path, never an exception; text PyYAML itself cannot
load (nesting past about 490 levels) fails in PyYAML's loader, as at base.
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
Tests: `tests/unit/validate/test_json_yaml_validator.py::TestYamlValidation::test_a_key_that_is_not_a_string_is_invalid`, `tests/unit/validate/test_json_yaml_validator.py::TestYamlValidation::test_a_cycle_or_a_value_past_64_levels_is_invalid`, `tests/unit/validate/test_json_yaml_validator.py::TestYamlValidation::test_a_meta_key_value_is_not_walked`, `tests/unit/validate/test_json_yaml_validator.py::TestYamlValidation::test_a_yaml_scalar_value_keeps_its_verdict`, `tests/unit/cli/test_cli_validate.py::TestCliValidation::test_a_yaml_key_that_is_not_a_string_exits_one`

#### Scenario: A number as a key

- **WHEN** `configuration: {system: {host-name: r1}, 64496: x}` is validated as `yaml`
- **THEN** the result is invalid with "YAML int key has no JSON spelling" at `configuration`, where validation raised `TypeError` inside jsonschema

### Requirement: JSON validation refuses what the json reader refuses

WHEN a document is validated as `json` through `validate_config(format="json")`,
`JunosValidator.validate_json` or `junoscfg convert -v -i json` and holds a value nested
deeper than 64 levels THEN the system SHALL give an invalid result "JSON value is nested
deeper than 64 levels" at that value's path, never valid and never an exception; CLI exit 1.
Measured at base: a leaf holding 1,600 nested lists was judged valid, and `convert -v`
printed "Validation: OK" before the conversion crashed. Every other document gets the
verdict the JSON schema gives, as before.
Tests: `tests/unit/validate/test_json_yaml_validator.py::TestJsonValidationDepth::test_a_value_past_64_levels_is_invalid`, `tests/unit/cli/test_cli_validate.py::TestCliValidation::test_json_past_64_levels_exits_one`

#### Scenario: A leaf nested 1,600 levels deep

- **WHEN** `host-name` holds 1,600 nested mappings and the document is validated as `json`
- **THEN** the result is invalid with "JSON value is nested deeper than 64 levels"

### Requirement: A JSON validation message names the path and the keys

WHEN JSON, yaml-new or yaml validation reports an error THEN the message SHALL name the
deepest failing path and the offending keys or the kind of the failure (an unexpected key, a
wrong type), and SHALL NOT reprint the instance or a subtree of it: a list entry's failure is
reported at the entry, never as the whole list's repr.
Tests: `tests/unit/validate/test_json_yaml_validator.py::TestAMessageNamesThePathAndTheKeys::test_a_failing_entry_is_named_by_its_path_and_key`, `tests/unit/validate/test_json_yaml_validator.py::TestAMessageNamesThePathAndTheKeys::test_no_message_reprints_a_value`, `tests/unit/validate/test_json_yaml_validator.py::TestAMessageNamesThePathAndTheKeys::test_a_failure_deep_in_a_list_is_named_where_it_is`

#### Scenario: An unknown key in a list entry

- **WHEN** an interface entry in a JSON configuration carries an unknown key beside a
  `description`
- **THEN** the one error names `configuration.interfaces.interface.0` and the key, and holds
  no description text

### Requirement: Presence statements validate in both device spellings

WHEN an empty statement is written `[null]` or `{}` in JSON or yaml-new (the vMX 23.2R2
capture writes `[null]` where the QFX5120 25.2R2 capture writes an empty container `{}`)
THEN JSON validation and field validation SHALL accept both.
Tests: `tests/unit/validate/test_json_yaml_validator.py::TestPresenceInBothDeviceSpellings::test_both_spellings_validate`

#### Scenario: BGP flags

- **WHEN** `family inet-vpn unicast`, `multipath` and `bgp-error-tolerance` are written `{}`
- **THEN** the JSON is valid, as with `[null]`
