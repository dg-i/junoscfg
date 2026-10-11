"""Tests for the IP anonymization rule.

What every rule keeps -- determinism, the salt, consistency, the mapping and
revert -- is `tests/contract/test_every_rule.py`; this file keeps what is the
IP rule's own: which leaves it takes and the form of its replacements.
"""

from __future__ import annotations

import copy
import dataclasses
import json
from typing import Any

import pytest

from junoscfg.anonymize import AnonymizeConfig, IpRule, anonymize

# Minimal IR with IP addresses for unit testing
SAMPLE_IR_WITH_IPS: dict[str, Any] = {
    "configuration": {
        "system": {"host-name": "router1"},
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
    },
}

# IR with multiple IP fields across different sections
SAMPLE_IR_MULTI_IP: dict[str, Any] = {
    "configuration": {
        "system": {
            "host-name": "router1",
            "name-server": [{"name": "8.8.8.8"}, {"name": "8.8.4.4"}],
        },
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
    },
}


@pytest.fixture
def ip_config() -> AnonymizeConfig:
    """Config with only IP anonymization enabled and a fixed salt."""
    return AnonymizeConfig(ips=True, salt="test-salt-42")


@pytest.fixture
def sample_ir_ips() -> dict[str, Any]:
    """IR with IP addresses."""
    return copy.deepcopy(SAMPLE_IR_WITH_IPS)


@pytest.fixture
def sample_ir_multi_ip() -> dict[str, Any]:
    """IR with multiple IP addresses."""
    return copy.deepcopy(SAMPLE_IR_MULTI_IP)


class TestIpRuleMatches:
    def _make_rule(self, **kwargs) -> IpRule:
        return IpRule(AnonymizeConfig(ips=True, salt="test", **kwargs))

    def test_matches_ipv4addr(self) -> None:
        rule = self._make_rule()
        assert rule.matches("10.0.0.1", {"tr": "ipv4addr", "l": True}, ["x"])

    def test_matches_ipv6addr(self) -> None:
        rule = self._make_rule()
        assert rule.matches("2001:db8::1", {"tr": "ipv6addr", "l": True}, ["x"])

    def test_matches_ipaddr(self) -> None:
        rule = self._make_rule()
        assert rule.matches("10.0.0.1", {"tr": "ipaddr", "l": True}, ["x"])

    def test_matches_ipprefix(self) -> None:
        rule = self._make_rule()
        assert rule.matches("10.0.0.0/8", {"tr": "ipprefix", "l": True}, ["x"])

    def test_matches_ipaddr_or_interface(self) -> None:
        rule = self._make_rule()
        assert rule.matches("10.0.0.1", {"tr": "ipaddr-or-interface", "l": True}, ["x"])

    def test_matches_case_insensitive(self) -> None:
        rule = self._make_rule()
        assert rule.matches("10.0.0.1", {"tr": "IPv4Addr", "l": True}, ["x"])

    def test_no_match_on_string_type(self) -> None:
        rule = self._make_rule()
        assert not rule.matches("hello", {"tr": "string", "l": True}, ["x"])

    def test_no_match_without_type_ref(self) -> None:
        rule = self._make_rule()
        assert not rule.matches("hello", {"l": True}, ["x"])

    def test_matches_qualified_next_hop_ipv4(self) -> None:
        """qualified-next-hop named-list key with an IPv4 address, offered as the
        leaf the tree declares for it (`atr` `ipaddr-or-interface`): the type
        answers, not the list's name (change anonymize-every-placed-value)."""
        rule = self._make_rule()
        path = ["routing-options", "static", "route", "qualified-next-hop", "name"]
        leaf = {"l": True, "nk": True, "atr": "ipaddr-or-interface"}
        assert rule.matches("10.0.0.1", leaf, path)

    def test_matches_qualified_next_hop_ipv6(self) -> None:
        """qualified-next-hop named-list key with an IPv6 address."""
        rule = self._make_rule()
        path = [
            "routing-instances",
            "instance",
            "routing-options",
            "rib",
            "static",
            "route",
            "qualified-next-hop",
            "name",
        ]
        ipv6 = "3ffe:0b00:0002:0::901:ffff"
        assert rule.matches(ipv6, {"l": True, "nk": True, "atr": "ipaddr-or-interface"}, path)


class TestIpRuleTransform:
    def test_ipv4_address_is_anonymized(self) -> None:
        rule = IpRule(AnonymizeConfig(ips=True, salt="test-salt"))
        result = rule.transform("10.1.2.3")
        assert result != "10.1.2.3"
        # Private 10.x stays in 10.x range (Cat A range-preserved)
        assert result.startswith("10.")

    def test_ipv4_prefix_preserves_format(self) -> None:
        rule = IpRule(AnonymizeConfig(ips=True, salt="test-salt"))
        result = rule.transform("10.1.2.3/24")
        assert "/" in result
        assert result.endswith("/24")
        assert result != "10.1.2.3/24"

    def test_private_range_preserved(self) -> None:
        """Private IPs stay in their original range (Cat A)."""
        rule = IpRule(AnonymizeConfig(ips=True, salt="test"))
        # 192.168.x.x should stay in 192.168.x.x
        result = rule.transform("192.168.1.100")
        assert result.startswith("192.168.")

    def test_loopback_passthrough(self) -> None:
        """Loopback addresses are pass-through (Cat B)."""
        rule = IpRule(AnonymizeConfig(ips=True, salt="test"))
        result = rule.transform("127.0.0.1")
        assert result == "127.0.0.1"


class TestIpRuleOptions:
    def test_preserve_prefixes(self) -> None:
        rule = IpRule(AnonymizeConfig(ips=True, salt="test", preserve_prefixes=["10.1.0.0/16"]))
        # IPs in the pass-through range should be unchanged
        result = rule.transform("10.1.2.3")
        assert result == "10.1.2.3"

    def test_ignore_subnets(self) -> None:
        """With ignore_subnets, 192.168.x.x is treated as public (Cat C)."""
        rule = IpRule(AnonymizeConfig(ips=True, salt="test", ignore_subnets=True))
        result = rule.transform("192.168.1.1")
        # Should NOT be in 192.168.x.x range anymore
        assert not result.startswith("192.168.")

    def test_ignore_reserved(self) -> None:
        """With ignore_reserved, even loopback is anonymized."""
        rule = IpRule(AnonymizeConfig(ips=True, salt="test", ignore_reserved=True))
        result = rule.transform("127.0.0.1")
        assert result != "127.0.0.1"


class TestIpRuleReplaceIpsInString:
    """Tests for replace_ips_in_string (embedded IP replacement)."""

    def _make_rule(self, **kwargs) -> IpRule:
        return IpRule(AnonymizeConfig(ips=True, salt="string-test", **kwargs))

    def test_ip_in_url(self) -> None:
        rule = self._make_rule()
        result = rule.replace_ips_in_string("scp://user@192.168.1.100:22/path")
        assert "192.168." in result  # Private range preserved
        assert "192.168.1.100" not in result

    def test_ip_in_host_combo(self) -> None:
        rule = self._make_rule()
        result = rule.replace_ips_in_string("hostname.example.com,10.1.2.3")
        assert "hostname.example.com," in result
        assert "10.1.2.3" not in result

    def test_no_ip_unchanged(self) -> None:
        rule = self._make_rule()
        result = rule.replace_ips_in_string("just a regular string")
        assert result == "just a regular string"

    def test_standalone_ip_also_replaced(self) -> None:
        rule = self._make_rule()
        result = rule.replace_ips_in_string("10.1.2.3")
        assert result != "10.1.2.3"

    def test_ip_with_cidr_in_string(self) -> None:
        rule = self._make_rule()
        result = rule.replace_ips_in_string("prefix 10.1.2.0/24 is blocked")
        assert "10.1.2.0/24" not in result
        assert "/24" in result  # CIDR preserved

    def test_multiple_ips_in_string(self) -> None:
        rule = self._make_rule()
        result = rule.replace_ips_in_string("from 10.1.2.3 to 10.4.5.6")
        assert "10.1.2.3" not in result
        assert "10.4.5.6" not in result

    def test_deterministic(self) -> None:
        rule = self._make_rule()
        r1 = rule.replace_ips_in_string("http://10.1.2.3/page")
        r2 = rule.replace_ips_in_string("http://10.1.2.3/page")
        assert r1 == r2

    def test_loopback_passthrough(self) -> None:
        rule = self._make_rule()
        result = rule.replace_ips_in_string("connect to 127.0.0.1:8080")
        assert "127.0.0.1" in result


class TestIpAnonymizeIntegration:
    """Test the full anonymize() function with IP rule on real-ish IR."""

    def test_anonymize_single_ip(self, sample_ir_ips: dict, ip_config: AnonymizeConfig) -> None:
        result = anonymize(sample_ir_ips, ip_config)
        ir = result.ir
        addr = ir["configuration"]["interfaces"]["interface"][0]["unit"][0]["family"]["inet"][
            "address"
        ][0]["name"]
        assert addr != "10.1.2.3/24"
        assert addr.startswith("10.")
        assert addr.endswith("/24")

    def test_non_ip_fields_unchanged(self, sample_ir_ips: dict, ip_config: AnonymizeConfig) -> None:
        result = anonymize(sample_ir_ips, ip_config)
        ir = result.ir
        # host-name is not an IP field
        assert ir["configuration"]["system"]["host-name"] == "router1"
        # interface name is not an IP field
        assert ir["configuration"]["interfaces"]["interface"][0]["name"] == "ge-0/0/0"

    def test_multiple_ips_all_anonymized(
        self, sample_ir_multi_ip: dict, ip_config: AnonymizeConfig
    ) -> None:
        result = anonymize(sample_ir_multi_ip, ip_config)
        ir = result.ir

        # Check name-server IPs
        ns = ir["configuration"]["system"]["name-server"]
        assert ns[0]["name"] != "8.8.8.8"
        assert ns[1]["name"] != "8.8.4.4"

        # Check interface IPs
        ge_addr = ir["configuration"]["interfaces"]["interface"][0]["unit"][0]["family"]["inet"][
            "address"
        ][0]["name"]
        assert ge_addr != "10.1.2.3/24"

        lo_addr = ir["configuration"]["interfaces"]["interface"][1]["unit"][0]["family"]["inet"][
            "address"
        ][0]["name"]
        assert lo_addr != "192.168.1.1/32"

    def test_ips_in_strings_second_pass(self) -> None:
        """With ips_in_strings, IPs in URLs and host combos are replaced."""
        cfg = AnonymizeConfig(ips=True, salt="str-test", ips_in_strings=True)
        ir = {
            "configuration": {
                "security": {
                    "ssh-known-hosts": {
                        "host": [
                            {"name": "server01.example.com,10.1.2.3"},
                        ],
                    },
                },
                "system": {
                    "archival": {
                        "configuration": {
                            "archive-sites": [
                                {"name": "scp://backup@10.4.5.6:22/data"},
                            ],
                        },
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        host_val = result.ir["configuration"]["security"]["ssh-known-hosts"]["host"][0]["name"]
        assert "10.1.2.3" not in host_val
        assert "server01.example.com," in host_val

        archive_val = result.ir["configuration"]["system"]["archival"]["configuration"][
            "archive-sites"
        ][0]["name"]
        assert "10.4.5.6" not in archive_val
        assert "scp://backup@" in archive_val

    def test_an_address_inside_free_text_is_replaced(self) -> None:
        """Without ips_in_strings an address beside other text is replaced: it
        is the IP rule's whatever the leaf's type. This test asserted the
        opposite, the leak ANON-P5 (specification challenge S1 of change
        anonymize-embedded-values; spec anonymization/embedded-values)."""
        cfg = AnonymizeConfig(ips=True, salt="str-test")
        ir = {
            "configuration": {
                "security": {
                    "ssh-known-hosts": {
                        "host": [
                            {"name": "server01.example.com,10.1.2.3"},
                        ],
                    },
                },
                "system": {
                    "archival": {
                        "configuration": {
                            "archive-sites": [{"name": "scp://admin@203.0.114.5/path"}],
                        },
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        cfg_out = result.ir["configuration"]
        host_val = cfg_out["security"]["ssh-known-hosts"]["host"][0]["name"]
        assert "10.1.2.3" not in host_val
        assert host_val.startswith("server01.example.com,")
        [site] = cfg_out["system"]["archival"]["configuration"]["archive-sites"]
        assert site["name"] == f"scp://admin@{result.mapping['ip']['203.0.114.5']}/path"


def _addresses(*addresses: str) -> dict[str, Any]:
    """One interface unit holding *addresses*."""
    inet = {"address": [{"name": address} for address in addresses]}
    unit = {"name": "0", "family": {"inet": inet}}
    return {"configuration": {"interfaces": {"interface": [{"name": "ge-0/0/0", "unit": [unit]}]}}}


class TestAPassThroughCollision:
    """An address whose replacement falls inside a preserved prefix is refused,
    and the refusal names neither address.

    `ipanon`'s `PassThroughCollisionError` read "Anonymized IP <replacement>
    (from <original>) collides with --pass-through prefix ...": the pair the
    mapping holds, on stderr beside the output (NEW-R10, spec
    anonymization/placed-values). The error keeps its class.
    """

    def test_the_error_names_no_address(self) -> None:
        from ipanon import PassThroughCollisionError

        replacement = IpRule(AnonymizeConfig(ips=True, salt="test")).transform("203.0.114.9")
        rule = IpRule(
            AnonymizeConfig(ips=True, salt="test", preserve_prefixes=[f"{replacement}/32"])
        )
        with pytest.raises(PassThroughCollisionError) as raised:
            rule.transform("203.0.114.9")
        message = str(raised.value)
        assert "collides" in message
        assert "203.0.114.9" not in message
        assert replacement not in message


class TestNetworksAutoNeedsSourceText:
    """``networks=["auto"]`` scans the configuration text for subnets.

    It used to read that text from ``_source_text``, attached dynamically by
    ``cli.py`` with a ``type: ignore`` and read back through ``hasattr``. A
    caller using the documented Python API never set it, so asking for
    auto-detection silently did nothing. ``source_text`` is a declared field
    now, and asking for auto without it is an error rather than a no-op. The
    CLI, the one caller that sets it, is
    `tests/unit/cli/test_cli.py::TestAnonymizeOptions::test_networks_auto_scans_the_input_for_subnets`.
    """

    def test_auto_without_source_text_is_an_error(self) -> None:
        config = AnonymizeConfig(ips=True, networks=["auto"], salt="pin-salt")
        config.expand_all()
        with pytest.raises(ValueError, match="source_text"):
            anonymize(_addresses("203.0.114.1/24"), config)

    def test_auto_with_source_text_preserves_subnet_structure(self) -> None:
        """What `auto` is for: host bits survive within a subnet.

        Asserting only that the address changed would pass even if
        auto-detection found nothing, because plain IP anonymization changes it
        too. The point of `auto` is that two addresses in one subnet stay in
        one subnet, keeping their host bits.
        """
        config = AnonymizeConfig(
            ips=True,
            networks=["auto"],
            salt="pin-salt",
            source_text=(
                "set interfaces ge-0/0/0 unit 0 family inet address 203.0.114.1/24\n"
                "set interfaces ge-0/0/0 unit 0 family inet address 203.0.114.254/24\n"
            ),
        )
        config.expand_all()
        result = anonymize(_addresses("203.0.114.1/24", "203.0.114.254/24"), config)
        unit = result.ir["configuration"]["interfaces"]["interface"][0]["unit"][0]
        first, second = (a["name"] for a in unit["family"]["inet"]["address"])
        assert first != "203.0.114.1/24"
        # host bits kept, and both still in the same /24
        assert first.endswith(".1/24")
        assert second.endswith(".254/24")
        assert first.rsplit(".", 1)[0] == second.rsplit(".", 1)[0]

    def test_source_text_is_a_declared_field(self) -> None:
        names = {f.name for f in dataclasses.fields(AnonymizeConfig)}
        assert "source_text" in names
        assert "_source_text" not in names


class TestTheLeafsTypeAnswers:
    """The IP rule takes a value that parses as an address or prefix on a leaf
    whose type can hold one, and nothing else.

    It ignored `host`, `hostname` and `ipprefix-only` (the tacplus-server
    addresses of the device example, ANON-P2, NEW-A-N6), decided every key of
    15 lists by the list's name, handed any value of an address type to the
    address anonymizer, which crashes on an interface name (NEW-R8), and left
    the untyped `apply-macro` value as written. Free text and `areaid` are no
    address types: an SNMP OID and an area are syntax (Test/Challenge finding
    6, ruling); the list's name answers only for the keys of those 15 lists the
    tree types as free text (`syslog host`), and the leaf's name for
    `ipv6-router-id` and BGP `cluster` (specification challenge S4). Change
    anonymize-every-placed-value; spec anonymization/placed-values.
    """

    @staticmethod
    def _rule() -> IpRule:
        return IpRule(AnonymizeConfig(ips=True, salt="test"))

    @pytest.mark.parametrize(
        "node",
        [
            {"l": True, "tr": "host"},
            {"l": True, "tr": "hostname"},
            {"l": True, "nk": True, "atr": "hostname"},
            {"l": True, "atr": "ipprefix-only"},
            {"l": True},
            {},
        ],
        ids=lambda node: str(node.get("atr", node.get("tr", "untyped"))),
    )
    @pytest.mark.parametrize("value", ["203.0.114.49", "203.0.114.0/26", "3ffe:0b00::1"])
    def test_an_address_on_these_types_is_replaced(self, node: dict, value: str) -> None:
        assert self._rule().matches(value, node, ["x", "y"])

    @pytest.mark.parametrize("value", ["tacacs.example.net", "router1", "lo0.0"])
    @pytest.mark.parametrize("node", [{"l": True, "tr": "hostname"}, {"l": True}])
    def test_a_name_on_a_host_type_is_not(self, node: dict, value: str) -> None:
        assert not self._rule().matches(value, node, ["x", "y"])

    @pytest.mark.parametrize(
        "node",
        [
            {"l": True, "tr": "interface-name"},
            {"l": True, "tr": "xsd:unsignedInt"},
            {"l": True, "tr": "mac-addr"},
            {"l": True, "tr": "unreadable"},
            {"l": True, "tr": "policy-algebra"},
        ],
        ids=lambda node: node["tr"],
    )
    @pytest.mark.parametrize("parent", ["host", "route", "server", "neighbor"])
    def test_no_other_type_takes_an_address(self, node: dict, parent: str) -> None:
        """Not even as the key of a list whose name used to decide."""
        assert not self._rule().matches("203.0.114.49", node, ["x", parent, "name"])

    def test_an_address_on_an_enum_only_leaf_is_replaced(self) -> None:
        """An enum-only leaf (`ssh protocol-version`, ``{"l": True, "e": ...}``)
        names no type, so an address there is replaced, and no message of the
        run quotes it, `--strict` included (Test/Challenge finding 9 of change
        anonymize-every-placed-value, NEW-R9: fixed there by owner rule 5; this
        pins it)."""
        from junoscfg import FieldValidationError, Format, convert_config_result

        source = "set system services ssh protocol-version 203.0.114.9\n"
        config = AnonymizeConfig(ips=True, salt="test")
        assert self._rule().matches("203.0.114.9", {"l": True, "e": 16}, ["ssh", "x"])
        result = convert_config_result(
            source, from_format=Format.SET, to_format=Format.SET, anon_config=config
        )
        assert "203.0.114.9" not in result.output
        assert result.diagnostics, "the enum mismatch is reported"
        assert not any("203.0.114.9" in d.render() for d in result.diagnostics)
        with pytest.raises(FieldValidationError) as raised:
            convert_config_result(
                source,
                from_format=Format.SET,
                to_format=Format.SET,
                anon_config=config,
                strict=True,
            )
        assert "203.0.114.9" not in str(raised.value)

    @pytest.mark.parametrize(
        "line",
        [
            "set policy-options policy-statement P term T from interface ge-0/0/0.0",
            "set routing-options static route 198.51.100.0/24 next-hop ge-0/0/0.0",
        ],
    )
    def test_an_interface_name_never_reaches_the_address_anonymizer(self, line: str) -> None:
        """`ipaddr-or-interface` holds an interface name too; the run crashed."""
        from junoscfg import Format, convert_config

        out = convert_config(
            line,
            from_format=Format.SET,
            to_format=Format.SET,
            anon_config=AnonymizeConfig(ips=True, salt="test"),
        )
        assert "ge-0/0/0.0" in out

    @pytest.mark.parametrize(
        ("lines", "addresses"),
        [
            (
                ["set system tacplus-server 203.0.114.49 source-address 203.0.114.50"],
                {"203.0.114.49", "203.0.114.50"},
            ),
            (
                ['set system radius-server 203.0.114.51 secret "$9$ExAmPlEhAsH.KEY"'],
                {"203.0.114.51"},
            ),
            (["set snmp trap-group TG targets 203.0.114.53"], {"203.0.114.53"}),
            (
                ["set services nat rule R1 term T1 then translated source-prefix 203.0.114.0/26"],
                {"203.0.114.0/26"},
            ),
            (["set system syslog host 203.0.114.57 any any"], {"203.0.114.57"}),
            (["set system apply-macro M2 peer 203.0.114.8"], {"203.0.114.8"}),
            (
                [
                    "set routing-options router-id 203.0.114.61",
                    "set routing-options ipv6-router-id 203.0.114.61",
                ],
                {"203.0.114.61"},
            ),
            (["set protocols bgp group G cluster 203.0.114.60"], {"203.0.114.60"}),
        ],
        ids=[
            "tacplus-hostname",
            "radius-hostname",
            "trap-group-hostname",
            "nat-ipprefix-only",
            "syslog-host-free-text-key",
            "nested-apply-macro-untyped",
            "ipv6-router-id-string-s4",
            "bgp-cluster-areaid-s4",
        ],
    )
    def test_every_address_the_device_writes_there_is_replaced(
        self, lines: list[str], addresses: set[str]
    ) -> None:
        """Through the conversion, each address is replaced, alike everywhere,
        and the mapping names it."""
        from junoscfg import Format, convert_config
        from junoscfg.convert import to_dict

        config = AnonymizeConfig(ips=True, salt="test")
        source = "\n".join(lines) + "\n"
        ir = {"configuration": to_dict(source, "set")}
        result = anonymize(ir, config)
        assert addresses <= set(result.mapping.get("ip", {}))
        assert all(result.mapping["ip"][a] != a for a in addresses)
        out = convert_config(
            source,
            from_format=Format.SET,
            to_format=Format.SET,
            anon_config=AnonymizeConfig(ips=True, salt="test"),
        )
        words = {word for line in out.splitlines() for word in line.split()}
        assert not addresses & words, out
        assert {result.mapping["ip"][a] for a in addresses} <= words
        assert json.dumps(result.ir).count(result.mapping["ip"][next(iter(addresses))]) >= len(
            lines
        )

    @pytest.mark.parametrize(
        "line",
        [
            "set snmp view V oid 1.3.6.1 include",
            "set policy-options policy-statement P term T from area 0.0.0.0",
            "set policy-options policy-statement P term T from area 198.0.2.1",
            "set protocols bgp group G cluster 64496",
        ],
        ids=["snmp-oid", "from-area-backbone", "from-area", "bgp-cluster-integer"],
    )
    def test_syntax_shaped_like_an_address_is_unchanged(self, line: str) -> None:
        """An OID and an area are syntax, not addresses (ruling on Test/Challenge
        finding 6): free text and `areaid` take no address, but for
        `ipv6-router-id` and BGP `cluster` (S4), and an integer cluster is none."""
        from junoscfg import Format, convert_config

        config = AnonymizeConfig(ips=True, ignore_reserved=True, salt="test")
        out = convert_config(line, from_format=Format.SET, to_format=Format.SET, anon_config=config)
        assert out.strip() == line

    @pytest.mark.xfail(
        strict=True,
        reason="SPECIFICATION CHALLENGE S3 (pending the owner): under --anonymize-ignore-reserved "
        "`protocols ospf area 0.0.0.0` is rewritten through the list name `area`, as the base "
        "did; interim: base behaviour kept, not extended to `from area`",
    )
    def test_the_backbone_area_is_unchanged_s3(self) -> None:
        from junoscfg import Format, convert_config

        line = "set protocols ospf area 0.0.0.0 interface ge-0/0/0.0"
        config = AnonymizeConfig(ips=True, ignore_reserved=True, salt="test")
        out = convert_config(line, from_format=Format.SET, to_format=Format.SET, anon_config=config)
        assert out.strip() == line

    @pytest.mark.parametrize(
        ("text", "address"),
        [
            ("203.0.114.9/rack-4", "203.0.114.9"),
            ("203.0.114.0/24,", "203.0.114.0/24"),
            ("203.0.114.9/33", "203.0.114.9"),
            ("3ffe:0b00::1/129", "3ffe:0b00::1"),
            ("3ffe:0b00::1%ge-0/0/0.0", "3ffe:0b00::1"),
            ("203.0.114.9/", "203.0.114.9"),
        ],
    )
    def test_a_malformed_value_never_crashes(self, text: str, address: str) -> None:
        """Text beside an address is text: the address is replaced and the run
        goes on, on an untyped leaf, a typed leaf and content the walk cannot
        place (Test/Challenge finding 5); the address anonymizer raised on each."""
        rule = self._rule()
        for node in ({}, {"l": True, "tr": "ipaddr"}):
            assert rule.matches(text, node, ["x"])
            replaced = rule.transform(text)
            assert address not in replaced
            assert replaced.endswith(text[len(address) :])
        assert address not in (rule.lexical(f'"{text}"') or "")
        ir = {"configuration": {"system": {"bogus": f"peer {text}"}}}
        assert address not in json.dumps(anonymize(ir, AnonymizeConfig(ips=True, salt="t")).ir)

    @pytest.mark.parametrize(
        "line",
        [
            "set interfaces ge-0/0/0 description "
            '"nat64 64:ff9b::203.0.114.5 mapped ::ffff:203.0.114.5"',
            "set routing-options static route 198.51.100.0/24 next-hop ::ffff:203.0.114.5",
            "set routing-options static route 198.51.100.0/24 next-hop ::203.0.114.5",
        ],
        ids=["prose", "mapped-next-hop", "compatible-next-hop"],
    )
    def test_an_ipv4_address_inside_an_ipv6_form_is_replaced(self, line: str) -> None:
        """The address anonymizer keeps the IPv4-mapped, -compatible and NAT64
        blocks as they are, so `::ffff:203.0.114.5` kept the IPv4 address it
        names; the IPv4 address takes its own replacement and the IPv6 form
        stays (Test/Challenge T3, specification challenge S5)."""
        from junoscfg import Format, convert_config
        from junoscfg.anonymize import apply_revert
        from junoscfg.convert import to_dict

        source = {"configuration": to_dict(line, "set")}
        result = anonymize(json.loads(json.dumps(source)), AnonymizeConfig(ips=True, salt="test"))
        out = json.dumps(result.ir)
        assert "203.0.114.5" not in out
        assert result.mapping["ip"]["203.0.114.5"] in out
        assert apply_revert(result.ir, result.mapping) == source
        assert convert_config(line, from_format=Format.SET, to_format=Format.SET).strip() == line

    @pytest.mark.parametrize(
        "line",
        [
            "set routing-instances VRF-A route-distinguisher 203.0.114.65:100",
            "set routing-instances VRF-A vrf-target target:203.0.114.65:100",
            "set routing-instances VRF-A vrf-target import target:203.0.114.65:100",
        ],
        ids=["route-distinguisher", "vrf-target", "vrf-target-import"],
    )
    def test_an_address_inside_a_route_distinguisher_or_target_is_replaced(self, line: str) -> None:
        """A route distinguisher and a VRF target in their address form carry
        the router's loopback; the tree types them as free text. 75,279 JVD
        route distinguishers held one and passed `--anonymize-ips` as written
        (the proof that counts addresses inside words, specification challenges
        S4 and S5). The number after the address stays; an AS-form value
        (`target:64496:100`) holds no address and is unchanged."""
        from junoscfg import Format, convert_config

        config = AnonymizeConfig(ips=True, salt="test")
        out = convert_config(line, from_format=Format.SET, to_format=Format.SET, anon_config=config)
        assert "203.0.114.65" not in out
        assert out.strip().endswith(":100")
        as_form = line.replace("203.0.114.65", "64496")
        out = convert_config(
            as_form, from_format=Format.SET, to_format=Format.SET, anon_config=config
        )
        assert out.strip() == as_form

    def test_a_policy_community_matches_its_renamed_target(self) -> None:
        """`policy-options community ... members target:<address>:<n>` takes the
        pseudonym the `vrf-target` takes, so a `vrf-import` policy still matches
        the route target; AS-form, regular-expression and well-known members
        hold no address and stay (Reviewer R1)."""
        from junoscfg.anonymize import apply_revert
        from junoscfg.convert import to_dict

        source = (
            "set routing-instances VRF-A vrf-target target:203.0.114.1:100\n"
            "set policy-options community C1 members target:203.0.114.1:100\n"
            "set policy-options community C2 members origin:203.0.114.1:7\n"
            "set policy-options community C3 members target:64496:100\n"
            'set policy-options community C4 members "^target:10\\.0\\..*$"\n'
            "set policy-options community C5 members no-export\n"
        )
        ir = {"configuration": to_dict(source, "set")}
        original = json.loads(json.dumps(ir))
        result = anonymize(ir, AnonymizeConfig(ips=True, salt="test"))
        cfg = result.ir["configuration"]
        pseudonym = result.mapping["ip"]["203.0.114.1"]
        target = f"target:{pseudonym}:100"
        assert cfg["routing-instances"]["instance"][0]["vrf-target"]["community"] == target
        members = {c["name"]: c["members"] for c in cfg["policy-options"]["community"]}
        assert members["C1"] == [target]
        assert members["C2"] == [f"origin:{pseudonym}:7"]
        before = {
            c["name"]: c["members"]
            for c in original["configuration"]["policy-options"]["community"]
        }
        for name in ("C3", "C4", "C5"):
            assert members[name] == before[name]
        assert apply_revert(result.ir, result.mapping) == original
