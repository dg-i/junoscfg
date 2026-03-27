"""Tests for set→dict converter (Phase 3).

Tests the set_to_dict function that parses display set commands into
the JSON dict IR.
"""

from __future__ import annotations

import pytest

from junoscfg.convert.input.set_input import set_to_dict
from junoscfg.convert.output.set_output import dict_to_set

# ── Simple leaves ────────────────────────────────────────────────────


class TestSimpleLeaves:
    def test_single_leaf(self) -> None:
        result = set_to_dict("set system host-name r1")
        assert result == {"system": {"host-name": "r1"}}

    def test_quoted_value(self) -> None:
        result = set_to_dict('set system host-name "my router"')
        assert result == {"system": {"host-name": "my router"}}

    def test_nested_leaf(self) -> None:
        result = set_to_dict("set system services ssh root-login deny")
        assert result == {"system": {"services": {"ssh": {"root-login": "deny"}}}}


# ── Named lists ──────────────────────────────────────────────────────


class TestNamedLists:
    def test_transparent_named_list(self) -> None:
        result = set_to_dict("set interfaces ge-0/0/0 description uplink")
        assert result == {
            "interfaces": {"interface": [{"name": "ge-0/0/0", "description": "uplink"}]}
        }

    def test_transparent_named_list_no_children(self) -> None:
        result = set_to_dict("set interfaces ge-0/0/0")
        assert result == {"interfaces": {"interface": [{"name": "ge-0/0/0"}]}}

    def test_multiple_transparent_entries(self) -> None:
        source = (
            "set interfaces ge-0/0/0 description uplink\n"
            "set interfaces ge-0/0/1 description downlink\n"
        )
        result = set_to_dict(source)
        assert result == {
            "interfaces": {
                "interface": [
                    {"name": "ge-0/0/0", "description": "uplink"},
                    {"name": "ge-0/0/1", "description": "downlink"},
                ]
            }
        }

    def test_regular_named_list(self) -> None:
        result = set_to_dict("set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1")
        assert result == {
            "routing-options": {
                "static": {"route": [{"name": "0.0.0.0/0", "next-hop": ["10.0.0.1"]}]}
            }
        }

    def test_nested_named_lists(self) -> None:
        result = set_to_dict("set firewall family inet filter PROTECT term accept-ssh then accept")
        assert result["firewall"]["family"]["inet"]["filter"] == [
            {"name": "PROTECT", "term": [{"name": "accept-ssh", "then": {"accept": [None]}}]}
        ]


# ── Simple string lists (normalized from dict entries) ───────────────


class TestSimpleStringLists:
    def test_simple_list_with_children_schema(self) -> None:
        """Named lists with children in schema always produce dict entries."""
        source = "set system name-server 8.8.8.8\nset system name-server 8.8.4.4\n"
        result = set_to_dict(source)
        # name-server has children in schema (routing-instance, source-address),
        # so entries are always dict format with "name" key
        assert result == {
            "system": {
                "name-server": [
                    {"name": "8.8.8.8"},
                    {"name": "8.8.4.4"},
                ]
            }
        }


# ── Presence flags ───────────────────────────────────────────────────


class TestPresenceFlags:
    def test_presence(self) -> None:
        result = set_to_dict("set firewall family inet filter PROTECT term accept-ssh then accept")
        then = result["firewall"]["family"]["inet"]["filter"][0]["term"][0]["then"]
        assert then == {"accept": [None]}


# ── Merging multiple set commands ────────────────────────────────────


class TestMerging:
    def test_merge_siblings(self) -> None:
        source = "set system host-name r1\nset system domain-name example.com\n"
        result = set_to_dict(source)
        assert result == {"system": {"host-name": "r1", "domain-name": "example.com"}}

    def test_merge_named_list_entries(self) -> None:
        source = (
            "set firewall family inet filter PROTECT term accept-ssh from protocol tcp\n"
            "set firewall family inet filter PROTECT term accept-ssh from destination-port ssh\n"
            "set firewall family inet filter PROTECT term accept-ssh then accept\n"
        )
        result = set_to_dict(source)
        term = result["firewall"]["family"]["inet"]["filter"][0]["term"][0]
        assert term["name"] == "accept-ssh"
        assert term["from"]["protocol"] == ["tcp"]
        assert term["from"]["destination-port"] == ["ssh"]
        assert term["then"]["accept"] == [None]

    def test_merge_interface_children(self) -> None:
        source = "set interfaces ge-0/0/0 unit 0 family inet address 10.0.0.1/24\n"
        result = set_to_dict(source)
        iface = result["interfaces"]["interface"][0]
        assert iface["name"] == "ge-0/0/0"
        assert iface["unit"][0]["name"] == "0"
        assert iface["unit"][0]["family"]["inet"]["address"] == [{"name": "10.0.0.1/24"}]


# ── Meta commands ────────────────────────────────────────────────────


class TestMetaCommands:
    def test_deactivate_container(self) -> None:
        source = "set system host-name r1\ndeactivate system\n"
        result = set_to_dict(source)
        assert result == {"system": {"@": {"inactive": True}, "host-name": "r1"}}

    def test_protect_container(self) -> None:
        source = "set system host-name r1\nprotect system\n"
        result = set_to_dict(source)
        assert result["system"]["@"]["protect"] == "protect"

    def test_delete_container(self) -> None:
        source = "set system host-name r1\ndelete system\n"
        result = set_to_dict(source)
        assert result["system"]["@"]["operation"] == "delete"

    def test_activate_container(self) -> None:
        source = "set system host-name r1\nactivate system\n"
        result = set_to_dict(source)
        assert result["system"]["@"]["active"] == "active"

    def test_deactivate_transparent_entry(self) -> None:
        source = "set interfaces ge-0/0/0 description uplink\ndeactivate interfaces ge-0/0/0\n"
        result = set_to_dict(source)
        entry = result["interfaces"]["interface"][0]
        assert entry["@"]["inactive"] is True


# ── Apply-groups ─────────────────────────────────────────────────────


class TestApplyGroups:
    def test_top_level_apply_groups(self) -> None:
        source = "set apply-groups FOO\nset apply-groups BAR\n"
        result = set_to_dict(source)
        assert result == {"apply-groups": ["FOO", "BAR"]}

    def test_embedded_apply_groups(self) -> None:
        source = "set system host-name r1\nset system apply-groups FOO\n"
        result = set_to_dict(source)
        assert result["system"]["apply-groups"] == ["FOO"]


# ── Parser bug fixes ────────────────────────────────────────────────


class TestParserBugFixes:
    def test_leaf_list_accumulation(self) -> None:
        """Bug 1: Repeated leaf values accumulate into a list."""
        source = (
            "set system services ssh ciphers aes128-ctr\n"
            "set system services ssh ciphers aes256-ctr\n"
        )
        result = set_to_dict(source)
        assert result["system"]["services"]["ssh"]["ciphers"] == ["aes128-ctr", "aes256-ctr"]

    def test_leaf_triple_accumulation(self) -> None:
        """Bug 1: Three repeated leaf values accumulate correctly."""
        source = (
            "set system services ssh ciphers aes128-ctr\n"
            "set system services ssh ciphers aes256-ctr\n"
            "set system services ssh ciphers aes128-gcm\n"
        )
        result = set_to_dict(source)
        assert result["system"]["services"]["ssh"]["ciphers"] == [
            "aes128-ctr",
            "aes256-ctr",
            "aes128-gcm",
        ]

    def test_route_filter_entry_key(self) -> None:
        """Bug 2: route-filter uses 'address' as entry key, not 'name'."""
        result = set_to_dict(
            "set policy-options policy-statement FOO term BAR from route-filter 0.0.0.0/0 exact"
        )
        rf = result["policy-options"]["policy-statement"][0]["term"][0]["from"]["route-filter"]
        assert rf == [{"address": "0.0.0.0/0", "exact": [None]}]

    def test_prefix_list_filter_entry_key(self) -> None:
        """Bug 2: prefix-list-filter uses 'list_name' as entry key, not 'name'."""
        result = set_to_dict(
            "set policy-options policy-statement FOO term BAR from prefix-list-filter MY-LIST exact"
        )
        plf = result["policy-options"]["policy-statement"][0]["term"][0]["from"][
            "prefix-list-filter"
        ]
        assert plf == [{"list_name": "MY-LIST", "exact": [None]}]

    def test_presence_named_list_with_value(self) -> None:
        """Bug 3: L+p node with value creates dict entry, not bare string."""
        # snmp filter-interfaces interfaces has both L and p flags
        result = set_to_dict('set snmp filter-interfaces interfaces "^ge-"')
        ifaces = result["snmp"]["filter-interfaces"]["interfaces"]
        assert isinstance(ifaces, list)
        assert len(ifaces) == 1
        assert ifaces[0] == {"name": "^ge-"}

    def test_presence_named_list_without_value(self) -> None:
        """Bug 3: L+p node without value creates presence [null]."""
        result = set_to_dict("set snmp filter-interfaces interfaces")
        assert result["snmp"]["filter-interfaces"]["interfaces"] == [None]

    def test_multi_token_leaf_value(self) -> None:
        """Bug 4: All remaining tokens after a leaf are joined as the value."""
        result = set_to_dict("set system host-name foo bar baz")
        assert result["system"]["host-name"] == "foo bar baz"

    def test_leaf_followed_by_sibling(self) -> None:
        """Leaf consumes only one token when next token is a schema sibling."""
        source = (
            "set system syslog file messages_firewall_any"
            " archive size 10m files 5 no-world-readable"
        )
        result = set_to_dict(source)
        archive = result["system"]["syslog"]["file"][0]["archive"]
        assert archive["size"] == "10m"
        assert archive["files"] == "5"
        assert archive["no-world-readable"] == [None]

    def test_nokeyword_leaf_with_siblings(self) -> None:
        """Nokeyword leaf (like traceoptions filename) preserves sibling tokens."""
        source = "set protocols bgp traceoptions file bgp-log size 10m files 10"
        result = set_to_dict(source)
        f = result["protocols"]["bgp"]["traceoptions"]["file"]
        assert f["filename"] == "bgp-log"
        assert f["size"] == "10m"
        assert f["files"] == "10"

    def test_nokeyword_maximum_prefixes_with_siblings(self) -> None:
        """maximum-prefixes nokeyword limit preserves threshold and log-interval."""
        source = "set routing-options maximum-prefixes 3000000 threshold 50 log-interval 5"
        result = set_to_dict(source)
        mp = result["routing-options"]["maximum-prefixes"]
        assert mp["limit"] == "3000000"
        assert mp["threshold"] == ["50"]
        assert mp["log-interval"] == "5"

    def test_trigger_flat_dict_nokeyword(self) -> None:
        """Trigger (fd) with nokeyword count value is preserved."""
        source = "set event-options policy test within 1800 trigger 1"
        result = set_to_dict(source)
        trigger = result["event-options"]["policy"][0]["within"][0]["trigger"]
        assert trigger["count"] == "1"

    def test_confederation_members(self) -> None:
        """Confederation members leaf accumulates values."""
        source = (
            "set routing-options confederation members 64529\n"
            "set routing-options confederation members 64530\n"
        )
        result = set_to_dict(source)
        members = result["routing-options"]["confederation"]["members"]
        assert members == ["64529", "64530"]

    def test_ntp_server_sibling_leaves(self) -> None:
        """NTP server with version, prefer, and routing-instance siblings."""
        source = "set system ntp server 198.51.100.1 version 4 prefer routing-instance mgmt_junos"
        result = set_to_dict(source)
        server = result["system"]["ntp"]["server"][0]
        assert server["name"] == "198.51.100.1"
        assert server["version"] == "4"
        assert server["prefer"] == [None]
        assert server["routing-instance"] == ["mgmt_junos"]

    def test_filter_interfaces_multiple_entries(self) -> None:
        """Bug 3: filter-interfaces interfaces creates dict entries."""
        source = (
            'set snmp filter-interfaces interfaces "^ge-0/0/0"\n'
            'set snmp filter-interfaces interfaces "^ge-0/0/1"\n'
        )
        result = set_to_dict(source)
        ifaces = result["snmp"]["filter-interfaces"]["interfaces"]
        assert isinstance(ifaces, list)
        assert len(ifaces) == 2
        assert ifaces[0] == {"name": "^ge-0/0/0"}
        assert ifaces[1] == {"name": "^ge-0/0/1"}

    def test_attributes_match_values_preserved(self) -> None:
        """Bug 5: attributes-match preserves condition and value tokens."""
        source = (
            "set event-options policy test-policy "
            'attributes-match ping_test_failed.test-owner matches "^inet6-ping-uptime$"'
        )
        result = set_to_dict(source)
        am = result["event-options"]["policy"][0]["attributes-match"]
        assert isinstance(am, list)
        assert len(am) == 1
        entry = am[0]
        assert isinstance(entry, dict)
        assert entry["name"] == "ping_test_failed.test-owner"
        # Remaining tokens stored as ordered values
        assert entry["_v0"] == "matches"
        assert entry["_v1"] == "^inet6-ping-uptime$"

    def test_ephemeral_instance_named_list(self) -> None:
        """Ephemeral instance preserves instance names as dict entries."""
        source = (
            "set system configuration-database ephemeral instance dgipingtest\n"
            "set system configuration-database ephemeral instance 0\n"
        )
        result = set_to_dict(source)
        instances = result["system"]["configuration-database"]["ephemeral"]["instance"]
        assert instances == [{"name": "dgipingtest"}, {"name": "0"}]

    def test_named_list_without_children_produces_dicts(self) -> None:
        """Named lists without schema children produce dict entries, not bare strings."""
        # ephemeral instance has {L: true} — no children, no fe
        source = (
            "set system configuration-database ephemeral instance dgipingtest\n"
            "set system configuration-database ephemeral instance testdb\n"
        )
        result = set_to_dict(source)
        instances = result["system"]["configuration-database"]["ephemeral"]["instance"]
        assert isinstance(instances, list)
        assert all(isinstance(e, dict) for e in instances)
        assert instances[0] == {"name": "dgipingtest"}
        assert instances[1] == {"name": "testdb"}

    def test_community_action_first_pattern(self) -> None:
        """Community entries use action-first pattern: community add VALUE."""
        source = (
            "set policy-options policy-statement STMT term T then community add COMM1\n"
            "set policy-options policy-statement STMT term T then community delete COMM2\n"
        )
        result = set_to_dict(source)
        comms = result["policy-options"]["policy-statement"][0]["term"][0]["then"]["community"]
        assert isinstance(comms, list)
        assert len(comms) == 2
        assert comms[0] == {"community-name": "COMM1", "add": [None]}
        assert comms[1] == {"community-name": "COMM2", "delete": [None]}

    def test_community_action_first_roundtrip(self) -> None:
        """Community action-first entries survive set round-trip."""
        source = (
            "set policy-options policy-statement STMT term T then community add COMM1\n"
            "set policy-options policy-statement STMT term T then community delete COMM2\n"
        )
        ir = set_to_dict(source)
        roundtripped = dict_to_set(ir)
        assert roundtripped == source, f"IR was: {ir}"

    def test_key_alias_ieee_802_3ad(self) -> None:
        """Key alias: ieee-802.3ad resolves to 802.3ad for schema lookup."""
        source = (
            "set interfaces ae0 aggregated-ether-options lacp force-up\n"
            "set interfaces ae0 aggregated-ether-options lacp active\n"
        )
        ir = set_to_dict(source)
        iface = ir["interfaces"]["interface"][0]
        assert iface["name"] == "ae0"
        assert "aggregated-ether-options" in iface

    def test_key_alias_ieee_802_3ad_roundtrip(self) -> None:
        """802.3ad round-trips through set output (bundle is nk, omitted)."""
        source = "set interfaces ge-0/0/0 ether-options 802.3ad ae22\n"
        ir = set_to_dict(source)
        # IR stores 802.3ad (the schema/conf keyword), with bundle as nk child
        iface = ir["interfaces"]["interface"][0]
        assert "802.3ad" in iface["ether-options"]
        assert iface["ether-options"]["802.3ad"]["bundle"] == "ae22"
        roundtripped = dict_to_set(ir)
        assert roundtripped == source, f"IR was: {ir}"

    def test_key_alias_ieee_802_3ad_from_json(self) -> None:
        """JSON key ieee-802.3ad maps to 802.3ad in output."""
        # JSON uses ieee-802.3ad, output should use 802.3ad
        ir = {
            "interfaces": {
                "interface": [
                    {"name": "ge-0/0/0", "ether-options": {"ieee-802.3ad": {"bundle": "ae22"}}}
                ]
            }
        }
        result = dict_to_set(ir)
        assert "802.3ad ae22" in result
        assert "ieee-802.3ad" not in result

    def test_attributes_match_roundtrip(self) -> None:
        """Bug 5: attributes-match round-trips through set output."""
        source = (
            "set event-options policy test-policy "
            'attributes-match ping_test_failed.test-owner matches "^inet6-ping-uptime$"\n'
        )
        ir = set_to_dict(source)
        roundtripped = dict_to_set(ir)
        assert roundtripped == source, f"IR was: {ir}"


# ── Deactivate ordering ────────────────────────────────────────────────


# ── Partial config: transparent lookup without parent ────────────────


class TestPartialConfigTransparentLookup:
    """When set commands lack the parent keyword (e.g., 'interfaces'),
    the child-scan logic should still resolve transparent named lists."""

    def test_interface_without_parent(self) -> None:
        """set ge-0/0/0 description 'foo' produces nested interfaces.interface."""
        result = set_to_dict('set ge-0/0/0 description "foo"')
        assert "interfaces" in result
        iface = result["interfaces"]["interface"]
        assert isinstance(iface, list)
        assert len(iface) == 1
        assert iface[0]["name"] == "ge-0/0/0"
        assert iface[0]["description"] == "foo"

    def test_loopback_without_parent(self) -> None:
        """set lo0 unit 0 family inet address ... produces proper nesting."""
        result = set_to_dict("set lo0 unit 0 family inet address 10.0.36.103/32")
        assert "interfaces" in result
        iface = result["interfaces"]["interface"]
        assert isinstance(iface, list)
        assert iface[0]["name"] == "lo0"
        assert iface[0]["unit"][0]["name"] == "0"
        assert iface[0]["unit"][0]["family"]["inet"]["address"] == [{"name": "10.0.36.103/32"}]

    def test_ae_without_parent(self) -> None:
        """set ae100 mtu 9192 works via child-scan."""
        result = set_to_dict("set ae100 mtu 9192")
        assert "interfaces" in result
        iface = result["interfaces"]["interface"]
        assert isinstance(iface, list)
        assert iface[0]["name"] == "ae100"
        assert iface[0]["mtu"] == "9192"

    def test_deactivate_without_parent(self) -> None:
        """deactivate ge-0/0/0 applies inactive attribute via child-scan."""
        source = 'set ge-0/0/0 description "uplink"\ndeactivate ge-0/0/0\n'
        result = set_to_dict(source)
        assert "interfaces" in result
        entry = result["interfaces"]["interface"][0]
        assert entry["@"]["inactive"] is True

    def test_unknown_token_still_flattens(self) -> None:
        """Truly unknown tokens still get the flat-key fallback."""
        result = set_to_dict("set xyzzy-nonexistent-thing some-value")
        # Should NOT create any known parent — falls through to flat key
        assert "xyzzy-nonexistent-thing some-value" in result


# ── Transparent list key (tk flag) ───────────────────────────────────


class TestTransparentListKey:
    """Tests for transparent-list-key children (tk flag) like
    prefix-list-item and syslog file contents."""

    def test_prefix_list_item_single(self) -> None:
        """prefix-list-item entry is created for a single prefix."""
        result = set_to_dict("set policy-options prefix-list MY-LIST 127.0.0.1/32")
        pl = result["policy-options"]["prefix-list"][0]
        assert pl["name"] == "MY-LIST"
        assert pl["prefix-list-item"] == [{"name": "127.0.0.1/32"}]

    def test_prefix_list_item_multiple(self) -> None:
        """Multiple prefixes accumulate in the same prefix-list-item list."""
        source = (
            "set policy-options prefix-list MY-LIST 127.0.0.1/32\n"
            "set policy-options prefix-list MY-LIST 10.0.0.0/8\n"
        )
        result = set_to_dict(source)
        pl = result["policy-options"]["prefix-list"][0]
        assert pl["name"] == "MY-LIST"
        items = pl["prefix-list-item"]
        assert len(items) == 2
        assert items[0]["name"] == "127.0.0.1/32"
        assert items[1]["name"] == "10.0.0.0/8"

    def test_syslog_contents_with_level(self) -> None:
        """Syslog file contents entry preserves the facility and level."""
        result = set_to_dict("set system syslog file messages interactive-commands any")
        contents = result["system"]["syslog"]["file"][0]["contents"]
        assert isinstance(contents, list)
        assert len(contents) == 1
        assert contents[0]["name"] == "interactive-commands"
        assert contents[0]["any"] == [None]

    def test_syslog_contents_multiple_facilities(self) -> None:
        """Multiple syslog facilities create separate contents entries."""
        source = (
            "set system syslog file messages interactive-commands any\n"
            "set system syslog file messages any notice\n"
        )
        result = set_to_dict(source)
        contents = result["system"]["syslog"]["file"][0]["contents"]
        assert len(contents) == 2
        names = [c["name"] for c in contents]
        assert "interactive-commands" in names
        assert "any" in names

    def test_deactivate_prefix_list_item(self) -> None:
        """Deactivate targets a prefix-list-item entry correctly."""
        source = (
            "set policy-options prefix-list MY-LIST 10.0.0.0/8\n"
            "deactivate policy-options prefix-list MY-LIST 10.0.0.0/8\n"
        )
        result = set_to_dict(source)
        item = result["policy-options"]["prefix-list"][0]["prefix-list-item"][0]
        assert item["name"] == "10.0.0.0/8"
        assert item["@"]["inactive"] is True


class TestDeactivateOrdering:
    def test_deactivate_appears_near_set(self) -> None:
        """Deactivate lines appear right after related set lines, not at end."""
        source = (
            "set interfaces ge-0/0/0 description uplink\n"
            "deactivate interfaces ge-0/0/0\n"
            "set interfaces ge-0/0/1 description downlink\n"
        )
        ir = set_to_dict(source)
        result = dict_to_set(ir)
        lines = result.strip().split("\n")
        # deactivate should come right after the related set, not at the end
        deact_idx = next(
            idx
            for idx, line in enumerate(lines)
            if "ge-0/0/0" in line and line.startswith("deactivate")
        )
        other_set_idx = next(
            idx for idx, line in enumerate(lines) if "ge-0/0/1" in line and line.startswith("set")
        )
        assert deact_idx < other_set_idx, (
            f"deactivate at {deact_idx} should come before set ge-0/0/1 at {other_set_idx}"
        )

    def test_protect_appears_near_set(self) -> None:
        """Protect lines appear right after related set lines."""
        source = (
            "set system host-name r1\n"
            "protect system\n"
            "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n"
        )
        ir = set_to_dict(source)
        result = dict_to_set(ir)
        lines = result.strip().split("\n")
        protect_idx = next(idx for idx, line in enumerate(lines) if line.startswith("protect"))
        route_idx = next(idx for idx, line in enumerate(lines) if "routing-options" in line)
        assert protect_idx < route_idx


# ── Round-trip: dict→set→dict ────────────────────────────────────────


ROUND_TRIP_CONFIGS = [
    {"system": {"host-name": "r1"}},
    {"system": {"services": {"ssh": {"root-login": "deny"}}}},
    {
        "interfaces": {
            "interface": [
                {"name": "ge-0/0/0", "description": "uplink"},
                {"name": "ge-0/0/1", "description": "downlink"},
            ]
        }
    },
    {
        "interfaces": {
            "interface": [
                {
                    "name": "ge-0/0/0",
                    "unit": [
                        {
                            "name": "0",
                            "family": {"inet": {"address": [{"name": "10.0.0.1/24"}]}},
                        }
                    ],
                }
            ]
        }
    },
    {
        "system": {
            "host-name": "r1",
            "domain-name": "example.com",
            "name-server": ["8.8.8.8", "8.8.4.4"],
        }
    },
    {"system": {"@": {"inactive": True}, "host-name": "r1"}},
    {"routing-options": {"static": {"route": [{"name": "0.0.0.0/0", "next-hop": "10.0.0.1"}]}}},
    {
        "firewall": {
            "family": {
                "inet": {
                    "filter": [
                        {
                            "name": "PROTECT",
                            "term": [
                                {
                                    "name": "accept-ssh",
                                    "from": {
                                        "protocol": "tcp",
                                        "destination-port": "ssh",
                                    },
                                    "then": {"accept": [None]},
                                }
                            ],
                        }
                    ],
                }
            }
        }
    },
]


class TestDictSetDictRoundTrip:
    """dict→set→dict round-trip: the IR dict survives a set conversion.

    Because the set format is lossy (can't distinguish bare-string list
    entries from dict entries with only a 'name' key), we compare via
    set output rather than exact dict equality.
    """

    @pytest.mark.parametrize("config", ROUND_TRIP_CONFIGS)
    def test_roundtrip_via_set(self, config: dict) -> None:
        set_text = dict_to_set(config)
        roundtripped = set_to_dict(set_text)
        assert dict_to_set(roundtripped) == set_text, (
            f"Set output differs after round-trip:\n{set_text}"
        )


# ── Round-trip: set→dict→set ────────────────────────────────────────


SET_ROUND_TRIP_SOURCES = [
    "set system host-name r1\n",
    "set system services ssh root-login deny\n",
    "set interfaces ge-0/0/0 description uplink\nset interfaces ge-0/0/1 description downlink\n",
    "set interfaces ge-0/0/0 unit 0 family inet address 10.0.0.1/24\n",
    (
        "set system host-name r1\nset system domain-name example.com\n"
        "set system name-server 8.8.8.8\nset system name-server 8.8.4.4\n"
    ),
    "deactivate system\nset system host-name r1\n",
    "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n",
    (
        "set firewall family inet filter PROTECT term accept-ssh from protocol tcp\n"
        "set firewall family inet filter PROTECT term accept-ssh from destination-port ssh\n"
        "set firewall family inet filter PROTECT term accept-ssh then accept\n"
    ),
]


class TestSetDictSetRoundTrip:
    """set→dict→set round-trip: set commands survive a dict conversion."""

    @pytest.mark.parametrize("source", SET_ROUND_TRIP_SOURCES)
    def test_roundtrip(self, source: str) -> None:
        ir = set_to_dict(source)
        roundtripped = dict_to_set(ir)
        assert roundtripped == source, f"IR was: {ir}"
