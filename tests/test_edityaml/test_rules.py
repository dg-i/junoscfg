"""Tests for edityaml rule parsing and loading."""

from __future__ import annotations

import pytest
import yaml

from junoscfg.edityaml.rules import load_rules_file, merge_rulesets, parse_inline_rules


class TestLoadRulesFile:
    def test_load_basic_rule_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        rules_yaml = {
            "rules": [
                {
                    "path": "configuration.system",
                    "transforms": [
                        {"type": "static", "target": "_managed", "value": True},
                    ],
                }
            ]
        }
        rule_file = tmp_path / "rules.yaml"
        rule_file.write_text(yaml.dump(rules_yaml))

        ruleset = load_rules_file(str(rule_file))
        assert len(ruleset["rules"]) == 1
        assert ruleset["rules"][0]["path"] == "configuration.system"
        assert ruleset["rules"][0]["transforms"][0]["type"] == "static"

    def test_load_multiple_rules(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        rules_yaml = {
            "rules": [
                {
                    "path": "configuration.system",
                    "transforms": [
                        {"type": "static", "target": "_a", "value": 1},
                    ],
                },
                {
                    "path": "configuration.interfaces.interface[*]",
                    "transforms": [
                        {"type": "copy", "source": "name", "target": "_name"},
                    ],
                },
            ]
        }
        rule_file = tmp_path / "rules.yaml"
        rule_file.write_text(yaml.dump(rules_yaml))

        ruleset = load_rules_file(str(rule_file))
        assert len(ruleset["rules"]) == 2

    def test_load_nonexistent_file_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_rules_file("/no/such/file.yaml")

    def test_load_invalid_yaml_raises(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        rule_file = tmp_path / "bad.yaml"
        rule_file.write_text("rules:\n  - path: 'a'\n    transforms: [invalid")
        with pytest.raises(yaml.YAMLError):
            load_rules_file(str(rule_file))

    def test_load_missing_rules_key_raises(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        rule_file = tmp_path / "bad.yaml"
        rule_file.write_text("other_key: true\n")
        with pytest.raises(ValueError, match="rules"):
            load_rules_file(str(rule_file))


class TestParseInlineRules:
    def test_regex_extract(self) -> None:
        ruleset = parse_inline_rules(
            "a.b[*]",
            ["_peer=regex_extract(description, 'overlay: (\\\\w+)')"],
        )
        assert len(ruleset["rules"]) == 1
        rule = ruleset["rules"][0]
        assert rule["path"] == "a.b[*]"
        t = rule["transforms"][0]
        assert t["type"] == "regex_extract"
        assert t["source"] == "description"
        assert t["target"] == "_peer"

    def test_regex_extract_with_group(self) -> None:
        ruleset = parse_inline_rules(
            "a.b[*]",
            ["_rack=regex_extract(description, 'overlay: (\\\\w+) rack: (\\\\w+)', 2)"],
        )
        t = ruleset["rules"][0]["transforms"][0]
        assert t["group"] == 2

    def test_static_explicit(self) -> None:
        ruleset = parse_inline_rules("a", ["_managed=static(true)"])
        t = ruleset["rules"][0]["transforms"][0]
        assert t["type"] == "static"
        assert t["target"] == "_managed"
        assert t["value"] is True

    def test_static_false(self) -> None:
        ruleset = parse_inline_rules("a", ["_flag=static(false)"])
        t = ruleset["rules"][0]["transforms"][0]
        assert t["value"] is False

    def test_static_number(self) -> None:
        ruleset = parse_inline_rules("a", ["_pri=static(42)"])
        t = ruleset["rules"][0]["transforms"][0]
        assert t["value"] == 42

    def test_bare_value(self) -> None:
        ruleset = parse_inline_rules("a", ["_foo=bar"])
        t = ruleset["rules"][0]["transforms"][0]
        assert t["type"] == "static"
        assert t["value"] == "bar"

    def test_copy(self) -> None:
        ruleset = parse_inline_rules("a", ["_name=copy(name)"])
        t = ruleset["rules"][0]["transforms"][0]
        assert t["type"] == "copy"
        assert t["source"] == "name"

    def test_template(self) -> None:
        ruleset = parse_inline_rules("a", ["_label=template('intf-{name}-{unit}')"])
        t = ruleset["rules"][0]["transforms"][0]
        assert t["type"] == "template"
        assert t["template"] == "intf-{name}-{unit}"

    def test_multiple_set_exprs(self) -> None:
        ruleset = parse_inline_rules("a.b[*]", ["_x=static(1)", "_y=copy(name)"])
        assert len(ruleset["rules"]) == 1
        assert len(ruleset["rules"][0]["transforms"]) == 2


class TestMergeRulesets:
    def test_merge_two(self) -> None:
        r1 = {"rules": [{"path": "a", "transforms": []}]}
        r2 = {"rules": [{"path": "b", "transforms": []}]}
        merged = merge_rulesets(r1, r2)
        assert len(merged["rules"]) == 2

    def test_merge_empty(self) -> None:
        r1 = {"rules": [{"path": "a", "transforms": []}]}
        merged = merge_rulesets(r1)
        assert len(merged["rules"]) == 1

    def test_merge_none(self) -> None:
        merged = merge_rulesets()
        assert merged["rules"] == []
