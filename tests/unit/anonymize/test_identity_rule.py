"""Tests for the username/identity anonymization rule.

What every rule keeps -- determinism, the salt, consistency, the mapping and
revert -- is `tests/contract/test_every_rule.py`; this file keeps what is the
identity rule's own: which leaves it takes and the form of its replacements.
"""

from __future__ import annotations

import json

from junoscfg import Format, convert_config
from junoscfg.anonymize import AnonymizeConfig, IdentityRule, anonymize, apply_revert


class TestIdentityRuleMatches:
    def _make_rule(self) -> IdentityRule:
        return IdentityRule(AnonymizeConfig(identities=True, salt="test"))

    def test_matches_login_user_name(self) -> None:
        rule = self._make_rule()
        path = ["system", "login", "user", "name"]
        assert rule.matches("admin", {"l": True}, path)

    def test_matches_login_user_in_groups(self) -> None:
        rule = self._make_rule()
        path = ["groups", "system", "login", "user", "name"]
        assert rule.matches("admin", {"l": True}, path)

    def test_matches_full_name(self) -> None:
        rule = self._make_rule()
        path = ["system", "login", "user", "full-name"]
        assert rule.matches("John Doe", {"l": True, "tr": "xsd:string"}, path)

    def test_matches_snmp_security_name(self) -> None:
        rule = self._make_rule()
        path = ["snmp", "v3", "target-parameters", "parameters", "security-name"]
        assert rule.matches("snmpuser", {"l": True}, path)

    def test_matches_snmp_vacm_security_name(self) -> None:
        rule = self._make_rule()
        path = ["snmp", "v3", "vacm", "security-to-group", "security-model", "security-name"]
        assert rule.matches("snmpuser", {"l": True}, path)

    def test_matches_snmp_usm_local_user(self) -> None:
        """SNMPv3 USM local-engine user name should match."""
        rule = self._make_rule()
        path = ["snmp", "v3", "usm", "local-engine", "user", "name"]
        assert rule.matches("monitoring", {"l": True}, path)

    def test_matches_snmp_usm_remote_user(self) -> None:
        """SNMPv3 USM remote-engine user name should match."""
        rule = self._make_rule()
        path = ["snmp", "v3", "usm", "remote-engine", "user", "name"]
        assert rule.matches("observium", {"l": True}, path)

    def test_matches_vacm_security_name_named_list_key(self) -> None:
        """VACM security-name named-list key (path[-1]==name, path[-2]==security-name)."""
        rule = self._make_rule()
        path = [
            "snmp",
            "v3",
            "vacm",
            "security-to-group",
            "security-model",
            "security-name",
            "name",
        ]
        assert rule.matches("monitoring", {"l": True}, path)

    def test_no_match_on_non_login_user(self) -> None:
        """user[*].name in non-login context should not match."""
        rule = self._make_rule()
        path = ["system", "services", "user", "name"]
        assert not rule.matches("someuser", {"l": True}, path)

    def test_no_match_on_hostname(self) -> None:
        rule = self._make_rule()
        path = ["system", "host-name"]
        assert not rule.matches("router1", {"l": True}, path)

    def test_no_match_on_interface_name(self) -> None:
        rule = self._make_rule()
        path = ["interfaces", "interface", "name"]
        assert not rule.matches("ge-0/0/0", {"l": True}, path)

    def test_no_match_on_empty_path(self) -> None:
        rule = self._make_rule()
        assert not rule.matches("admin", {"l": True}, [])


class TestIdentityRuleTransform:
    def _make_rule(self, salt: str = "test-salt") -> IdentityRule:
        return IdentityRule(AnonymizeConfig(identities=True, salt=salt))

    def test_user_prefix(self) -> None:
        rule = self._make_rule()
        result = rule.transform("admin")
        assert result.startswith("user_")
        assert result != "admin"


class TestIdentityAnonymizeIntegration:
    """Test the full anonymize() function with identity rule."""

    def test_login_username_anonymized(self) -> None:
        cfg = AnonymizeConfig(identities=True, salt="test")
        ir = {
            "configuration": {
                "system": {
                    "login": {
                        "user": [
                            {
                                "name": "jdoe",
                                "full-name": "John Doe",
                                "class": "super-user",
                            },
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        user = result.ir["configuration"]["system"]["login"]["user"][0]
        assert user["name"] != "jdoe"
        assert user["name"].startswith("user_")
        # full-name should also be anonymized
        assert user["full-name"] != "John Doe"
        # class should NOT be anonymized
        assert user["class"] == "super-user"
        assert "identity" in result.mapping

    def test_multiple_users_anonymized(self) -> None:
        cfg = AnonymizeConfig(identities=True, salt="test")
        ir = {
            "configuration": {
                "system": {
                    "login": {
                        "user": [
                            {"name": "admin", "full-name": "Administrator"},
                            {"name": "operator", "full-name": "NOC Operator"},
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        users = result.ir["configuration"]["system"]["login"]["user"]
        assert users[0]["name"] != "admin"
        assert users[1]["name"] != "operator"
        assert users[0]["name"] != users[1]["name"]

    def test_users_in_groups(self) -> None:
        """Users inside config groups should be anonymized."""
        cfg = AnonymizeConfig(identities=True, salt="test")
        ir = {
            "configuration": {
                "groups": [
                    {
                        "name": "users-group",
                        "system": {
                            "login": {
                                "user": [
                                    {"name": "rancid", "full-name": "RANCID"},
                                ],
                            },
                        },
                    },
                ],
            },
        }
        result = anonymize(ir, cfg)
        user = result.ir["configuration"]["groups"][0]["system"]["login"]["user"][0]
        assert user["name"] != "rancid"
        assert user["full-name"] != "RANCID"


class TestAUrlUserIsAnIdentity:
    """A URL's user (`scp://operator@...`) is an identity: it survived
    `--anonymize-identities` beside the login user the rule renamed (NEW-A-N4).
    It takes the pseudonym a login user of that name takes; the host and path
    stay. Spec anonymization/embedded-values.
    """

    def test_it_takes_the_login_users_pseudonym(self) -> None:
        text = (
            "set system login user operator class super-user\n"
            "set system archival configuration archive-sites "
            '"scp://operator@203.0.114.5/path"\n'
            "set system archival configuration archive-sites "
            '"ftp://admin@host.example:21/cfg"\n'
        )
        source = json.loads(
            convert_config(text, from_format=Format.SET, to_format=Format.JSON, validate=False)
        )
        result = anonymize(source, AnonymizeConfig(identities=True, salt="s"))
        sites = [
            site["name"]
            for site in result.ir["configuration"]["system"]["archival"]["configuration"][
                "archive-sites"
            ]
        ]
        pseudonym = result.mapping["identity"]["operator"]
        assert sites[0] == f"scp://{pseudonym}@203.0.114.5/path"
        assert sites[1] == f"ftp://{result.mapping['identity']['admin']}@host.example:21/cfg"
        assert apply_revert(result.ir, result.mapping) == source
