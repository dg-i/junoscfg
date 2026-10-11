"""Sensitive word and pattern substring replacement rule.

Performs case-insensitive substring replacement of user-provided words
and regex patterns in any string leaf value that was not already handled
by a higher-priority rule.  Surrounding text is preserved; only the
matched substring is replaced.
"""

from __future__ import annotations

import hashlib
import hmac
import re
from typing import TYPE_CHECKING, Any

from junoscfg.anonymize.rules import Rule

if TYPE_CHECKING:
    from junoscfg.anonymize.config import AnonymizeConfig


class SensitiveWordRule(Rule):
    """Replace sensitive words and patterns with deterministic pseudonyms.

    Each word in :attr:`~junoscfg.anonymize.config.AnonymizeConfig.sensitive_words`
    is replaced case-insensitively wherever it appears as a substring.
    Each pattern in :attr:`~junoscfg.anonymize.config.AnonymizeConfig.sensitive_patterns`
    is used as a raw regex.  Both are combined into a single alternation regex.
    The replacement is ``word_<8-hex-hash>`` where the hash is derived
    from the lowercased matched text and the salt.
    """

    name = "sensitive_word"
    priority = 90  # Lowest priority — last resort
    keeps_text = True

    def __init__(self, config: AnonymizeConfig) -> None:
        """Build the rule from *config*: the salt and the word list."""
        self._salt = config.salt or ""
        self._words = config.sensitive_words
        self._raw_patterns = config.sensitive_patterns

        # Build a single alternation regex: escaped words + raw patterns
        parts: list[str] = [re.escape(w) for w in self._words]
        for p in self._raw_patterns:
            re.compile(p)  # validate — raises re.error on bad pattern
            parts.append(f"(?:{p})")  # wrap in non-capturing group for safe alternation

        if parts:
            self._pattern: re.Pattern[str] | None = re.compile("|".join(parts), re.IGNORECASE)
        else:
            self._pattern = None
        # Cache: lowercased matched text -> replacement
        self._word_cache: dict[str, str] = {}
        self._mapping: dict[str, str] = {}

    def matches(
        self,
        value: Any,
        schema_node: dict[str, Any],
        path: list[str],
    ) -> bool:
        """Match if the value contains any of the sensitive words."""
        if not self._pattern:
            return False
        return isinstance(value, str) and bool(self._pattern.search(value))

    def lexical(self, word: str) -> str | None:
        """A word holding a sensitive word or pattern has it replaced."""
        return self.transform(word) if self.matches(word, {}, []) else None

    def wildcard(
        self, text: str, schema_node: dict[str, Any], path: list[str]
    ) -> tuple[str, bool] | None:
        """A wildcard's text: a word it holds literally is replaced as in any name.

        A word it can spell only through wildcard syntax -- a class or `?`,
        either case (`[Aa]cme-*`) -- has no replacement inside the pattern:
        the text is left as written and reported, as is any class or `?` while
        a sensitive pattern is on, which no class can be checked against
        (specification challenge S3).
        """
        if self._pattern is None:
            return None
        replaced = self.transform(text) if self._pattern.search(text) else text
        hidden = bool(self._raw_patterns) and bool(re.search(r"[?\[]", text))
        if hidden or any(_spells_through_syntax(text, word) for word in self._words):
            return replaced, False
        return None

    def transform(self, value: str) -> str:
        """Replace all occurrences of sensitive words in the value."""
        if value in self._mapping:
            return self._mapping[value]

        if not self._pattern:
            return value

        replaced = self._pattern.sub(self._replace_match, value)
        if replaced != value:
            self._mapping[value] = replaced
        return replaced

    def _replace_match(self, match: re.Match[str]) -> str:
        """Return the replacement for a single regex match."""
        original = match.group()
        key = original.lower()
        if key in self._word_cache:
            return self._word_cache[key]

        hex_digest = hmac.new(self._salt.encode(), key.encode(), hashlib.sha256).hexdigest()
        replacement = f"word_{hex_digest[:24]}"
        self._word_cache[key] = replacement
        return replacement

    def get_mapping(self) -> dict[str, str]:
        """Return the original -> anonymized value mapping."""
        return dict(self._mapping)


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


def _accepts(position: frozenset[str] | str, char: str) -> bool:
    """Whether a position takes *char* in either case."""
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


def _spells_through_syntax(text: str, word: str) -> bool:
    """Whether *text* matches a string holding *word* where a class or `?` stands in it.

    A word the text holds in literals alone is the rule's to replace; a `*`
    stands for text the pattern does not hold.
    """
    positions = _glob_positions(text)
    for start in range(len(positions) - len(word) + 1):
        window = [
            position for position in positions[start : start + len(word)] if position is not None
        ]
        if (
            len(window) == len(word)
            and not all(isinstance(position, str) for position in window)
            and all(_accepts(position, char) for position, char in zip(window, word, strict=True))
        ):
            return True
    return False
