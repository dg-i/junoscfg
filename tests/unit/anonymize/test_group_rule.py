"""Tests for the group/view name anonymization rule.

What every rule keeps -- determinism, the salt, consistency, the mapping and
revert -- is `tests/contract/test_every_rule.py`; this file keeps what is the
group rule's own: which leaves it takes and the form of its replacements.
"""

from __future__ import annotations

import pytest

from junoscfg.anonymize import AnonymizeConfig, GroupRule, anonymize


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


class TestApplyGroupsIsAReference:
    """`apply-groups` and `apply-groups-except` name a group wherever they
    stand, so the group rule claims them in the walk, ahead of the
    sensitive-word rule. A second pass rewrote every reference again after
    the walk, so with both rules on the root's reference named no group
    (ANON-P1, NEW-C13). Spec anonymization/placed-values."""

    @pytest.mark.parametrize("statement", ["apply-groups", "apply-groups-except"])
    @pytest.mark.parametrize(
        "where", [(), ("system",), ("interfaces",), ("protocols", "bgp", "group")]
    )
    def test_the_rule_claims_both_statements(self, statement: str, where: tuple) -> None:
        rule = GroupRule(AnonymizeConfig(groups=True, salt="s"))
        assert rule.matches("SAMPLE-GROUP", {"l": True, "ll": True, "u": True}, [*where, statement])
