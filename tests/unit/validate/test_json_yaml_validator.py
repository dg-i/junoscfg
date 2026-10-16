"""Tests for JSON and YAML validators."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
import yaml

from junoscfg import Format, convert_config_result
from junoscfg.validate import JsonYamlValidator, SchemaLoadError
from tests.support.aliases import (
    ANCHORED_BESIDE,
    ANCHORED_BESIDE_WRITTEN_OUT,
    SHARED_BLOCK,
    SHARED_BLOCK_WRITTEN_OUT,
    alias_chain_yaml,
    hosts_sharing_contents,
    nested_yaml,
)
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

    def test_a_value_past_64_levels_is_invalid(self, validator):
        """A value past 64 levels is an invalid result naming its path, never an
        exception; reuse of a block the old bounds refused is judged written out
        (owner rulings on SC-2 and SC-A)."""
        for source, path in (
            (nested_yaml(62), "configuration.system.x" + ".0" * 62),
            (nested_yaml(400), "configuration.system.x" + ".0" * 62),
            (alias_chain_yaml(), "s3" + ".0" * 64),
        ):
            result = validator.validate_yaml_as_json(source)
            assert result.valid is False
            assert [(e.message, e.path) for e in result.errors] == [
                ("YAML value is nested deeper than 64 levels", path)
            ]
        reused = validator.validate_yaml_as_json(ANCHORED_BESIDE)
        assert reused == validator.validate_yaml_as_json(ANCHORED_BESIDE_WRITTEN_OUT)
        eleven = hosts_sharing_contents(11)
        written_out = eleven.replace("contents: &c\n", "contents:\n").replace(
            "        contents: *c\n",
            "        contents:\n        - name: any\n          any: [null]\n",
        )
        assert validator.validate_yaml_as_json(eleven) == validator.validate_yaml_as_json(
            written_out
        )

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


#: A value no message may quote: a message names a path and keys, never values.
_VALUE = "uplink to sw1 private-words"


class TestAMessageNamesThePathAndTheKeys:
    """jsonschema's own message for a failing `anyOf` is the instance's repr: a list
    of interfaces or BGP groups whole, `secret` values included (owner's log,
    2026-10-16; change device-validation). A message names the deepest failing path
    and the offending keys or the kind of failure, never a value."""

    def test_a_failing_entry_is_named_by_its_path_and_key(self, bundled_validator) -> None:
        doc = {
            "configuration": {
                "interfaces": {
                    "interface": [
                        {"name": "ge-0/0/0", "description": _VALUE},
                        {"name": "ge-0/0/1", "description": _VALUE, "no-such-child": "y"},
                    ]
                }
            }
        }
        result = bundled_validator.validate_json(json.dumps(doc))
        assert [(e.path, e.message) for e in result.errors] == [
            (
                "configuration.interfaces.interface.1",
                "'no-such-child' is not a statement the schema places here",
            )
        ]

    @pytest.mark.parametrize(
        "doc",
        [
            {"configuration": {"system": [{"host-name": _VALUE}, {"bogus": _VALUE}]}},
            {"configuration": {"interfaces": [{"name": _VALUE, "mtu": 1500}]}},
            {"configuration": "garbage " + _VALUE},
            {
                "configuration": {
                    "protocols": {
                        "bgp": {"group": [{"name": _VALUE, "family": {"bogus": {"a": _VALUE}}}]}
                    }
                }
            },
        ],
        ids=["array-wrapped", "transparent-as-list", "a-string", "deep-in-a-list"],
    )
    @pytest.mark.parametrize("door", ["validate_json", "validate_yaml_as_json", "validate_yaml"])
    def test_no_message_reprints_a_value(self, bundled_validator, doc, door) -> None:
        text = json.dumps(doc) if door == "validate_json" else yaml.safe_dump(doc)
        result = getattr(bundled_validator, door)(text)
        assert result.errors
        for error in result.errors:
            assert _VALUE not in error.message, error.message
            assert "{" not in error.message and "[" not in error.message, error.message

    def test_a_failure_deep_in_a_list_is_named_where_it_is(self, bundled_validator) -> None:
        doc = {
            "configuration": {
                "protocols": {
                    "bgp": {"group": [{"name": _VALUE, "family": {"bogus": {"a": _VALUE}}}]}
                }
            }
        }
        result = bundled_validator.validate_json(json.dumps(doc))
        assert [(e.path, e.message) for e in result.errors] == [
            (
                "configuration.protocols.bgp.group.0.family",
                "'bogus' is not a statement the schema places here",
            )
        ]


class TestPresenceInBothDeviceSpellings:
    """vMX 23.2R2-S7.5 writes an empty presence statement `[null]`, QFX5120
    25.2R2-S1.5 `{}` (`junoscfg-oracle.json.gz` of each); both are the device's."""

    @pytest.mark.parametrize("empty", [[None], {}], ids=["null-list", "empty-object"])
    def test_both_spellings_validate(self, bundled_validator, empty) -> None:
        doc = {
            "configuration": {
                "protocols": {
                    "bgp": {
                        "group": [
                            {
                                "name": "IBGP",
                                "family": {"inet-vpn": {"unicast": empty}},
                                "multipath": empty,
                                "bgp-error-tolerance": empty,
                            }
                        ]
                    }
                }
            }
        }
        text = json.dumps(doc)
        assert not bundled_validator.validate_json(text).errors
        result = convert_config_result(text, from_format=Format.JSON, to_format=Format.SET)
        assert not [d for d in result.diagnostics if d.source == "field-validate"]
