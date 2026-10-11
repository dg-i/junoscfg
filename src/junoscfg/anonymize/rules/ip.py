"""IP address anonymization rule using the ipanon library."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ipanon import Anonymizer, NetworkRegistry

from junoscfg.anonymize.rules import Rule, address_tokens, replace_addresses
from junoscfg.display import strip_type_prefix

if TYPE_CHECKING:
    from junoscfg.anonymize.config import AnonymizeConfig

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

#: Leaves the tree types only as free text or `areaid` although they hold an
#: address: `routing-options ipv6-router-id` (`string`, the IPv4-shaped router
#: ID), BGP `cluster` (`areaid`, usually the loopback), a route distinguisher
#: (`route-distinguisher rd-type`, `<address>:<n>`) and a VRF target
#: (`vrf-target` `community`/`import`/`export`, `target:<address>:<n>`), and
#: the policy community that matches it (`policy-options community <c> members
#: target:<address>:<n>`, `origin:<address>:<n>`), so a `vrf-import` policy
#: still matches the target (Reviewer R1). Matched
#: by the leaf's own name (and its parent's), only with those types, where the
#: value holds an address (specification challenges S4, S5). Retires with
#: `_ADDRESS_KEYED_LISTS`, when change 18 retypes them on device evidence.
_ADDRESS_VALUED_LEAVES = frozenset(
    {
        ("", "ipv6-router-id"),
        ("", "cluster"),
        ("route-distinguisher", "rd-type"),
        ("vrf-target", "community"),
        ("vrf-target", "import"),
        ("vrf-target", "export"),
        ("community", "members"),
    }
)


def _address_valued(path: list[str]) -> bool:
    parent = path[-2] if len(path) >= 2 else ""
    return ("", path[-1]) in _ADDRESS_VALUED_LEAVES or (parent, path[-1]) in _ADDRESS_VALUED_LEAVES


class IpRule(Rule):
    """Anonymize IP addresses using prefix-preserving permutation."""

    name = "ip"
    priority = 30  # After passwords (10) and SSH keys (20)
    keeps_text = True

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
        (`_ADDRESS_KEYED_LISTS`); a leaf of `_ADDRESS_VALUED_LEAVES` so typed
        by its own name, wherever in the value the address stands. Any other
        type never takes an address, and a value holding none never reaches
        the address anonymizer.
        """
        tokens = address_tokens(value) if isinstance(value, str) else []
        if not tokens:
            return False
        if path and _address_valued(path):
            return self._types(schema_node) <= _KEY_TEXT_TYPES
        if tokens[0][0] != 0:
            # An address inside other text is `ips_in_strings`' (`scp://...`).
            return False
        types = self._types(schema_node)
        if not types or types & _ADDRESS_TYPES:
            return True
        return (
            types <= _KEY_TEXT_TYPES
            and len(path) >= 2
            and path[-1] == "name"
            and path[-2] in _ADDRESS_KEYED_LISTS
        )

    @staticmethod
    def _types(schema_node: dict[str, Any]) -> set[str]:
        return {
            strip_type_prefix(str(ref)).lower()
            for ref in (schema_node.get("atr"), schema_node.get("tr"))
            if ref is not None
        }

    def transform(self, value: str) -> str:
        """Anonymize each address or prefix in *value*; the text around it stays."""
        return replace_addresses(value, self._anonymizer.anonymize)

    def lexical(self, word: str) -> str | None:
        """A word holding an address has the address replaced."""
        return self.transform(word) if address_tokens(word) else None

    def replace_ips_in_string(self, value: str, *, done: frozenset[str] = frozenset()) -> str:
        """Replace every address embedded in a string, IPv4 and IPv6.

        Used for the ``ips_in_strings`` option to catch addresses inside URLs,
        host+address combos, and other non-standalone contexts. An address in
        *done* -- a replacement the walk already wrote -- is left as it is.
        """
        return replace_addresses(
            value, lambda token: token if token in done else self._anonymizer.anonymize(token)
        )

    def get_mapping(self) -> dict[str, str]:
        """Return the original -> anonymized IP mapping."""
        return self._anonymizer.get_mapping()
