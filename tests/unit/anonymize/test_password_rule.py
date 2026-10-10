"""Tests for the password anonymization rule.

What every rule keeps -- determinism, the salt, consistency, the mapping and
revert -- is `tests/contract/test_every_rule.py`; this file keeps what is the
password rule's own: which leaves it takes and the form of its replacements.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import subprocess
import sys

import pytest
from netutils.password import JUNIPER_KEYS_STRING, decrypt_juniper_type9

import junoscfg.anonymize as anonymize_door
from junoscfg.anonymize import AnonymizeConfig, PasswordRule, anonymize
from tests.support.paths import PACKAGE_SRC

#: The alphabet crypt salts and bodies are drawn from.
_CRYPT64 = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def _body_stream(salt: str, value: str, length: int) -> str:
    """HMAC-SHA256 of *value* keyed by *salt*, as hex, folded forward to *length*.

    The derivation a crypt body is drawn from, written out here rather than
    imported from the rule, so the tests that use it check the rule against an
    independent statement of it: each fold appends the SHA-256 hex of
    everything so far.
    """
    out = hmac.new(salt.encode(), value.encode(), hashlib.sha256).hexdigest()
    while len(out) < length:
        out += hashlib.sha256(out.encode()).hexdigest()
    return out[:length]


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
        assert result.startswith("$1$")
        assert result != original
        # The original salt is per-password entropy from the customer's
        # configuration; re-emitting it would leave a correlation handle.
        assert "abc123" not in result
        _, _, salt, body = result.split("$")
        assert len(salt) == len("abc123")
        assert len(body) == len("xyzHashValueHere")

    def test_sha256_format_preserved(self) -> None:
        rule = self._make_rule()
        original = "$5$rounds=5000$saltsalt$hashbodyhashbodyhashbody"
        result = rule.transform(original)
        # rounds= is a parameter and survives; the salt after it does not.
        assert result.startswith("$5$rounds=5000$")
        assert result != original
        assert "saltsalt" not in result

    def test_sha512_format_preserved(self) -> None:
        rule = self._make_rule()
        original = "$6$abc$xyzLongHashValueHereThatIsLong"
        result = rule.transform(original)
        assert result.startswith("$6$")
        assert result != original
        assert "$abc$" not in result
        _, _, salt, body = result.split("$")
        assert len(salt) == len("abc")
        assert len(body) == len("xyzLongHashValueHereThatIsLong")

    def test_sha1_format_preserved(self) -> None:
        """$sha1$ (NetBSD crypt-sha1, used in FIPS mode) format preserved."""
        rule = self._make_rule()
        original = "$sha1$19418$aoTClyGU$cix8MhZsXwG6OrwUgeHAoOA8f.AX"
        result = rule.transform(original)
        assert result.startswith("$sha1$19418$")  # iterations are a parameter
        assert "aoTClyGU" not in result  # the salt is not
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
        assert result.startswith("$3$")
        assert "$salt$" not in result  # the salt is replaced, not copied
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

    def test_crypt_hash_valid_format(self) -> None:
        """Anonymized $6$ output must match the $6$salt$hash pattern."""
        rule = self._make_rule()
        original = "$6$abc$xyzLongHashValueHereThatIsLong"
        result = rule.transform(original)
        assert result.startswith("$6$")
        # Must be $6$<salt>$<hash> with valid crypt64 characters in the hash
        crypt64 = re.compile(r"^\$6\$[^$]+\$[./A-Za-z0-9]+$")
        assert crypt64.match(result), f"Invalid crypt format: {result!r}"


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
        assert ep.startswith("$6$")
        assert "$abc$" not in ep  # the original salt is replaced, not copied

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


class TestThePasswordRuleLoadsOnFirstUse:
    """The door hands out `PasswordRule` without importing netutils up front.

    netutils costs more to import than the rest of the package together, and a
    run without passwords on never needs it.
    """

    def test_importing_the_door_leaves_netutils_unloaded(self) -> None:
        probe = (
            "import sys, junoscfg.anonymize as door\n"
            "before = 'netutils' in sys.modules\n"
            "rule = door.PasswordRule\n"
            "print(before, 'netutils' in sys.modules, rule.__name__)\n"
        )
        out = subprocess.run(
            [sys.executable, "-c", probe], capture_output=True, text=True, check=True
        ).stdout
        assert out.split() == ["False", "True", "PasswordRule"]

    def test_the_door_hands_out_the_rule_itself(self) -> None:
        assert anonymize_door.PasswordRule is PasswordRule

    def test_a_name_the_door_lacks_is_an_attribute_error(self) -> None:
        with pytest.raises(AttributeError, match="NoSuchRule"):
            getattr(anonymize_door, "NoSuchRule")  # noqa: B009 - the name is the case


class TestCryptIndependence:
    """The password rule must not depend on the stdlib ``crypt`` module.

    ``crypt.crypt()`` answers an unsupported ``$N$`` salt with a 13-character
    DES hash on macOS, and the module was removed in Python 3.13, so output
    used to depend on both the host libc and the interpreter. These pin the
    deterministic replacement.
    """

    def test_no_crypt_import_anywhere_in_the_package(self) -> None:
        import ast

        package = PACKAGE_SRC
        assert package.is_dir(), package
        scanned = 0
        offenders = []
        for path in package.rglob("*.py"):
            scanned += 1
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import) and any(a.name == "crypt" for a in node.names):
                    offenders.append(str(path))
                if isinstance(node, ast.ImportFrom) and node.module == "crypt":
                    offenders.append(str(path))
        assert scanned > 50, f"only scanned {scanned} files; the glob is wrong"
        assert offenders == []

    def test_output_is_fixed_for_a_fixed_salt(self) -> None:
        """Byte-for-byte stable, so two machines anonymize a config alike."""
        rule = self._make_rule()
        # The body is as long as the one it replaces (17 chars here), which is
        # what every other format in password.py already does.
        assert rule.transform("$1$abc123$xyzHashValueHere") == "$1$yzmBmY$9f910e33980334f5"

    def test_body_length_matches_the_format(self) -> None:
        """A $1$/$5$/$6$ body keeps the length of the body it replaces."""
        rule = self._make_rule()
        for prefix, length in (("$1$", 22), ("$5$", 43), ("$6$", 86)):
            out = rule.transform(f"{prefix}abcdefgh${'x' * length}")
            assert len(out.split("$")[-1]) == length, f"{prefix} body wrong length: {out}"

    @staticmethod
    def _make_rule() -> PasswordRule:
        config = AnonymizeConfig(passwords=True, salt="fixed-salt")
        config.expand_all()
        return PasswordRule(config)


class TestSaltIsNotCopied:
    """The original crypt salt must not survive into the output.

    A crypt salt is per-password entropy lifted from the customer's
    configuration. The hash body is safe -- HMAC-SHA256 is one-way -- but
    re-emitting the salt verbatim leaves a correlation handle: anyone holding
    the original hash can match ``$6$<salt>$...`` to the exact account.
    """

    @staticmethod
    def _make_rule() -> PasswordRule:
        config = AnonymizeConfig(passwords=True, salt="fixed-salt")
        config.expand_all()
        return PasswordRule(config)

    def test_salt_is_replaced_for_every_crypt_format(self) -> None:
        rule = self._make_rule()
        for prefix, salt, body_len in (
            ("$1$", "abc123", 22),
            ("$5$", "saltsalt", 43),
            ("$6$", "s8chars.", 86),
        ):
            out = rule.transform(f"{prefix}{salt}${'x' * body_len}")
            assert salt not in out, f"{prefix} leaked its salt: {out}"
            new_salt = out.split("$")[2]
            assert len(new_salt) == len(salt)
            assert all(c in _CRYPT64 for c in new_salt)

    def test_rounds_is_a_parameter_not_a_salt(self) -> None:
        """$5$rounds=N$ keeps the rounds field and still replaces the salt."""
        rule = self._make_rule()
        out = rule.transform("$5$rounds=5000$realsalt$" + "y" * 43)
        assert out.startswith("$5$rounds=5000$")
        assert "realsalt" not in out
        assert len(out.split("$")[3]) == len("realsalt")

    def test_no_format_copies_its_salt(self) -> None:
        """Every hash family, not just the crypt three.

        bcrypt carries a 22-character salt and $8$ carries a salt, an IV and a
        GCM authentication tag -- a MAC over the real plaintext. Each is at
        least as good a correlation handle as the $6$ salt.
        """
        rule = self._make_rule()
        cases = [
            (
                "$2a$12$WApznUPhDubN0oeveSXVqeG7HqBSly4o7.gphTrw5KjYz5GBrmGOK",
                ["WApznUPhDubN0oeveSXVqe"],
            ),
            ("$sha1$12345$SaltyMcSalt$hhhhhhhhhhhhhhhhhhh", ["SaltyMcSalt"]),
            ("$3$MyNtSalt$ffffffffffffffffffffffffffffffff", ["MyNtSalt"]),
            (
                "$8$9$sha256$5000$MyAesSalt$MyIVvalue$MyTagValue$cipherpayload",
                ["MyAesSalt", "MyIVvalue", "MyTagValue"],
            ),
        ]
        for original, secrets in cases:
            out = rule.transform(original)
            for secret in secrets:
                assert secret not in out, f"{original[:12]} leaked {secret!r}: {out}"

    def test_eight_keeps_its_parameters(self) -> None:
        """$8$ algorithm and iteration fields are structure, not entropy."""
        rule = self._make_rule()
        out = rule.transform("$8$9$sha256$5000$MyAesSalt$MyIVvalue$MyTagValue$cipherpayload")
        assert out.startswith("$8$9$sha256$5000$")
        assert len(out.split("$")) == len(["", "8", "9", "sha256", "5000", "s", "i", "t", "c"])

    def test_salt_is_not_recomputable_from_the_body(self) -> None:
        """The salt and the body come from separate streams.

        Both used to be prefixes of one digest, so the salt was a pure
        function of the first characters of the body it sat next to. That
        leaks nothing, but it gives the output a self-consistency property
        that fingerprints it, and costs nothing to avoid.
        """
        original = "$6$s8chars.$" + "z" * 86
        out = self._make_rule().transform(original)
        salt, body = out.split("$")[2], out.split("$")[3]

        # What the salt would be if it shared the body's stream, as before.
        shared = _body_stream("fixed-salt", original, len(salt) * 2)
        recomputed = "".join(
            _CRYPT64[int(shared[i * 2 : i * 2 + 2], 16) % len(_CRYPT64)] for i in range(len(salt))
        )
        assert salt != recomputed
        assert body.startswith(shared[: len(body)][: len(body)])  # body still is that stream

    def test_replacement_salt_is_deterministic(self) -> None:
        a, b = self._make_rule(), self._make_rule()
        original = "$6$saltsalt$" + "z" * 86
        assert a.transform(original) == b.transform(original)
