"""Tests for the group/view name anonymization rule."""

from __future__ import annotations

from junoscfg.anonymize import anonymize
from junoscfg.anonymize.config import AnonymizeConfig
from junoscfg.anonymize.rules.group import GroupRule


class TestGroupRuleMatches:
    def _make_rule(self) -> GroupRule:
        return GroupRule(AnonymizeConfig(groups=True, salt="test"))

    def test_matches_config_group_name(self) -> None:
        rule = self._make_rule()
        path = ["groups", "name"]
        assert rule.matches("global-settings", {"l": True}, path)

    def test_matches_bgp_group_name(self) -> None:
        rule = self._make_rule()
        path = ["protocols", "bgp", "group", "name"]
        assert rule.matches("PEERS", {"l": True}, path)

    def test_matches_bgp_group_in_groups(self) -> None:
        rule = self._make_rule()
        path = ["groups", "protocols", "bgp", "group", "name"]
        assert rule.matches("inet-Upstream-AS64496", {"l": True}, path)

    def test_matches_snmp_view_name(self) -> None:
        rule = self._make_rule()
        path = ["snmp", "view", "name"]
        assert rule.matches("all", {"l": True}, path)

    def test_matches_snmp_group_name_field(self) -> None:
        rule = self._make_rule()
        path = ["snmp", "v3", "vacm", "security-to-group", "group-name"]
        assert rule.matches("snmp-group", {"l": True}, path)

    def test_matches_vacm_group_leaf(self) -> None:
        """VACM security-to-group.security-model[*].security-name[*].group leaf."""
        rule = self._make_rule()
        path = [
            "snmp",
            "v3",
            "vacm",
            "security-to-group",
            "security-model",
            "security-name",
            "group",
        ]
        assert rule.matches("snmp-group", {"l": True}, path)

    def test_matches_vacm_access_group_named_list_key(self) -> None:
        """VACM access.group[*].name named-list key."""
        rule = self._make_rule()
        path = ["snmp", "v3", "vacm", "access", "group", "name"]
        assert rule.matches("snmp-group", {"l": True}, path)

    def test_no_match_on_interface_name(self) -> None:
        rule = self._make_rule()
        path = ["interfaces", "interface", "name"]
        assert not rule.matches("ge-0/0/0", {"l": True}, path)

    def test_no_match_on_user_name(self) -> None:
        """User names should be handled by identity rule, not group rule."""
        rule = self._make_rule()
        path = ["system", "login", "user", "name"]
        assert not rule.matches("admin", {"l": True}, path)

    def test_no_match_on_firewall_term(self) -> None:
        rule = self._make_rule()
        path = ["firewall", "filter", "term", "name"]
        assert not rule.matches("allow-ssh", {"l": True}, path)

    def test_no_match_empty_path(self) -> None:
        rule = self._make_rule()
        assert not rule.matches("x", {"l": True}, [])


class TestGroupRuleTransform:
    def _make_rule(self, salt: str = "test-salt") -> GroupRule:
        return GroupRule(AnonymizeConfig(groups=True, salt=salt))

    def test_group_prefix(self) -> None:
        rule = self._make_rule()
        result = rule.transform("global-settings")
        assert result.startswith("group_")
        assert result != "global-settings"

    def test_deterministic(self) -> None:
        rule1 = self._make_rule(salt="same")
        rule2 = self._make_rule(salt="same")
        assert rule1.transform("PEERS") == rule2.transform("PEERS")

    def test_different_salt(self) -> None:
        rule1 = self._make_rule(salt="a")
        rule2 = self._make_rule(salt="b")
        assert rule1.transform("PEERS") != rule2.transform("PEERS")

    def test_consistency(self) -> None:
        rule = self._make_rule()
        assert rule.transform("PEERS") == rule.transform("PEERS")

    def test_different_groups(self) -> None:
        rule = self._make_rule()
        assert rule.transform("group-a") != rule.transform("group-b")

    def test_get_mapping(self) -> None:
        rule = self._make_rule()
        rule.transform("group-a")
        rule.transform("group-b")
        mapping = rule.get_mapping()
        assert "group-a" in mapping
        assert "group-b" in mapping


class TestGroupAnonymizeIntegration:
    """Test the full anonymize() function with group rule."""

    def test_bgp_group_names_anonymized(self) -> None:
        cfg = AnonymizeConfig(groups=True, salt="test")
        ir = {
            "configuration": {
                "protocols": {
                    "bgp": {
                        "group": [
                            {
                                "name": "inet-Upstream-AS64496",
                                "type": "external",
                            },
                            {
                                "name": "inet-Internal-Full",
                                "type": "internal",
                            },
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        groups = result.ir["configuration"]["protocols"]["bgp"]["group"]
        assert groups[0]["name"] != "inet-Upstream-AS64496"
        assert groups[0]["name"].startswith("group_")
        assert groups[1]["name"] != "inet-Internal-Full"
        # type should NOT be anonymized
        assert groups[0]["type"] == "external"
        assert "group" in result.mapping

    def test_snmp_view_anonymized(self) -> None:
        cfg = AnonymizeConfig(groups=True, salt="test")
        ir = {
            "configuration": {
                "snmp": {
                    "view": [
                        {
                            "name": "all",
                            "oid": [{"name": ".1", "include": True}],
                        },
                    ],
                },
            },
        }
        result = anonymize(ir, cfg)
        assert result.ir["configuration"]["snmp"]["view"][0]["name"] != "all"
        assert result.ir["configuration"]["snmp"]["view"][0]["name"].startswith("group_")

    def test_config_group_names_anonymized(self) -> None:
        """Configuration group names in the groups array should be anonymized."""
        cfg = AnonymizeConfig(groups=True, salt="test")
        ir = {
            "configuration": {
                "groups": [
                    {
                        "name": "global-settings",
                        "system": {"host-name": "router1"},
                    },
                ],
            },
        }
        result = anonymize(ir, cfg)
        group = result.ir["configuration"]["groups"][0]
        assert group["name"] != "global-settings"
        assert group["name"].startswith("group_")
        # Inner content should be untouched (groups rule only handles names)
        assert group["system"]["host-name"] == "router1"

    def test_group_with_all_rules(self) -> None:
        """Group rule coexists with password, IP, community, and identity rules."""
        cfg = AnonymizeConfig(
            groups=True,
            passwords=True,
            ips=True,
            communities=True,
            identities=True,
            salt="test",
        )
        ir = {
            "configuration": {
                "protocols": {
                    "bgp": {
                        "group": [
                            {
                                "name": "PEERS",
                                "authentication-key": "$9$abc123",
                                "neighbor": [{"name": "10.0.0.1"}],
                            },
                        ],
                    },
                },
                "system": {
                    "login": {
                        "user": [{"name": "admin"}],
                    },
                },
                "snmp": {
                    "community": [{"name": "public"}],
                },
            },
        }
        result = anonymize(ir, cfg)
        # BGP group name anonymized
        bgp = result.ir["configuration"]["protocols"]["bgp"]["group"][0]
        assert bgp["name"] != "PEERS"
        # Auth key anonymized by password rule
        assert bgp["authentication-key"] != "$9$abc123"
        # Neighbor IP anonymized by IP rule
        assert bgp["neighbor"][0]["name"] != "10.0.0.1"
        # User anonymized by identity rule
        assert result.ir["configuration"]["system"]["login"]["user"][0]["name"] != "admin"
        # Community anonymized by community rule
        assert result.ir["configuration"]["snmp"]["community"][0]["name"] != "public"
