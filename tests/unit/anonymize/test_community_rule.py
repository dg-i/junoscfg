"""Tests for the SNMP community string anonymization rule."""

from __future__ import annotations

from junoscfg.anonymize import anonymize
from junoscfg.anonymize.config import AnonymizeConfig
from junoscfg.anonymize.rules.community import CommunityRule


class TestCommunityRuleMatches:
    def _make_rule(self) -> CommunityRule:
        return CommunityRule(AnonymizeConfig(communities=True, salt="test"))

    def test_matches_snmp_community_name(self) -> None:
        rule = self._make_rule()
        assert rule.matches("public", {"l": True}, ["snmp", "community", "name"])

    def test_matches_snmp_community_in_groups(self) -> None:
        rule = self._make_rule()
        assert rule.matches("example_ro", {"l": True}, ["groups", "snmp", "community", "name"])

    def test_no_match_without_snmp_context(self) -> None:
        rule = self._make_rule()
        assert not rule.matches("public", {"l": True}, ["community", "name"])

    def test_no_match_on_non_name_key(self) -> None:
        rule = self._make_rule()
        assert not rule.matches("read-only", {"l": True}, ["snmp", "community", "authorization"])

    def test_no_match_on_other_named_list(self) -> None:
        rule = self._make_rule()
        assert not rule.matches("ge-0/0/0", {"l": True}, ["snmp", "interface", "name"])

    def test_skip_variable_reference(self) -> None:
        rule = self._make_rule()
        assert not rule.matches("$community_var", {"l": True}, ["snmp", "community", "name"])

    def test_no_match_on_short_path(self) -> None:
        rule = self._make_rule()
        assert not rule.matches("public", {"l": True}, ["name"])


class TestCommunityRuleTransform:
    def _make_rule(self, salt: str = "test-salt") -> CommunityRule:
        return CommunityRule(AnonymizeConfig(communities=True, salt=salt))

    def test_community_replaced(self) -> None:
        rule = self._make_rule()
        result = rule.transform("public")
        assert result != "public"
        assert result.startswith("community_")

    def test_deterministic_with_same_salt(self) -> None:
        rule1 = self._make_rule(salt="same")
        rule2 = self._make_rule(salt="same")
        assert rule1.transform("public") == rule2.transform("public")

    def test_different_salt_different_output(self) -> None:
        rule1 = self._make_rule(salt="salt-a")
        rule2 = self._make_rule(salt="salt-b")
        assert rule1.transform("public") != rule2.transform("public")

    def test_consistency_same_value_same_output(self) -> None:
        rule = self._make_rule()
        first = rule.transform("example_ro")
        second = rule.transform("example_ro")
        assert first == second

    def test_different_communities_different_output(self) -> None:
        rule = self._make_rule()
        r1 = rule.transform("public")
        r2 = rule.transform("private")
        assert r1 != r2

    def test_get_mapping_tracks_transformations(self) -> None:
        rule = self._make_rule()
        rule.transform("public")
        rule.transform("private")
        mapping = rule.get_mapping()
        assert "public" in mapping
        assert "private" in mapping


class TestCommunityAnonymizeIntegration:
    """Test the full anonymize() function with community rule."""

    def test_snmp_community_anonymized(self) -> None:
        cfg = AnonymizeConfig(communities=True, salt="test")
        ir = {
            "configuration": {
                "snmp": {
                    "community": [
                        {
                            "name": "public",
                            "authorization": "read-only",
                        },
                    ],
                },
            },
        }
        result = anonymize(ir, cfg)
        name = result.ir["configuration"]["snmp"]["community"][0]["name"]
        assert name != "public"
        assert name.startswith("community_")
        # authorization should NOT be anonymized (not a community name)
        auth = result.ir["configuration"]["snmp"]["community"][0]["authorization"]
        assert auth == "read-only"

    def test_multiple_communities_all_anonymized(self) -> None:
        cfg = AnonymizeConfig(communities=True, salt="test")
        ir = {
            "configuration": {
                "snmp": {
                    "community": [
                        {"name": "public", "authorization": "read-only"},
                        {"name": "private", "authorization": "read-write"},
                    ],
                },
            },
        }
        result = anonymize(ir, cfg)
        names = [c["name"] for c in result.ir["configuration"]["snmp"]["community"]]
        assert "public" not in names
        assert "private" not in names

    def test_community_in_groups_anonymized(self) -> None:
        cfg = AnonymizeConfig(communities=True, salt="test")
        ir = {
            "configuration": {
                "groups": [
                    {
                        "name": "global-settings",
                        "snmp": {
                            "community": [
                                {"name": "example_ro", "authorization": "read-only"},
                            ],
                        },
                    },
                ],
            },
        }
        result = anonymize(ir, cfg)
        community = result.ir["configuration"]["groups"][0]["snmp"]["community"][0]
        assert community["name"] != "example_ro"
        assert community["name"].startswith("community_")

    def test_mapping_returned(self) -> None:
        cfg = AnonymizeConfig(communities=True, salt="test")
        ir = {
            "configuration": {
                "snmp": {
                    "community": [{"name": "public"}],
                },
            },
        }
        result = anonymize(ir, cfg)
        assert "community" in result.mapping
        assert "public" in result.mapping["community"]

    def test_community_and_ip_together(self) -> None:
        """Community rule + IP rule: community name anonymized, client IPs anonymized."""
        cfg = AnonymizeConfig(communities=True, ips=True, salt="test")
        ir = {
            "configuration": {
                "snmp": {
                    "community": [
                        {
                            "name": "example_ro",
                            "clients": [{"name": "203.0.114.0/24"}],
                        },
                    ],
                },
            },
        }
        result = anonymize(ir, cfg)
        # Community name anonymized
        assert result.ir["configuration"]["snmp"]["community"][0]["name"] != "example_ro"
        # Client IP anonymized
        assert (
            result.ir["configuration"]["snmp"]["community"][0]["clients"][0]["name"]
            != "203.0.114.0/24"
        )
        assert "community" in result.mapping
        assert "ip" in result.mapping

    def test_community_with_password_priority(self) -> None:
        """Password rule (priority 10) runs before community (priority 40)."""
        cfg = AnonymizeConfig(passwords=True, communities=True, salt="test")
        ir = {
            "configuration": {
                "snmp": {
                    "community": [{"name": "public"}],
                },
                "system": {
                    "root-authentication": {
                        "encrypted-password": "$6$abc$hash",
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        # Both should be anonymized by their respective rules
        assert result.ir["configuration"]["snmp"]["community"][0]["name"] != "public"
        assert (
            result.ir["configuration"]["system"]["root-authentication"]["encrypted-password"]
            != "$6$abc$hash"
        )
        assert "community" in result.mapping
        assert "password" in result.mapping
