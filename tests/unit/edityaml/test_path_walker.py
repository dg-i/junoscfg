"""Path syntax: which nodes a dot-separated path with wildcards selects.

resolve_path returns the dict nodes a path selects; ansibilize names each
extracted value after the wildcards it passed (the discriminators).
"""

from __future__ import annotations

from typing import Any

import pytest

from junoscfg.edityaml import ansibilize, resolve_path

# (id, path, data, the nodes selected) for each segment kind. A plain key,
# ``*`` before a list, ``[name]`` and ``inet*`` before a list are in
# TestResolvePath.
SEGMENT_CASES: list[tuple[str, str, dict[str, Any], list[dict[str, Any]]]] = [
    (
        "wildcard-segment",
        "a.b[*].c",
        {"a": {"b": [{"c": {"x": 1}}, {"c": {"x": 2}}, {"d": {"x": 3}}]}},
        [{"x": 1}, {"x": 2}],
    ),
    (
        "multiple-wildcards",
        "a[*].b[*].c",
        {"a": [{"b": [{"c": {"x": 1}}]}, {"b": [{"c": {"x": 2}}, {"c": {"x": 3}}]}]},
        [{"x": 1}, {"x": 2}, {"x": 3}],
    ),
    ("single-segment", "root", {"root": {"x": 1}, "other": {"x": 2}}, [{"x": 1}]),
    (
        "trailing-wildcard",
        "a.items[*]",
        {"a": {"items": [{"n": 1}, {"n": 2}]}},
        [{"n": 1}, {"n": 2}],
    ),
    (
        "dict-wildcard-standalone",
        "*",
        {"a": {"x": 1}, "b": {"y": 2}, "c": "a string"},
        [{"x": 1}, {"y": 2}],
    ),
    (
        "named-match-simple",
        "items[foo]",
        {"items": [{"name": "foo", "x": 1}, {"name": "bar", "x": 2}]},
        [{"name": "foo", "x": 1}],
    ),
    (
        "glob-bracket",
        "groups[ansible-*].interfaces",
        {
            "groups": [
                {"name": "ansible-managed", "interfaces": {"i": 1}},
                {"name": "ansible-testing", "interfaces": {"i": 2}},
                {"name": "other-group", "interfaces": {"i": 3}},
            ]
        },
        [{"i": 1}, {"i": 2}],
    ),
    (
        "glob-dict-key-standalone",
        "inet*",
        {"inet": {"x": 1}, "inet6": {"y": 2}, "mpls": {"z": 3}},
        [{"x": 1}, {"y": 2}],
    ),
]


class TestPathSyntax:
    @pytest.mark.parametrize(
        ("path", "data", "expected"),
        [case[1:] for case in SEGMENT_CASES],
        ids=[case[0] for case in SEGMENT_CASES],
    )
    def test_each_segment_kind_selects_its_nodes(
        self, path: str, data: dict[str, Any], expected: list[dict[str, Any]]
    ) -> None:
        assert resolve_path(data, path) == expected


class TestResolvePath:
    def test_simple_dict_path(self) -> None:
        data = {"a": {"b": {"c": {"x": 1}}}}
        result = resolve_path(data, "a.b.c")
        assert result == [{"x": 1}]

    def test_wildcard_iterates_list(self) -> None:
        data = {"items": [{"name": "a"}, {"name": "b"}]}
        result = resolve_path(data, "items[*]")
        assert result == [{"name": "a"}, {"name": "b"}]

    def test_nested_wildcard(self) -> None:
        data = {
            "groups": [
                {"members": [{"id": 1}, {"id": 2}]},
                {"members": [{"id": 3}]},
            ]
        }
        result = resolve_path(data, "groups[*].members[*]")
        assert result == [{"id": 1}, {"id": 2}, {"id": 3}]

    def test_dict_then_wildcard(self) -> None:
        data = {"config": {"interfaces": [{"name": "eth0"}, {"name": "eth1"}]}}
        result = resolve_path(data, "config.interfaces[*]")
        assert result == [{"name": "eth0"}, {"name": "eth1"}]

    def test_missing_key_returns_empty(self) -> None:
        data = {"a": {"b": 1}}
        result = resolve_path(data, "a.c.d")
        assert result == []

    def test_wildcard_on_non_list_returns_empty(self) -> None:
        data = {"a": {"b": "not a list"}}
        result = resolve_path(data, "a.b[*]")
        assert result == []

    def test_wildcard_skips_non_dict_items(self) -> None:
        data = {"items": [{"name": "a"}, "string_item", {"name": "b"}]}
        result = resolve_path(data, "items[*]")
        # Non-dict items in list are skipped
        assert result == [{"name": "a"}, {"name": "b"}]

    def test_real_world_bgp_path(self) -> None:
        data = {
            "configuration": {
                "protocols": {
                    "bgp": {
                        "group": [
                            {
                                "name": "overlay",
                                "neighbor": [
                                    {"name": "10.0.0.1", "description": "overlay: spine1"},
                                    {"name": "10.0.0.2", "description": "overlay: spine2"},
                                ],
                            }
                        ]
                    }
                }
            }
        }
        result = resolve_path(data, "configuration.protocols.bgp.group[*].neighbor[*]")
        assert len(result) == 2
        assert result[0]["description"] == "overlay: spine1"
        assert result[1]["description"] == "overlay: spine2"

    def test_path_ending_at_scalar_returns_empty(self) -> None:
        data = {"a": {"b": "scalar"}}
        result = resolve_path(data, "a.b")
        # b is a scalar, not a dict, so we can't return it as a mutable node
        assert result == []

    def test_empty_list_returns_empty(self) -> None:
        data = {"items": []}
        result = resolve_path(data, "items[*]")
        assert result == []

    def test_dict_wildcard_iterates_values(self) -> None:
        data = {
            "family": {
                "inet": {"address": [{"name": "10.0.0.1/30"}]},
                "inet6": {"address": [{"name": "2001:db8::1/64"}]},
            }
        }
        result = resolve_path(data, "family.*")
        assert len(result) == 2
        # Both inet and inet6 dicts are returned
        names = {r["address"][0]["name"] for r in result}
        assert names == {"10.0.0.1/30", "2001:db8::1/64"}

    def test_dict_wildcard_then_list(self) -> None:
        data = {
            "family": {
                "inet": {"address": [{"name": "10.0.0.1/30"}]},
                "inet6": {"address": [{"name": "2001:db8::1/64"}]},
            }
        }
        result = resolve_path(data, "family.*.address[*]")
        assert len(result) == 2
        names = {r["name"] for r in result}
        assert names == {"10.0.0.1/30", "2001:db8::1/64"}

    def test_dict_wildcard_skips_non_dict_values(self) -> None:
        data = {"family": {"inet": {"x": 1}, "description": "a string"}}
        result = resolve_path(data, "family.*")
        assert result == [{"x": 1}]

    def test_named_match_selects_by_name(self) -> None:
        data = {
            "groups": [
                {"name": "alpha", "x": 1},
                {"name": "beta", "x": 2},
            ]
        }
        result = resolve_path(data, "groups[beta]")
        assert result == [{"name": "beta", "x": 2}]

    def test_named_match_with_hyphen(self) -> None:
        data = {
            "groups": [
                {"name": "ansible-managed", "interfaces": {"interface": []}},
                {"name": "other-group", "interfaces": {"interface": []}},
            ]
        }
        result = resolve_path(data, "groups[ansible-managed].interfaces")
        assert len(result) == 1
        assert result[0] == {"interface": []}

    def test_named_match_no_match_returns_empty(self) -> None:
        data = {"groups": [{"name": "alpha"}, {"name": "beta"}]}
        result = resolve_path(data, "groups[gamma]")
        assert result == []

    def test_named_match_then_wildcard(self) -> None:
        data = {
            "groups": [
                {
                    "name": "ansible-managed",
                    "interfaces": {"interface": [{"name": "ge-0/0/0"}, {"name": "ge-0/0/1"}]},
                },
            ]
        }
        result = resolve_path(data, "groups[ansible-managed].interfaces.interface[*]")
        assert len(result) == 2
        assert result[0]["name"] == "ge-0/0/0"
        assert result[1]["name"] == "ge-0/0/1"

    def test_glob_bracket_matches_by_pattern(self) -> None:
        data = {
            "groups": [
                {"name": "ansible-managed", "x": 1},
                {"name": "ansible-testing", "x": 2},
                {"name": "other-group", "x": 3},
            ]
        }
        result = resolve_path(data, "groups[ansible-*]")
        assert len(result) == 2
        assert result[0]["x"] == 1
        assert result[1]["x"] == 2

    def test_glob_bracket_no_match(self) -> None:
        data = {"groups": [{"name": "alpha"}, {"name": "beta"}]}
        result = resolve_path(data, "groups[zzz-*]")
        assert result == []

    def test_glob_dict_key_matches_keys(self) -> None:
        data = {
            "family": {
                "inet": {"address": [{"name": "10.0.0.1/30"}]},
                "inet6": {"address": [{"name": "2001:db8::1/64"}]},
                "mpls": {"label": "foo"},
            }
        }
        result = resolve_path(data, "family.inet*")
        assert len(result) == 2
        names = {r["address"][0]["name"] for r in result}
        assert names == {"10.0.0.1/30", "2001:db8::1/64"}

    def test_glob_dict_key_then_list(self) -> None:
        data = {
            "family": {
                "inet": {"address": [{"name": "10.0.0.1/30"}]},
                "inet6": {"address": [{"name": "2001:db8::1/64"}]},
            }
        }
        result = resolve_path(data, "family.inet*.address[*]")
        assert len(result) == 2
        names = {r["name"] for r in result}
        assert names == {"10.0.0.1/30", "2001:db8::1/64"}

    def test_glob_dict_key_no_match(self) -> None:
        data = {"family": {"inet": {"x": 1}, "mpls": {"y": 2}}}
        result = resolve_path(data, "family.zzz*")
        assert result == []

    def test_glob_dict_key_skips_non_dict_values(self) -> None:
        data = {"family": {"inet": {"x": 1}, "inet6": "a string"}}
        result = resolve_path(data, "family.inet*")
        assert result == [{"x": 1}]


class TestDiscriminators:
    """Each wildcard a path passes adds one part to the variable name.

    ``[*]`` adds the item's ``name``, except the last ``[*]`` when the leaf is
    ``name`` itself, which adds the list index; ``*`` and ``inet*`` add the
    dict key, ``[glob*]`` the item's name; a ``[name]`` match is a fixed
    filter and adds nothing.
    """

    def test_single_list_wildcard_uses_name(self) -> None:
        data = {"items": [{"name": "alpha", "val": 1}, {"name": "beta", "val": 2}]}
        host_vars, _ = ansibilize(data, "items[*].val", "p")
        assert host_vars == {"p_alpha": 1, "p_beta": 2}

    def test_terminal_list_with_leaf_name_uses_index(self) -> None:
        """When the leaf is ``name`` and this is the last ``[*]``, the index is used."""
        data = {"items": [{"name": "10.0.0.1/30"}, {"name": "10.0.0.5/30"}]}
        host_vars, _ = ansibilize(data, "items[*].name", "p")
        assert host_vars == {"p_0": "10.0.0.1/30", "p_1": "10.0.0.5/30"}

    def test_dict_wildcard_uses_key_name(self) -> None:
        data = {
            "family": {
                "inet": {"address": [{"name": "10.0.0.1/30"}]},
                "inet6": {"address": [{"name": "2001:db8::1/64"}]},
            }
        }
        host_vars, _ = ansibilize(data, "family.*.address[*].name", "p")
        assert host_vars == {"p_inet_0": "10.0.0.1/30", "p_inet6_0": "2001:db8::1/64"}

    def test_nested_lists_with_dict_wildcard(self) -> None:
        """interface and unit add their names, family its key, address its index."""
        data = {
            "interface": [
                {
                    "name": "xe-0/0/0",
                    "unit": [
                        {
                            "name": "100",
                            "family": {"inet": {"address": [{"name": "10.0.0.1/30"}]}},
                        }
                    ],
                }
            ]
        }
        host_vars, _ = ansibilize(data, "interface[*].unit[*].family.*.address[*].name", "p")
        assert host_vars == {"p_xe_0_0_0_100_inet_0": "10.0.0.1/30"}

    def test_non_terminal_list_with_leaf_name_uses_name(self) -> None:
        """When the leaf is ``name`` but this is not the last ``[*]``, the name is used."""
        data = {"groups": [{"name": "g1", "items": [{"name": "i1"}]}]}
        host_vars, _ = ansibilize(data, "groups[*].items[*].name", "p")
        assert host_vars == {"p_g1_0": "i1"}

    def test_empty_result(self) -> None:
        data = {"a": {"b": 1}}
        host_vars, group_vars = ansibilize(data, "a.c[*].name", "p")
        assert host_vars == {}
        assert group_vars == data

    def test_glob_bracket_adds_discriminator(self) -> None:
        """``[pattern*]`` is a wildcard: it adds the item's name."""
        data = {
            "groups": [
                {"name": "ansible-managed", "items": [{"name": "10.0.0.1"}]},
                {"name": "ansible-testing", "items": [{"name": "10.0.0.2"}]},
            ]
        }
        host_vars, _ = ansibilize(data, "groups[ansible-*].items[*].name", "p")
        assert host_vars == {"p_ansible_managed_0": "10.0.0.1", "p_ansible_testing_0": "10.0.0.2"}

    def test_glob_dict_key_adds_discriminator(self) -> None:
        """``inet*`` adds the matching key."""
        data = {
            "family": {
                "inet": {"address": [{"name": "10.0.0.1/30"}]},
                "inet6": {"address": [{"name": "2001:db8::1/64"}]},
            }
        }
        host_vars, _ = ansibilize(data, "family.inet*.address[*].name", "p")
        assert host_vars == {"p_inet_0": "10.0.0.1/30", "p_inet6_0": "2001:db8::1/64"}

    def test_named_match_no_discriminator(self) -> None:
        """``[value]`` is a fixed filter: only the ``[*]`` adds a part."""
        data = {"groups": [{"name": "ansible-managed", "items": [{"name": "10.0.0.1"}]}]}
        host_vars, _ = ansibilize(data, "groups[ansible-managed].items[*].name", "p")
        assert host_vars == {"p_0": "10.0.0.1"}


class TestAWildcardSkipsTheRecordOfKeptStatements:
    """A level's record of kept statements (`junoscfg:unplaced`) is no
    configuration node: `*` and a glob segment pass it by, so a rule never
    writes into it a statement the writers would print verbatim
    (Test/Challenge F5, change kept-whole-statements)."""

    _DATA: dict[str, Any] = {
        "configuration": {
            "system": {
                "services": {"ssh": {"root-login": "deny"}},
                "junoscfg:unplaced": {"host-name": True},
            }
        }
    }

    @pytest.mark.parametrize("path", ["configuration.system.*", "configuration.system.junos*"])
    def test_the_record_is_not_selected(self, path: str) -> None:
        selected = resolve_path(self._DATA, path)
        assert {"host-name": True} not in selected
        if path.endswith("*") and not path.endswith("junos*"):
            assert selected == [{"ssh": {"root-login": "deny"}}]

    def test_a_static_rule_over_a_wildcard_leaves_the_record_alone(self) -> None:
        from junoscfg.edityaml import apply_rules

        ruleset = {
            "rules": [
                {
                    "path": "configuration.system.*",
                    "transforms": [{"type": "static", "target": "_new", "value": True}],
                }
            ]
        }
        result = apply_rules(self._DATA, ruleset)
        assert result["configuration"]["system"]["junoscfg:unplaced"] == {"host-name": True}
        assert result["configuration"]["system"]["services"]["_new"] is True
