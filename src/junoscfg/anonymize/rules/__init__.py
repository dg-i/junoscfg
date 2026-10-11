"""Anonymization rule base class and registry."""

from __future__ import annotations

import ipaddress
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from junoscfg.anonymize.config import AnonymizeConfig


#: An address token, the one answer to "where is an address in this text" for
#: the IP rule, content the walk cannot place, the strings pass and revert. An
#: IPv4 address is bounded by anything but a digit or a dot (`:8080`, `lo_`,
#: `host:`, `peer=` are text), an IPv6 address by anything but a word
#: character, a dot or a colon. A prefix length in range follows it; anything
#: else beside it (`/rack-4`, `,`, `/33`, `%ge-0/0/0.0`) is text and stays.
_ADDRESS_TOKEN = re.compile(
    r"(?<![\d.])(?P<v4>\d{1,3}(?:\.\d{1,3}){3})(?:/(?P<l4>\d{1,3}))?(?![\d.])"
    r"|(?<![\w.:])(?P<v6>[0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{0,4}){2,7}(?:\.\d{1,3}){0,3})"
    r"(?:/(?P<l6>\d{1,3}))?(?![\w.:])"
)


def address_tokens(text: str) -> list[tuple[int, int, str]]:
    """Each address or prefix in *text*: its start, its end, and the token. Never raises."""
    found = []
    for match in _ADDRESS_TOKEN.finditer(text):
        group, length_group = ("v4", "l4") if match.group("v4") else ("v6", "l6")
        try:
            parsed = ipaddress.ip_address(match.group(group))
        except ValueError:
            continue
        end = match.end(group)
        length = match.group(length_group)
        if length is not None and int(length) <= parsed.max_prefixlen:
            end = match.end(length_group)
        found.append((match.start(), end, text[match.start() : end]))
    return found


def replace_addresses(text: str, replace: Callable[[str], str]) -> str:
    """*text* with each address token replaced by *replace*; the text around it stays."""
    tokens = address_tokens(text)
    if not tokens:
        return text
    parts: list[str] = []
    last = 0
    for start, end, token in tokens:
        parts.extend((text[last:start], replace(token)))
        last = end
    parts.append(text[last:])
    return "".join(parts)


#: Junos's wildcard characters in a wildcard name: `*`, `?` and a class `[...]`.
_WILDCARD_CHARACTERS = re.compile(r"[*?\[]")
#: Inside a wildcard's text: two or more octets that a wildcard character
#: follows (`peer-203.0.114.*`, `203.0.11*`, `203.0.114.7?`).
ADDRESS_FRAGMENT = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d{1,3})+)(\.\*|[*?\[])")
#: An IPv4 pattern of whole octets: `203.0.114.*`, `203.0.*`, `203.*`.
_OCTET_PATTERN = re.compile(r"((?:\d{1,3}\.){1,3})\*")


def wildcard_text(value: object) -> str | None:
    """The text inside a Junos wildcard name (`<ge-*>` gives `ge-*`), or ``None``.

    Inside a configuration group a name in angle brackets is a pattern that
    selects names (Junos OS "Configuration Groups"), not a name.
    """
    if isinstance(value, str) and len(value) > 2 and value[0] == "<" and value[-1] == ">":
        return value[1:-1]
    return None


def has_wildcard_characters(text: str) -> bool:
    """Whether *text* holds `*`, `?` or `[`: it selects more than the one name it spells."""
    return bool(_WILDCARD_CHARACTERS.search(text))


def address_pattern_prefix(text: str) -> str | None:
    """The prefix an IPv4 pattern of whole octets selects (`203.0.114.*` gives
    `203.0.114.0/24`), or ``None`` for any other text."""
    match = _OCTET_PATTERN.fullmatch(text)
    if match is None:
        return None
    octets = match.group(1).rstrip(".").split(".")
    if any(int(octet) > 255 for octet in octets):
        return None
    return ".".join(octets + ["0"] * (4 - len(octets))) + f"/{8 * len(octets)}"


def prefix_pattern(prefix: str, like: str) -> str | None:
    """*prefix* as a pattern of the octets *like* (a pattern of whole octets) spells,
    or ``None`` when it is no such prefix."""
    try:
        network = ipaddress.ip_network(prefix, strict=False)
    except ValueError:
        return None
    octets = like.count(".")
    if network.version != 4 or network.prefixlen != 8 * octets:
        return None
    return ".".join(str(network.network_address).split(".")[:octets]) + ".*"


class Rule(ABC):
    """Base class for anonymization rules.

    Each rule handles one category of sensitive data. The walker calls
    :meth:`matches` to check whether the rule applies to a given leaf,
    then :meth:`transform` to produce the anonymized value.
    """

    #: Human-readable name for logging and revert-dictionary keys.
    name: str = ""

    #: Lower numbers run first. A leaf is processed by the first matching rule.
    priority: int = 100

    #: Whether a replacement leaves the text around what it replaced, so a
    #: later rule may still recognise a shape in it (`acme-203.0.114.9`: the
    #: address, then the sensitive word). A rule that replaces a whole value
    #: ends the chain.
    keeps_text: bool = False

    @abstractmethod
    def matches(
        self,
        value: Any,
        schema_node: dict[str, Any],
        path: list[str],
    ) -> bool:
        """Return True if this rule should anonymize *value*."""

    @abstractmethod
    def transform(self, value: str) -> str:
        """Return the anonymized replacement for *value*."""

    def get_mapping(self) -> dict[str, str]:
        """Return the mapping of original -> anonymized values."""
        return {}

    def lexical(self, word: str) -> str | None:
        """Replace *word* by its shape alone, or ``None`` when the shape is not this rule's.

        Content the walk cannot place carries no type and no path a rule can
        read, so only a rule that recognises a value by its shape -- an
        address, a password hash, a sensitive word -- rewrites it, word by
        word, never by a keyword (owner answer 5). The default recognises
        nothing.
        """
        return None

    def wildcard(
        self, text: str, schema_node: dict[str, Any], path: list[str]
    ) -> tuple[str, bool] | None:
        """Rewrite the text of a wildcard name as a pattern, or ``None`` to treat it as a name.

        A rule that knows patterns of its values answers with the rewritten
        text and whether the rewrite keeps the pattern selecting the
        replacements of the names it selected; ``False`` has the walker report
        the wildcard. The default knows none: the text is offered as a name
        (`matches`, then `transform`).
        """
        return None


def build_rules(config: AnonymizeConfig) -> list[Rule]:
    """Build an ordered list of active rules from *config*.

    Only rules whose category is enabled in *config* are included.
    The list is sorted by :attr:`Rule.priority` (ascending).
    """
    rules: list[Rule] = []

    if config.passwords:
        from junoscfg.anonymize.rules.password import PasswordRule

        rules.append(PasswordRule(config))

    if config.ips:
        from junoscfg.anonymize.rules.ip import IpRule

        rules.append(IpRule(config))

    if config.communities:
        from junoscfg.anonymize.rules.community import CommunityRule

        rules.append(CommunityRule(config))

    if config.ssh_keys:
        from junoscfg.anonymize.rules.ssh_key import SshKeyRule

        rules.append(SshKeyRule(config))

    if config.identities:
        from junoscfg.anonymize.rules.identity import IdentityRule

        rules.append(IdentityRule(config))

    if config.groups:
        from junoscfg.anonymize.rules.group import GroupRule

        rules.append(GroupRule(config))

    if config.descriptions:
        from junoscfg.anonymize.rules.description import DescriptionRule

        rules.append(DescriptionRule(config))

    if config.as_numbers:
        from junoscfg.anonymize.rules.as_number import AsNumberRule

        rules.append(AsNumberRule(config))

    if config.sensitive_words or config.sensitive_patterns:
        from junoscfg.anonymize.rules.sensitive_word import SensitiveWordRule

        rules.append(SensitiveWordRule(config))

    rules.sort(key=lambda r: r.priority)
    return rules
