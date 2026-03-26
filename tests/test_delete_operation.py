"""Tests for the delete operation support (JSON/YAML → set & structured)."""

from __future__ import annotations

import json

import yaml

from junoscfg import Format, convert_config
from junoscfg.display import filter_set_by_path, is_display_set
from junoscfg.display.config_store import filter_structured_by_path
from junoscfg.display.set_converter import SetConverter


class TestJsonDeleteToSet:
    """JSON with operation=delete → set mode."""

    def test_delete_container(self) -> None:
        """Container-level delete annotation produces 'delete <path>'."""
        data = {
            "configuration": {
                "system": {
                    "services": {
                        "@": {"operation": "delete"},
                        "ssh": [None],
                    }
                }
            }
        }
        result = convert_config(json.dumps(data), from_format=Format.JSON, to_format=Format.SET)
        assert "delete system services" in result

    def test_delete_leaf(self) -> None:
        """Leaf-level delete annotation produces 'delete <path> <leaf>'."""
        data = {
            "configuration": {
                "system": {
                    "host-name": "router1",
                    "@host-name": {"operation": "delete"},
                }
            }
        }
        result = convert_config(json.dumps(data), from_format=Format.JSON, to_format=Format.SET)
        assert "delete system host-name" in result


class TestJsonDeleteToStructured:
    """JSON with operation=delete → structured mode."""

    def test_delete_container_structured(self) -> None:
        """Container-level delete produces 'delete:' prefix in structured output."""
        data = {
            "configuration": {
                "system": {
                    "services": {
                        "@": {"operation": "delete"},
                        "ssh": [None],
                    }
                }
            }
        }
        result = convert_config(
            json.dumps(data), from_format=Format.JSON, to_format=Format.STRUCTURED
        )
        assert "delete:" in result
        assert "services" in result

    def test_delete_leaf_structured(self) -> None:
        """Leaf-level delete produces 'delete:' prefix in structured output."""
        data = {
            "configuration": {
                "system": {
                    "host-name": "router1",
                    "@host-name": {"operation": "delete"},
                }
            }
        }
        result = convert_config(
            json.dumps(data), from_format=Format.JSON, to_format=Format.STRUCTURED
        )
        assert "delete:" in result
        assert "host-name" in result


class TestSetToStructuredDelete:
    """'delete' set commands → structured with delete: prefix."""

    def test_delete_command_to_structured(self) -> None:
        """'delete system services ssh' → structured with delete: prefix."""
        input_text = "set system services ssh\ndelete system services ssh"
        result = convert_config(input_text, from_format=Format.SET, to_format=Format.STRUCTURED)
        assert "delete:" in result
        assert "ssh" in result


class TestStructuredToSetDelete:
    """Structured with delete: prefix → set commands."""

    def test_delete_prefix_to_set(self) -> None:
        """'delete: services { ssh; }' → 'delete services' (marks the container)."""
        input_text = "delete: services {\n    ssh;\n}"
        result = SetConverter(input_text).to_set()
        assert "delete services" in result
        assert "set services ssh" in result

    def test_delete_prefix_leaf(self) -> None:
        """'system { delete: host-name router1; }' → 'delete system host-name router1'."""
        input_text = "system {\n    delete: host-name router1;\n}"
        result = SetConverter(input_text).to_set()
        assert "delete system host-name router1" in result


class TestYamlDeleteToSet:
    """YAML with @: {operation: delete} → set mode."""

    def test_yaml_delete_container(self) -> None:
        """YAML delete annotation on container produces 'delete <path>'."""
        data = {
            "configuration": {
                "system": {
                    "services": {
                        "@": {"operation": "delete"},
                        "ssh": None,
                    }
                }
            }
        }
        yaml_text = yaml.dump(data, default_flow_style=False)
        result = convert_config(yaml_text, from_format=Format.YAML, to_format=Format.SET)
        assert "delete system services" in result


class TestFilterSetDelete:
    """filter_set_by_path handles delete lines."""

    def test_filters_delete_lines(self) -> None:
        text = (
            "set system services ssh\ndelete system services ssh\nset interfaces ge-0/0/0 unit 0\n"
        )
        result = filter_set_by_path(text, ["system", "services"])
        assert "set system services ssh\n" in result
        assert "delete system services ssh\n" in result
        assert "interfaces" not in result

    def test_relative_with_delete(self) -> None:
        text = "set system services ssh\ndelete system services ssh\n"
        result = filter_set_by_path(text, ["system", "services"], relative=True)
        assert "set ssh\n" in result
        assert "delete ssh\n" in result


class TestFilterStructuredDelete:
    """filter_structured_by_path handles delete: prefix."""

    def test_preserves_delete_prefix(self) -> None:
        text = "system {\n    delete: services {\n        ssh;\n    }\n}\n"
        result = filter_structured_by_path(text, ["system"], relative=True)
        assert "delete: services {" in result


class TestIsDisplaySetDelete:
    """is_display_set accepts delete lines."""

    def test_delete_only(self) -> None:
        assert is_display_set("delete system services ssh\n")

    def test_mixed_set_delete(self) -> None:
        assert is_display_set("set system host-name r1\ndelete system services ssh\n")

    def test_mixed_set_deactivate_delete(self) -> None:
        assert is_display_set(
            "set system host-name r1\ndeactivate system syslog\ndelete system services ssh\n"
        )
