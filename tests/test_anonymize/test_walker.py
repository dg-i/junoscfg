"""Tests for the schema-guided anonymization walker."""

from __future__ import annotations

from typing import Any

from junoscfg.anonymize.path_filter import PathFilter
from junoscfg.anonymize.rules import Rule
from junoscfg.anonymize.walker import _try_rules, _walk_node


class StubRule(Rule):
    """Test rule that matches on a specific type_ref and uppercases values."""

    name = "stub"
    priority = 10

    def __init__(self, match_tr: str = "ipv4addr") -> None:
        self._match_tr = match_tr
        self._seen: list[str] = []

    def matches(self, value: Any, schema_node: dict[str, Any], path: list[str]) -> bool:
        return schema_node.get("tr") == self._match_tr

    def transform(self, value: str) -> str:
        self._seen.append(value)
        return f"ANON_{value}"

    def get_mapping(self) -> dict[str, str]:
        return {v: f"ANON_{v}" for v in self._seen}


class TestTryRules:
    def test_matching_rule_transforms(self) -> None:
        rule = StubRule("ipv4addr")
        schema = {"l": True, "tr": "ipv4addr"}
        result = _try_rules("10.1.2.3/24", schema, ["interfaces", "address"], [rule], False)
        assert result == "ANON_10.1.2.3/24"

    def test_non_matching_rule_returns_original(self) -> None:
        rule = StubRule("ipv4addr")
        schema = {"l": True, "tr": "string"}
        result = _try_rules("hello", schema, ["system", "host-name"], [rule], False)
        assert result == "hello"

    def test_first_matching_rule_wins(self) -> None:
        rule1 = StubRule("ipv4addr")
        rule1.priority = 10
        rule2 = StubRule("ipv4addr")
        rule2.priority = 20
        schema = {"l": True, "tr": "ipv4addr"}
        result = _try_rules("10.0.0.1", schema, ["x"], [rule1, rule2], False)
        assert result == "ANON_10.0.0.1"
        assert len(rule1._seen) == 1
        assert len(rule2._seen) == 0


class TestWalkNode:
    def _make_schema(self) -> dict:
        """Build a minimal schema for testing walker traversal."""
        return {
            "c": {
                "system": {
                    "c": {
                        "host-name": {"l": True, "r": 0},
                        "name-server": {
                            "L": True,
                            "c": {
                                "name": {"l": True, "tr": "ipv4addr"},
                            },
                        },
                    },
                },
                "interfaces": {
                    "t": "interface",
                    "c": {
                        "interface": {
                            "L": True,
                            "c": {
                                "name": {"l": True},
                                "description": {"l": True},
                                "unit": {
                                    "L": True,
                                    "c": {
                                        "name": {"l": True},
                                        "family": {
                                            "c": {
                                                "inet": {
                                                    "c": {
                                                        "address": {
                                                            "L": True,
                                                            "c": {
                                                                "name": {
                                                                    "l": True,
                                                                    "tr": "ipv4addr",
                                                                },
                                                            },
                                                        },
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        }

    def test_walks_leaf_with_matching_type(self) -> None:
        rule = StubRule("ipv4addr")
        schema = self._make_schema()
        ir = {
            "interfaces": {
                "interface": [
                    {
                        "name": "ge-0/0/0",
                        "unit": [
                            {
                                "name": "0",
                                "family": {
                                    "inet": {
                                        "address": [{"name": "10.1.2.3/24"}],
                                    },
                                },
                            },
                        ],
                    },
                ],
            },
        }
        path_filter = PathFilter()
        _walk_node(ir, schema, [], [rule], path_filter, False)
        # The IP address should have been transformed
        addr = ir["interfaces"]["interface"][0]["unit"][0]["family"]["inet"]["address"][0]["name"]
        assert addr == "ANON_10.1.2.3/24"

    def test_walks_named_list(self) -> None:
        rule = StubRule("ipv4addr")
        schema = self._make_schema()
        ir = {
            "system": {
                "name-server": [
                    {"name": "8.8.8.8"},
                    {"name": "8.8.4.4"},
                ],
            },
        }
        path_filter = PathFilter()
        _walk_node(ir, schema, [], [rule], path_filter, False)
        assert ir["system"]["name-server"][0]["name"] == "ANON_8.8.8.8"
        assert ir["system"]["name-server"][1]["name"] == "ANON_8.8.4.4"

    def test_skips_non_matching_leaves(self) -> None:
        rule = StubRule("ipv4addr")
        schema = self._make_schema()
        ir = {
            "system": {"host-name": "router1"},
        }
        path_filter = PathFilter()
        _walk_node(ir, schema, [], [rule], path_filter, False)
        assert ir["system"]["host-name"] == "router1"

    def test_skips_attribute_keys(self) -> None:
        rule = StubRule("ipv4addr")
        schema = self._make_schema()
        ir = {
            "@": {"xmlns": "http://example.com"},
            "system": {"host-name": "router1"},
        }
        path_filter = PathFilter()
        _walk_node(ir, schema, [], [rule], path_filter, False)
        # @ keys should be preserved unchanged
        assert ir["@"] == {"xmlns": "http://example.com"}

    def test_transparent_container_traversal(self) -> None:
        rule = StubRule("ipv4addr")
        schema = self._make_schema()
        ir = {
            "interfaces": {
                "interface": [
                    {
                        "name": "lo0",
                        "unit": [
                            {
                                "name": "0",
                                "family": {
                                    "inet": {
                                        "address": [{"name": "192.168.1.1/32"}],
                                    },
                                },
                            },
                        ],
                    },
                ],
            },
        }
        path_filter = PathFilter()
        _walk_node(ir, schema, [], [rule], path_filter, False)
        addr = ir["interfaces"]["interface"][0]["unit"][0]["family"]["inet"]["address"][0]["name"]
        assert addr == "ANON_192.168.1.1/32"
