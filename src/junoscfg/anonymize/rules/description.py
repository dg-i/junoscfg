"""Description, contact, and location field anonymization rule.

Matches fields by key name: ``description``, ``contact``, ``location``.
Produces hash-based whole-value replacements with a ``descr_`` prefix.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import TYPE_CHECKING, Any

from junoscfg.anonymize.rules import Rule

if TYPE_CHECKING:
    from junoscfg.anonymize.config import AnonymizeConfig

_DESCRIPTION_KEY_NAMES: frozenset[str] = frozenset(
    {
        "description",
        "contact",
        "location",
    }
)


class DescriptionRule(Rule):
    """Replace description, contact, and location values with pseudonyms.

    Detects fields purely by key name — any leaf whose key is
    ``description``, ``contact``, or ``location`` is anonymized.
    """

    name = "description"
    priority = 70  # After group (60)

    def __init__(self, config: AnonymizeConfig) -> None:
        self._salt = config.salt or ""
        self._mapping: dict[str, str] = {}

    def matches(
        self,
        value: Any,
        schema_node: dict[str, Any],
        path: list[str],
    ) -> bool:
        """Match description/contact/location fields by key name."""
        if not path:
            return False
        return path[-1] in _DESCRIPTION_KEY_NAMES

    def transform(self, value: str) -> str:
        """Replace a description with a pseudonym."""
        if value in self._mapping:
            return self._mapping[value]

        replaced = self._make_pseudonym(value)
        self._mapping[value] = replaced
        return replaced

    def _make_pseudonym(self, value: str) -> str:
        """Generate a deterministic description pseudonym."""
        hex_digest = hmac.new(self._salt.encode(), value.encode(), hashlib.sha256).hexdigest()
        return f"descr_{hex_digest[:24]}"

    def get_mapping(self) -> dict[str, str]:
        """Return the original -> anonymized description mapping."""
        return dict(self._mapping)
