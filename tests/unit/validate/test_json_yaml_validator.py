"""Tests for JSON and YAML validators."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from junoscfg.validate import JsonYamlValidator, SchemaLoadError
from tests.support.aliases import SHARED_BLOCK, SHARED_BLOCK_WRITTEN_OUT, alias_bomb_yaml
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


class TestYamlAsJsonValidation:
    """yaml-new validates as the JSON object it spells: the JSON schema, not the
    YAML one (spec validation/junos-json-yaml)."""

    def test_valid_document(self, validator):
        yaml_str = "configuration:\n  system:\n    host-name: router1\n"
        assert validator.validate_yaml_as_json(yaml_str).valid is True

    @pytest.mark.parametrize("key", ["_ansible_var", "_meta_info"])
    def test_a_meta_key_is_rejected_as_json_rejects_it(self, validator, key):
        document = {"configuration": {"system": {"host-name": "router1", key: "test"}}}
        yaml_str = f"configuration:\n  system:\n    host-name: router1\n    {key}: test\n"
        as_json = validator.validate_json(json.dumps(document))
        result = validator.validate_yaml_as_json(yaml_str)
        assert result.valid is False
        assert result.errors == as_json.errors
        assert validator.validate_yaml(yaml_str).valid is True

    def test_a_parse_error_names_its_line(self, validator):
        result = validator.validate_yaml_as_json("configuration:\n  system: [unclosed\n")
        assert result.valid is False
        assert "YAML parse error" in result.errors[0].message
        assert result.errors[0].line == 3

    @pytest.mark.parametrize(
        ("document", "kind", "path"),
        [
            (
                "configuration:\n  system:\n    host-name: 2026-10-15\n",
                "date",
                "configuration.system.host-name",
            ),
            ("configuration:\n  system:\n    on: x\n", "bool key", "configuration.system"),
            ("configuration:\n  system:\n    64496: x\n", "int key", "configuration.system"),
            ("configuration: &a\n  system:\n    x: *a\n", "cycle", "configuration.system.x"),
        ],
        ids=["date", "bool-key", "int-key", "cycle"],
    )
    def test_a_value_json_cannot_hold_is_invalid(self, validator, document, kind, path):
        """Never an exception and never valid: the verdict conversion's refusal
        gives (Test/Challenge B2)."""
        result = validator.validate_yaml_as_json(document)
        assert result.valid is False
        assert [(e.message, e.path) for e in result.errors] == [
            (f"YAML {kind} has no JSON spelling", path)
        ]

    def test_a_shared_block_validates_written_out(self, validator):
        """A block shared through an alias is judged as the document written out
        (owner ruling on PO-2/SC-1)."""
        shared = validator.validate_yaml_as_json(SHARED_BLOCK)
        assert shared == validator.validate_yaml_as_json(SHARED_BLOCK_WRITTEN_OUT)
        assert not any("JSON spelling" in e.message for e in shared.errors)

    def test_an_alias_bomb_is_invalid(self, validator):
        """A bomb is an invalid result naming its alias, never an expansion."""
        result = validator.validate_yaml_as_json(alias_bomb_yaml())
        assert result.valid is False
        assert [e.message for e in result.errors] == [
            "YAML alias expands the document past twice its size"
        ]
        assert result.errors[0].path.startswith("lol1.")

    def test_an_empty_document_is_judged_as_json_null(self, validator):
        assert validator.validate_yaml_as_json("").errors == validator.validate_json("null").errors
        assert validator.validate_yaml_as_json("").valid is False


class TestSchemaLoadError:
    def test_no_json_schema_raises(self):
        v = JsonYamlValidator()
        with pytest.raises(SchemaLoadError):
            v.validate_json("{}")

    def test_no_yaml_schema_raises(self):
        v = JsonYamlValidator()
        with pytest.raises(SchemaLoadError):
            v.validate_yaml("")

    def test_yaml_as_json_needs_the_json_schema(self, tmp_path):
        minimal = make_artifacts_dir(tmp_path)
        v = JsonYamlValidator(yaml_schema_path=minimal.yaml_schema)
        with pytest.raises(SchemaLoadError, match="JSON schema"):
            v.validate_yaml_as_json("configuration: {}")
