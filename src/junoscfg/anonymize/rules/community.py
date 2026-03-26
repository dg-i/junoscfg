"""SNMP community string anonymization rule.

Matches community names at ``snmp.community[*].name`` and related paths.
Since community names are named-list keys without a type_ref, this rule
uses path-based detection: the parent path segment must be ``community``
within an ``snmp`` context.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import TYPE_CHECKING, Any

from junoscfg.anonymize.rules import Rule

if TYPE_CHECKING:
    from junoscfg.anonymize.config import AnonymizeConfig

# Path segments that indicate an SNMP community context.
_COMMUNITY_PARENTS: frozenset[str] = frozenset(
    {
        "community",
    }
)


class CommunityRule(Rule):
    """Replace SNMP community strings with deterministic pseudonyms.

    Community strings are identified by their schema path
    (``snmp.community[*].name``). Values starting with ``$`` are
    skipped as they are variable references, not actual community strings.
    """

    name = "community"
    priority = 40  # After IPs (30)

    def __init__(self, config: AnonymizeConfig) -> None:
        self._salt = config.salt or ""
        self._mapping: dict[str, str] = {}
        self._counter = 0
        self._cache: dict[str, str] = {}

    def matches(
        self,
        value: Any,
        schema_node: dict[str, Any],
        path: list[str],
    ) -> bool:
        """Match named-list key fields under ``snmp.community``."""
        # Must be a "name" key field inside a "community" named list
        if len(path) < 3 or path[-1] != "name":
            return False

        parent = path[-2]
        if parent not in _COMMUNITY_PARENTS:
            return False

        # Must be within an "snmp" context somewhere in the path
        if "snmp" not in path:
            return False

        # Skip variable references (e.g., $community_var)
        return not (isinstance(value, str) and value.startswith("$"))

    def transform(self, value: str) -> str:
        """Replace an SNMP community string with a pseudonym."""
        if value in self._mapping:
            return self._mapping[value]

        replaced = self.__make_pseudonym(value)
        self._mapping[value] = replaced
        return replaced

    def __make_pseudonym(self, value: str) -> str:
        """Generate a deterministic community pseudonym."""
        if value in self._cache:
            return self._cache[value]

        hex_digest = hmac.new(self._salt.encode(), value.encode(), hashlib.sha256).hexdigest()
        result = f"community_{hex_digest[:24]}"
        self._cache[value] = result
        return result

    def get_mapping(self) -> dict[str, str]:
        """Return the original -> anonymized community mapping."""
        return dict(self._mapping)
