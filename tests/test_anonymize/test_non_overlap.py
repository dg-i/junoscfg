"""Tests for rule priority and non-overlap guarantee.

Each value should be processed by at most one rule. The first matching
rule (by priority) wins.
"""

from __future__ import annotations

from junoscfg.anonymize import anonymize
from junoscfg.anonymize.config import AnonymizeConfig


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
        assert ep.startswith("$6$abc$")
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

        # IP: anonymized
        assert result.ir["configuration"]["system"]["name-server"][0]["name"] != "8.8.8.8"

        # Community: anonymized
        assert result.ir["configuration"]["snmp"]["community"][0]["name"] != "public"

        # Non-sensitive fields untouched
        assert result.ir["configuration"]["snmp"]["community"][0]["authorization"] == "read-only"
