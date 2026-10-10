"""Tests for the IP anonymization rule."""

from __future__ import annotations

import copy

from junoscfg.anonymize import anonymize
from junoscfg.anonymize.config import AnonymizeConfig
from junoscfg.anonymize.rules.ip import IpRule


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
        """qualified-next-hop named-list key with an IPv4 address."""
        rule = self._make_rule()
        path = ["routing-options", "static", "route", "qualified-next-hop", "name"]
        assert rule.matches("10.0.0.1", {"L": True, "tr": "qualified-nh-obj"}, path)

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
        assert rule.matches(ipv6, {"L": True, "tr": "qualified-nh-obj"}, path)


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

    def test_deterministic_with_same_salt(self) -> None:
        rule1 = IpRule(AnonymizeConfig(ips=True, salt="same-salt"))
        rule2 = IpRule(AnonymizeConfig(ips=True, salt="same-salt"))
        assert rule1.transform("10.1.2.3") == rule2.transform("10.1.2.3")

    def test_different_salt_different_output(self) -> None:
        rule1 = IpRule(AnonymizeConfig(ips=True, salt="salt-a"))
        rule2 = IpRule(AnonymizeConfig(ips=True, salt="salt-b"))
        assert rule1.transform("10.1.2.3") != rule2.transform("10.1.2.3")

    def test_consistency_same_ip_same_output(self) -> None:
        """Same IP address should always produce the same output."""
        rule = IpRule(AnonymizeConfig(ips=True, salt="test"))
        first = rule.transform("10.1.2.3")
        second = rule.transform("10.1.2.3")
        assert first == second

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

    def test_get_mapping_tracks_transformations(self) -> None:
        rule = IpRule(AnonymizeConfig(ips=True, salt="test"))
        rule.transform("10.1.2.3")
        rule.transform("10.4.5.6")
        mapping = rule.get_mapping()
        assert "10.1.2.3" in mapping
        assert "10.4.5.6" in mapping


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

    def test_mapping_returned(self, sample_ir_ips: dict, ip_config: AnonymizeConfig) -> None:
        result = anonymize(sample_ir_ips, ip_config)
        assert "ip" in result.mapping
        assert "10.1.2.3/24" in result.mapping["ip"]

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

    def test_ips_in_strings_disabled_by_default(self) -> None:
        """Without ips_in_strings, embedded IPs are NOT replaced."""
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
            },
        }
        result = anonymize(ir, cfg)
        host_val = result.ir["configuration"]["security"]["ssh-known-hosts"]["host"][0]["name"]
        # With ips_in_strings disabled, the embedded IP should still be there
        assert "10.1.2.3" in host_val

    def test_no_rules_enabled_returns_unchanged(self) -> None:
        cfg = AnonymizeConfig()
        ir = {"configuration": {"system": {"host-name": "r1"}}}
        original = copy.deepcopy(ir)
        result = anonymize(ir, cfg)
        assert result.ir == original
        assert result.mapping == {}
