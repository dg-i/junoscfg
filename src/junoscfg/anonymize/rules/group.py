"""Group and view name anonymization rule.

Matches configuration group names (``groups[*].name``), the references to them
(``apply-groups`` and ``apply-groups-except`` at every level), BGP peer group
names (``*.bgp.group[*].name``), and SNMP view names (``snmp.view[*].name``).
Produces hash-based pseudonyms with type-appropriate prefixes.

The walker reaches a reference at every level: the tree declares both
statements on its root, flagged universal, and `junoscfg.display.schema_child`
resolves them below it. The rule claims them in the walk, so a group and every
reference to it get one replacement whichever other rules are on; the second
pass that rewrote every reference again after the walk is gone (ANON-P1,
change anonymize-every-placed-value).

A group name Junos gives a meaning of its own passes unchanged, as a group
and as a reference: ``re0`` and ``re1`` apply to that Routing Engine,
``node0`` and ``node1`` to that chassis-cluster node, ``member<N>`` to that
Virtual Chassis member, and ``${node}`` (any ``$`` variable) is expanded by
Junos at commit (Junos OS "Configuration Groups" documentation: groups named
for a Routing Engine, cluster node or member are applied to it alone).
Renamed, the group would apply nowhere.
"""

from __future__ import annotations

import hashlib
import hmac
import re
from typing import TYPE_CHECKING, Any

from junoscfg.anonymize.rules import Rule

if TYPE_CHECKING:
    from junoscfg.anonymize.config import AnonymizeConfig


#: Group names Junos reserves for a Routing Engine, a cluster node or a
#: Virtual Chassis member, and variables Junos expands (`${node}`).
_RESERVED_GROUP = re.compile(r"^(?:re[01]|node[01]|member\d+|\$.*)$")
_REFERENCES = frozenset({"apply-groups", "apply-groups-except"})


class GroupRule(Rule):
    """Replace group and view names with deterministic pseudonyms.

    Detects group-related fields by schema path:

    - Configuration groups: ``groups[*].name``, and every ``apply-groups`` and
      ``apply-groups-except`` naming one
    - BGP peer groups: ``*.bgp.group[*].name``
    - SNMP views: ``snmp.view[*].name``
    - SNMP access groups: ``snmp.v3.vacm.*.group-name``
    """

    name = "group"
    priority = 60  # After identity (50)

    def __init__(self, config: AnonymizeConfig) -> None:
        """Build the rule from *config*: the salt and an empty mapping."""
        self._salt = config.salt or ""
        self._mapping: dict[str, str] = {}

    def matches(
        self,
        value: Any,
        schema_node: dict[str, Any],
        path: list[str],
    ) -> bool:
        """Match group/view name fields and group references by path pattern."""
        if not path:
            return False

        key = path[-1]

        if (
            isinstance(value, str)
            and _RESERVED_GROUP.match(value)
            and (key in _REFERENCES or (key == "name" and len(path) >= 2 and path[-2] == "groups"))
        ):
            return False

        # A reference to a configuration group, at any level.
        if key in _REFERENCES:
            return True

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
