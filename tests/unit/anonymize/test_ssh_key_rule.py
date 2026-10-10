"""Tests for the SSH public key anonymization rule.

What every rule keeps -- determinism, the salt, consistency, the mapping and
revert -- is `tests/contract/test_every_rule.py`; this file keeps what is the
SSH key rule's own: which leaves it takes and the form of its replacements.
"""

from __future__ import annotations

from junoscfg.anonymize import AnonymizeConfig, SshKeyRule, anonymize


class TestSshKeyRuleMatches:
    def _make_rule(self) -> SshKeyRule:
        return SshKeyRule(AnonymizeConfig(ssh_keys=True, salt="test"))

    def test_matches_ssh_rsa_in_authentication(self) -> None:
        rule = self._make_rule()
        path = ["system", "root-authentication", "ssh-rsa", "name"]
        assert rule.matches("ssh-rsa AAAA...", {"l": True}, path)

    def test_matches_ssh_ed25519_in_user_authentication(self) -> None:
        rule = self._make_rule()
        path = ["system", "login", "user", "authentication", "ssh-ed25519", "name"]
        assert rule.matches("ssh-ed25519 AAAA...", {"l": True}, path)

    def test_matches_ssh_ecdsa(self) -> None:
        rule = self._make_rule()
        path = ["system", "login", "user", "authentication", "ssh-ecdsa", "name"]
        assert rule.matches("ecdsa-sha2-nistp521 AAAA...", {"l": True}, path)

    def test_matches_ssh_dsa(self) -> None:
        rule = self._make_rule()
        path = ["system", "login", "user", "authentication", "ssh-dsa", "name"]
        assert rule.matches("ssh-dss AAAA...", {"l": True}, path)

    def test_matches_in_groups_context(self) -> None:
        rule = self._make_rule()
        path = ["groups", "system", "login", "user", "authentication", "ssh-rsa", "name"]
        assert rule.matches("ssh-rsa AAAA...", {"l": True}, path)

    def test_matches_without_explicit_authentication_segment(self) -> None:
        """ssh-rsa parent is sufficient — no need for explicit 'authentication'."""
        rule = self._make_rule()
        path = ["system", "ssh-rsa", "name"]
        assert rule.matches("ssh-rsa AAAA...", {"l": True}, path)

    def test_no_match_on_non_ssh_parent(self) -> None:
        rule = self._make_rule()
        path = ["system", "authentication", "other-key", "name"]
        assert not rule.matches("some-value", {"l": True}, path)

    def test_no_match_on_non_name_key(self) -> None:
        rule = self._make_rule()
        path = ["system", "authentication", "ssh-rsa", "from"]
        assert not rule.matches("10.0.0.0/8", {"l": True}, path)

    def test_no_match_short_path(self) -> None:
        rule = self._make_rule()
        assert not rule.matches("ssh-rsa AAAA...", {"l": True}, ["name"])


class TestSshKeyRuleTransform:
    def _make_rule(self, salt: str = "test-salt") -> SshKeyRule:
        return SshKeyRule(AnonymizeConfig(ssh_keys=True, salt=salt))

    def test_preserves_key_type_prefix(self) -> None:
        rule = self._make_rule()
        original = "ssh-rsa AAAAB3NzaC1yc2EAAAA user@host"
        result = rule.transform(original)
        assert result.startswith("ssh-rsa ")
        assert result != original

    def test_preserves_ed25519_prefix(self) -> None:
        rule = self._make_rule()
        original = "ssh-ed25519 AAAAGnNrLXNzaC1lZDI1NTE5 comment"
        result = rule.transform(original)
        assert result.startswith("ssh-ed25519 ")

    def test_removes_original_comment(self) -> None:
        rule = self._make_rule()
        original = "ssh-rsa AAAAB3NzaC1yc2EAAAA user@secrethost.example.com"
        result = rule.transform(original)
        assert "secrethost" not in result
        assert "user@" not in result
        assert "anonymized-key" in result

    def test_blob_same_length(self) -> None:
        rule = self._make_rule()
        original = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDx comment"
        result = rule.transform(original)
        # Extract blob from result
        parts = result.split()
        orig_blob = "AAAAB3NzaC1yc2EAAAADAQABAAABAQDx"
        assert len(parts[1]) == len(orig_blob)


class TestSshKeyAnonymizeIntegration:
    """Test the full anonymize() function with SSH key rule."""

    def test_ssh_rsa_key_anonymized(self) -> None:
        cfg = AnonymizeConfig(ssh_keys=True, salt="test")
        ir = {
            "configuration": {
                "system": {
                    "root-authentication": {
                        "ssh-rsa": [
                            {
                                "name": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDx admin@router",
                            },
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        key = result.ir["configuration"]["system"]["root-authentication"]["ssh-rsa"][0]["name"]
        assert key != "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDx admin@router"
        assert key.startswith("ssh-rsa ")
        assert "admin@router" not in key
        assert "ssh_key" in result.mapping

    def test_ssh_key_in_login_user(self) -> None:
        cfg = AnonymizeConfig(ssh_keys=True, salt="test")
        ir = {
            "configuration": {
                "system": {
                    "login": {
                        "user": [
                            {
                                "name": "admin",
                                "authentication": {
                                    "ssh-ed25519": [
                                        {"name": "ssh-ed25519 AAAAGnNrLXNzaC1 admin@host"},
                                    ],
                                },
                            },
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        key = result.ir["configuration"]["system"]["login"]["user"][0]["authentication"][
            "ssh-ed25519"
        ][0]["name"]
        assert "admin@host" not in key
        assert key.startswith("ssh-ed25519 ")

    def test_ssh_key_in_groups(self) -> None:
        """SSH keys inside configuration groups should be anonymized."""
        cfg = AnonymizeConfig(ssh_keys=True, salt="test")
        ir = {
            "configuration": {
                "groups": [
                    {
                        "name": "ssh-users",
                        "system": {
                            "login": {
                                "user": [
                                    {
                                        "name": "testuser",
                                        "authentication": {
                                            "ssh-rsa": [
                                                {
                                                    "name": "ssh-rsa AAAA user@secret.local",
                                                },
                                            ],
                                        },
                                    },
                                ],
                            },
                        },
                    },
                ],
            },
        }
        result = anonymize(ir, cfg)
        key = result.ir["configuration"]["groups"][0]["system"]["login"]["user"][0][
            "authentication"
        ]["ssh-rsa"][0]["name"]
        assert "secret.local" not in key
        assert key.startswith("ssh-rsa ")
