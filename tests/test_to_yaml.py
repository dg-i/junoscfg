"""Tests for JSON/XML → standard YAML conversion."""

from __future__ import annotations

import json

import pytest
import yaml

from junoscfg import Format, convert_config
from junoscfg.display import xml_to_dict
from junoscfg.display.to_yaml import xml_to_yaml


def _convert_json_to_yaml(source: str) -> str:
    """Exercise the supported JSON-to-YAML conversion through its public door."""
    return convert_config(source, from_format=Format.JSON, to_format=Format.YAML)


class TestJsonToYamlBasic:
    """Basic JSON → YAML transformations (1:1 structural mapping)."""

    def test_simple_container(self) -> None:
        j = json.dumps({"configuration": {"system": {"host-name": "test"}}})
        result = yaml.safe_load(_convert_json_to_yaml(j))
        assert result == {"configuration": {"system": {"host-name": "test"}}}

    def test_named_entries_preserved_as_arrays(self) -> None:
        """Arrays with 'name' field stay as arrays (not dict-keyed)."""
        j = json.dumps(
            {"configuration": {"interfaces": {"interface": [{"name": "ae0", "mtu": 9216}]}}}
        )
        result = yaml.safe_load(_convert_json_to_yaml(j))
        assert result == {
            "configuration": {"interfaces": {"interface": [{"name": "ae0", "mtu": 9216}]}}
        }

    def test_null_presence_preserved(self) -> None:
        """[null] stays as [null] (not converted to true)."""
        j = json.dumps({"configuration": {"system": {"management-instance": [None]}}})
        result = yaml.safe_load(_convert_json_to_yaml(j))
        assert result == {"configuration": {"system": {"management-instance": [None]}}}

    def test_single_element_array_preserved(self) -> None:
        """Single-element arrays stay as arrays (not unwrapped)."""
        j = json.dumps({"configuration": {"system": {"name-server": ["8.8.8.8"]}}})
        result = yaml.safe_load(_convert_json_to_yaml(j))
        assert result["configuration"]["system"]["name-server"] == ["8.8.8.8"]

    def test_multi_element_array_preserved(self) -> None:
        """Multi-element arrays stay as lists."""
        j = json.dumps(
            {
                "configuration": {
                    "system": {
                        "login": {"class": [{"name": "FOO", "permissions": ["access", "admin"]}]}
                    }
                }
            }
        )
        result = yaml.safe_load(_convert_json_to_yaml(j))
        assert result["configuration"]["system"]["login"]["class"][0]["permissions"] == [
            "access",
            "admin",
        ]

    def test_configuration_wrapper_preserved(self) -> None:
        """The 'configuration' key is preserved in output."""
        j = json.dumps({"configuration": {"system": {"host-name": "test"}}})
        result = yaml.safe_load(_convert_json_to_yaml(j))
        assert "configuration" in result


class TestJsonToYamlAttributes:
    """JSON @ attributes preserved in standard YAML."""

    def test_at_attributes_preserved(self) -> None:
        """@ keys are preserved as-is."""
        j = json.dumps(
            {
                "configuration": {
                    "@": {"junos:changed-seconds": "12345"},
                    "system": {"host-name": "test"},
                }
            }
        )
        result = yaml.safe_load(_convert_json_to_yaml(j))
        assert result["configuration"]["@"] == {"junos:changed-seconds": "12345"}

    def test_inactive_attribute_preserved(self) -> None:
        """@ inactive stays as @ (not converted to _inactive)."""
        j = json.dumps(
            {
                "configuration": {
                    "system": {
                        "host-name": "test",
                        "@": {"inactive": True},
                    }
                }
            }
        )
        result = yaml.safe_load(_convert_json_to_yaml(j))
        assert result["configuration"]["system"]["@"] == {"inactive": True}
        assert result["configuration"]["system"]["host-name"] == "test"

    def test_leaf_inactive_attribute_preserved(self) -> None:
        """@key inactive attributes stay as-is."""
        j = json.dumps(
            {
                "configuration": {
                    "system": {
                        "host-name": "test",
                        "@host-name": {"inactive": True},
                    }
                }
            }
        )
        result = yaml.safe_load(_convert_json_to_yaml(j))
        assert result["configuration"]["system"]["@host-name"] == {"inactive": True}


class TestJsonToYamlFlatEntries:
    """Flat entries preserved as-is in standard YAML."""

    def test_route_filter_preserved(self) -> None:
        j = json.dumps(
            {
                "configuration": {
                    "policy-options": {
                        "policy-statement": [
                            {
                                "name": "test",
                                "term": [
                                    {
                                        "name": "t1",
                                        "from": {
                                            "route-filter": [
                                                {"address": "10.0.0.0/8", "exact": [None]}
                                            ]
                                        },
                                    }
                                ],
                            }
                        ],
                    }
                }
            }
        )
        result = yaml.safe_load(_convert_json_to_yaml(j))
        rf = result["configuration"]["policy-options"]["policy-statement"][0]["term"][0]["from"][
            "route-filter"
        ]
        assert isinstance(rf, list)
        assert rf[0]["address"] == "10.0.0.0/8"
        assert rf[0]["exact"] == [None]

    def test_leaf_lists_preserved(self) -> None:
        j = json.dumps(
            {
                "configuration": {
                    "system": {
                        "login": {
                            "class": [
                                {
                                    "name": "FOO",
                                    "permissions": ["access", "admin"],
                                }
                            ]
                        }
                    }
                }
            }
        )
        result = yaml.safe_load(_convert_json_to_yaml(j))
        assert result["configuration"]["system"]["login"]["class"][0]["permissions"] == [
            "access",
            "admin",
        ]


class TestJsonToYamlRoundtrip:
    """JSON → YAML → JSON should be lossless (exact match)."""

    def test_lossless_roundtrip(self) -> None:
        original = {
            "configuration": {
                "system": {"host-name": "r1", "domain-name": "example.com"},
                "interfaces": {
                    "interface": [
                        {
                            "name": "ae0",
                            "mtu": 9216,
                            "unit": [
                                {
                                    "name": "0",
                                    "family": {"inet": {"address": [{"name": "10.0.0.1/24"}]}},
                                }
                            ],
                        }
                    ]
                },
            }
        }
        j = json.dumps(original)
        yaml_output = _convert_json_to_yaml(j)
        roundtrip = yaml.safe_load(yaml_output)
        assert roundtrip == original

    def test_json_yaml_set_match(self) -> None:
        """JSON → YAML → set produces same output as JSON → set."""
        j = json.dumps(
            {
                "configuration": {
                    "system": {"host-name": "r1", "domain-name": "example.com"},
                    "interfaces": {
                        "interface": [
                            {
                                "name": "ae0",
                                "mtu": 9216,
                                "unit": [
                                    {
                                        "name": "0",
                                        "family": {"inet": {"address": [{"name": "10.0.0.1/24"}]}},
                                    }
                                ],
                            }
                        ]
                    },
                }
            }
        )
        yaml_output = _convert_json_to_yaml(j)
        yaml_set = convert_config(yaml_output, from_format=Format.YAML, to_format=Format.SET)
        json_set = convert_config(j, from_format=Format.JSON, to_format=Format.SET)

        assert set(yaml_set.strip().splitlines()) == set(json_set.strip().splitlines())


class TestXmlToYamlBasic:
    """XML → YAML transformations (produces Junos JSON-equivalent structure)."""

    def test_package_door_dict_matches_yaml_mapping(self) -> None:
        xml = "<configuration><system><host-name>router1</host-name></system></configuration>"
        assert xml_to_dict(xml) == yaml.safe_load(xml_to_yaml(xml))

    def test_simple_elements(self) -> None:
        xml = "<configuration><system><host-name>test</host-name></system></configuration>"
        result = yaml.safe_load(xml_to_yaml(xml))
        assert result == {"configuration": {"system": {"host-name": "test"}}}

    def test_named_entries_as_arrays(self) -> None:
        """Named entries become arrays with name field (Junos JSON style)."""
        xml = """<configuration>
            <interfaces>
                <interface>
                    <name>ae0</name>
                    <mtu>9216</mtu>
                </interface>
            </interfaces>
        </configuration>"""
        result = yaml.safe_load(xml_to_yaml(xml))
        iface = result["configuration"]["interfaces"]["interface"]
        assert isinstance(iface, list)
        assert len(iface) == 1
        assert iface[0]["name"] == "ae0"
        assert iface[0]["mtu"] == "9216"  # the IR is string-valued in every path

    def test_inactive_attribute_becomes_at_key(self) -> None:
        """inactive XML attribute becomes @ key with inactive: true."""
        xml = """<configuration>
            <system inactive="inactive">
                <host-name>test</host-name>
            </system>
        </configuration>"""
        result = yaml.safe_load(xml_to_yaml(xml))
        assert result["configuration"]["system"]["@"] == {"inactive": True}
        assert result["configuration"]["system"]["host-name"] == "test"

    def test_empty_element_is_null_list(self) -> None:
        """Empty XML element becomes [null] (presence marker)."""
        xml = """<configuration>
            <system><management-instance/></system>
        </configuration>"""
        result = yaml.safe_load(xml_to_yaml(xml))
        assert result["configuration"]["system"]["management-instance"] == [None]

    def test_multiple_same_tag_siblings(self) -> None:
        """Multiple same-tag siblings → array of dicts."""
        xml = """<configuration>
            <interfaces>
                <interface><name>ae0</name><mtu>9216</mtu></interface>
                <interface><name>ge-0/0/0</name><description>uplink</description></interface>
            </interfaces>
        </configuration>"""
        result = yaml.safe_load(xml_to_yaml(xml))
        ifaces = result["configuration"]["interfaces"]["interface"]
        assert isinstance(ifaces, list)
        assert len(ifaces) == 2
        assert ifaces[0]["name"] == "ae0"
        assert ifaces[0]["mtu"] == "9216"
        assert ifaces[1]["name"] == "ge-0/0/0"
        assert ifaces[1]["description"] == "uplink"


class TestLazyXmlImport:
    """Verify lxml is lazily imported — not loaded until XML features are used."""

    def test_json_to_yaml_pipeline_without_lxml(self) -> None:
        """Public JSON-to-YAML conversion does not require the XML dependency."""
        # to_yaml module should be importable; lxml may be in sys.modules
        # from other tests, but the key check is that the public conversion
        # pipeline itself doesn't fail
        j = json.dumps({"configuration": {"system": {"host-name": "test"}}})
        result = yaml.safe_load(_convert_json_to_yaml(j))
        assert result["configuration"]["system"]["host-name"] == "test"

    def test_filter_yaml_by_path_without_lxml(self) -> None:
        """filter_yaml_by_path works without lxml — it only uses PyYAML."""
        from junoscfg.display.to_yaml import filter_yaml_by_path

        yaml_text = yaml.dump({"configuration": {"system": {"host-name": "r1"}}})
        result = filter_yaml_by_path(yaml_text, ["system"])
        parsed = yaml.safe_load(result)
        assert parsed["configuration"]["system"]["host-name"] == "r1"

    def test_xml_to_yaml_requires_lxml(self) -> None:
        """xml_to_yaml uses lxml and works when lxml is available."""
        xml = "<configuration><system><host-name>r1</host-name></system></configuration>"
        result = yaml.safe_load(xml_to_yaml(xml))
        assert result["configuration"]["system"]["host-name"] == "r1"

    def test_to_yaml_module_level_has_no_lxml(self) -> None:
        """The to_yaml module does not import lxml at the top level."""
        import ast
        import inspect

        import junoscfg.display.to_yaml as mod

        source = inspect.getsource(mod)
        tree = ast.parse(source)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                else:
                    names = [node.module or ""]
                for name in names:
                    assert "lxml" not in name, f"lxml imported at module level (line {node.lineno})"

    """XML → YAML → set produces same output as XML → set."""

    def test_simple_roundtrip(self) -> None:
        from junoscfg import Format, convert_config

        xml = """<configuration>
            <system>
                <host-name>r1</host-name>
                <domain-name>example.com</domain-name>
            </system>
            <interfaces>
                <interface>
                    <name>ae0</name>
                    <mtu>9216</mtu>
                </interface>
            </interfaces>
        </configuration>"""

        yaml_output = xml_to_yaml(xml)
        yaml_set = convert_config(yaml_output, from_format=Format.YAML, to_format=Format.SET)
        xml_set = convert_config(xml, from_format=Format.XML, to_format=Format.SET)

        assert set(yaml_set.strip().splitlines()) == set(xml_set.strip().splitlines())


class TestInvalidXmlIsReported:
    """Bad XML is an error, not a traceback.

    A device renders `show configuration | display xml` inside an `<rpc-reply>`
    carrying the `junos:` namespace declaration, and the `<configuration>`
    element inside uses that prefix for its commit attributes. Pasting the
    inner element on its own — an ordinary thing to do — leaves the prefix
    undeclared. lxml raised straight through the CLI as a stack trace, where
    malformed JSON and malformed XML both reported an error and exited 2.
    """

    def test_an_undeclared_namespace_prefix_is_an_error(self) -> None:
        inner = (
            '<configuration junos:commit-user="x">'
            "<chassis><dump-on-panic/></chassis></configuration>"
        )
        with pytest.raises(ValueError, match="Invalid XML"):
            xml_to_yaml(inner)

    def test_the_same_element_inside_its_rpc_reply_converts(self) -> None:
        """The namespace is declared on the parent, which is how a device sends it."""
        full = (
            '<rpc-reply xmlns:junos="http://xml.juniper.net/junos/23.2R2/junos">'
            '<configuration junos:commit-user="x">'
            "<chassis><undocumented><dump-on-panic/></undocumented></chassis>"
            "</configuration></rpc-reply>"
        )
        assert "dump-on-panic" in xml_to_yaml(full)


# ── identifier-key-fields: a lone XML entry takes its shape from the tree ──
#
# Spec: openspec/changes/identifier-key-fields/specs/conversion/entry-keys.
# One `<as-path-neighbors>` has no `<name>` child, so the walker's heuristic
# made it a dict where the device's JSON holds a one-entry list.

_XML_TERM = (
    '<rpc-reply xmlns:junos="http://xml.juniper.net/junos/23.2R2/junos">'
    '<configuration junos:changed-seconds="1759900000" '
    'junos:changed-localtime="2026-10-08 09:00:00 UTC">'
    "<policy-options><policy-statement><name>SAMPLE-POLICY</name>"
    "<term><name>T1</name>{body}</term>"
    "</policy-statement></policy-options></configuration></rpc-reply>"
)


class TestLoneEntryFollowsTheTree:
    LONE = {
        "as-path-neighbors": (
            '<from><as-path-neighbors junos:changed-seconds="1759900000">'
            "<list-type>as-list</list-type><list-name>SAMPLE-AS-LIST</list-name>"
            "</as-path-neighbors></from>",
            ("from", "as-path-neighbors"),
            {"list-type": "as-list", "list-name": "SAMPLE-AS-LIST"},
        ),
        "as-path-transits": (
            "<from><as-path-transits>"
            "<list-type>as-list-group</list-type><list-name>SAMPLE-ASG</list-name>"
            "</as-path-transits></from>",
            ("from", "as-path-transits"),
            {"list-type": "as-list-group", "list-name": "SAMPLE-ASG"},
        ),
        "route-filter": (
            "<from><route-filter><address>198.51.100.0/24</address><exact/><accept/>"
            "</route-filter></from>",
            ("from", "route-filter"),
            {"address": "198.51.100.0/24", "exact": [None], "accept": [None]},
        ),
        "community": (
            "<then><community><add/><community-name>SAMPLE-COMM</community-name>"
            "</community></then>",
            ("then", "community"),
            {"add": [None], "community-name": "SAMPLE-COMM"},
        ),
    }

    @pytest.mark.parametrize("slot", list(LONE))
    def test_a_lone_keyed_entry_is_a_list(self, slot: str) -> None:
        body, (where, key), entry = self.LONE[slot]
        xml = _XML_TERM.format(body=body)
        for got in (
            xml_to_dict(xml)["configuration"],
            json.loads(
                convert_config(xml, from_format=Format.XML, to_format=Format.JSON, validate=False)
            )["configuration"],
        ):
            term = got["policy-options"]["policy-statement"][0]["term"][0]
            assert term[where][key] == [entry], slot

    def test_a_lone_attributes_match_is_a_list(self) -> None:
        xml = (
            "<configuration><event-options><policy><name>SAMPLE-EVENT-POLICY</name>"
            "<attributes-match><from-event-attribute>ping.test-owner</from-event-attribute>"
            "<condition>matches</condition>"
            "<to-event-attribute-value>^uptime$</to-event-attribute-value>"
            "</attributes-match></policy></event-options></configuration>"
        )
        got = xml_to_dict(xml)["configuration"]["event-options"]["policy"][0]
        assert got["attributes-match"] == [
            {
                "from-event-attribute": "ping.test-owner",
                "condition": "matches",
                "to-event-attribute-value": "^uptime$",
            }
        ]

    def test_an_element_outside_the_tree_keeps_the_name_heuristic(self) -> None:
        """Pinned as it is: where the tree does not reach, a `<name>` child
        still makes a list and its absence a container."""
        got = xml_to_dict(
            "<configuration><unknown-thing><name>x</name><v>1</v></unknown-thing>"
            "<other-thing><v>1</v></other-thing><system><host-name>r1</host-name></system>"
            "</configuration>"
        )["configuration"]
        assert got == {
            "unknown-thing": [{"name": "x", "v": "1"}],
            "other-thing": {"v": "1"},
            "system": {"host-name": "r1"},
        }


class TestInactiveLeaf:
    """A tag on a leaf marks the leaf, never a value of it.

    The CLI rejects `deactivate policy-options community C1 members 64496:2`
    and accepts `… members`, after which the device's XML tags every
    `<members>` element and its JSON writes one `"@members"` (23.2R2).
    """

    @staticmethod
    def _community(members: str) -> dict:
        return xml_to_dict(
            "<configuration><policy-options><community><name>C1</name>"
            f"{members}</community></policy-options></configuration>"
        )["configuration"]["policy-options"]["community"][0]

    def test_an_inactive_leaf_list_takes_one_marker(self) -> None:
        community = self._community(
            '<members inactive="inactive">64496:1</members>'
            '<members inactive="inactive">64496:2</members>'
        )
        assert community == {
            "name": "C1",
            "members": ["64496:1", "64496:2"],
            "@members": {"inactive": True},
        }

    def test_a_partly_inactive_leaf_list_is_refused(self) -> None:
        with pytest.raises(ValueError, match="members"):
            self._community(
                '<members>64496:1</members><members inactive="inactive">64496:2</members>'
            )

    def test_an_inactive_presence_flag_matches_set_input(self) -> None:
        xml = xml_to_dict(
            '<configuration><system><no-redirects inactive="inactive"/></system></configuration>'
        )["configuration"]["system"]
        from_set = json.loads(
            convert_config(
                "set system no-redirects\ndeactivate system no-redirects\n",
                from_format=Format.SET,
                to_format=Format.JSON,
            )
        )["configuration"]["system"]
        assert xml == from_set == {"no-redirects": [None], "@no-redirects": {"inactive": True}}
