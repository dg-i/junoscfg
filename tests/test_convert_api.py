"""Tests for the unified convert_config() API and Format enum."""

from __future__ import annotations

import json

import pytest

from junoscfg import FieldValidationError, Format, convert_config, validate_config


class TestFormatEnum:
    def test_format_values(self) -> None:
        assert Format.SET.value == "set"
        assert Format.STRUCTURED.value == "structured"
        assert Format.JSON.value == "json"
        assert Format.YAML.value == "yaml"
        assert Format.XML.value == "xml"

    def test_format_from_string(self) -> None:
        assert Format("set") is Format.SET
        assert Format("json") is Format.JSON


class TestConvertJsonToSet:
    def test_simple(self) -> None:
        source = '{"configuration": {"system": {"host-name": "r1"}}}'
        result = convert_config(source, from_format=Format.JSON, to_format=Format.SET)
        assert "set system host-name r1" in result


class TestConvertJsonToStructured:
    def test_simple(self) -> None:
        source = '{"configuration": {"system": {"host-name": "r1"}}}'
        result = convert_config(source, from_format=Format.JSON, to_format=Format.STRUCTURED)
        assert "host-name r1;" in result


class TestConvertXmlToSet:
    def test_simple(self) -> None:
        source = "<configuration><system><host-name>r1</host-name></system></configuration>"
        result = convert_config(source, from_format=Format.XML, to_format=Format.SET)
        assert "set system host-name r1" in result


class TestConvertXmlToStructured:
    def test_simple(self) -> None:
        source = "<configuration><system><host-name>r1</host-name></system></configuration>"
        result = convert_config(source, from_format=Format.XML, to_format=Format.STRUCTURED)
        assert "host-name r1;" in result


class TestConvertYamlToSet:
    def test_simple(self) -> None:
        source = "configuration:\n  system:\n    host-name: router1\n"
        result = convert_config(source, from_format=Format.YAML, to_format=Format.SET)
        assert "set system host-name router1" in result


class TestConvertYamlToStructured:
    def test_simple(self) -> None:
        source = "configuration:\n  system:\n    host-name: router1\n"
        result = convert_config(source, from_format=Format.YAML, to_format=Format.STRUCTURED)
        assert "host-name router1;" in result


class TestConvertSetToStructured:
    def test_simple(self) -> None:
        source = "set system host-name router1"
        result = convert_config(source, from_format=Format.SET, to_format=Format.STRUCTURED)
        assert "host-name router1;" in result


class TestConvertStructuredToSet:
    def test_simple(self) -> None:
        source = "system {\n    host-name foo;\n}"
        result = convert_config(source, from_format=Format.STRUCTURED, to_format=Format.SET)
        assert "set system host-name foo" in result


class TestConvertJsonToYaml:
    def test_simple(self) -> None:
        source = '{"configuration": {"system": {"host-name": "r1"}}}'
        result = convert_config(source, from_format=Format.JSON, to_format=Format.YAML)
        assert "host-name: r1" in result


class TestConvertXmlToYaml:
    def test_simple(self) -> None:
        source = "<configuration><system><host-name>r1</host-name></system></configuration>"
        result = convert_config(source, from_format=Format.XML, to_format=Format.YAML)
        assert "host-name: r1" in result


class TestConvertSetToJson:
    def test_simple(self) -> None:
        source = "set system host-name r1"
        result = convert_config(source, from_format=Format.SET, to_format=Format.JSON)
        assert '"host-name": "r1"' in result
        assert '"configuration"' in result

    def test_multiple_commands(self) -> None:
        source = "set system host-name r1\nset system domain-name example.com"
        result = convert_config(source, from_format=Format.SET, to_format=Format.JSON)
        import json

        parsed = json.loads(result)
        assert parsed["configuration"]["system"]["host-name"] == "r1"
        assert parsed["configuration"]["system"]["domain-name"] == "example.com"


class TestConvertSetToYaml:
    def test_simple(self) -> None:
        source = "set system host-name r1"
        result = convert_config(source, from_format=Format.SET, to_format=Format.YAML)
        assert "host-name: r1" in result


class TestConvertStructuredToJson:
    def test_simple(self) -> None:
        source = "system {\n    host-name r1;\n}"
        result = convert_config(source, from_format=Format.STRUCTURED, to_format=Format.JSON)
        assert '"host-name": "r1"' in result
        assert '"configuration"' in result


class TestJsonOutputGroupsFormat:
    """Verify JSON output uses native Junos format for groups.

    Native Junos JSON uses ``"groups": [...]`` directly, not
    ``"groups": {"group": [...]}``.
    """

    def test_set_to_json_groups_native_format(self) -> None:
        source = (
            "set groups mygroup system host-name r1\n"
            "set groups other system domain-name example.com\n"
        )
        result = convert_config(source, from_format=Format.SET, to_format=Format.JSON)
        parsed = json.loads(result)
        groups = parsed["configuration"]["groups"]
        assert isinstance(groups, list), f"expected list, got {type(groups).__name__}"
        names = [g["name"] for g in groups]
        assert "mygroup" in names
        assert "other" in names

    def test_structured_to_json_groups_native_format(self) -> None:
        source = (
            "groups {\n    mygroup {\n        system {\n"
            "            host-name r1;\n        }\n    }\n}\n"
        )
        result = convert_config(
            source, from_format=Format.STRUCTURED, to_format=Format.JSON
        )
        parsed = json.loads(result)
        groups = parsed["configuration"]["groups"]
        assert isinstance(groups, list), f"expected list, got {type(groups).__name__}"
        assert groups[0]["name"] == "mygroup"

    def test_json_roundtrip_preserves_native_groups(self) -> None:
        source = json.dumps(
            {
                "configuration": {
                    "groups": [
                        {"name": "g1", "system": {"host-name": "r1"}},
                    ]
                }
            }
        )
        result = convert_config(source, from_format=Format.JSON, to_format=Format.JSON)
        parsed = json.loads(result)
        groups = parsed["configuration"]["groups"]
        assert isinstance(groups, list)
        assert groups[0]["name"] == "g1"


class TestConvertStructuredToYaml:
    def test_simple(self) -> None:
        source = "system {\n    host-name r1;\n}"
        result = convert_config(source, from_format=Format.STRUCTURED, to_format=Format.YAML)
        assert "host-name: r1" in result


class TestConvertYamlToJson:
    def test_simple(self) -> None:
        source = "configuration:\n  system:\n    host-name: r1\n"
        result = convert_config(source, from_format=Format.YAML, to_format=Format.JSON)
        assert '"host-name": "r1"' in result
        assert '"configuration"' in result


class TestConvertXmlToJson:
    def test_simple(self) -> None:
        source = "<configuration><system><host-name>r1</host-name></system></configuration>"
        result = convert_config(source, from_format=Format.XML, to_format=Format.JSON)
        assert '"host-name": "r1"' in result
        assert '"configuration"' in result


class TestPartialStructuredConfig:
    """End-to-end: structured partial config (no parent wrapper) → JSON."""

    def test_interfaces_partial_to_json(self) -> None:
        source = (
            "ge-0/0/0 {\n"
            '    description "Core: srv06.dc1.example.net (igb0)";\n'
            "}\n"
            "lo0 {\n"
            "    unit 0 {\n"
            "        family inet {\n"
            "            address 10.0.36.103/32;\n"
            "        }\n"
            "    }\n"
            "}\n"
        )
        result = convert_config(source, from_format=Format.STRUCTURED, to_format=Format.JSON)
        parsed = json.loads(result)
        config = parsed["configuration"]
        assert "interfaces" in config
        ifaces = config["interfaces"]["interface"]
        assert isinstance(ifaces, list)
        names = [i["name"] for i in ifaces]
        assert "ge-0/0/0" in names
        assert "lo0" in names
        ge = next(i for i in ifaces if i["name"] == "ge-0/0/0")
        assert ge["description"] == "Core: srv06.dc1.example.net (igb0)"
        lo = next(i for i in ifaces if i["name"] == "lo0")
        assert lo["unit"][0]["family"]["inet"]["address"] == [{"name": "10.0.36.103/32"}]


class TestTransparentListKeyRoundTrip:
    """End-to-end: prefix-list-item and syslog contents survive round-trip."""

    def test_prefix_list_json_roundtrip(self) -> None:
        source = json.dumps(
            {
                "configuration": {
                    "policy-options": {
                        "prefix-list": [
                            {
                                "name": "MY-LIST",
                                "prefix-list-item": [
                                    {"name": "127.0.0.1/32"},
                                    {"name": "10.0.0.0/8"},
                                ],
                            }
                        ]
                    }
                }
            }
        )
        # JSON → set → JSON
        set_text = convert_config(source, from_format=Format.JSON, to_format=Format.SET)
        result = convert_config(set_text, from_format=Format.SET, to_format=Format.JSON)
        parsed = json.loads(result)
        items = parsed["configuration"]["policy-options"]["prefix-list"][0]["prefix-list-item"]
        names = [i["name"] for i in items]
        assert "127.0.0.1/32" in names
        assert "10.0.0.0/8" in names

    def test_syslog_contents_json_roundtrip(self) -> None:
        source = json.dumps(
            {
                "configuration": {
                    "system": {
                        "syslog": {
                            "file": [
                                {
                                    "name": "messages",
                                    "contents": [
                                        {"name": "interactive-commands", "any": [None]},
                                    ],
                                }
                            ]
                        }
                    }
                }
            }
        )
        # JSON → set → JSON
        set_text = convert_config(source, from_format=Format.JSON, to_format=Format.SET)
        result = convert_config(set_text, from_format=Format.SET, to_format=Format.JSON)
        parsed = json.loads(result)
        contents = parsed["configuration"]["system"]["syslog"]["file"][0]["contents"]
        assert len(contents) == 1
        assert contents[0]["name"] == "interactive-commands"
        assert contents[0]["any"] == [None]


class TestConvertUnsupported:
    def test_xml_output_not_supported(self) -> None:
        source = '{"configuration": {"system": {"host-name": "r1"}}}'
        with pytest.raises(NotImplementedError, match="XML output"):
            convert_config(source, from_format=Format.JSON, to_format=Format.XML)


class TestConvertIdentity:
    """Identity conversions parse and re-render through the pipeline."""

    def test_json_to_json(self) -> None:
        source = '{"configuration": {"system": {"host-name": "r1"}}}'
        result = convert_config(source, from_format=Format.JSON, to_format=Format.JSON)
        import json

        parsed = json.loads(result)
        assert parsed["configuration"]["system"]["host-name"] == "r1"

    def test_set_to_set(self) -> None:
        source = "set system host-name r1"
        result = convert_config(source, from_format=Format.SET, to_format=Format.SET)
        assert "set system host-name r1" in result

    def test_yaml_to_yaml(self) -> None:
        source = "configuration:\n  system:\n    host-name: r1\n"
        result = convert_config(source, from_format=Format.YAML, to_format=Format.YAML)
        assert "host-name: r1" in result

    def test_structured_to_structured(self) -> None:
        source = "system {\n    host-name r1;\n}"
        result = convert_config(source, from_format=Format.STRUCTURED, to_format=Format.STRUCTURED)
        assert "host-name r1;" in result


_PATH_FILTER_SOURCE = (
    '{"configuration": {"system": {"host-name": "r1",'
    ' "syslog": {"file": [{"name": "messages"}]}}, "interfaces": {}}}'
)


class TestPathFiltering:
    """Tests for path and relative parameters on convert_config()."""

    def test_path_filter_set(self) -> None:
        result = convert_config(
            _PATH_FILTER_SOURCE, from_format=Format.JSON, to_format=Format.SET, path="system"
        )
        assert "system" in result
        assert "interfaces" not in result

    def test_path_filter_structured(self) -> None:
        result = convert_config(
            _PATH_FILTER_SOURCE,
            from_format=Format.JSON,
            to_format=Format.STRUCTURED,
            path="system",
        )
        assert "system" in result
        assert "interfaces" not in result

    def test_path_filter_yaml(self) -> None:
        result = convert_config(
            _PATH_FILTER_SOURCE, from_format=Format.JSON, to_format=Format.YAML, path="system"
        )
        assert "host-name" in result
        assert "interfaces" not in result

    def test_path_filter_json(self) -> None:
        result = convert_config(
            _PATH_FILTER_SOURCE, from_format=Format.JSON, to_format=Format.JSON, path="system"
        )
        parsed = json.loads(result)
        assert "system" in parsed["configuration"]
        assert "interfaces" not in parsed.get("configuration", {})

    def test_path_filter_relative(self) -> None:
        result = convert_config(
            _PATH_FILTER_SOURCE,
            from_format=Format.JSON,
            to_format=Format.SET,
            path="system",
            relative=True,
        )
        assert "system" not in result
        assert "host-name r1" in result

    def test_path_filter_not_found(self) -> None:
        result = convert_config(
            _PATH_FILTER_SOURCE,
            from_format=Format.JSON,
            to_format=Format.SET,
            path="nonexistent",
        )
        assert result == ""

    def test_relative_without_path_raises(self) -> None:
        with pytest.raises(ValueError, match="relative.*requires.*path"):
            convert_config(
                _PATH_FILTER_SOURCE,
                from_format=Format.JSON,
                to_format=Format.SET,
                relative=True,
            )


class TestValidateConfig:
    """Tests for the unified validate_config() API."""

    def test_validate_json_valid(self, artifacts_dir: str) -> None:
        source = '{"configuration": {"system": {"host-name": "r1"}}}'
        result = validate_config(source, format="json", artifacts_dir=artifacts_dir)
        assert result.valid is True

    def test_validate_set_valid(self, artifacts_dir: str) -> None:
        source = "set system host-name r1"
        result = validate_config(source, format="set", artifacts_dir=artifacts_dir)
        assert result.valid is True

    def test_validate_json_invalid(self, artifacts_dir: str) -> None:
        source = '{"configuration": {"bogus-top-level": {"x": "y"}}}'
        result = validate_config(source, format="json", artifacts_dir=artifacts_dir)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_format_enum(self, artifacts_dir: str) -> None:
        source = '{"configuration": {"system": {"host-name": "r1"}}}'
        result = validate_config(source, format=Format.JSON, artifacts_dir=artifacts_dir)
        assert result.valid is True

    def test_validate_auto_detect_set(self, artifacts_dir: str) -> None:
        source = "set system host-name r1"
        result = validate_config(source, format=None, artifacts_dir=artifacts_dir)
        assert result.valid is True

    def test_validate_auto_detect_structured(self, artifacts_dir: str) -> None:
        source = "system {\n    host-name r1;\n}"
        result = validate_config(source, format=None, artifacts_dir=artifacts_dir)
        assert result.valid is True


class TestFieldValidationErrorExport:
    """FieldValidationError is accessible from the public API."""

    def test_importable_from_top_level(self) -> None:
        assert FieldValidationError is not None
        assert issubclass(FieldValidationError, Exception)
