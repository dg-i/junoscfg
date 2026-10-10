"""Tests for edityaml path walker."""

from __future__ import annotations

from junoscfg.edityaml.path_walker import _parse_path, resolve_path, resolve_path_with_context


class TestParsePath:
    def test_simple_dotted(self) -> None:
        result = _parse_path("a.b.c")
        assert result == [("a", "key"), ("b", "key"), ("c", "key")]

    def test_wildcard_segment(self) -> None:
        result = _parse_path("a.b[*].c")
        assert result == [("a", "key"), ("b", "list"), ("c", "key")]

    def test_multiple_wildcards(self) -> None:
        result = _parse_path("a[*].b[*].c")
        assert result == [("a", "list"), ("b", "list"), ("c", "key")]

    def test_single_segment(self) -> None:
        result = _parse_path("root")
        assert result == [("root", "key")]

    def test_trailing_wildcard(self) -> None:
        result = _parse_path("a.items[*]")
        assert result == [("a", "key"), ("items", "list")]

    def test_dict_wildcard(self) -> None:
        result = _parse_path("family.*.address[*]")
        assert result == [("family", "key"), ("", "dict"), ("address", "list")]

    def test_dict_wildcard_standalone(self) -> None:
        result = _parse_path("*")
        assert result == [("", "dict")]

    def test_named_match(self) -> None:
        result = _parse_path("groups[ansible-managed].interfaces")
        assert result == [("groups", "match:ansible-managed"), ("interfaces", "key")]

    def test_named_match_simple(self) -> None:
        result = _parse_path("items[foo]")
        assert result == [("items", "match:foo")]

    def test_glob_bracket(self) -> None:
        result = _parse_path("groups[ansible-*].interfaces")
        assert result == [("groups", "glob:ansible-*"), ("interfaces", "key")]

    def test_glob_dict_key(self) -> None:
        result = _parse_path("family.inet*.address[*]")
        assert result == [("family", "key"), ("inet*", "dictglob"), ("address", "list")]

    def test_glob_dict_key_standalone(self) -> None:
        result = _parse_path("inet*")
        assert result == [("inet*", "dictglob")]


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


class TestResolvePathWithContext:
    def test_single_list_wildcard_uses_name(self) -> None:
        data = {"items": [{"name": "alpha", "val": 1}, {"name": "beta", "val": 2}]}
        result = resolve_path_with_context(data, "items[*]", leaf_key="val")
        assert len(result) == 2
        assert result[0] == ({"name": "alpha", "val": 1}, ["alpha"])
        assert result[1] == ({"name": "beta", "val": 2}, ["beta"])

    def test_terminal_list_with_leaf_name_uses_index(self) -> None:
        """When leaf_key is 'name' and this is the last [*], use list index."""
        data = {"items": [{"name": "10.0.0.1/30"}, {"name": "10.0.0.5/30"}]}
        result = resolve_path_with_context(data, "items[*]", leaf_key="name")
        assert len(result) == 2
        assert result[0] == ({"name": "10.0.0.1/30"}, ["0"])
        assert result[1] == ({"name": "10.0.0.5/30"}, ["1"])

    def test_dict_wildcard_uses_key_name(self) -> None:
        data = {
            "family": {
                "inet": {"address": [{"name": "10.0.0.1/30"}]},
                "inet6": {"address": [{"name": "2001:db8::1/64"}]},
            }
        }
        result = resolve_path_with_context(data, "family.*.address[*]", leaf_key="name")
        assert len(result) == 2
        # Dict wildcard contributes the key name as discriminator
        # Terminal list with leaf=name uses index
        nodes = {r[0]["name"]: r[1] for r in result}
        assert nodes["10.0.0.1/30"] == ["inet", "0"]
        assert nodes["2001:db8::1/64"] == ["inet6", "0"]

    def test_nested_lists_with_dict_wildcard(self) -> None:
        """Full interface path: interface[*].unit[*].family.*.address[*]"""
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
        result = resolve_path_with_context(
            data, "interface[*].unit[*].family.*.address[*]", leaf_key="name"
        )
        assert len(result) == 1
        node, discs = result[0]
        assert node["name"] == "10.0.0.1/30"
        # interface uses name, unit uses name, family uses dict key, address uses index
        assert discs == ["xe-0/0/0", "100", "inet", "0"]

    def test_non_terminal_list_with_leaf_name_uses_name(self) -> None:
        """When leaf_key is 'name' but this is NOT the last [*], use item['name']."""
        data = {
            "groups": [
                {"name": "g1", "items": [{"name": "i1"}]},
            ]
        }
        result = resolve_path_with_context(data, "groups[*].items[*]", leaf_key="name")
        assert len(result) == 1
        node, discs = result[0]
        assert node["name"] == "i1"
        # groups[*] is non-terminal -> uses name "g1"
        # items[*] is terminal with leaf=name -> uses index "0"
        assert discs == ["g1", "0"]

    def test_empty_result(self) -> None:
        data = {"a": {"b": 1}}
        result = resolve_path_with_context(data, "a.c[*]", leaf_key="name")
        assert result == []

    def test_glob_bracket_adds_discriminator(self) -> None:
        """Glob bracket [pattern*] adds name as discriminator (it's a wildcard)."""
        data = {
            "groups": [
                {"name": "ansible-managed", "items": [{"name": "10.0.0.1"}]},
                {"name": "ansible-testing", "items": [{"name": "10.0.0.2"}]},
            ]
        }
        result = resolve_path_with_context(data, "groups[ansible-*].items[*]", leaf_key="name")
        assert len(result) == 2
        nodes = {r[0]["name"]: r[1] for r in result}
        assert nodes["10.0.0.1"] == ["ansible-managed", "0"]
        assert nodes["10.0.0.2"] == ["ansible-testing", "0"]

    def test_glob_dict_key_adds_discriminator(self) -> None:
        """Dict key glob (inet*) adds matching key as discriminator."""
        data = {
            "family": {
                "inet": {"address": [{"name": "10.0.0.1/30"}]},
                "inet6": {"address": [{"name": "2001:db8::1/64"}]},
            }
        }
        result = resolve_path_with_context(data, "family.inet*.address[*]", leaf_key="name")
        assert len(result) == 2
        nodes = {r[0]["name"]: r[1] for r in result}
        assert nodes["10.0.0.1/30"] == ["inet", "0"]
        assert nodes["2001:db8::1/64"] == ["inet6", "0"]

    def test_named_match_no_discriminator(self) -> None:
        """Named match [value] does not add a discriminator (it's a fixed filter)."""
        data = {
            "groups": [
                {
                    "name": "ansible-managed",
                    "items": [{"name": "10.0.0.1"}],
                },
            ]
        }
        result = resolve_path_with_context(
            data, "groups[ansible-managed].items[*]", leaf_key="name"
        )
        assert len(result) == 1
        node, discs = result[0]
        assert node["name"] == "10.0.0.1"
        # Named match doesn't contribute a discriminator — only [*] and * do
        assert discs == ["0"]
