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
#: the IP rule, free text, content the walk cannot place and revert. An IPv4
#: address is bounded by anything but a digit, or a dot that a digit follows
#: (`:8080`, `lo_`, `host:`, `peer=` and a sentence's closing `.` are text); an
#: IPv6 address by anything but a hex digit, a dot or a colon before it -- a
#: word that is no hex number may stand before its colon (`host:3ffe::1`), and
#: `_` (`lo_3ffe::1`) -- and anything but a word character, a colon or a dot
#: that a word character follows after it. A prefix length in range follows
#: it; anything else beside it (`/rack-4`, `,`, `/33`, `%ge-0/0/0.0`) is text.
_ADDRESS_TOKEN = re.compile(
    r"(?<![\d.])(?P<v4>\d{1,3}(?:\.\d{1,3}){3})(?:/(?P<l4>\d{1,3}))?(?!\d|\.\d)"
    r"|(?:(?<![0-9A-Za-z.:])|(?<=[G-Zg-z_]:))"
    r"(?P<v6>[0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{0,4}){2,7}(?:\.\d{1,3}){0,3})"
    r"(?:/(?P<l6>\d{1,3}))?(?![\w:]|\.\w)"
)
#: The IPv6 blocks that write an IPv4 address in their last 32 bits as a dotted
#: quad: IPv4-mapped, IPv4-compatible and the NAT64 well-known prefix.
_IPV4_IN_IPV6 = tuple(
    ipaddress.ip_network(block) for block in ("::ffff:0:0/96", "::/96", "64:ff9b::/96")
)


def parse_address(text: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    """*text* as an address, a zero-padded dotted quad (`203.000.114.006`) included."""
    try:
        return ipaddress.ip_address(text)
    except ValueError:
        pass
    octets = text.split(".")
    if len(octets) == 4 and all(octet.isdigit() and int(octet) <= 255 for octet in octets):
        return ipaddress.IPv4Address(".".join(str(int(octet)) for octet in octets))
    return None


def ipv4_inside(token: str) -> tuple[str, str] | None:
    """An IPv6 token that writes an IPv4 address as a dotted quad in a block that
    carries one (`::ffff:203.0.114.5`): the text before the quad, and the quad."""
    head, _, quad = token.rpartition(":")
    if "." not in quad or not head:
        return None
    try:
        parsed = ipaddress.IPv6Address(token)
    except ValueError:
        return None
    if not any(parsed in block for block in _IPV4_IN_IPV6):
        return None
    return f"{head}:", quad


def address_tokens(text: str) -> list[tuple[int, int, str]]:
    """Each address or prefix in *text*: its start, its end, and the token. Never raises."""
    found = []
    for match in _ADDRESS_TOKEN.finditer(text):
        group, length_group = ("v4", "l4") if match.group("v4") else ("v6", "l6")
        parsed = parse_address(match.group(group))
        if parsed is None:
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


def _glob_positions(text: str) -> list[frozenset[str] | str | None]:
    """*text*, a wildcard's text, as one position per character it matches.

    A literal is its character folded, `?` and a negated class (`[!...]`, and
    `[^...]`, which Junos may read so) the empty set, taking any character --
    whether a word can pass it is answered yes, the safe side for a report --
    a class `[...]` the characters it names, and `*` ``None``.
    """
    positions: list[frozenset[str] | str | None] = []
    index = 0
    while index < len(text):
        char = text[index]
        end = text.find("]", index + 2) if char == "[" else -1
        if char == "*":
            positions.append(None)
        elif char == "?" or (end > 0 and text[index + 1] in "!^"):
            positions.append(frozenset())
            index = max(index, end)
        elif end > 0:
            positions.append(_class_members(text[index + 1 : end]) or frozenset("["))
            index = end
        else:
            positions.append(char.casefold())
        index += 1
    return positions


def _accepts(position: frozenset[str] | str | None, char: str) -> bool:
    """Whether a position takes *char* in either case (`*` takes any)."""
    if position is None:
        return True
    if isinstance(position, str):
        return char.casefold() == position
    return not position or char.lower() in position or char.upper() in position


def _class_members(body: str) -> frozenset[str]:
    """The characters a class body names: single characters and ranges `a-z`."""
    members: set[str] = set()
    index = 0
    while index < len(body):
        if index + 2 < len(body) and body[index + 1] == "-":
            members.update(chr(code) for code in range(ord(body[index]), ord(body[index + 2]) + 1))
            index += 3
        else:
            members.add(body[index])
            index += 1
    return frozenset(members)


def spells_through_syntax(text: str, word: str, *, between_non_digits: bool = False) -> bool:
    """Whether *text*, a wildcard's text, matches a string holding *word* where a
    class or `?` stands in it.

    A word the text holds in literals alone is a rule's to replace; a `*`
    stands for text the pattern does not hold. With *between_non_digits*, the
    word must be able to stand between non-digits there (an AS number in a
    longer number is none).
    """
    positions = _glob_positions(text)
    for start in range(len(positions) - len(word) + 1):
        window = [
            position for position in positions[start : start + len(word)] if position is not None
        ]
        if not (
            len(window) == len(word)
            and not all(isinstance(position, str) for position in window)
            and all(_accepts(position, char) for position, char in zip(window, word, strict=True))
        ):
            continue
        if between_non_digits and not (
            _may_be_no_digit(positions, start - 1)
            and _may_be_no_digit(positions, start + len(word))
        ):
            continue
        return True
    return False


def _may_be_no_digit(positions: list[frozenset[str] | str | None], index: int) -> bool:
    """Whether the position at *index* (the text's edge outside it) can be no digit."""
    if index < 0 or index >= len(positions):
        return True
    position = positions[index]
    if position is None or (isinstance(position, frozenset) and not position):
        return True
    if isinstance(position, str):
        return not position.isdigit()
    return any(not char.isdigit() for char in position)


#: A URL's userinfo: any scheme in any case, from `//` to the last `@` before
#: the host (RFC 3986), the user up to its first `:` and the password after it.
_URL_USERINFO = re.compile(
    r"(?<![A-Za-z0-9+.-])[A-Za-z][A-Za-z0-9+.-]*://(?P<userinfo>[^\s/?#\"'<>]*)@"
)


def url_userinfo(text: str) -> list[tuple[tuple[int, int] | None, tuple[int, int] | None]]:
    """Each URL's user and password in *text*, as spans (``None`` where empty)."""
    found = []
    for match in _URL_USERINFO.finditer(text):
        start, end = match.span("userinfo")
        colon = text.find(":", start, end)
        user_end = end if colon < 0 else colon
        user = (start, user_end) if user_end > start else None
        password = (colon + 1, end) if 0 <= colon < end - 1 else None
        found.append((user, password))
    return found


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

    def spans(self, text: str) -> list[tuple[int, int]]:
        """Where in *text* this rule recognises a value by its shape alone, in order.

        Free text -- a value no rule takes whole, an annotation, content the
        walk cannot place -- carries no type a rule can read for what stands
        inside it, so only a rule that recognises a value by its shape (an
        address, a URL's user or password, a password hash, a sensitive word,
        an AS number) rewrites it there, never a keyword (owner answer 5). The
        default recognises nothing.
        """
        return []

    def replace(self, fragment: str) -> str:
        """The replacement of *fragment*, a part `spans` found."""
        return self.transform(fragment)

    def record(self, before: str, after: str) -> None:  # noqa: B027 - optional hook
        """Note that the parts this rule found turned *before* into *after*.

        A rule whose mapping names the whole values it rewrote records them
        here; the default's mapping names each part (`replace`).
        """

    def lexical(self, word: str) -> str | None:
        """*word* with each part this rule recognises by its shape replaced, or
        ``None`` when it holds none."""
        found = self.spans(word)
        if not found:
            return None
        return rewrite(self, word, found)[0]

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


def rewrite(
    rule: Rule, text: str, spans: list[tuple[int, int]]
) -> tuple[str, list[tuple[int, int]]]:
    """*text* with each of *spans* replaced by *rule*, and where each replacement stands."""
    parts: list[str] = []
    written: list[tuple[int, int]] = []
    last = 0
    length = 0
    for start, end in spans:
        parts.append(text[last:start])
        length += start - last
        replacement = rule.replace(text[start:end])
        written.append((length, length + len(replacement)))
        parts.append(replacement)
        length += len(replacement)
        last = end
    parts.append(text[last:])
    result = "".join(parts)
    if result != text:
        rule.record(text, result)
    return result, written


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
