"""Tests for the password anonymization rule."""

from __future__ import annotations

import copy
import re

from netutils.password import JUNIPER_KEYS_STRING, decrypt_juniper_type9

from junoscfg.anonymize import anonymize
from junoscfg.anonymize.config import AnonymizeConfig
from junoscfg.anonymize.rules.password import PasswordRule


class TestPasswordRuleMatches:
    """Test the three matching strategies: schema tr, key name, content pattern."""

    def _make_rule(self) -> PasswordRule:
        return PasswordRule(AnonymizeConfig(passwords=True, salt="test"))

    # --- Strategy 1: schema type_ref ---

    def test_matches_unreadable_type_ref(self) -> None:
        rule = self._make_rule()
        assert rule.matches("$9$abc", {"tr": "unreadable", "l": True}, ["x"])

    def test_matches_unreadable_case_insensitive(self) -> None:
        rule = self._make_rule()
        assert rule.matches("secret", {"tr": "Unreadable", "l": True}, ["x"])

    def test_no_match_on_string_type(self) -> None:
        rule = self._make_rule()
        assert not rule.matches("hello", {"tr": "string", "l": True}, ["x"])

    def test_no_match_on_ip_type(self) -> None:
        rule = self._make_rule()
        assert not rule.matches("10.0.0.1", {"tr": "ipv4addr", "l": True}, ["x"])

    # --- Strategy 2: key name matching ---

    def test_matches_encrypted_password_key(self) -> None:
        """encrypted-password has no tr in schema but should still match."""
        rule = self._make_rule()
        path = ["system", "root-authentication", "encrypted-password"]
        assert rule.matches("$6$abc$hash", {"l": True}, path)

    def test_matches_authentication_key(self) -> None:
        """BGP authentication-key has no tr in schema but should still match."""
        rule = self._make_rule()
        path = ["protocols", "bgp", "group", "authentication-key"]
        assert rule.matches("$9$abc", {"l": True}, path)

    def test_matches_secret_key(self) -> None:
        """key-chain secret has no tr in schema but should still match."""
        rule = self._make_rule()
        assert rule.matches("$9$abc", {"l": True}, ["security", "key-chain", "key", "secret"])

    def test_matches_simple_password_key(self) -> None:
        """OSPF simple-password should match by key name."""
        rule = self._make_rule()
        path = ["protocols", "ospf", "area", "interface", "authentication", "simple-password"]
        assert rule.matches("$9$abc", {"l": True}, path)

    def test_matches_authentication_password_key(self) -> None:
        """SNMPv3 authentication-password should match by key name."""
        rule = self._make_rule()
        path = ["snmp", "v3", "usm", "local-engine", "user", "authentication-password"]
        assert rule.matches("$9$abc", {"l": True}, path)

    # --- Strategy 3: content-based matching ---

    def test_matches_j9_content_without_tr(self) -> None:
        """$9$ value should match by content even without tr or key name."""
        rule = self._make_rule()
        assert rule.matches("$9$LxNdsYaJUjqf", {"l": True}, ["some", "random", "field"])

    def test_matches_sha512_content_without_tr(self) -> None:
        """$6$ value should match by content even without tr or key name."""
        rule = self._make_rule()
        assert rule.matches("$6$salt$hash", {"l": True}, ["some", "random", "field"])

    def test_matches_sha1_content(self) -> None:
        """$sha1$ value should match by content pattern."""
        rule = self._make_rule()
        assert rule.matches("$sha1$19418$aoTClyGU$hash", {"l": True}, ["some", "field"])

    def test_matches_j8_content(self) -> None:
        """$8$ value should match by content pattern."""
        rule = self._make_rule()
        value = "$8$AES256-GCM$hmac-sha2-256$100$salt$iv$tag$enc"
        assert rule.matches(value, {"l": True}, ["field"])

    # --- Non-matching cases ---

    def test_no_match_plain_text_no_context(self) -> None:
        """Plain text without tr, key name, or hash prefix should not match."""
        rule = self._make_rule()
        assert not rule.matches("hello", {"l": True}, ["x"])

    def test_no_match_hostname(self) -> None:
        rule = self._make_rule()
        assert not rule.matches("router1", {"l": True}, ["system", "host-name"])


class TestPasswordRuleTransform:
    def _make_rule(self, salt: str = "test-salt") -> PasswordRule:
        return PasswordRule(AnonymizeConfig(passwords=True, salt=salt))

    def test_j9_format_preserved(self) -> None:
        rule = self._make_rule()
        original = "$9$LxNdsYaJUjqfik5Qz6O1I"
        result = rule.transform(original)
        assert result.startswith("$9$")
        assert result != original

    def test_md5_format_preserved(self) -> None:
        rule = self._make_rule()
        original = "$1$abc123$xyzHashValueHere"
        result = rule.transform(original)
        assert result.startswith("$1$abc123$")
        assert result != original

    def test_sha256_format_preserved(self) -> None:
        rule = self._make_rule()
        original = "$5$rounds=5000$saltsalt$hashbodyhashbodyhashbody"
        result = rule.transform(original)
        assert result.startswith("$5$")
        assert result != original

    def test_sha512_format_preserved(self) -> None:
        rule = self._make_rule()
        original = "$6$abc$xyzLongHashValueHereThatIsLong"
        result = rule.transform(original)
        assert result.startswith("$6$abc$")
        assert result != original

    def test_sha1_format_preserved(self) -> None:
        """$sha1$ (NetBSD crypt-sha1, used in FIPS mode) format preserved."""
        rule = self._make_rule()
        original = "$sha1$19418$aoTClyGU$cix8MhZsXwG6OrwUgeHAoOA8f.AX"
        result = rule.transform(original)
        assert result.startswith("$sha1$19418$aoTClyGU$")
        assert result != original

    def test_j8_format_preserved(self) -> None:
        """$8$ (AES-256-GCM master password) format preserved."""
        rule = self._make_rule()
        original = "$8$AES256-GCM$hmac-sha2-256$100$abc123$iv456$tag789$encryptedpayload"
        result = rule.transform(original)
        assert result.startswith("$8$")
        # Structure fields should be mostly preserved, encrypted payload replaced
        assert result != original

    def test_bcrypt_format_preserved(self) -> None:
        """$2a$ (bcrypt) format preserved."""
        rule = self._make_rule()
        # bcrypt: $2a$cost$22-char-salt + 31-char-hash
        original = "$2a$12$WApznUPhDubN0oeveSXVqeG7HqBSly4o7.gphTrw5KjYz5GBrmGOK"
        result = rule.transform(original)
        assert result.startswith("$2a$12$")
        assert result != original

    def test_nthash_format_preserved(self) -> None:
        """$3$ (NTHASH, FreeBSD inherited) format preserved."""
        rule = self._make_rule()
        original = "$3$salt$hashvalue123"
        result = rule.transform(original)
        assert result.startswith("$3$salt$")
        assert result != original

    def test_plain_text_replaced(self) -> None:
        rule = self._make_rule()
        result = rule.transform("mysecretpassword")
        assert result.startswith("netconanRemoved")
        assert "mysecretpassword" not in result

    def test_plain_text_sequential(self) -> None:
        rule = self._make_rule()
        r1 = rule.transform("password1")
        r2 = rule.transform("password2")
        assert r1 == "netconanRemoved0"
        assert r2 == "netconanRemoved1"

    def test_deterministic_with_same_salt(self) -> None:
        rule1 = self._make_rule(salt="same")
        rule2 = self._make_rule(salt="same")
        assert rule1.transform("$9$abc") == rule2.transform("$9$abc")

    def test_different_salt_different_output(self) -> None:
        rule1 = self._make_rule(salt="salt-a")
        rule2 = self._make_rule(salt="salt-b")
        assert rule1.transform("$9$abc") != rule2.transform("$9$abc")

    def test_consistency_same_value_same_output(self) -> None:
        rule = self._make_rule()
        first = rule.transform("$9$secret123")
        second = rule.transform("$9$secret123")
        assert first == second

    def test_plain_text_consistency(self) -> None:
        rule = self._make_rule()
        first = rule.transform("plaintext")
        second = rule.transform("plaintext")
        assert first == second

    def test_j9_output_contains_only_valid_chars(self) -> None:
        """Anonymized $9$ body must only contain characters from the Junos alphabet."""
        rule = self._make_rule()
        for original in [
            "$9$LxNdsYaJUjqfik5Qz6O1I",
            "$9$abc",
            "$9$ExAmPlEhAsH.KEY",
            "$9$j1Hqf3nCO1ECApBI",
        ]:
            result = rule.transform(original)
            body = result[3:]  # Strip "$9$"
            for ch in body:
                assert ch in JUNIPER_KEYS_STRING, f"Invalid char {ch!r} in $9$ body of {result!r}"

    def test_j9_output_decrypts_without_error(self) -> None:
        """Anonymized $9$ output must be structurally valid (decryptable)."""
        rule = self._make_rule()
        for original in [
            "$9$LxNdsYaJUjqfik5Qz6O1I",
            "$9$ExAmPlEhAsH.KEY",
            "$9$j1Hqf3nCO1ECApBI",
        ]:
            result = rule.transform(original)
            # decrypt_juniper_type9 raises on structurally invalid input
            decrypted = decrypt_juniper_type9(result)
            assert isinstance(decrypted, str)
            assert len(decrypted) > 0

    def test_j9_deterministic_same_salt(self) -> None:
        """Same input + same salt must produce the same $9$ output."""
        rule1 = self._make_rule(salt="fixed")
        rule2 = self._make_rule(salt="fixed")
        original = "$9$LxNdsYaJUjqfik5Qz6O1I"
        assert rule1.transform(original) == rule2.transform(original)

    def test_j9_different_inputs_different_output(self) -> None:
        """Different $9$ passwords must produce different anonymized hashes."""
        rule = self._make_rule()
        r1 = rule.transform("$9$LxNdsYaJUjqfik5Qz6O1I")
        r2 = rule.transform("$9$ExAmPlEhAsH.KEY")
        assert r1 != r2

    def test_crypt_hash_valid_format(self) -> None:
        """Anonymized $6$ output must match the $6$salt$hash pattern."""
        rule = self._make_rule()
        original = "$6$abc$xyzLongHashValueHereThatIsLong"
        result = rule.transform(original)
        assert result.startswith("$6$")
        # Must be $6$<salt>$<hash> with valid crypt64 characters in the hash
        crypt64 = re.compile(r"^\$6\$[^$]+\$[./A-Za-z0-9]+$")
        assert crypt64.match(result), f"Invalid crypt format: {result!r}"

    def test_get_mapping_tracks_transformations(self) -> None:
        rule = self._make_rule()
        rule.transform("$9$abc")
        rule.transform("secretword")
        mapping = rule.get_mapping()
        assert "$9$abc" in mapping
        assert "secretword" in mapping


class TestPasswordAnonymizeIntegration:
    """Test the full anonymize() function with password rule."""

    def test_encrypted_password_anonymized(self) -> None:
        cfg = AnonymizeConfig(passwords=True, salt="test")
        ir = {
            "configuration": {
                "system": {
                    "root-authentication": {
                        "encrypted-password": "$6$abc$longHashValue123",
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        ep = result.ir["configuration"]["system"]["root-authentication"]["encrypted-password"]
        assert ep != "$6$abc$longHashValue123"
        assert ep.startswith("$6$abc$")

    def test_j9_password_in_login_user(self) -> None:
        cfg = AnonymizeConfig(passwords=True, salt="test")
        ir = {
            "configuration": {
                "system": {
                    "login": {
                        "user": [
                            {
                                "name": "admin",
                                "authentication": {
                                    "encrypted-password": "$9$LxNdsYaJUjqf",
                                },
                            },
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        ep = result.ir["configuration"]["system"]["login"]["user"][0]["authentication"][
            "encrypted-password"
        ]
        assert ep != "$9$LxNdsYaJUjqf"
        assert ep.startswith("$9$")

    def test_non_password_fields_unchanged(self) -> None:
        cfg = AnonymizeConfig(passwords=True, salt="test")
        ir = {
            "configuration": {
                "system": {
                    "host-name": "router1",
                    "root-authentication": {
                        "encrypted-password": "$6$abc$hash",
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        assert result.ir["configuration"]["system"]["host-name"] == "router1"

    def test_mapping_returned(self) -> None:
        cfg = AnonymizeConfig(passwords=True, salt="test")
        ir = {
            "configuration": {
                "system": {
                    "root-authentication": {
                        "encrypted-password": "$6$abc$hash",
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        assert "password" in result.mapping
        assert "$6$abc$hash" in result.mapping["password"]

    def test_no_rules_enabled_unchanged(self) -> None:
        cfg = AnonymizeConfig()
        ir = {
            "configuration": {
                "system": {
                    "root-authentication": {
                        "encrypted-password": "$6$abc$hash",
                    },
                },
            },
        }
        original = copy.deepcopy(ir)
        result = anonymize(ir, cfg)
        assert result.ir == original

    def test_bgp_authentication_key_anonymized(self) -> None:
        """BGP authentication-key should be anonymized (no tr in schema)."""
        cfg = AnonymizeConfig(passwords=True, salt="test")
        ir = {
            "configuration": {
                "protocols": {
                    "bgp": {
                        "group": [
                            {
                                "name": "PEERS",
                                "authentication-key": "$9$ExAmPlEhAsH.KEY",
                            },
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        ak = result.ir["configuration"]["protocols"]["bgp"]["group"][0]["authentication-key"]
        assert ak != "$9$ExAmPlEhAsH.KEY"
        assert ak.startswith("$9$")
        assert "password" in result.mapping

    def test_key_chain_secret_anonymized(self) -> None:
        """Key-chain secret should be anonymized."""
        cfg = AnonymizeConfig(passwords=True, salt="test")
        ir = {
            "configuration": {
                "security": {
                    "authentication-key-chains": {
                        "key-chain": [
                            {
                                "name": "ISIS-AUTH",
                                "key": [
                                    {
                                        "name": "1",
                                        "secret": "$9$j1Hqf3nCO1ECApBI",
                                        "start-time": "2024-01-01.00:00:00",
                                    },
                                ],
                            },
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        secret = result.ir["configuration"]["security"]["authentication-key-chains"]["key-chain"][
            0
        ]["key"][0]["secret"]
        assert secret != "$9$j1Hqf3nCO1ECApBI"
        assert secret.startswith("$9$")

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
