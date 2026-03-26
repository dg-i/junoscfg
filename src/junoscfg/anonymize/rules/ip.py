"""IP address anonymization rule using the ipanon library."""

from __future__ import annotations

import ipaddress
import re
from typing import TYPE_CHECKING, Any

from ipanon import Anonymizer

from junoscfg.anonymize.rules import Rule

if TYPE_CHECKING:
    from junoscfg.anonymize.config import AnonymizeConfig

# Regex for matching IPv4 addresses embedded in larger strings.
# Uses word-boundary-like anchoring: not preceded/followed by a dot or digit
# to avoid matching partial numbers (e.g., "1.2.3.4.5" or "x11.2.3.4").
_IPV4_IN_STRING_RE = re.compile(
    r"(?<!\d)(?<!\.)"  # Not preceded by digit or dot
    r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IPv4 address
    r"(?:/(\d{1,2}))?"  # Optional CIDR prefix
    r"(?![\d.])"  # Not followed by digit or dot
)

# Type references from the schema that indicate IP address fields.
# Matches the sets in field_validator.py plus additional variants from the plan.
_IP_TYPE_REFS: frozenset[str] = frozenset(
    {
        "ipaddr",
        "ipv4addr",
        "ipv6addr",
        "ipprefix",
        "ipv4prefix",
        "ipv6prefix",
        "ipaddr-or-interface",
        "ipprefix-optional",
        "ipprefix-mandatory",
        "ipv4prefix-only",
        "ipv6prefix-mandatory",
        "ipv4addr-or-interface",
        # Include the *address variants from field_validator
        "ipv4address",
        "ipv6address",
    }
)

# Schema path segments whose named-list key ("name" field) is known
# to be an IP address, even when the schema has no tr on the list node.
_IP_NAMED_LIST_PARENTS: frozenset[str] = frozenset(
    {
        "address",
        "area",
        "clients",
        "destination",
        "destination-address",
        "host",
        "name-server",
        "neighbor",
        "next-hop",
        "prefix-list-item",
        "qualified-next-hop",
        "route",
        "server",
        "source-address",
        "static-route",
    }
)


def _looks_like_ip(value: str) -> bool:
    """Return True if *value* parses as an IP address or CIDR prefix."""
    # Strip CIDR suffix for validation
    addr_part = value.split("/")[0] if "/" in value else value
    try:
        ipaddress.ip_address(addr_part)
        return True
    except ValueError:
        return False


class IpRule(Rule):
    """Anonymize IP addresses using prefix-preserving permutation."""

    name = "ip"
    priority = 30  # After passwords (10) and SSH keys (20)

    def __init__(self, config: AnonymizeConfig) -> None:
        self._anonymizer = Anonymizer(
            salt=config.salt,
            pass_through_prefixes=config.preserve_prefixes or None,
            ignore_subnets=config.ignore_subnets,
            ignore_reserved=config.ignore_reserved,
            quiet=config.log_level != "debug",
        )

    def matches(
        self,
        value: Any,
        schema_node: dict[str, Any],
        path: list[str],
    ) -> bool:
        """Match leaf values whose schema type_ref indicates an IP field.

        For named-list key fields without a type_ref, falls back to checking
        if the parent path segment is a known IP-keyed list and the value
        parses as an IP address.
        """
        type_ref = schema_node.get("tr")
        if type_ref is not None and type_ref.lower() in _IP_TYPE_REFS:
            return True

        # Fallback for named-list key fields: check parent path + value shape.
        # path is like [..., "address", "name"] — check the segment before "name".
        if len(path) >= 2 and path[-1] == "name":
            parent_key = path[-2]
            if parent_key in _IP_NAMED_LIST_PARENTS and _looks_like_ip(str(value)):
                return True

        return False

    def transform(self, value: str) -> str:
        """Anonymize an IP address or CIDR prefix string."""
        return self._anonymizer.anonymize(value)

    def replace_ips_in_string(self, value: str) -> str:
        """Replace all embedded IPv4 addresses in a string.

        Used for the ``ips_in_strings`` option to catch IPs inside URLs,
        host+IP combos, and other non-standalone contexts.
        """

        def _replace(m: re.Match[str]) -> str:
            addr_str = m.group(1)
            cidr = m.group(2)
            try:
                ipaddress.ip_address(addr_str)
            except ValueError:
                return m.group(0)
            if cidr:
                anon = self._anonymizer.anonymize(f"{addr_str}/{cidr}")
                return anon
            return self._anonymizer.anonymize(addr_str)

        return _IPV4_IN_STRING_RE.sub(_replace, value)

    def get_mapping(self) -> dict[str, str]:
        """Return the original -> anonymized IP mapping."""
        return self._anonymizer.get_mapping()
