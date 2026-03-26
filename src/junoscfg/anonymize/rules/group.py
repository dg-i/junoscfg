"""Group and view name anonymization rule.

Matches configuration group names (``groups[*].name``), BGP peer group
names (``*.bgp.group[*].name``), and SNMP view names
(``snmp.view[*].name``).  Produces hash-based pseudonyms with
type-appropriate prefixes.

``apply-groups`` and ``apply-groups-except`` values are handled by a
second pass in :func:`junoscfg.anonymize.anonymize` because their schema
nodes are empty (``{}``), making them invisible to the schema-guided walker.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import TYPE_CHECKING, Any

from junoscfg.anonymize.rules import Rule

if TYPE_CHECKING:
    from junoscfg.anonymize.config import AnonymizeConfig


class GroupRule(Rule):
    """Replace group and view names with deterministic pseudonyms.

    Detects group-related fields by schema path:

    - Configuration groups: ``groups[*].name``
    - BGP peer groups: ``*.bgp.group[*].name``
    - SNMP views: ``snmp.view[*].name``
    - SNMP access groups: ``snmp.v3.vacm.*.group-name``
    """

    name = "group"
    priority = 60  # After identity (50)

    def __init__(self, config: AnonymizeConfig) -> None:
        self._salt = config.salt or ""
        self._mapping: dict[str, str] = {}

    def matches(
        self,
        value: Any,
        schema_node: dict[str, Any],
        path: list[str],
    ) -> bool:
        """Match group/view name fields by path pattern."""
        if not path:
            return False

        key = path[-1]

        # Configuration group names: groups.name (named-list key in
        # the transparent container's inner node)
        if key == "name" and len(path) >= 2 and path[-2] == "groups":
            return True

        # BGP peer group names: *.bgp.group.name
        if key == "name" and len(path) >= 3 and path[-2] == "group" and "bgp" in path:
            return True

        # VACM access.group[*].name named-list key
        if key == "name" and len(path) >= 3 and path[-2] == "group" and "vacm" in path:
            return True

        # SNMP view names: snmp.view.name
        if key == "name" and len(path) >= 3 and path[-2] == "view" and "snmp" in path:
            return True

        # SNMP v3 group-name fields
        if key == "group-name" and "snmp" in path:
            return True

        # VACM security-to-group.*.security-name[*].group leaf
        return bool(key == "group" and "vacm" in path)

    def transform(self, value: str) -> str:
        """Replace a group/view name with a pseudonym."""
        if value in self._mapping:
            return self._mapping[value]

        replaced = self._make_pseudonym(value)
        self._mapping[value] = replaced
        return replaced

    def _make_pseudonym(self, value: str) -> str:
        """Generate a deterministic group pseudonym."""
        hex_digest = hmac.new(self._salt.encode(), value.encode(), hashlib.sha256).hexdigest()
        return f"group_{hex_digest[:24]}"

    def get_mapping(self) -> dict[str, str]:
        """Return the original -> anonymized group mapping."""
        return dict(self._mapping)
