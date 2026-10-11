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
