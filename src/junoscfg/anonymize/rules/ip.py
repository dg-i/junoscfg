"""IP address anonymization rule using the ipanon library."""

from __future__ import annotations

import ipaddress
import re
from typing import TYPE_CHECKING, Any

from ipanon import Anonymizer, NetworkRegistry

from junoscfg.anonymize.rules import Rule
from junoscfg.display import strip_type_prefix

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

#: Leaf types that hold an address or a prefix: the IP families, and the host
#: families, which hold a name or an address. The rule takes a value of such a
#: leaf where it holds an address (spec anonymization/placed-values).
_ADDRESS_TYPES: frozenset[str] = frozenset(
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
        "ipprefix-only",
        "ipv4prefix-only",
        "ipv6prefix-mandatory",
        "ipv4addr-or-interface",
        "ipv4address",
        "ipv6address",
        "host",
        "hostname",
    }
)

#: Lists whose key the 25.2R2 tree types only as free text (`string`,
#: `key-attribute-string-type`) or as `areaid` although it holds an address:
#: `system syslog host`, `... server`, `... route`, `... source-address`,
#: `protocols ospf area`. For those keys alone the list's name decides, as it
#: did for every key until change anonymize-every-placed-value; a typed key
#: answers by its type. Retires when the schema model types these keys
#: (schema-model gaps, change 18). An SNMP OID (`oid 1.3.6.1`) and a `from
#: area` reference are free text and `areaid` beyond these keys, and stay.
_ADDRESS_KEYED_LISTS: frozenset[str] = frozenset(
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
_KEY_TEXT_TYPES = frozenset({"string", "key-attribute-string-type", "areaid"})

#: An address token: an IPv4 or IPv6 address, with a prefix length when one in
#: range follows. A neighbour that continues a number, a word or an address
#: (`1.2.3.4.5`, `x10.0.0.1`) is no boundary. Anything else beside it
#: (`/rack-4`, `,`, `%ge-0/0/0.0`, `/33`, a trailing `/`) is text and stays.
_ADDRESS_TOKEN = re.compile(
    r"(?<![\w.:])"
    r"(?:(?P<v4>\d{1,3}(?:\.\d{1,3}){3})|(?P<v6>[0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{0,4}){2,7}"
    r"(?:\.\d{1,3}){0,3}))"
    r"(?:/(?P<length>\d{1,3})(?![\w.:]))?"
    r"(?![\w.:])"
)


def _addresses(value: str) -> list[tuple[int, int, str]]:
    """Each address token in *value*: its start, its end, and the token."""
    found = []
    for match in _ADDRESS_TOKEN.finditer(value):
        address = match.group("v4") or match.group("v6")
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError:
            continue
        end = match.end("v4") if match.group("v4") else match.end("v6")
        length = match.group("length")
        if length is not None and int(length) <= parsed.max_prefixlen:
            end = match.end("length")
        found.append((match.start(), end, value[match.start() : end]))
    return found


class IpRule(Rule):
    """Anonymize IP addresses using prefix-preserving permutation."""

    name = "ip"
    priority = 30  # After passwords (10) and SSH keys (20)

    def __init__(self, config: AnonymizeConfig) -> None:
        """Build the rule from *config*, including its network registry."""
        registry = self._build_network_registry(config)
        self._anonymizer = Anonymizer(
            salt=config.salt,
            pass_through_prefixes=config.preserve_prefixes or None,
            ignore_subnets=config.ignore_subnets,
            ignore_reserved=config.ignore_reserved,
            quiet=config.log_level != "debug",
            network_registry=registry,
        )

    @staticmethod
    def _build_network_registry(config: AnonymizeConfig) -> NetworkRegistry | None:
        """Build a NetworkRegistry from config, or return None."""
        if not config.networks and not config.network_file:
            return None
        registry = NetworkRegistry()
        for spec in config.networks:
            if spec == "auto":
                # "auto" scans the configuration text for subnets, so it needs
                # that text. A caller who asks for it without supplying
                # source_text gets told, rather than silently getting nothing.
                if not config.source_text:
                    raise ValueError(
                        'networks=["auto"] needs the configuration text: set '
                        "AnonymizeConfig.source_text to the source being anonymized."
                    )
                registry.load_from_text(config.source_text)
            else:
                registry.add(spec)
        if config.network_file:
            registry.load_file(config.network_file)
        if not registry.entries():
            return None
        return registry

    def matches(
        self,
        value: Any,
        schema_node: dict[str, Any],
        path: list[str],
    ) -> bool:
        """Match a value that is an address on a leaf whose type can hold one.

        The value starts with an address or prefix; what follows it in the
        same word (`/rack-4`, `,`, `%ge-0/0/0.0`) is text. The type answers:
        an address or host type, or none at all (a leaf the tree gives no
        type, content the walk cannot place). A list key the tree types only
        as free text or `areaid` answers by its list's name
        (`_ADDRESS_KEYED_LISTS`). Any other type never takes an address, and
        a value holding none never reaches the address anonymizer.
        """
        tokens = _addresses(value) if isinstance(value, str) else []
        if not tokens or tokens[0][0] != 0:
            # An address inside other text is `ips_in_strings`' (`scp://...`).
            return False
        types = {
            strip_type_prefix(str(ref)).lower()
            for ref in (schema_node.get("atr"), schema_node.get("tr"))
            if ref is not None
        }
        if not types or types & _ADDRESS_TYPES:
            return True
        return (
            len(path) >= 2
            and path[-1] == "name"
            and path[-2] in _ADDRESS_KEYED_LISTS
            and types <= _KEY_TEXT_TYPES
        )

    def transform(self, value: str) -> str:
        """Anonymize each address or prefix in *value*; the text around it stays."""
        tokens = _addresses(value)
        if not tokens:
            return value
        if len(tokens) == 1 and tokens[0][2] == value:
            return self._anonymizer.anonymize(value)
        parts: list[str] = []
        last = 0
        for start, end, token in tokens:
            parts.extend((value[last:start], self._anonymizer.anonymize(token)))
            last = end
        parts.append(value[last:])
        return "".join(parts)

    def lexical(self, word: str) -> str | None:
        """A word holding an address has the address replaced."""
        return self.transform(word) if _addresses(word) else None

    def replace_ips_in_string(self, value: str, *, done: frozenset[str] = frozenset()) -> str:
        """Replace all embedded IPv4 addresses in a string.

        Used for the ``ips_in_strings`` option to catch IPs inside URLs,
        host+IP combos, and other non-standalone contexts. An address in
        *done* -- a replacement the walk already wrote -- is left as it is.
        """

        def _replace(m: re.Match[str]) -> str:
            addr_str = m.group(1)
            cidr = m.group(2)
            if m.group(0) in done or addr_str in done:
                return m.group(0)
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
