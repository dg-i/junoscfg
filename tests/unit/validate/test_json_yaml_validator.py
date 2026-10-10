"""Tests for JSON and YAML validators."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from junoscfg.validate import JsonYamlValidator, SchemaLoadError
from tests.support.artifacts import make_artifacts_dir

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def validator(tmp_path: Path) -> JsonYamlValidator:
    """Both minimal schemas of `tests/support/artifacts.py`."""
    minimal = make_artifacts_dir(tmp_path)
    return JsonYamlValidator(
        json_schema_path=minimal.json_schema, yaml_schema_path=minimal.yaml_schema
    )


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
