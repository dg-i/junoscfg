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
