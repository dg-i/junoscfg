"""Password and secret anonymization rule.

Matches fields using three strategies (any match triggers anonymization):

1. Schema ``tr == "unreadable"`` (~718 nodes — ``password``, ``secret``, etc.)
2. Key name in ``_PASSWORD_KEY_NAMES`` (covers ``encrypted-password``,
   ``authentication-key``, ``secret``, etc. that lack ``tr`` in the schema)
3. Content-based: value starts with a known hash prefix (``$9$``, ``$6$``, etc.)

This is intentionally broad — false positives (over-anonymizing) are
preferable to missing real secrets.

Juniper password/secret formats handled:

- ``$9$``   — Juniper Type 9 obfuscation (reversible, most common for shared secrets)
- ``$8$``   — AES-256-GCM master password encryption (reversible, since JunOS 16.2)
- ``$6$``   — SHA-512 crypt hash (current default for login passwords)
- ``$5$``   — SHA-256 crypt hash (15.x era)
- ``$sha1$``— NetBSD SHA-1/HMAC (FIPS default)
- ``$1$``   — MD5 crypt hash (legacy, ≤12.3)
- ``$2$``/``$2a$``/``$2b$``/``$2y$`` — bcrypt/Blowfish (FreeBSD inherited)
- ``$3$``   — NTHASH (FreeBSD inherited, rare)
- Plain text secrets → ``netconanRemoved<N>``
"""

from __future__ import annotations

import hashlib
import hmac
import re
from typing import TYPE_CHECKING, Any

from netutils.password import (
    JUNIPER_CHARACTER_KEYS,
    JUNIPER_ENCODING,
    JUNIPER_KEYS_LENGTH,
    JUNIPER_KEYS_STRING,
)

from junoscfg.anonymize.rules import Rule

if TYPE_CHECKING:
    from junoscfg.anonymize.config import AnonymizeConfig

# Known hash/encryption prefixes in Juniper configurations.
# Order matters: longer prefixes first to avoid false prefix matches.
_HASH_PREFIXES = (
    "$sha1$",
    "$2y$",
    "$2b$",
    "$2a$",
    "$2$",
    "$9$",
    "$8$",
    "$6$",
    "$5$",
    "$3$",
    "$1$",
)

# Key names that always hold password/secret values, even when the schema
# node lacks ``tr: "unreadable"``.  These cover encrypted-password fields,
# BGP/OSPF/IS-IS authentication keys, key-chain secrets, SNMP auth, etc.
_PASSWORD_KEY_NAMES: frozenset[str] = frozenset(
    {
        "encrypted-password",
        "authentication-key",
        "authentication-password",
        "simple-password",
        "secret",
        "preauthentication-secret",
        "community-string",
        "privacy-key",
    }
)

# Regex to detect any value starting with a hash prefix ($N$ or $sha1$).
_HASH_VALUE_RE = re.compile(r"^\$(?:sha1|[0-9]+[a-z]?)\$")


def _hmac_hex(salt: str, value: str) -> str:
    """Return a hex HMAC-SHA256 digest of *value* keyed by *salt*."""
    return hmac.new(salt.encode(), value.encode(), hashlib.sha256).hexdigest()


def _encrypt_j9_deterministic(hex_digest: str, plaintext: str) -> str:
    """Produce a structurally valid ``$9$`` string using the netutils encoding.

    Uses the same encoding algorithm as ``netutils.password.encrypt_juniper_type9``
    but replaces all random choices with values derived from *hex_digest* so the
    output is deterministic for a given input.
    """
    # Derive a deterministic salt index from the digest.
    salt_idx = int(hex_digest[:2], 16) % JUNIPER_KEYS_LENGTH
    first_char = JUNIPER_KEYS_STRING[salt_idx]

    # Derive deterministic padding characters (same role as random chars in netutils).
    num_padding = JUNIPER_CHARACTER_KEYS[first_char]
    padding_chars = ""
    for i in range(num_padding):
        pad_idx = int(hex_digest[2 + i : 4 + i], 16) % JUNIPER_KEYS_LENGTH
        padding_chars += JUNIPER_KEYS_STRING[pad_idx]

    encrypted = "$9$" + first_char + padding_chars

    # Encode each plaintext character using the Juniper encoding table.
    previous_char = first_char
    for index, char in enumerate(plaintext):
        encode = JUNIPER_ENCODING[index % len(JUNIPER_ENCODING)][::-1]
        char_ord = ord(char)
        gaps: list[int] = []
        for modulus in encode:
            gaps = [int(char_ord / modulus)] + gaps
            char_ord %= modulus

        for gap in gaps:
            gap += JUNIPER_KEYS_STRING.index(previous_char) + 1
            new_char = JUNIPER_KEYS_STRING[gap % JUNIPER_KEYS_LENGTH]
            previous_char = new_char
            encrypted += new_char

    return encrypted


# Body lengths the crypt formats specify, used when the original gives no
# length to copy.  md5crypt is 22 characters, sha256crypt 43, sha512crypt 86.
_CRYPT_BODY_LENGTH = {"$1$": 22, "$5$": 43, "$6$": 86}

# The alphabet crypt salts and bodies are drawn from.
_CRYPT64 = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def _pseudo_field(hex_digest: str, length: int, domain: str) -> str:
    """A replacement field of *length* crypt64 characters.

    Every per-password field a hash carries -- the salt, and for ``$8$`` the
    IV and the authentication tag -- is entropy lifted straight from the
    customer's configuration.  Re-emitting any of them verbatim leaves a
    correlation handle: anyone holding the original string can match it to the
    exact account even though the body is safe.

    *domain* separates the streams, so no field can be recomputed from another
    and the salt is not a function of the emitted body.
    """
    if length <= 0:
        return ""
    seed = hashlib.sha256(f"{domain}:{hex_digest}".encode()).hexdigest()
    source = _extend_hex(seed, max(length * 2, 2))
    return "".join(
        _CRYPT64[int(source[i * 2 : i * 2 + 2], 16) % len(_CRYPT64)] for i in range(length)
    )


def _extend_hex(hex_digest: str, length: int) -> str:
    """Deterministic hex of exactly *length* characters.

    One SHA-256 hexdigest is 64 characters, which is shorter than a
    sha512crypt body, so the digest is folded forward until it is long enough.
    Same input, same output, on every platform.
    """
    out = hex_digest
    while len(out) < length:
        out += hashlib.sha256(out.encode()).hexdigest()
    return out[:length]


def _make_crypt_hash(hex_digest: str, prefix: str, original_salt: str, body_length: int) -> str:
    """Produce a structurally valid ``$1$``/``$5$``/``$6$`` hash.

    The body is derived deterministically from *hex_digest* and is as long as
    the body it replaces, which is what every other format in this module
    already does.  Same input and salt give the same output on every platform
    and interpreter: a configuration anonymized on one machine has to match one
    anonymized on another.

    This used to call ``crypt.crypt()``.  macOS answers an unsupported ``$N$``
    salt with a 13-character DES hash rather than the requested format, so the
    result depended on the host's libc; and ``crypt`` was removed from the
    standard library in 3.13, which silently made the fallback the only path
    there.  The fallback is now the only path everywhere, and length-correct.
    """
    length = body_length or _CRYPT_BODY_LENGTH.get(prefix, 64)
    return f"{prefix}{original_salt}${_extend_hex(hex_digest, length)}"


class PasswordRule(Rule):
    """Replace passwords and secrets with format-preserving pseudonyms.

    Matching uses three strategies (any match triggers anonymization):

    1. Schema ``tr == "unreadable"`` (covers ~718 nodes)
    2. Key name in ``_PASSWORD_KEY_NAMES`` (covers ``encrypted-password``,
       ``authentication-key``, etc.)
    3. Content looks like a password hash (``$9$...``, ``$6$...``, etc.)

    Produces replacements that keep the hash algorithm prefix but replace
    the hash body with a deterministic pseudonym derived from
    HMAC-SHA256(salt, original).  Plain-text secrets are replaced with
    ``netconanRemoved<N>``.
    """

    name = "password"
    priority = 10  # Highest priority — checked before all other rules

    def __init__(self, config: AnonymizeConfig) -> None:
        """Build the rule from *config*: the salt and an empty mapping."""
        self._salt = config.salt or ""
        self._mapping: dict[str, str] = {}
        self._plain_counter = 0
        # Cache plain-text replacements for determinism
        self._plain_cache: dict[str, str] = {}

    def matches(
        self,
        value: Any,
        schema_node: dict[str, Any],
        path: list[str],
    ) -> bool:
        """Match leaves that contain password/secret data.

        Uses three complementary strategies:

        1. Schema ``tr == "unreadable"`` — explicit schema marking
        2. Key name in ``_PASSWORD_KEY_NAMES`` — covers fields that lack
           ``tr`` in the schema but always hold secrets
        3. Content pattern — value starts with a known hash prefix
        """
        # Strategy 1: schema type_ref
        type_ref = schema_node.get("tr")
        if type_ref is not None and type_ref.lower() == "unreadable":
            return True

        # Strategy 2: known password key names
        if path and path[-1] in _PASSWORD_KEY_NAMES:
            return True

        # Strategy 3: content looks like a password hash
        return isinstance(value, str) and bool(_HASH_VALUE_RE.match(value))

    def transform(self, value: str) -> str:
        """Replace a password/secret with a format-preserving pseudonym."""
        if value in self._mapping:
            return self._mapping[value]

        replaced = self._do_transform(value)
        self._mapping[value] = replaced
        return replaced

    def _do_transform(self, value: str) -> str:
        """Produce the replacement string."""
        # Detect hash format and preserve prefix
        for prefix in _HASH_PREFIXES:
            if value.startswith(prefix):
                return self._replace_hashed(value, prefix)

        # Plain-text secret
        return self._replace_plain(value)

    def _replace_hashed(self, value: str, prefix: str) -> str:
        """Replace a hashed password, preserving the algorithm prefix."""
        body = value[len(prefix) :]
        hex_digest = _hmac_hex(self._salt, value)

        if prefix == "$9$":
            # Derive a pseudo-plaintext from the HMAC and encode it using
            # the real Juniper $9$ algorithm for structurally valid output.
            pseudo_plain = hex_digest[:8]
            return _encrypt_j9_deterministic(hex_digest[8:], pseudo_plain)

        if prefix in ("$6$", "$5$", "$1$"):
            # Unix crypt formats: $N$[rounds=X$]salt$hash.  The rounds field is
            # a parameter, not a salt, and was previously mistaken for one,
            # which dropped the real salt and left rounds= in its place.
            rounds = ""
            rest = body
            if rest.startswith("rounds="):
                rounds_field, _, remainder = rest.partition("$")
                if remainder:
                    rounds = f"{rounds_field}$"
                    rest = remainder
            parts = rest.split("$", 1)
            if len(parts) == 2:
                original_salt, original_body = parts
                return _make_crypt_hash(
                    hex_digest,
                    f"{prefix}{rounds}",
                    _pseudo_field(hex_digest, len(original_salt), "salt"),
                    len(original_body),
                )

        if prefix == "$8$":
            # AES-256-GCM: $8$crypt-algo$hash-algo$iterations$salt$iv$tag$encrypted
            # Preserve structure markers, replace encrypted payload
            parts = body.split("$")
            if len(parts) >= 7:
                # $8$crypt-algo$hash-algo$iterations$salt$iv$tag$encrypted.
                # The first three are parameters; salt, IV and the GCM
                # authentication tag are per-password entropy and a tag is a
                # MAC over the real plaintext, so none may survive.
                for index, domain in ((3, "salt"), (4, "iv"), (5, "tag")):
                    parts[index] = _pseudo_field(hex_digest, len(parts[index]), domain)
                parts[-1] = hex_digest[: len(parts[-1])] if parts[-1] else hex_digest[:32]
                return f"$8${'$'.join(parts)}"
            if len(parts) >= 6:
                parts[-1] = hex_digest[: len(parts[-1])] if parts[-1] else hex_digest[:32]
                return f"$8${'$'.join(parts)}"
            # Fallback: replace entire body
            new_body = hex_digest[: len(body)] if body else hex_digest[:32]
            return f"$8${new_body}"

        if prefix == "$sha1$":
            # NetBSD sha1crypt: $sha1$iterations$salt$hash
            parts = body.split("$", 2)
            if len(parts) == 3:
                iterations, sha_salt, sha_hash = parts
                new_hash = hex_digest[: len(sha_hash)] if sha_hash else hex_digest[:28]
                new_salt = _pseudo_field(hex_digest, len(sha_salt), "salt")
                return f"$sha1${iterations}${new_salt}${new_hash}"
            new_body = hex_digest[: len(body)] if body else hex_digest[:32]
            return f"$sha1${new_body}"

        if prefix.startswith("$2"):
            # bcrypt: $2<variant>$cost$salt+hash (22-char salt + 31-char hash)
            parts = body.split("$", 1)
            if len(parts) == 2:
                cost = parts[0]
                salt_hash = parts[1]
                if len(salt_hash) >= 22:
                    hash_len = len(salt_hash) - 22
                    new_hash = hex_digest[:hash_len] if hash_len > 0 else hex_digest[:31]
                    new_salt = _pseudo_field(hex_digest, 22, "salt")
                    return f"{prefix}{cost}${new_salt}{new_hash}"
                new_body = hex_digest[: len(salt_hash)] if salt_hash else hex_digest[:53]
                return f"{prefix}{cost}${new_body}"

        # Other Unix crypt formats ($3$): prefix$salt$hash
        parts = body.split("$", 1)
        if len(parts) == 2:
            new_hash = hex_digest[: len(parts[1])] if parts[1] else hex_digest[:32]
            new_salt = _pseudo_field(hex_digest, len(parts[0]), "salt")
            return f"{prefix}{new_salt}${new_hash}"

        # Fallback: just replace the body with hex
        new_body = hex_digest[: len(body)] if body else hex_digest[:32]
        return f"{prefix}{new_body}"

    def _replace_plain(self, value: str) -> str:
        """Replace a plain-text secret with a numbered pseudonym."""
        if value in self._plain_cache:
            return self._plain_cache[value]

        result = f"netconanRemoved{self._plain_counter}"
        self._plain_counter += 1
        self._plain_cache[value] = result
        return result

    def get_mapping(self) -> dict[str, str]:
        """Return the original -> anonymized password mapping."""
        return dict(self._mapping)
