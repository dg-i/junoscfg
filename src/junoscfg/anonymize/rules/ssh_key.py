"""SSH public key anonymization rule.

Matches SSH key entries at ``*.authentication.ssh-{rsa,dsa,ecdsa,ed25519}``
named-list keys. The key value has the format::

    <type> <base64-blob> [comment]

The type prefix is preserved, the base64 blob is replaced with a
deterministic same-length pseudonym, and the comment (which often
contains usernames, hostnames, or emails) is removed.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from typing import TYPE_CHECKING, Any

from junoscfg.anonymize.rules import Rule

if TYPE_CHECKING:
    from junoscfg.anonymize.config import AnonymizeConfig

_SSH_KEY_PARENTS: frozenset[str] = frozenset(
    {
        "ssh-rsa",
        "ssh-dsa",
        "ssh-ecdsa",
        "ssh-ed25519",
    }
)


class SshKeyRule(Rule):
    """Replace SSH public keys with deterministic pseudonyms.

    Preserves the key type prefix (``ssh-rsa``, ``ssh-ed25519``, etc.)
    and produces a same-length base64 replacement for the key blob.
    Comments (which often contain usernames, hostnames, or email
    addresses) are replaced with a generic label.
    """

    name = "ssh_key"
    priority = 20  # After passwords (10), before IPs (30)

    def __init__(self, config: AnonymizeConfig) -> None:
        self._salt = config.salt or ""
        self._mapping: dict[str, str] = {}

    def matches(
        self,
        value: Any,
        schema_node: dict[str, Any],
        path: list[str],
    ) -> bool:
        """Match named-list key fields under SSH key types.

        SSH key types (``ssh-rsa``, ``ssh-ed25519``, etc.) only appear as
        named-list parents under ``authentication`` or
        ``root-authentication`` contexts, so the parent check is
        sufficient without requiring an exact ``authentication`` segment.
        """
        if len(path) < 2 or path[-1] != "name":
            return False

        # Parent must be an SSH key type
        return path[-2] in _SSH_KEY_PARENTS

    def transform(self, value: str) -> str:
        """Replace an SSH public key with a pseudonym."""
        if value in self._mapping:
            return self._mapping[value]

        replaced = self._do_transform(value)
        self._mapping[value] = replaced
        return replaced

    def _do_transform(self, value: str) -> str:
        """Produce the replacement SSH key string."""
        parts = value.split(None, 2)
        if len(parts) < 2:
            # Fallback: just replace entire value
            return self._make_pseudonym(value, len(value))

        key_type = parts[0]
        blob = parts[1]

        # Generate a deterministic base64-like blob of the same length
        new_blob = self._make_base64_blob(value, len(blob))

        return f"{key_type} {new_blob} anonymized-key"

    def _make_base64_blob(self, value: str, length: int) -> str:
        """Generate a deterministic base64 string of *length* characters."""
        # Generate enough HMAC bytes to fill the required length
        chunks: list[str] = []
        total = 0
        counter = 0
        while total < length:
            digest = hmac.new(
                self._salt.encode(),
                f"{value}:{counter}".encode(),
                hashlib.sha256,
            ).digest()
            b64 = base64.b64encode(digest).decode().rstrip("=")
            chunks.append(b64)
            total += len(b64)
            counter += 1
        return "".join(chunks)[:length]

    def _make_pseudonym(self, value: str, length: int) -> str:
        """Fallback: generate a hex pseudonym."""
        hex_digest = hmac.new(self._salt.encode(), value.encode(), hashlib.sha256).hexdigest()
        return hex_digest[:length] if length > 0 else hex_digest[:32]

    def get_mapping(self) -> dict[str, str]:
        """Return the original -> anonymized SSH key mapping."""
        return dict(self._mapping)
