"""Tests for JSON and YAML validators."""

from __future__ import annotations

import json
import tempfile

import pytest

from junoscfg.validate import SchemaLoadError
from junoscfg.validate.json_yaml_validator import JsonYamlValidator

# Minimal JSON Schema for testing
MINIMAL_JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "configuration": {
            "type": "object",
            "properties": {
                "system": {
                    "type": "object",
                    "properties": {
                        "host-name": {},
                    },
                    "additionalProperties": False,
                },
            },
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
}

MINIMAL_YAML_SCHEMA = {
    **MINIMAL_JSON_SCHEMA,
    "properties": {
        "configuration": {
            "type": "object",
            "properties": {
                "system": {
                    "type": "object",
                    "properties": {
                        "host-name": {},
                    },
                    "additionalProperties": False,
                    "patternProperties": {
                        "^_ansible_": {},
                        "^_meta_": {},
                    },
                },
            },
            "additionalProperties": False,
            "patternProperties": {
                "^_ansible_": {},
                "^_meta_": {},
            },
        },
    },
}


@pytest.fixture
def schema_paths():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as json_f:
        json.dump(MINIMAL_JSON_SCHEMA, json_f)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as yaml_f:
        json.dump(MINIMAL_YAML_SCHEMA, yaml_f)

    return json_f.name, yaml_f.name


@pytest.fixture
def validator(schema_paths):
    json_path, yaml_path = schema_paths
    return JsonYamlValidator(json_schema_path=json_path, yaml_schema_path=yaml_path)


class TestJsonValidation:
    def test_valid_json(self, validator):
        data = json.dumps({"configuration": {"system": {"host-name": "router1"}}})
        result = validator.validate_json(data)
        assert result.valid is True

    def test_invalid_json_extra_field(self, validator):
        data = json.dumps({"configuration": {"system": {"bogus": "value"}}})
        result = validator.validate_json(data)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_json_parse_error(self, validator):
        result = validator.validate_json("{not valid json")
        assert result.valid is False
        assert "parse error" in result.errors[0].message.lower()

    def test_bare_config_wrapped(self, validator):
        # Config without "configuration" wrapper should be auto-wrapped
        data = json.dumps({"system": {"host-name": "router1"}})
        result = validator.validate_json(data)
        assert result.valid is True


class TestYamlValidation:
    def test_valid_yaml(self, validator):
        yaml_str = "configuration:\n  system:\n    host-name: router1\n"
        result = validator.validate_yaml(yaml_str)
        assert result.valid is True

    def test_yaml_with_ansible_key(self, validator):
        yaml_str = "configuration:\n  system:\n    host-name: router1\n    _ansible_var: test\n"
        result = validator.validate_yaml(yaml_str)
        assert result.valid is True

    def test_yaml_with_meta_key(self, validator):
        yaml_str = "configuration:\n  system:\n    host-name: router1\n    _meta_info: test\n"
        result = validator.validate_yaml(yaml_str)
        assert result.valid is True

    def test_invalid_yaml_element(self, validator):
        yaml_str = "configuration:\n  system:\n    bogus: value\n"
        result = validator.validate_yaml(yaml_str)
        assert result.valid is False

    def test_yaml_parse_error(self, validator):
        result = validator.validate_yaml(":\n  bad: [unclosed")
        assert result.valid is False

    def test_empty_yaml(self, validator):
        result = validator.validate_yaml("")
        assert result.valid is True


class TestSchemaLoadError:
    def test_no_json_schema_raises(self):
        v = JsonYamlValidator()
        with pytest.raises(SchemaLoadError):
            v.validate_json("{}")

    def test_no_yaml_schema_raises(self):
        v = JsonYamlValidator()
        with pytest.raises(SchemaLoadError):
            v.validate_yaml("")


# ── identifier-key-fields: the bundled schemas and keyed entries ─────
#
# Spec: openspec/changes/identifier-key-fields/specs/validation/keyed-entries,
# "The JSON and YAML schemas name the key fields". Through the public doors,
# against the bundled artefacts.


def _document(entry: dict, slot: str = "as-path-neighbors", where: str = "from") -> dict:
    return {
        "configuration": {
            "policy-options": {
                "policy-statement": [
                    {"name": "SAMPLE-POLICY", "term": [{"name": "T1", where: {slot: [entry]}}]}
                ]
            }
        }
    }


class TestKeyedEntries:
    DEVICE = {"list-type": "as-list", "list-name": "SAMPLE-AS-LIST"}

    @staticmethod
    def _doors(document: dict) -> dict[str, bool]:
        import yaml

        from junoscfg import Format, validate_config, validate_json, validate_yaml

        text = json.dumps(document)
        as_yaml = yaml.safe_dump(document)
        return {
            "validate_json": validate_json(text).valid,
            "validate_yaml": validate_yaml(as_yaml).valid,
            "validate_config json": validate_config(text, format=Format.JSON).valid,
            "validate_config yaml": validate_config(as_yaml, format=Format.YAML).valid,
        }

    @pytest.mark.parametrize(
        ("slot", "where", "entry"),
        [
            ("as-path-neighbors", "from", {"list-type": "as-list", "list-name": "SAMPLE-AS-LIST"}),
            ("as-path-origins", "from", {"list-type": "as-list-group", "list-name": "SAMPLE-ASG"}),
            (
                "route-filter",
                "from",
                {"address": "198.51.100.0/24", "exact": [None], "accept": [None]},
            ),
            (
                "source-address-filter",
                "from",
                {"address": "198.51.100.0/24", "exact": [None], "accept": [None]},
            ),
            ("community", "then", {"add": [None], "community-name": "SAMPLE-COMM"}),
        ],
    )
    def test_the_device_shaped_as_list_reference_validates(
        self, slot: str, where: str, entry: dict
    ) -> None:
        assert all(self._doors(_document(entry, slot, where)).values())

    @pytest.mark.parametrize(
        ("slot", "entry"),
        [
            ("as-path-neighbors", {"name": "as-list"}),
            ("as-path-neighbors", {"name": "SAMPLE-AS-LIST", "list-type": "as-list"}),
            ("source-address-filter", {"name": "198.51.100.0/24", "exact": [None]}),
            ("route-filter", {"name": "198.51.100.0/24", "exact": [None]}),
        ],
    )
    def test_name_under_an_as_list_reference_is_rejected(self, slot: str, entry: dict) -> None:
        doors = self._doors(_document(entry, slot))
        assert not any(doors.values()), doors
