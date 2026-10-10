"""Tests for display output path filters."""

from __future__ import annotations

import yaml

from junoscfg.display import filter_set_by_path
from junoscfg.display.config_store import filter_structured_by_path
from junoscfg.display.path_filter import filter_dict_by_path
from junoscfg.display.to_yaml import filter_yaml_by_path


class TestFilterSetByPath:
    """Tests for set command output filtering by path."""

    def test_absolute_filters_matching_lines(self) -> None:
        text = (
            "set system host-name router1\n"
            "set system syslog file messages any notice\n"
            "set interfaces ge-0/0/0 description uplink\n"
        )
        result = filter_set_by_path(text, ["system", "syslog"])
        assert result == "set system syslog file messages any notice\n"

    def test_relative_strips_path_prefix(self) -> None:
        text = (
            "set system syslog file messages any notice\n"
            "set system syslog file interactive any error\n"
        )
        result = filter_set_by_path(text, ["system", "syslog"], relative=True)
        assert result == "set file messages any notice\nset file interactive any error\n"

    def test_filters_deactivate_lines(self) -> None:
        text = (
            "set system syslog file messages any notice\n"
            "deactivate system syslog file messages\n"
            "set interfaces ge-0/0/0 unit 0\n"
        )
        result = filter_set_by_path(text, ["system", "syslog"])
        assert "set system syslog file messages any notice\n" in result
        assert "deactivate system syslog file messages\n" in result
        assert "interfaces" not in result

    def test_filters_protect_and_activate_lines(self) -> None:
        text = (
            "set system syslog file messages any notice\n"
            "protect system syslog\n"
            "activate system syslog file messages\n"
        )
        result = filter_set_by_path(text, ["system", "syslog"])
        assert "set system syslog file messages any notice\n" in result
        assert "protect system syslog\n" in result
        assert "activate system syslog file messages\n" in result

    def test_relative_with_deactivate(self) -> None:
        text = (
            "set system syslog file messages any notice\ndeactivate system syslog file messages\n"
        )
        result = filter_set_by_path(text, ["system", "syslog"], relative=True)
        assert "set file messages any notice\n" in result
        assert "deactivate file messages\n" in result

    def test_path_not_found_returns_empty(self) -> None:
        text = "set system host-name router1\n"
        result = filter_set_by_path(text, ["interfaces"])
        assert result == ""

    def test_empty_path_returns_all(self) -> None:
        text = "set system host-name router1\nset interfaces ge-0/0/0 unit 0\n"
        result = filter_set_by_path(text, [])
        assert result == text

    def test_exact_path_match_included(self) -> None:
        """A line whose path exactly equals the filter path should be included."""
        text = "set system syslog\n"
        result = filter_set_by_path(text, ["system", "syslog"])
        assert result == "set system syslog\n"

    def test_partial_token_not_matched(self) -> None:
        """'system' should not match 'system-services'."""
        text = "set system-services ssh\nset system host-name r1\n"
        result = filter_set_by_path(text, ["system"])
        assert "system-services" not in result
        assert result == "set system host-name r1\n"


class TestFilterYamlByPath:
    """Tests for YAML output filtering by path."""

    def test_absolute_wraps_in_path(self) -> None:
        text = yaml.dump(
            {"configuration": {"system": {"syslog": {"file": "messages"}}}},
            default_flow_style=False,
        )
        result = filter_yaml_by_path(text, ["system", "syslog"])
        parsed = yaml.safe_load(result)
        assert parsed == {"configuration": {"system": {"syslog": {"file": "messages"}}}}

    def test_relative_returns_subtree(self) -> None:
        text = yaml.dump(
            {"configuration": {"system": {"syslog": {"file": "messages"}, "host-name": "r1"}}},
            default_flow_style=False,
        )
        result = filter_yaml_by_path(text, ["system", "syslog"], relative=True)
        parsed = yaml.safe_load(result)
        assert parsed == {"file": "messages"}

    def test_filters_out_sibling_branches(self) -> None:
        text = yaml.dump(
            {
                "configuration": {
                    "system": {"host-name": "r1"},
                    "interfaces": {"ge-0/0/0": {}},
                }
            },
            default_flow_style=False,
        )
        result = filter_yaml_by_path(text, ["system"])
        parsed = yaml.safe_load(result)
        assert "interfaces" not in parsed.get("configuration", {})
        assert parsed["configuration"]["system"]["host-name"] == "r1"

    def test_path_not_found_returns_empty(self) -> None:
        text = yaml.dump(
            {"configuration": {"system": {"host-name": "r1"}}},
            default_flow_style=False,
        )
        result = filter_yaml_by_path(text, ["interfaces"])
        assert result == ""

    def test_empty_path_returns_all(self) -> None:
        text = yaml.dump(
            {"configuration": {"system": {"host-name": "r1"}}},
            default_flow_style=False,
        )
        result = filter_yaml_by_path(text, [])
        parsed = yaml.safe_load(result)
        assert parsed == {"configuration": {"system": {"host-name": "r1"}}}

    def test_single_level_path(self) -> None:
        text = yaml.dump(
            {"configuration": {"system": {"host-name": "r1"}, "interfaces": {}}},
            default_flow_style=False,
        )
        result = filter_yaml_by_path(text, ["system"], relative=True)
        parsed = yaml.safe_load(result)
        assert parsed == {"host-name": "r1"}


class TestFilterStructuredByPath:
    """Tests for structured (curly-brace) output filtering by path."""

    def test_absolute_wraps_in_path(self) -> None:
        text = (
            "system {\n"
            "    syslog {\n"
            "        file messages {\n"
            "            any notice;\n"
            "        }\n"
            "    }\n"
            "    host-name router1;\n"
            "}\n"
        )
        result = filter_structured_by_path(text, ["system", "syslog"])
        assert "system {" in result
        assert "syslog {" in result
        assert "file messages" in result
        assert "host-name" not in result

    def test_relative_omits_path(self) -> None:
        text = (
            "system {\n"
            "    syslog {\n"
            "        file messages {\n"
            "            any notice;\n"
            "        }\n"
            "    }\n"
            "}\n"
        )
        result = filter_structured_by_path(text, ["system", "syslog"], relative=True)
        assert "system" not in result
        assert "syslog" not in result
        assert "file messages {" in result
        assert "any notice;" in result

    def test_relative_correct_indentation(self) -> None:
        """Relative output should start at indent level 0."""
        text = (
            "system {\n"
            "    syslog {\n"
            "        file messages {\n"
            "            any notice;\n"
            "        }\n"
            "    }\n"
            "}\n"
        )
        result = filter_structured_by_path(text, ["system", "syslog"], relative=True)
        lines = [line for line in result.splitlines() if line.strip()]
        # First line should start at column 0
        assert lines[0] == "file messages {"
        assert lines[1] == "    any notice;"

    def test_path_not_found_returns_empty(self) -> None:
        text = "system host-name router1;\n"
        result = filter_structured_by_path(text, ["interfaces"])
        assert result == ""

    def test_empty_path_returns_all(self) -> None:
        text = "system host-name router1;\n"
        result = filter_structured_by_path(text, [])
        assert result == text

    def test_preserves_inactive_prefix(self) -> None:
        text = (
            "system {\n"
            "    syslog {\n"
            "        inactive: file messages {\n"
            "            any notice;\n"
            "        }\n"
            "    }\n"
            "}\n"
        )
        result = filter_structured_by_path(text, ["system", "syslog"], relative=True)
        assert "inactive: file messages {" in result

    def test_single_level_filter(self) -> None:
        text = (
            "system {\n"
            "    host-name router1;\n"
            "}\n"
            "interfaces {\n"
            "    ge-0/0/0 {\n"
            "        description uplink;\n"
            "    }\n"
            "}\n"
        )
        result = filter_structured_by_path(text, ["interfaces"])
        assert "interfaces {" in result
        assert "ge-0/0/0 {" in result
        assert "system" not in result

    def test_oneliner_match(self) -> None:
        """A collapsed oneliner like 'system host-name r1;' matches path ['system']."""
        text = "system host-name router1;\n"
        result = filter_structured_by_path(text, ["system"], relative=True)
        assert "host-name router1;" in result


class TestFilterDictByPath:
    """Tests for the shared filter_dict_by_path() helper."""

    def test_navigate_simple_path(self) -> None:
        data = {"configuration": {"system": {"host-name": "r1", "syslog": {"file": "messages"}}}}
        result = filter_dict_by_path(data, ["system", "syslog"])
        assert result == {"configuration": {"system": {"syslog": {"file": "messages"}}}}

    def test_configuration_wrapper(self) -> None:
        """Handles 'configuration' key transparently."""
        data = {"configuration": {"system": {"host-name": "r1"}}}
        result = filter_dict_by_path(data, ["system"])
        assert result == {"configuration": {"system": {"host-name": "r1"}}}

    def test_no_configuration_wrapper(self) -> None:
        """Works without 'configuration' wrapper."""
        data = {"system": {"host-name": "r1"}}
        result = filter_dict_by_path(data, ["system"])
        assert result == {"system": {"host-name": "r1"}}

    def test_path_not_found(self) -> None:
        data = {"configuration": {"system": {"host-name": "r1"}}}
        result = filter_dict_by_path(data, ["interfaces"])
        assert result is None

    def test_relative_strips_prefix(self) -> None:
        data = {"configuration": {"system": {"syslog": {"file": "messages"}}}}
        result = filter_dict_by_path(data, ["system", "syslog"], relative=True)
        assert result == {"file": "messages"}

    def test_empty_path_tokens(self) -> None:
        """Empty path navigates nowhere — returns the root unchanged."""
        data = {"configuration": {"system": {"host-name": "r1"}}}
        # With empty tokens, the "configuration" wrapper node is returned as-is
        # (relative=False rebuilds nothing, has_config_wrapper wraps it back)
        result = filter_dict_by_path(data, [])
        assert result == {"configuration": {"system": {"host-name": "r1"}}}
