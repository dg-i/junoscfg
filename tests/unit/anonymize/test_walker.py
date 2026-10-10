"""Tests for the schema-guided anonymization walker.

Every test goes through ``walk``, the walker's door, against the bundled tree,
with test rules that decide on the schema node the walker hands them.
"""

from __future__ import annotations

from typing import Any

from junoscfg.anonymize import AnonymizeConfig, Rule, anonymize, walk

#: The types the bundled tree declares for the address leaves used below.
_ADDRESS_TYPES = frozenset({"ipaddr", "ipv4prefix"})


class StubRule(Rule):
    """Test rule that matches on the leaf's declared address type and marks values."""

    name = "stub"
    priority = 10

    def __init__(self, match_types: frozenset[str] = _ADDRESS_TYPES) -> None:
        self.match_types = match_types
        self.seen: list[str] = []

    def matches(self, value: Any, schema_node: dict[str, Any], path: list[str]) -> bool:
        return schema_node.get("atr", schema_node.get("tr")) in self.match_types

    def transform(self, value: str) -> str:
        self.seen.append(value)
        return f"ANON_{value}"

    def get_mapping(self) -> dict[str, str]:
        return {v: f"ANON_{v}" for v in self.seen}


def _walk(ir: dict[str, Any], *rules: Rule) -> dict[str, Any]:
    """Walk *ir*, wrapped as a configuration, with *rules*; return the configuration."""
    wrapped = {"configuration": ir}
    walk(wrapped, list(rules), AnonymizeConfig())
    return wrapped["configuration"]


def _address_ir(address: str, interface: str = "ge-0/0/0") -> dict[str, Any]:
    return {
        "interfaces": {
            "interface": [
                {
                    "name": interface,
                    "unit": [
                        {
                            "name": "0",
                            "family": {"inet": {"address": [{"name": address}]}},
                        },
                    ],
                },
            ],
        },
    }


def _address(ir: dict[str, Any]) -> str:
    return ir["interfaces"]["interface"][0]["unit"][0]["family"]["inet"]["address"][0]["name"]


class TestRulesAtALeaf:
    """Which rule the walker applies to a leaf it reaches."""

    def test_a_matching_rule_transforms_the_leaf(self) -> None:
        ir = _walk(_address_ir("10.1.2.3/24"), StubRule())
        assert _address(ir) == "ANON_10.1.2.3/24"

    def test_a_leaf_no_rule_matches_is_unchanged(self) -> None:
        ir = _walk({"system": {"host-name": "hello"}}, StubRule())
        assert ir == {"system": {"host-name": "hello"}}

    def test_the_first_matching_rule_wins(self) -> None:
        rule1 = StubRule()
        rule1.priority = 10
        rule2 = StubRule()
        rule2.priority = 20
        ir = _walk({"system": {"name-server": [{"name": "10.0.0.1"}]}}, rule1, rule2)
        assert ir["system"]["name-server"][0]["name"] == "ANON_10.0.0.1"
        assert len(rule1.seen) == 1
        assert len(rule2.seen) == 0


class TestTheWalkerTraversal:
    """The walker reaches every leaf the tree declares, through lists and containers."""

    def test_walks_leaf_with_matching_type(self) -> None:
        ir = _walk(_address_ir("10.1.2.3/24"), StubRule())
        # The IP address should have been transformed
        assert _address(ir) == "ANON_10.1.2.3/24"

    def test_walks_named_list(self) -> None:
        ir = _walk(
            {"system": {"name-server": [{"name": "8.8.8.8"}, {"name": "8.8.4.4"}]}},
            StubRule(),
        )
        assert ir["system"]["name-server"][0]["name"] == "ANON_8.8.8.8"
        assert ir["system"]["name-server"][1]["name"] == "ANON_8.8.4.4"

    def test_skips_non_matching_leaves(self) -> None:
        ir = _walk({"system": {"host-name": "router1"}}, StubRule())
        assert ir["system"]["host-name"] == "router1"

    def test_skips_attribute_keys(self) -> None:
        ir = _walk(
            {"@": {"xmlns": "http://example.com"}, "system": {"host-name": "router1"}},
            StubRule(),
        )
        # @ keys should be preserved unchanged
        assert ir["@"] == {"xmlns": "http://example.com"}

    def test_transparent_container_traversal(self) -> None:
        ir = _walk(_address_ir("192.168.1.1/32", interface="lo0"), StubRule())
        assert _address(ir) == "ANON_192.168.1.1/32"

    def test_an_unwrapped_ir_is_walked_from_the_configuration_root(self) -> None:
        """An IR without the ``configuration`` wrapper is walked as its content."""
        ir = {"system": {"name-server": [{"name": "10.0.0.1"}]}}
        walk(ir, [StubRule()], AnonymizeConfig())
        assert ir["system"]["name-server"][0]["name"] == "ANON_10.0.0.1"


class RecordingRule(Rule):
    """Sees every leaf the walker offers; matches none."""

    name = "recording"
    priority = 1

    def __init__(self) -> None:
        self.seen: list[tuple[str, dict[str, Any], tuple[str, ...]]] = []

    def matches(self, value: Any, schema_node: dict[str, Any], path: list[str]) -> bool:
        self.seen.append((value, schema_node, tuple(path)))
        return False

    def transform(self, value: str) -> str:  # pragma: no cover - never matched
        return value


def _bundled_tree() -> dict[str, Any]:
    from junoscfg.display import load_schema_tree

    tree = load_schema_tree()
    assert tree is not None
    return tree


def _schema_at(*path: str) -> dict[str, Any]:
    current = _bundled_tree()
    for name in path:
        current = current["c"][name]
    return current


def _walked(ir: dict[str, Any]) -> RecordingRule:
    rule = RecordingRule()
    walk({"configuration": ir}, [rule], AnonymizeConfig())
    return rule


_FROM = ("policy-options", "policy-statement", "term", "from")


def _term(where: str, slot: str, entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy-options": {
            "policy-statement": [
                {"name": "SAMPLE-POLICY", "term": [{"name": "T1", where: {slot: [entry]}}]}
            ]
        }
    }


class TestKeyFieldsAreLeaves:
    """A list entry's key fields are the leaves the tree declares for them.

    Spec: ``openspec/specs/anonymization/keyed-entries`` (from the
    identifier-key-fields change). Through `walk` against the bundled tree,
    with a rule that records what it is asked and changes nothing.
    """

    def test_a_key_field_carries_the_trees_type(self) -> None:
        rule = _walked(
            _term(
                "from", "as-path-neighbors", {"list-type": "as-list", "list-name": "SAMPLE-AS-LIST"}
            )
        )
        declared = _schema_at(*_FROM, "as-path-neighbors")["c"]
        seen = {value: (schema, path) for value, schema, path in rule.seen}
        assert "SAMPLE-AS-LIST" in seen, "list-name was never offered to a rule"
        schema, path = seen["SAMPLE-AS-LIST"]
        assert schema is declared["list-name"]
        assert path[-2:] == ("as-path-neighbors", "list-name")

        rule = _walked(
            _term("from", "route-filter", {"address": "198.51.100.0/24", "exact": [None]})
        )
        seen = {value: schema for value, schema, _ in rule.seen}
        declared = _schema_at(*_FROM, "route-filter")["c"]["address"]
        assert seen["198.51.100.0/24"] is declared
        assert seen["198.51.100.0/24"].get("tr") == declared.get("tr")

    def test_a_key_choice_keyword_passes_unchanged(self) -> None:
        entry = {"address": "198.51.100.0/24", "exact": [None], "accept": [None]}
        community = {"add": [None], "community-name": "SAMPLE-COMM"}
        ir = _term("from", "route-filter", entry)
        ir["policy-options"]["policy-statement"][0]["term"][0]["then"] = {"community": [community]}
        config = AnonymizeConfig(
            ips=True,
            passwords=True,
            communities=True,
            ssh_keys=True,
            identities=True,
            groups=True,
            descriptions=True,
            as_numbers=[64496],
            salt="s",
        )
        result = anonymize({"configuration": ir}, config)
        term = result.ir["configuration"]["policy-options"]["policy-statement"][0]["term"][0]
        anonymized = term["from"]["route-filter"][0]
        assert anonymized["exact"] == [None] and anonymized["accept"] == [None]
        assert list(anonymized) == ["address", "exact", "accept"]
        assert term["then"]["community"][0]["add"] == [None]
        assert list(term["then"]["community"][0]) == ["add", "community-name"]
        # The keywords are no leaves, so no rule is offered them.
        rule = _walked(_term("from", "route-filter", entry))
        assert [v for v, _, p in rule.seen if p[-1] in ("exact", "accept")] == []
        assert "198.51.100.0/24" in [v for v, _, _ in rule.seen]

    def test_no_name_leaf_is_synthesised(self) -> None:
        rule = _walked({"policy-options": {"policy-statement": [{"name": "SAMPLE-POLICY"}]}})
        declared = _schema_at("policy-options", "policy-statement")
        offered = [schema for value, schema, _ in rule.seen if value == "SAMPLE-POLICY"]
        assert len(offered) == 1
        assert offered[0] is declared["c"]["name"], "a leaf built from the list node"

    def test_an_enum_key_passes_unchanged(self) -> None:
        ir = _term(
            "from",
            "as-path-neighbors",
            {"list-type": "as-list-group", "list-name": "SAMPLE-AS-LIST"},
        )
        rule = _walked(ir)
        offered = {value: schema for value, schema, _ in rule.seen}
        assert "as-list-group" in offered, "list-type was never offered to a rule"
        enums = _bundled_tree()["_enums"][offered["as-list-group"]["e"]]
        assert enums == ["as-list", "as-list-group"]

        config = AnonymizeConfig(
            ips=True,
            passwords=True,
            communities=True,
            identities=True,
            groups=True,
            descriptions=True,
            as_numbers=[64496],
            sensitive_words=["as-list"],
            salt="s",
        )
        result = anonymize({"configuration": ir}, config)
        entry = result.ir["configuration"]["policy-options"]["policy-statement"][0]["term"][0][
            "from"
        ]["as-path-neighbors"][0]
        assert entry["list-type"] == "as-list-group"
        assert set(entry) == {"list-type", "list-name"}
