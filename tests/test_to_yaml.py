"""Tests for JSON/XML → standard YAML conversion."""

from __future__ import annotations

import json

import yaml

from junoscfg.display.to_yaml import json_to_yaml, xml_to_yaml


class TestJsonToYamlBasic:
    """Basic JSON → YAML transformations (1:1 structural mapping)."""

    def test_simple_container(self) -> None:
        j = json.dumps({"configuration": {"system": {"host-name": "test"}}})
        result = yaml.safe_load(json_to_yaml(j))
        assert result == {"configuration": {"system": {"host-name": "test"}}}

    def test_named_entries_preserved_as_arrays(self) -> None:
        """Arrays with 'name' field stay as arrays (not dict-keyed)."""
        j = json.dumps(
            {"configuration": {"interfaces": {"interface": [{"name": "ae0", "mtu": 9216}]}}}
        )
        result = yaml.safe_load(json_to_yaml(j))
        assert result == {
            "configuration": {"interfaces": {"interface": [{"name": "ae0", "mtu": 9216}]}}
        }

    def test_null_presence_preserved(self) -> None:
        """[null] stays as [null] (not converted to true)."""
        j = json.dumps({"configuration": {"system": {"management-instance": [None]}}})
        result = yaml.safe_load(json_to_yaml(j))
        assert result == {"configuration": {"system": {"management-instance": [None]}}}

    def test_single_element_array_preserved(self) -> None:
        """Single-element arrays stay as arrays (not unwrapped)."""
        j = json.dumps({"configuration": {"system": {"name-server": ["8.8.8.8"]}}})
        result = yaml.safe_load(json_to_yaml(j))
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
        result = yaml.safe_load(json_to_yaml(j))
        assert result["configuration"]["system"]["login"]["class"][0]["permissions"] == [
            "access",
            "admin",
        ]

    def test_empty_json_returns_empty(self) -> None:
        assert json_to_yaml("{}") == ""

    def test_configuration_wrapper_preserved(self) -> None:
        """The 'configuration' key is preserved in output."""
        j = json.dumps({"configuration": {"system": {"host-name": "test"}}})
        result = yaml.safe_load(json_to_yaml(j))
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
        result = yaml.safe_load(json_to_yaml(j))
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
        result = yaml.safe_load(json_to_yaml(j))
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
        result = yaml.safe_load(json_to_yaml(j))
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
        result = yaml.safe_load(json_to_yaml(j))
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
        result = yaml.safe_load(json_to_yaml(j))
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
        yaml_output = json_to_yaml(j)
        roundtrip = yaml.safe_load(yaml_output)
        assert roundtrip == original

    def test_json_yaml_set_match(self) -> None:
        """JSON → YAML → set produces same output as JSON → set."""
        from junoscfg import Format, convert_config

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
        yaml_output = json_to_yaml(j)
        yaml_set = convert_config(yaml_output, from_format=Format.YAML, to_format=Format.SET)
        json_set = convert_config(j, from_format=Format.JSON, to_format=Format.SET)

        assert set(yaml_set.strip().splitlines()) == set(json_set.strip().splitlines())


class TestXmlToYamlBasic:
    """XML → YAML transformations (produces Junos JSON-equivalent structure)."""

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
        assert iface[0]["mtu"] == 9216

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
        assert ifaces[0]["mtu"] == 9216
        assert ifaces[1]["name"] == "ge-0/0/0"
        assert ifaces[1]["description"] == "uplink"


class TestLazyXmlImport:
    """Verify lxml is lazily imported — not loaded until XML features are used."""

    def test_json_to_yaml_without_lxml(self) -> None:
        """json_to_yaml works without lxml being imported at module level."""
        # to_yaml module should be importable; lxml may be in sys.modules
        # from other tests, but the key check is that json_to_yaml itself
        # doesn't fail
        j = json.dumps({"configuration": {"system": {"host-name": "test"}}})
        result = yaml.safe_load(json_to_yaml(j))
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
                    assert "lxml" not in name, (
                        f"lxml imported at module level (line {node.lineno})"
                    )



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
