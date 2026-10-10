"""Tests for rule priority and non-overlap guarantee.

Each value should be processed by at most one rule. The first matching
rule (by priority) wins. These are hand cases where rules meet on real
configuration paths; the law for every pair of rules is
`tests/contract/test_every_rule.py::TestRulesDoNotOverlap`.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from junoscfg.anonymize import AnonymizeConfig, anonymize, build_rules


class TestNonOverlap:
    """Each value should be processed by at most one rule."""

    def test_ip_only_scenario(self) -> None:
        """With only IP enabled, IP fields are anonymized and others untouched."""
        cfg = AnonymizeConfig(ips=True, salt="test")
        ir = {
            "configuration": {
                "system": {
                    "host-name": "router1",
                    "name-server": [{"name": "8.8.8.8"}],
                },
            },
        }
        result = anonymize(ir, cfg)

        # IP field should be changed
        assert result.ir["configuration"]["system"]["name-server"][0]["name"] != "8.8.8.8"
        # Non-IP field should be unchanged
        assert result.ir["configuration"]["system"]["host-name"] == "router1"

    def test_password_wins_over_ip_on_unreadable(self) -> None:
        """Password rule (priority 10) beats IP rule (30) on unreadable fields."""
        cfg = AnonymizeConfig(passwords=True, ips=True, salt="test")
        ir = {
            "configuration": {
                "system": {
                    "root-authentication": {
                        "encrypted-password": "$6$abc$hash123",
                    },
                    "name-server": [{"name": "8.8.8.8"}],
                },
            },
        }
        result = anonymize(ir, cfg)

        # Password field anonymized by password rule (not IP rule)
        ep = result.ir["configuration"]["system"]["root-authentication"]["encrypted-password"]
        assert ep != "$6$abc$hash123"
        assert ep.startswith("$6$")
        assert "$abc$" not in ep  # the original salt is replaced, not copied
        assert "password" in result.mapping
        assert "$6$abc$hash123" in result.mapping["password"]

        # IP field anonymized by IP rule
        assert result.ir["configuration"]["system"]["name-server"][0]["name"] != "8.8.8.8"
        assert "ip" in result.mapping

    def test_all_three_rules_non_overlapping(self) -> None:
        """Password, IP, and community rules each handle their own fields."""
        cfg = AnonymizeConfig(passwords=True, ips=True, communities=True, salt="test")
        ir = {
            "configuration": {
                "system": {
                    "root-authentication": {
                        "encrypted-password": "$9$secrethash",
                    },
                    "name-server": [{"name": "8.8.8.8"}],
                },
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

        # Each field handled by exactly one rule
        assert "password" in result.mapping
        assert "ip" in result.mapping
        assert "community" in result.mapping

        # Password: anonymized but format preserved
        ep = result.ir["configuration"]["system"]["root-authentication"]["encrypted-password"]
        assert ep.startswith("$9$")
        assert ep != "$9$secrethash"

        # the IP is anonymized
        assert result.ir["configuration"]["system"]["name-server"][0]["name"] != "8.8.8.8"

        # the community is anonymized
        assert result.ir["configuration"]["snmp"]["community"][0]["name"] != "public"

        # Non-sensitive fields untouched
        assert result.ir["configuration"]["snmp"]["community"][0]["authorization"] == "read-only"

    def test_password_and_ip_together(self) -> None:
        """Both rules enabled: password wins on unreadable, IP wins on ipaddr."""
        cfg = AnonymizeConfig(passwords=True, ips=True, salt="test")
        ir = {
            "configuration": {
                "system": {
                    "root-authentication": {
                        "encrypted-password": "$6$abc$hash",
                    },
                    "name-server": [{"name": "8.8.8.8"}],
                },
            },
        }
        result = anonymize(ir, cfg)
        # Password should be anonymized
        ep = result.ir["configuration"]["system"]["root-authentication"]["encrypted-password"]
        assert ep != "$6$abc$hash"
        # IP should be anonymized
        ns = result.ir["configuration"]["system"]["name-server"][0]["name"]
        assert ns != "8.8.8.8"
        # Both mappings present
        assert "password" in result.mapping
        assert "ip" in result.mapping

    def test_ssh_key_with_password_rule(self) -> None:
        """SSH key rule (priority 20) and password rule (priority 10) coexist."""
        cfg = AnonymizeConfig(ssh_keys=True, passwords=True, salt="test")
        ir = {
            "configuration": {
                "system": {
                    "login": {
                        "user": [
                            {
                                "name": "admin",
                                "authentication": {
                                    "encrypted-password": "$6$abc$hash",
                                    "ssh-rsa": [
                                        {"name": "ssh-rsa AAAA admin@host"},
                                    ],
                                },
                            },
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        # Password should be anonymized by password rule
        ep = result.ir["configuration"]["system"]["login"]["user"][0]["authentication"][
            "encrypted-password"
        ]
        assert ep != "$6$abc$hash"
        # SSH key should be anonymized by SSH key rule
        key = result.ir["configuration"]["system"]["login"]["user"][0]["authentication"]["ssh-rsa"][
            0
        ]["name"]
        assert "admin@host" not in key
        assert "password" in result.mapping
        assert "ssh_key" in result.mapping

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

    def test_identity_with_password_and_ip(self) -> None:
        """Identity, password, and IP rules coexist without conflict."""
        cfg = AnonymizeConfig(identities=True, passwords=True, ips=True, salt="test")
        ir = {
            "configuration": {
                "system": {
                    "login": {
                        "user": [
                            {
                                "name": "admin",
                                "authentication": {
                                    "encrypted-password": "$6$abc$hash",
                                },
                            },
                        ],
                    },
                    "name-server": [{"name": "8.8.8.8"}],
                },
            },
        }
        result = anonymize(ir, cfg)
        assert result.ir["configuration"]["system"]["login"]["user"][0]["name"] != "admin"
        ep = result.ir["configuration"]["system"]["login"]["user"][0]["authentication"][
            "encrypted-password"
        ]
        assert ep != "$6$abc$hash"
        ns = result.ir["configuration"]["system"]["name-server"][0]["name"]
        assert ns != "8.8.8.8"
        assert "identity" in result.mapping
        assert "password" in result.mapping
        assert "ip" in result.mapping

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

    def test_description_with_other_rules(self) -> None:
        """Description rule coexists with IP and password rules."""
        cfg = AnonymizeConfig(
            descriptions=True,
            ips=True,
            passwords=True,
            salt="test",
        )
        ir = {
            "configuration": {
                "interfaces": {
                    "interface": [
                        {
                            "name": "ge-0/0/0",
                            "description": "Link to core",
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
                "system": {
                    "root-authentication": {
                        "encrypted-password": "$6$abc$hash",
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        iface = result.ir["configuration"]["interfaces"]["interface"][0]
        assert iface["description"].startswith("descr_")
        addr = iface["unit"][0]["family"]["inet"]["address"][0]["name"]
        assert addr != "10.1.2.3/24"
        ep = result.ir["configuration"]["system"]["root-authentication"]["encrypted-password"]
        assert ep != "$6$abc$hash"
        assert "description" in result.mapping
        assert "ip" in result.mapping
        assert "password" in result.mapping

    def test_as_number_with_descriptions_and_ips(self) -> None:
        """AS number rule coexists with description and IP rules."""
        cfg = AnonymizeConfig(
            as_numbers=[64496],
            descriptions=True,
            ips=True,
            salt="test",
        )
        ir = {
            "configuration": {
                "protocols": {
                    "bgp": {
                        "group": [
                            {
                                "name": "peers",
                                "description": "Transit provider",
                                "peer-as": "64496",
                                "neighbor": [{"name": "10.0.0.1"}],
                            },
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        group = result.ir["configuration"]["protocols"]["bgp"]["group"][0]
        assert group["peer-as"] != "64496"
        assert group["description"].startswith("descr_")
        assert group["neighbor"][0]["name"] != "10.0.0.1"

    def test_sensitive_word_with_description_rule(self) -> None:
        """When both description and sensitive_word rules are enabled,
        description rule takes priority on 'description' fields."""
        cfg = AnonymizeConfig(
            descriptions=True,
            sensitive_words=["newyork"],
            salt="test",
        )
        ir = {
            "configuration": {
                "interfaces": {
                    "interface": [
                        {
                            "name": "ge-0/0/0",
                            "description": "Link to NewYork DC",
                        },
                    ],
                },
                "system": {
                    "host-name": "newyork-router1",
                },
            },
        }
        result = anonymize(ir, cfg)
        # Description field should be handled by description rule (higher priority)
        desc = result.ir["configuration"]["interfaces"]["interface"][0]["description"]
        assert desc.startswith("descr_")
        # Host-name should be handled by sensitive_word rule
        hostname = result.ir["configuration"]["system"]["host-name"]
        assert "newyork" not in hostname.lower()

    def test_sensitive_word_with_all_rules(self) -> None:
        """Sensitive word rule coexists with all other rules."""
        cfg = AnonymizeConfig(
            ips=True,
            passwords=True,
            descriptions=True,
            sensitive_words=["acmecorp"],
            salt="test",
        )
        ir = {
            "configuration": {
                "system": {
                    "host-name": "acmecorp-gw01",
                    "root-authentication": {
                        "encrypted-password": "$6$abc$hash",
                    },
                    "name-server": [{"name": "8.8.8.8"}],
                },
                "interfaces": {
                    "interface": [
                        {
                            "name": "ge-0/0/0",
                            "description": "Link to acmecorp-core",
                        },
                    ],
                },
            },
        }
        result = anonymize(ir, cfg)
        # Sensitive word in host-name
        assert "acmecorp" not in result.ir["configuration"]["system"]["host-name"].lower()
        # Password anonymized
        assert (
            result.ir["configuration"]["system"]["root-authentication"]["encrypted-password"]
            != "$6$abc$hash"
        )
        # IP anonymized
        assert result.ir["configuration"]["system"]["name-server"][0]["name"] != "8.8.8.8"
        # Description field handled by description rule
        desc = result.ir["configuration"]["interfaces"]["interface"][0]["description"]
        assert desc.startswith("descr_")


class TestNoRuleChangesNothing:
    """With no rule on, anonymize() hands the IR back as it came, with no mapping."""

    @pytest.mark.parametrize(
        "ir",
        [
            pytest.param({"configuration": {"system": {"host-name": "r1"}}}, id="host-name"),
            pytest.param(
                {
                    "configuration": {
                        "system": {
                            "root-authentication": {
                                "encrypted-password": "$6$abc$hash",
                            },
                        },
                    },
                },
                id="password",
            ),
        ],
    )
    def test_no_rule_enabled_changes_nothing(self, ir: dict[str, Any]) -> None:
        original = copy.deepcopy(ir)
        result = anonymize(ir, AnonymizeConfig())
        assert result.ir == original
        assert result.mapping == {}


class TestRulePrecedence:
    """build_rules builds the enabled rules only, in the order the walker tries them.

    `tests/contract/test_every_rule.py` lists its catalogue in this order and
    predicts which rule owns a contested value from it.
    """

    def test_every_rule_on_is_built_in_priority_order(self) -> None:
        config = AnonymizeConfig(sensitive_words=["acme"], as_numbers=[64496], salt="test")
        config.expand_all()
        assert [rule.name for rule in build_rules(config)] == [
            "password",
            "ssh_key",
            "ip",
            "community",
            "identity",
            "group",
            "description",
            "as_number",
            "sensitive_word",
        ]

    def test_only_the_enabled_rules_are_built(self) -> None:
        config = AnonymizeConfig(descriptions=True, ips=True, salt="test")
        assert [rule.name for rule in build_rules(config)] == ["ip", "description"]
        assert build_rules(AnonymizeConfig()) == []
