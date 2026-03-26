"""Tests for edityaml transform implementations."""

from __future__ import annotations

from junoscfg.edityaml.transforms import apply_transform


class TestRegexExtract:
    def test_basic_capture(self) -> None:
        node = {"description": "overlay: spine1"}
        rule = {
            "type": "regex_extract",
            "source": "description",
            "pattern": r"overlay: (\w+)",
            "target": "_peer",
        }
        apply_transform(node, rule)
        assert node["_peer"] == "spine1"

    def test_explicit_group(self) -> None:
        node = {"description": "overlay: spine1 rack: A"}
        rule = {
            "type": "regex_extract",
            "source": "description",
            "pattern": r"overlay: (\w+) rack: (\w+)",
            "target": "_rack",
            "group": 2,
        }
        apply_transform(node, rule)
        assert node["_rack"] == "A"

    def test_no_match_skips(self) -> None:
        node = {"description": "no match here"}
        rule = {
            "type": "regex_extract",
            "source": "description",
            "pattern": r"overlay: (\w+)",
            "target": "_peer",
        }
        apply_transform(node, rule)
        assert "_peer" not in node

    def test_missing_source_skips(self) -> None:
        node = {"name": "something"}
        rule = {
            "type": "regex_extract",
            "source": "description",
            "pattern": r"overlay: (\w+)",
            "target": "_peer",
        }
        apply_transform(node, rule)
        assert "_peer" not in node

    def test_non_string_source_skips(self) -> None:
        node = {"description": 42}
        rule = {
            "type": "regex_extract",
            "source": "description",
            "pattern": r"(\d+)",
            "target": "_num",
        }
        apply_transform(node, rule)
        assert "_num" not in node


class TestStatic:
    def test_set_string(self) -> None:
        node = {}
        rule = {"type": "static", "target": "_managed", "value": "yes"}
        apply_transform(node, rule)
        assert node["_managed"] == "yes"

    def test_set_bool(self) -> None:
        node = {}
        rule = {"type": "static", "target": "_managed", "value": True}
        apply_transform(node, rule)
        assert node["_managed"] is True

    def test_set_int(self) -> None:
        node = {"existing": "data"}
        rule = {"type": "static", "target": "_priority", "value": 100}
        apply_transform(node, rule)
        assert node["_priority"] == 100
        assert node["existing"] == "data"


class TestCopy:
    def test_copy_value(self) -> None:
        node = {"name": "eth0"}
        rule = {"type": "copy", "source": "name", "target": "_intf_name"}
        apply_transform(node, rule)
        assert node["_intf_name"] == "eth0"
        assert node["name"] == "eth0"

    def test_missing_source_skips(self) -> None:
        node = {"other": "val"}
        rule = {"type": "copy", "source": "name", "target": "_intf_name"}
        apply_transform(node, rule)
        assert "_intf_name" not in node


class TestRename:
    def test_rename_key(self) -> None:
        node = {"old-key": "value", "other": "x"}
        rule = {"type": "rename", "source": "old-key", "target": "new-key"}
        apply_transform(node, rule)
        assert node["new-key"] == "value"
        assert "old-key" not in node
        assert node["other"] == "x"

    def test_missing_source_skips(self) -> None:
        node = {"other": "x"}
        rule = {"type": "rename", "source": "old-key", "target": "new-key"}
        apply_transform(node, rule)
        assert "new-key" not in node


class TestTemplate:
    def test_basic_template(self) -> None:
        node = {"name": "ge-0/0/0", "unit": "0"}
        rule = {
            "type": "template",
            "target": "_label",
            "template": "intf-{name}-{unit}",
        }
        apply_transform(node, rule)
        assert node["_label"] == "intf-ge-0/0/0-0"

    def test_missing_key_in_template_raises(self) -> None:
        node = {"name": "eth0"}
        rule = {
            "type": "template",
            "target": "_label",
            "template": "intf-{name}-{missing}",
        }
        # Missing key in template should skip (not crash)
        apply_transform(node, rule)
        assert "_label" not in node


class TestConditional:
    def test_matches_applies_nested(self) -> None:
        node = {"description": "uplink to spine"}
        rule = {
            "type": "conditional",
            "when": {"key": "description", "matches": ".*uplink.*"},
            "transforms": [
                {"type": "static", "target": "_is_uplink", "value": True},
            ],
        }
        apply_transform(node, rule)
        assert node["_is_uplink"] is True

    def test_no_match_skips_nested(self) -> None:
        node = {"description": "downlink to leaf"}
        rule = {
            "type": "conditional",
            "when": {"key": "description", "matches": ".*uplink.*"},
            "transforms": [
                {"type": "static", "target": "_is_uplink", "value": True},
            ],
        }
        apply_transform(node, rule)
        assert "_is_uplink" not in node

    def test_missing_key_skips(self) -> None:
        node = {"name": "eth0"}
        rule = {
            "type": "conditional",
            "when": {"key": "description", "matches": ".*"},
            "transforms": [
                {"type": "static", "target": "_flag", "value": True},
            ],
        }
        apply_transform(node, rule)
        assert "_flag" not in node

    def test_equals_condition(self) -> None:
        node = {"status": "active"}
        rule = {
            "type": "conditional",
            "when": {"key": "status", "equals": "active"},
            "transforms": [
                {"type": "static", "target": "_active", "value": True},
            ],
        }
        apply_transform(node, rule)
        assert node["_active"] is True

    def test_equals_no_match(self) -> None:
        node = {"status": "inactive"}
        rule = {
            "type": "conditional",
            "when": {"key": "status", "equals": "active"},
            "transforms": [
                {"type": "static", "target": "_active", "value": True},
            ],
        }
        apply_transform(node, rule)
        assert "_active" not in node

    def test_nested_conditional(self) -> None:
        node = {"description": "uplink to spine", "speed": "10g"}
        rule = {
            "type": "conditional",
            "when": {"key": "description", "matches": ".*uplink.*"},
            "transforms": [
                {
                    "type": "conditional",
                    "when": {"key": "speed", "equals": "10g"},
                    "transforms": [
                        {"type": "static", "target": "_fast_uplink", "value": True},
                    ],
                },
            ],
        }
        apply_transform(node, rule)
        assert node["_fast_uplink"] is True
