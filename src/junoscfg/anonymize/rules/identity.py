"""Username and identity anonymization rule.

Matches login usernames (``system.login.user[*].name``), full names
(``*.full-name``), and SNMP v3 security names.  Produces hash-based
pseudonyms with type-appropriate prefixes (``user_``, ``fullname_``).
"""

from __future__ import annotations

import hashlib
import hmac
from typing import TYPE_CHECKING, Any

from junoscfg.anonymize.rules import Rule

if TYPE_CHECKING:
    from junoscfg.anonymize.config import AnonymizeConfig


class IdentityRule(Rule):
    """Replace usernames and identity fields with deterministic pseudonyms.

    Detects identity fields by schema path:

    - Login usernames: ``*.login.user[*].name``
    - Full names: ``*.full-name``
    - SNMP v3 security names: ``snmp.*.security-name``
    """

    name = "identity"
    priority = 50  # After community (40)

    def __init__(self, config: AnonymizeConfig) -> None:
        self._salt = config.salt or ""
        self._mapping: dict[str, str] = {}

    def matches(
        self,
        value: Any,
        schema_node: dict[str, Any],
        path: list[str],
    ) -> bool:
        """Match identity-related fields by path pattern."""
        if not path:
            return False

        key = path[-1]

        # Login username: *.login.user.name (named-list key)
        if key == "name" and len(path) >= 3 and path[-2] == "user" and "login" in path:
            return True

        # SNMPv3 USM user: snmp.v3.usm.{local,remote}-engine.user[*].name
        if key == "name" and len(path) >= 3 and path[-2] == "user" and "usm" in path:
            return True

        # Full name: *.full-name (leaf)
        if key == "full-name":
            return True

        # SNMP v3 security-name (leaf or named-list key)
        if key == "security-name" and "snmp" in path:
            return True

        # VACM security-name named-list key: *.security-name[*].name
        return bool(
            key == "name" and len(path) >= 3 and path[-2] == "security-name" and "snmp" in path
        )

    def transform(self, value: str) -> str:
        """Replace an identity with a pseudonym."""
        if value in self._mapping:
            return self._mapping[value]

        replaced = self._make_pseudonym(value)
        self._mapping[value] = replaced
        return replaced

    def _make_pseudonym(self, value: str) -> str:
        """Generate a deterministic identity pseudonym."""
        hex_digest = hmac.new(self._salt.encode(), value.encode(), hashlib.sha256).hexdigest()
        return f"user_{hex_digest[:24]}"

    def get_mapping(self) -> dict[str, str]:
        """Return the original -> anonymized identity mapping."""
        return dict(self._mapping)
