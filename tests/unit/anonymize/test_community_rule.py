"""Tests for the SNMP community string anonymization rule.

What every rule keeps -- determinism, the salt, consistency, the mapping and
revert -- is `tests/contract/test_every_rule.py`; this file keeps what is the
community rule's own: which leaves it takes and the form of its replacements.
"""

from __future__ import annotations

from junoscfg.anonymize import AnonymizeConfig, CommunityRule, anonymize


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
