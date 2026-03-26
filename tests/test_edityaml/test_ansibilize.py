"""Tests for edityaml ansibilize module."""

from __future__ import annotations

import pytest
import yaml

from junoscfg.edityaml.ansibilize import (
    ansibilize,
    ansibilize_multi,
    ansibilize_with_offset,
    detect_value_type,
    format_output,
    format_output_with_offset,
    generate_var_name,
    make_offset_expression,
    sanitize_var_component,
    split_leaf_from_path,
)


class TestSanitizeVarComponent:
    def test_simple_lowercase(self) -> None:
        assert sanitize_var_component("hello") == "hello"

    def test_uppercase_to_lower(self) -> None:
        assert sanitize_var_component("Hello") == "hello"

    def test_special_chars_to_underscore(self) -> None:
        assert sanitize_var_component("xe-0/0/0") == "xe_0_0_0"

    def test_colons_and_slashes(self) -> None:
        assert sanitize_var_component("2001:db8::1/64") == "2001_db8_1_64"

    def test_collapse_multiple_underscores(self) -> None:
        assert sanitize_var_component("a--b//c") == "a_b_c"

    def test_strip_edge_underscores(self) -> None:
        assert sanitize_var_component("-hello-") == "hello"

    def test_numeric_string(self) -> None:
        assert sanitize_var_component("1234") == "1234"


class TestGenerateVarName:
    def test_simple_prefix_and_discriminators(self) -> None:
        result = generate_var_name("junos_addr", ["xe_0_0_0", "100", "inet", "0"])
        assert result == "junos_addr_xe_0_0_0_100_inet_0"

    def test_discriminators_get_sanitized(self) -> None:
        result = generate_var_name("junos_addr", ["xe-0/0/0", "100"])
        assert result == "junos_addr_xe_0_0_0_100"

    def test_empty_discriminators(self) -> None:
        result = generate_var_name("prefix", [])
        assert result == "prefix"


class TestSplitLeafFromPath:
    def test_simple_key(self) -> None:
        path, leaf = split_leaf_from_path("configuration.system.host-name")
        assert path == "configuration.system"
        assert leaf == "host-name"

    def test_after_list_wildcard(self) -> None:
        path, leaf = split_leaf_from_path(
            "configuration.protocols.bgp.group[*].neighbor[*].description"
        )
        assert path == "configuration.protocols.bgp.group[*].neighbor[*]"
        assert leaf == "description"

    def test_after_dict_wildcard(self) -> None:
        path, leaf = split_leaf_from_path("family.*.address[*].name")
        assert path == "family.*.address[*]"
        assert leaf == "name"

    def test_after_glob_bracket(self) -> None:
        path, leaf = split_leaf_from_path("groups[ansible-*].peer-as")
        assert path == "groups[ansible-*]"
        assert leaf == "peer-as"

    def test_after_dict_glob(self) -> None:
        path, leaf = split_leaf_from_path("family.inet*.address[*].name")
        assert path == "family.inet*.address[*]"
        assert leaf == "name"

    def test_single_segment(self) -> None:
        path, leaf = split_leaf_from_path("host-name")
        assert path == ""
        assert leaf == "host-name"

    def test_raises_on_trailing_list_wildcard(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="leaf"):
            split_leaf_from_path("items[*]")

    def test_raises_on_trailing_dict_wildcard(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="leaf"):
            split_leaf_from_path("family.*")

    def test_raises_on_trailing_glob(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="leaf"):
            split_leaf_from_path("groups[ansible-*]")

    def test_raises_on_trailing_dict_glob(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="leaf"):
            split_leaf_from_path("family.inet*")


class TestAnsibilize:
    def test_simple_leaf_extraction(self) -> None:
        data = {"items": [{"name": "10.0.0.1", "desc": "first"}]}
        host_vars, group_vars = ansibilize(data, "items[*].name", "item")
        assert host_vars == {"item_0": "10.0.0.1"}
        assert group_vars["items"][0]["name"] == "{{ item_0 }}"
        # desc untouched
        assert group_vars["items"][0]["desc"] == "first"

    def test_does_not_mutate_input(self) -> None:
        data = {"items": [{"name": "10.0.0.1"}]}
        ansibilize(data, "items[*].name", "item")
        assert data["items"][0]["name"] == "10.0.0.1"

    def test_multiple_list_items(self) -> None:
        data = {
            "items": [
                {"name": "10.0.0.1", "desc": "a"},
                {"name": "10.0.0.2", "desc": "b"},
            ]
        }
        host_vars, group_vars = ansibilize(data, "items[*].name", "addr")
        assert host_vars == {"addr_0": "10.0.0.1", "addr_1": "10.0.0.2"}
        assert group_vars["items"][0]["name"] == "{{ addr_0 }}"
        assert group_vars["items"][1]["name"] == "{{ addr_1 }}"

    def test_full_interface_path(self) -> None:
        data = {
            "configuration": {
                "interfaces": {
                    "interface": [
                        {
                            "name": "xe-0/0/0",
                            "unit": [
                                {
                                    "name": "100",
                                    "family": {
                                        "inet": {"address": [{"name": "10.0.0.1/30"}]},
                                        "inet6": {"address": [{"name": "2001:db8::1/64"}]},
                                    },
                                }
                            ],
                        }
                    ]
                }
            }
        }
        host_vars, group_vars = ansibilize(
            data,
            "configuration.interfaces.interface[*].unit[*].family.*.address[*].name",
            "junos_interface_address",
        )
        # Should have 2 addresses extracted
        assert len(host_vars) == 2
        assert host_vars["junos_interface_address_xe_0_0_0_100_inet_0"] == "10.0.0.1/30"
        assert host_vars["junos_interface_address_xe_0_0_0_100_inet6_0"] == "2001:db8::1/64"

        # group_vars should have Jinja2 refs
        intf = group_vars["configuration"]["interfaces"]["interface"][0]
        unit = intf["unit"][0]
        inet_addr = unit["family"]["inet"]["address"][0]["name"]
        inet6_addr = unit["family"]["inet6"]["address"][0]["name"]
        assert inet_addr == "{{ junos_interface_address_xe_0_0_0_100_inet_0 }}"
        assert inet6_addr == "{{ junos_interface_address_xe_0_0_0_100_inet6_0 }}"

    def test_non_name_leaf(self) -> None:
        """When leaf is not 'name', list discriminator uses item['name']."""
        data = {
            "neighbors": [
                {"name": "10.0.0.1", "description": "spine1"},
                {"name": "10.0.0.2", "description": "spine2"},
            ]
        }
        host_vars, group_vars = ansibilize(data, "neighbors[*].description", "bgp_desc")
        assert host_vars == {
            "bgp_desc_10_0_0_1": "spine1",
            "bgp_desc_10_0_0_2": "spine2",
        }
        assert group_vars["neighbors"][0]["description"] == "{{ bgp_desc_10_0_0_1 }}"
        # name field untouched
        assert group_vars["neighbors"][0]["name"] == "10.0.0.1"

    def test_missing_leaf_key_skipped(self) -> None:
        data = {"items": [{"name": "a"}, {"name": "b", "val": 42}]}
        host_vars, group_vars = ansibilize(data, "items[*].val", "v")
        # Only the item with "val" gets extracted
        assert host_vars == {"v_b": 42}
        assert group_vars["items"][0] == {"name": "a"}
        assert group_vars["items"][1]["val"] == "{{ v_b }}"


class TestAnsibilizeMulti:
    def test_two_pairs_merged(self) -> None:
        data = {
            "configuration": {
                "system": {"host-name": "router1"},
                "protocols": {
                    "bgp": {
                        "group": [
                            {
                                "name": "overlay",
                                "neighbor": [
                                    {"name": "10.0.0.1", "description": "spine1"},
                                    {"name": "10.0.0.2", "description": "spine2"},
                                ],
                            }
                        ]
                    }
                },
            }
        }
        host_vars, group_vars = ansibilize_multi(
            data,
            [
                ("junos_hostname", "configuration.system.host-name"),
                (
                    "bgp_peer",
                    "configuration.protocols.bgp.group[*].neighbor[*].name",
                ),
            ],
        )
        # host_vars has entries from both pairs
        assert host_vars["junos_hostname"] == "router1"
        assert host_vars["bgp_peer_overlay_0"] == "10.0.0.1"
        assert host_vars["bgp_peer_overlay_1"] == "10.0.0.2"
        # group_vars has Jinja2 refs for both
        assert group_vars["configuration"]["system"]["host-name"] == "{{ junos_hostname }}"
        neighbors = group_vars["configuration"]["protocols"]["bgp"]["group"][0]["neighbor"]
        assert neighbors[0]["name"] == "{{ bgp_peer_overlay_0 }}"
        assert neighbors[1]["name"] == "{{ bgp_peer_overlay_1 }}"

    def test_does_not_mutate_input(self) -> None:
        data = {"items": [{"name": "10.0.0.1"}], "system": {"host-name": "r1"}}
        ansibilize_multi(
            data,
            [("addr", "items[*].name"), ("host", "system.host-name")],
        )
        assert data["items"][0]["name"] == "10.0.0.1"
        assert data["system"]["host-name"] == "r1"

    def test_single_pair_matches_ansibilize(self) -> None:
        data = {"items": [{"name": "10.0.0.1"}]}
        hv_multi, gv_multi = ansibilize_multi(data, [("addr", "items[*].name")])
        hv_single, gv_single = ansibilize(data, "items[*].name", "addr")
        assert hv_multi == hv_single
        assert gv_multi == gv_single


class TestConfigurationAutoDescend:
    """Tests that ansibilize auto-descends into 'configuration' wrapper."""

    def test_path_without_configuration_prefix(self) -> None:
        """Paths like 'interfaces.interface[*]...' should work with configuration wrapper."""
        data = {
            "configuration": {
                "interfaces": {
                    "interface": [
                        {
                            "name": "ge-0/0/0",
                            "unit": [
                                {
                                    "name": "0",
                                    "family": {"inet": {"address": [{"name": "10.0.0.1/30"}]}},
                                }
                            ],
                        }
                    ]
                }
            }
        }
        host_vars, group_vars = ansibilize(
            data, "interfaces.interface[*].unit[*].family.*.address[*].name", "addr"
        )
        assert host_vars == {"addr_ge_0_0_0_0_inet_0": "10.0.0.1/30"}
        addr = group_vars["configuration"]["interfaces"]["interface"][0]["unit"][0]
        assert addr["family"]["inet"]["address"][0]["name"] == "{{ addr_ge_0_0_0_0_inet_0 }}"

    def test_path_with_configuration_prefix_still_works(self) -> None:
        """Explicit configuration. prefix should still work."""
        data = {
            "configuration": {
                "system": {"host-name": "r1"},
            }
        }
        host_vars, _gv = ansibilize(data, "configuration.system.host-name", "host")
        assert host_vars == {"host": "r1"}

    def test_no_configuration_wrapper_unchanged(self) -> None:
        """Data without 'configuration' key works as before."""
        data = {"items": [{"name": "10.0.0.1"}]}
        host_vars, _gv = ansibilize(data, "items[*].name", "addr")
        assert host_vars == {"addr_0": "10.0.0.1"}

    def test_multi_paths_without_prefix(self) -> None:
        """Multiple paths without configuration prefix."""
        data = {
            "configuration": {
                "system": {"host-name": "router1"},
                "interfaces": {"interface": [{"name": "lo0", "description": "loopback"}]},
            }
        }
        host_vars, group_vars = ansibilize_multi(
            data,
            [
                ("host", "system.host-name"),
                ("desc", "interfaces.interface[*].description"),
            ],
        )
        assert host_vars["host"] == "router1"
        assert host_vars["desc_lo0"] == "loopback"
        assert group_vars["configuration"]["system"]["host-name"] == "{{ host }}"


class TestFormatOutput:
    def test_two_yaml_documents(self) -> None:
        host_vars = {"addr_0": "10.0.0.1"}
        group_vars = {"items": [{"name": "{{ addr_0 }}"}]}
        output = format_output(host_vars, group_vars)
        assert "---" in output
        parts = output.split("---\n")
        assert len(parts) == 2
        host = yaml.safe_load(parts[0])
        assert host == {"addr_0": "10.0.0.1"}
        group = yaml.safe_load(parts[1])
        assert group == {"items": [{"name": "{{ addr_0 }}"}]}

    def test_jinja2_values_are_quoted_for_ansible(self) -> None:
        """Jinja2 {{ }} references must be YAML-quoted for Ansible compatibility.

        Ansible requires values starting with { to be quoted, otherwise the
        YAML parser treats them as flow mappings. See:
        https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html
        """
        host_vars = {"x": "val"}
        group_vars = {"key": "{{ x }}"}
        output = format_output(host_vars, group_vars)
        parts = output.split("---\n")
        # Must be quoted — either 'single' or "double" quotes
        assert "'{{ x }}'" in parts[1] or '"{{ x }}"' in parts[1]
        # And the YAML must be parseable
        group = yaml.safe_load(parts[1])
        assert group == {"key": "{{ x }}"}


class TestGeneralizedAutoDescend:
    """Tests that auto-descend works for any single top-level key, not just 'configuration'."""

    def test_auto_descend_non_configuration_root(self) -> None:
        """Single top-level key 'interfaces_cfg' auto-descends."""
        data = {
            "interfaces_cfg": {
                "interfaces": {
                    "interface": [
                        {
                            "name": "ge-0/0/0",
                            "unit": [
                                {
                                    "name": "0",
                                    "family": {"inet": {"address": [{"name": "10.0.0.1/30"}]}},
                                }
                            ],
                        }
                    ]
                }
            }
        }
        host_vars, group_vars = ansibilize(
            data, "interfaces.interface[*].unit[*].family.*.address[*].name", "addr"
        )
        assert host_vars == {"addr_ge_0_0_0_0_inet_0": "10.0.0.1/30"}
        addr = group_vars["interfaces_cfg"]["interfaces"]["interface"][0]["unit"][0]
        assert addr["family"]["inet"]["address"][0]["name"] == "{{ addr_ge_0_0_0_0_inet_0 }}"

    def test_auto_descend_explicit_root_prefix_still_works(self) -> None:
        """Path starting with the single top-level key doesn't double-descend."""
        data = {
            "my_root": {
                "system": {"host-name": "r1"},
            }
        }
        host_vars, _gv = ansibilize(data, "my_root.system.host-name", "host")
        assert host_vars == {"host": "r1"}

    def test_no_auto_descend_with_multiple_top_keys(self) -> None:
        """Multiple top-level keys: no auto-descend, paths resolve at top level."""
        data = {
            "interfaces": {"interface": [{"name": "ge-0/0/0", "description": "uplink"}]},
            "system": {"host-name": "r1"},
        }
        host_vars, _gv = ansibilize(data, "interfaces.interface[*].description", "desc")
        assert host_vars == {"desc_ge_0_0_0": "uplink"}


class TestRootKeys:
    """Tests for explicit root_keys parameter with glob matching."""

    def test_root_keys_glob_match(self) -> None:
        """root_keys=['interfaces_*'] matches 'interfaces_cfg'."""
        data = {
            "interfaces_cfg": {
                "interfaces": {"interface": [{"name": "ge-0/0/0", "description": "uplink"}]}
            }
        }
        host_vars, group_vars = ansibilize_multi(
            data,
            [("desc", "interfaces.interface[*].description")],
            root_keys=["interfaces_*"],
        )
        assert host_vars == {"desc_ge_0_0_0": "uplink"}
        intf = group_vars["interfaces_cfg"]["interfaces"]["interface"][0]
        assert intf["description"] == "{{ desc_ge_0_0_0 }}"

    def test_root_keys_multiple(self) -> None:
        """Multiple root keys each get processed."""
        data = {
            "config_a": {"system": {"host-name": "r1"}},
            "config_b": {"system": {"host-name": "r2"}},
            "unrelated": {"system": {"host-name": "ignored"}},
        }
        host_vars, group_vars = ansibilize_multi(
            data,
            [("host", "system.host-name")],
            root_keys=["config_*"],
        )
        assert host_vars["host"] == "r2"  # second match overwrites first (same var name)
        # Both config_a and config_b get templatized
        assert group_vars["config_a"]["system"]["host-name"] == "{{ host }}"
        assert group_vars["config_b"]["system"]["host-name"] == "{{ host }}"
        # unrelated is untouched
        assert group_vars["unrelated"]["system"]["host-name"] == "ignored"

    def test_root_keys_no_match_no_crash(self) -> None:
        """Glob matches nothing — paths don't resolve, no crash."""
        data = {
            "interfaces_cfg": {
                "interfaces": {"interface": [{"name": "ge-0/0/0", "description": "uplink"}]}
            }
        }
        host_vars, group_vars = ansibilize_multi(
            data,
            [("desc", "interfaces.interface[*].description")],
            root_keys=["no_match_*"],
        )
        # Falls back to top-level — path won't resolve, so no host_vars
        assert host_vars == {}
        # group_vars unchanged
        intf = group_vars["interfaces_cfg"]["interfaces"]["interface"][0]
        assert intf["description"] == "uplink"

    def test_root_keys_exact_match(self) -> None:
        """Exact key name (no glob) works as a root_key."""
        data = {
            "my_config": {
                "system": {"host-name": "r1"},
            },
            "other": {"system": {"host-name": "r2"}},
        }
        host_vars, group_vars = ansibilize_multi(
            data,
            [("host", "system.host-name")],
            root_keys=["my_config"],
        )
        assert host_vars == {"host": "r1"}
        assert group_vars["my_config"]["system"]["host-name"] == "{{ host }}"
        assert group_vars["other"]["system"]["host-name"] == "r2"


class TestDetectValueType:
    def test_ipv4(self) -> None:
        assert detect_value_type("10.0.2.64") == "ip"

    def test_ipv4_with_mask(self) -> None:
        assert detect_value_type("10.0.2.64/31") == "ip"

    def test_ipv6(self) -> None:
        assert detect_value_type("2001:db8::1") == "ip"

    def test_ipv6_with_mask(self) -> None:
        assert detect_value_type("2001:db8::1:2e/112") == "ip"

    def test_mac_colon(self) -> None:
        assert detect_value_type("00:11:22:33:44:a5") == "mac"

    def test_mac_dash(self) -> None:
        assert detect_value_type("00-11-22-33-44-A5") == "mac"

    def test_mac_dot(self) -> None:
        assert detect_value_type("AABB.CCDD.EE55") == "mac"

    def test_trailing_numeric(self) -> None:
        assert detect_value_type("router04") == "trailing_numeric"

    def test_trailing_numeric_with_separator(self) -> None:
        assert detect_value_type("spine-1") == "trailing_numeric"

    def test_unrecognized_raises(self) -> None:
        with pytest.raises(ValueError, match="hello-world"):
            detect_value_type("hello-world")


class TestMakeOffsetExpression:
    def test_ipv4_with_mask(self) -> None:
        result = make_offset_expression("10.0.2.64/31", "base_address_offset")
        assert result == "{{ '10.0.2.64' | ansible.utils.ipmath(base_address_offset) }}/31"

    def test_ipv6_with_mask(self) -> None:
        result = make_offset_expression("2001:db8::1:2e/112", "base_address_offset")
        assert result == "{{ '2001:db8::1:2e' | ansible.utils.ipmath(base_address_offset) }}/112"

    def test_ip_no_mask(self) -> None:
        result = make_offset_expression("10.0.0.1", "base_address_offset")
        assert result == "{{ '10.0.0.1' | ansible.utils.ipmath(base_address_offset) }}"

    def test_mac_colon(self) -> None:
        result = make_offset_expression("00:11:22:33:44:a5", "base_address_offset")
        assert result == "00:11:22:33:44:{{ '%02x' % (165 + base_address_offset) }}"

    def test_mac_dash(self) -> None:
        result = make_offset_expression("00-11-22-33-44-A5", "base_address_offset")
        assert result == "00-11-22-33-44-{{ '%02x' % (165 + base_address_offset) }}"

    def test_mac_dot(self) -> None:
        result = make_offset_expression("AABB.CCDD.EE55", "base_address_offset")
        assert result == "AABB.CCDD.EE{{ '%02x' % (85 + base_address_offset) }}"

    def test_trailing_numeric_zero_padded(self) -> None:
        result = make_offset_expression("router04", "base_address_offset")
        assert result == "router{{ '%02d' % (4 + base_address_offset) }}"

    def test_trailing_numeric_unpadded(self) -> None:
        result = make_offset_expression("spine-1", "base_address_offset")
        assert result == "spine-{{ 1 + base_address_offset }}"

    def test_custom_offset_var(self) -> None:
        result = make_offset_expression("10.0.0.1/30", "my_offset")
        assert result == "{{ '10.0.0.1' | ansible.utils.ipmath(my_offset) }}/30"

    def test_unrecognized_raises(self) -> None:
        with pytest.raises(ValueError, match="no-digits-here"):
            make_offset_expression("no-digits-here", "base_address_offset")


class TestAnsibilizeWithOffset:
    def test_ipv4_offset_basic(self) -> None:
        data = {
            "interfaces": {
                "interface": [
                    {
                        "name": "ge-0/0/0",
                        "unit": [
                            {
                                "name": "0",
                                "family": {"inet": {"address": [{"name": "10.0.2.64/31"}]}},
                            }
                        ],
                    }
                ]
            }
        }
        host_vars, offset_vars, template = ansibilize_with_offset(
            data,
            literal_pairs=[],
            offset_pairs=[("addr", "interfaces.interface[*].unit[*].family.*.address[*].name")],
        )
        assert host_vars["base_address_offset"] == 0
        var_name = "addr_ge_0_0_0_0_inet_0"
        assert var_name in offset_vars
        assert "ipmath" in offset_vars[var_name]
        assert "10.0.2.64" in offset_vars[var_name]
        assert "/31" in offset_vars[var_name]
        assert template["interfaces"]["interface"][0]["unit"][0]["family"]["inet"]["address"][0][
            "name"
        ] == ("{{ " + var_name + " }}")

    def test_ipv6_offset(self) -> None:
        data = {"items": [{"name": "2001:db8::1:2e/112"}]}
        host_vars, offset_vars, template = ansibilize_with_offset(
            data, literal_pairs=[], offset_pairs=[("addr", "items[*].name")]
        )
        assert "ipmath" in offset_vars["addr_0"]
        assert "2001:db8::1:2e" in offset_vars["addr_0"]

    def test_mac_offset(self) -> None:
        data = {"items": [{"name": "00:11:22:33:44:a5"}]}
        host_vars, offset_vars, template = ansibilize_with_offset(
            data, literal_pairs=[], offset_pairs=[("mac", "items[*].name")]
        )
        assert "'%02x'" in offset_vars["mac_0"]
        assert "165" in offset_vars["mac_0"]

    def test_mixed_literal_and_offset(self) -> None:
        data = {
            "system": {"host-name": "router04"},
            "interfaces": {
                "interface": [
                    {
                        "name": "ge-0/0/0",
                        "unit": [
                            {
                                "name": "0",
                                "family": {"inet": {"address": [{"name": "10.0.2.64/31"}]}},
                            }
                        ],
                    }
                ]
            },
        }
        host_vars, offset_vars, template = ansibilize_with_offset(
            data,
            literal_pairs=[("host", "system.host-name")],
            offset_pairs=[("addr", "interfaces.interface[*].unit[*].family.*.address[*].name")],
        )
        # Literal goes to host_vars
        assert host_vars["host"] == "router04"
        assert host_vars["base_address_offset"] == 0
        # Offset goes to offset_vars
        assert "addr_ge_0_0_0_0_inet_0" in offset_vars
        # Both appear in template
        assert template["system"]["host-name"] == "{{ host }}"
        assert "{{ addr_ge_0_0_0_0_inet_0 }}" in str(template["interfaces"])

    def test_unrecognized_value_raises(self) -> None:
        data = {"items": [{"name": "hello"}]}
        with pytest.raises(ValueError, match="hello"):
            ansibilize_with_offset(data, literal_pairs=[], offset_pairs=[("x", "items[*].name")])

    def test_auto_descend_works_with_offset(self) -> None:
        data = {
            "configuration": {
                "interfaces": {
                    "interface": [
                        {
                            "name": "ge-0/0/0",
                            "unit": [
                                {
                                    "name": "0",
                                    "family": {"inet": {"address": [{"name": "10.0.0.1/30"}]}},
                                }
                            ],
                        }
                    ]
                }
            }
        }
        host_vars, offset_vars, template = ansibilize_with_offset(
            data,
            literal_pairs=[],
            offset_pairs=[("addr", "interfaces.interface[*].unit[*].family.*.address[*].name")],
        )
        assert "addr_ge_0_0_0_0_inet_0" in offset_vars

    def test_offset_var_in_host_vars(self) -> None:
        data = {"items": [{"name": "10.0.0.1/30"}]}
        host_vars, _, _ = ansibilize_with_offset(
            data,
            literal_pairs=[],
            offset_pairs=[("addr", "items[*].name")],
            offset_var="my_offset",
        )
        assert host_vars["my_offset"] == 0
        assert "base_address_offset" not in host_vars


class TestFormatOutputWithOffset:
    def test_three_yaml_documents(self) -> None:
        host_vars = {"base_address_offset": 0, "host": "router1"}
        offset_vars = {"addr_0": "{{ '10.0.0.1' | ansible.utils.ipmath(base_address_offset) }}/30"}
        template = {"items": [{"name": "{{ addr_0 }}"}]}
        output = format_output_with_offset(host_vars, offset_vars, template)
        parts = output.split("---\n")
        assert len(parts) == 3

    def test_jinja2_expressions_quoted(self) -> None:
        host_vars = {"base_address_offset": 0}
        offset_vars = {"addr_0": "{{ '10.0.0.1' | ansible.utils.ipmath(base_address_offset) }}/30"}
        template = {"items": [{"name": "{{ addr_0 }}"}]}
        output = format_output_with_offset(host_vars, offset_vars, template)
        parts = output.split("---\n")
        # Offset vars doc should have quoted Jinja2 expression
        assert "{{" in parts[1]
        # Template doc should have quoted Jinja2 reference
        assert "{{" in parts[2]

    def test_round_trip_parseable(self) -> None:
        host_vars = {"base_address_offset": 0}
        offset_vars = {"addr_0": "{{ '10.0.0.1' | ansible.utils.ipmath(base_address_offset) }}/30"}
        template = {"items": [{"name": "{{ addr_0 }}"}]}
        output = format_output_with_offset(host_vars, offset_vars, template)
        parts = output.split("---\n")
        for part in parts:
            parsed = yaml.safe_load(part)
            assert parsed is not None
