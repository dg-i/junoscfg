"""Tests for the description/contact/location anonymization rule.

What every rule keeps -- determinism, the salt, consistency, the mapping and
revert -- is `tests/contract/test_every_rule.py`; this file keeps what is the
description rule's own: which leaves it takes and the form of its replacements.
"""

from __future__ import annotations

from junoscfg.anonymize import AnonymizeConfig, DescriptionRule, anonymize


class TestDescriptionRuleMatches:
    def _make_rule(self) -> DescriptionRule:
        return DescriptionRule(AnonymizeConfig(descriptions=True, salt="test"))

    def test_matches_description(self) -> None:
        rule = self._make_rule()
        path = ["protocols", "bgp", "group", "description"]
        assert rule.matches("ExampleISP1 Transit", {"l": True}, path)

    def test_matches_contact(self) -> None:
        rule = self._make_rule()
        path = ["snmp", "contact"]
        assert rule.matches("noc@example.com", {"l": True, "tr": "xsd:string"}, path)

    def test_matches_location(self) -> None:
        rule = self._make_rule()
        path = ["snmp", "location"]
        assert rule.matches("NYC-DC1-Rack42", {"l": True, "tr": "xsd:string"}, path)

    def test_matches_description_in_groups(self) -> None:
        rule = self._make_rule()
        path = ["groups", "protocols", "bgp", "group", "neighbor", "description"]
        assert rule.matches("Upstream link", {"l": True}, path)

    def test_matches_interface_description(self) -> None:
        rule = self._make_rule()
        path = ["interfaces", "interface", "description"]
        assert rule.matches("Link to core", {"l": True}, path)

    def test_no_match_on_hostname(self) -> None:
        rule = self._make_rule()
        path = ["system", "host-name"]
        assert not rule.matches("router1", {"l": True}, path)

    def test_no_match_on_name(self) -> None:
        rule = self._make_rule()
        path = ["interfaces", "interface", "name"]
        assert not rule.matches("ge-0/0/0", {"l": True}, path)

    def test_no_match_on_empty_path(self) -> None:
        rule = self._make_rule()
        assert not rule.matches("something", {"l": True}, [])


class TestDescriptionRuleTransform:
    def _make_rule(self, salt: str = "test-salt") -> DescriptionRule:
        return DescriptionRule(AnonymizeConfig(descriptions=True, salt=salt))

    def test_descr_prefix(self) -> None:
        rule = self._make_rule()
        result = rule.transform("ExampleISP1 Transit")
        assert result.startswith("descr_")
        assert result != "ExampleISP1 Transit"


class TestDescriptionAnonymizeIntegration:
    """Test the full anonymize() function with description rule."""

    def test_bgp_description_anonymized(self) -> None:
        cfg = AnonymizeConfig(descriptions=True, salt="test")
        ir = {
            "configuration": {
                "protocols": {
                    "bgp": {
                        "group": [
                            {
                                "name": "inet-Upstream-AS64496",
                                "type": "external",
                                "description": "ExampleISP1 Transit",
                            },
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        group = result.ir["configuration"]["protocols"]["bgp"]["group"][0]
        assert group["description"] != "ExampleISP1 Transit"
        assert group["description"].startswith("descr_")
        # name and type should NOT be anonymized
        assert group["name"] == "inet-Upstream-AS64496"
        assert group["type"] == "external"
        assert "description" in result.mapping

    def test_interface_description_anonymized(self) -> None:
        cfg = AnonymizeConfig(descriptions=True, salt="test")
        ir = {
            "configuration": {
                "interfaces": {
                    "interface": [
                        {
                            "name": "ge-0/0/0",
                            "description": "Link to core router",
                        },
                    ],
                },
            },
        }
        result = anonymize(ir, cfg)
        iface = result.ir["configuration"]["interfaces"]["interface"][0]
        assert iface["description"] != "Link to core router"
        assert iface["description"].startswith("descr_")
        assert iface["name"] == "ge-0/0/0"

    def test_snmp_contact_and_location(self) -> None:
        cfg = AnonymizeConfig(descriptions=True, salt="test")
        ir = {
            "configuration": {
                "snmp": {
                    "contact": "noc@example.com",
                    "location": "NYC-DC1-Rack42",
                },
            },
        }
        result = anonymize(ir, cfg)
        snmp = result.ir["configuration"]["snmp"]
        assert snmp["contact"] != "noc@example.com"
        assert snmp["location"] != "NYC-DC1-Rack42"
        assert snmp["contact"].startswith("descr_")
        assert snmp["location"].startswith("descr_")
