"""IP address anonymization rule using the ipanon library."""

from __future__ import annotations

import ipaddress
import re
from typing import TYPE_CHECKING, Any

from ipanon import Anonymizer, NetworkRegistry, PassThroughCollisionError
from ipanon.ranges import CATEGORY_A_V4, CATEGORY_B_V4

from junoscfg.anonymize.rules import (
    ADDRESS_FRAGMENT,
    Rule,
    address_pattern_prefix,
    address_tokens,
    has_wildcard_characters,
    prefix_pattern,
    replace_addresses,
)
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
#: The text of a wildcard that spells an address pattern: address characters,
#: Junos's wildcard characters, and a dot or colon between groups of digits.
_ADDRESS_PATTERN = re.compile(r"(?=.*\d)(?=.*[.:])[0-9A-Fa-f.:*?\[\]!^-]+")

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
        self._treated_apart = _treated_apart(config)

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
        return self._takes_address(schema_node, path)

    def _takes_address(self, schema_node: dict[str, Any], path: list[str]) -> bool:
        """Whether the leaf's type, or its list's name, says it holds an address."""
        types = self._types(schema_node)
        if not types or types & _ADDRESS_TYPES:
            return True
        return (
            types <= _KEY_TEXT_TYPES
            and len(path) >= 2
            and path[-1] == "name"
            and path[-2] in _ADDRESS_KEYED_LISTS
        )

    def wildcard(
        self, text: str, schema_node: dict[str, Any], path: list[str]
    ) -> tuple[str, bool] | None:
        """An address pattern where an address stands (`neighbor <203.0.114.*>`).

        Replacements keep their prefixes, so a pattern of whole octets becomes
        the pattern of its prefix's replacement (`203.0.114.0/24` to
        `203.211.226.0/24`, `<203.211.226.*>`) and selects the replacements of
        the addresses it selected. Any other address pattern (`203.0.11*`,
        `3ffe:b00:*`) is left as written and reported (specification
        challenge S2).
        """
        if not (
            has_wildcard_characters(text)
            and _ADDRESS_PATTERN.fullmatch(text)
            and self._takes_address(schema_node, path)
        ):
            return None
        pattern = self._octet_pattern(text)
        return (text, False) if pattern is None else (pattern, True)

    def _octet_pattern(self, text: str) -> str | None:
        """*text*, a pattern of whole octets, as the pattern of its prefix's
        replacement, or ``None`` when it is no such pattern or its prefix is
        partly kept as written (a preserved prefix or a block the address
        anonymizer keeps or treats apart cuts it): then its addresses are
        replaced by different rules (Reviewer R5)."""
        prefix = address_pattern_prefix(text)
        if prefix is None:
            return None
        network = ipaddress.ip_network(prefix)
        if any(
            network.overlaps(block) and not network.subnet_of(block)  # type: ignore[arg-type]
            for block in self._treated_apart
        ):
            return None
        return prefix_pattern(self.transform(prefix), text)

    def pattern_in_string(self, text: str, *, done: frozenset[str]) -> tuple[str, bool]:
        """The text of a wildcard name in the strings pass, and whether it is vouched for.

        An address in it is replaced as in any string; a pattern of whole
        octets of at least two octets (`peer-203.0.114.*`) becomes the pattern
        of its prefix's replacement, unless the walk wrote it already (its
        prefix is a replacement); any other address fragment beside a
        wildcard character (`peer-203.0.11*`, `203.0.114.7*`) is left as
        written and not vouched for (Reviewer R2, specification challenge S4).
        """
        vouched = True

        def fragment(match: re.Match[str]) -> str:
            nonlocal vouched
            whole = match.group(0)
            if match.group(2) != ".*" or whole.count(".") > 3:
                vouched = False
                return whole
            prefix = address_pattern_prefix(whole)
            if prefix is not None and prefix in done:
                return whole
            pattern = self._octet_pattern(whole)
            if pattern is None:
                vouched = False
                return whole
            return pattern

        text = ADDRESS_FRAGMENT.sub(fragment, text)
        return self.replace_ips_in_string(text, done=done), vouched

    @staticmethod
    def _types(schema_node: dict[str, Any]) -> set[str]:
        return {
            strip_type_prefix(str(ref)).lower()
            for ref in (schema_node.get("atr"), schema_node.get("tr"))
            if ref is not None
        }

    def transform(self, value: str) -> str:
        """Anonymize each address or prefix in *value*; the text around it stays."""
        return replace_addresses(value, self._anonymize)

    def _anonymize(self, address: str) -> str:
        """*address*'s replacement; a collision with a preserved prefix names neither.

        `ipanon`'s error reads "Anonymized IP <replacement> (from <original>)
        collides with --pass-through prefix <prefix>": the pair the mapping
        holds, printed beside the output. It is raised afresh, its class kept,
        with no cause or context that carries the original (spec
        anonymization/placed-values).
        """
        try:
            return str(self._anonymizer.anonymize(address))
        except PassThroughCollisionError:
            pass
        # Raised outside the handler: the original is neither its cause nor its context.
        raise PassThroughCollisionError(
            "an address's replacement collides with a preserved prefix (`preserve_prefixes`, "
            "--anonymize-preserve-prefixes); the addresses are withheld: use another salt or "
            "adjust the preserved prefixes"
        )

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
            value, lambda token: token if token in done else self._anonymize(token)
        )

    def get_mapping(self) -> dict[str, str]:
        """Return the original -> anonymized IP mapping."""
        return self._anonymizer.get_mapping()


def _treated_apart(config: AnonymizeConfig) -> tuple[ipaddress.IPv4Network, ...]:
    """The IPv4 blocks the address anonymizer keeps or replaces by their own rule:
    the preserved prefixes, and `ipanon`'s kept and range-preserved blocks as
    the flags leave them."""
    blocks: list[ipaddress.IPv4Network] = []
    for prefix in config.preserve_prefixes or ():
        network = ipaddress.ip_network(prefix, strict=False)
        if isinstance(network, ipaddress.IPv4Network):
            blocks.append(network)
    if not config.ignore_reserved:
        blocks.extend(block for block in CATEGORY_B_V4 if isinstance(block, ipaddress.IPv4Network))
        blocks.extend(
            entry.network
            for entry in CATEGORY_A_V4
            if not config.ignore_subnets or entry.locked_bits == 8
        )
    return tuple(blocks)
