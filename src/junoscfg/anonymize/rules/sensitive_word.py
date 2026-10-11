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

from junoscfg.anonymize.rules import Rule, rewrite, spells_through_syntax

if TYPE_CHECKING:
    from junoscfg.anonymize.config import AnonymizeConfig


class SensitiveWordRule(Rule):
    """Replace sensitive words and patterns with deterministic pseudonyms.

    Each word in :attr:`~junoscfg.anonymize.config.AnonymizeConfig.sensitive_words`
    is replaced case-insensitively wherever it appears as a substring.
    Each pattern in :attr:`~junoscfg.anonymize.config.AnonymizeConfig.sensitive_patterns`
    is used as a raw regex.  Both are combined into a single alternation regex.
    The replacement is ``word_<24-hex-hash>`` where the hash is derived from
    the matched text as spelled and the salt: matching ignores case, the
    pseudonym does not, so `EBGP` and `ebgp` get two and each reverts to its
    own (NEW-R13; specification challenge S2 of change
    anonymize-embedded-values). The mapping names each whole value rewritten.
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
        # Cache: matched text as spelled -> replacement
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

    def spans(self, text: str) -> list[tuple[int, int]]:
        """Each sensitive word or pattern in *text*."""
        if self._pattern is None:
            return []
        return [
            match.span() for match in self._pattern.finditer(text) if match.end() > match.start()
        ]

    def replace(self, fragment: str) -> str:
        """The pseudonym of one spelling."""
        return self._word(fragment)

    def record(self, before: str, after: str) -> None:
        """The mapping names the whole value rewritten."""
        self._mapping[before] = after

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
        hidden = bool(self._raw_patterns) and bool(re.search(r"[?\[]", text))
        hidden = hidden or any(spells_through_syntax(text, word) for word in self._words)
        if not hidden and not self._pattern.search(text):
            return None
        return self.transform(text), not hidden

    def transform(self, value: str) -> str:
        """Replace all occurrences of sensitive words in the value."""
        if value in self._mapping:
            return self._mapping[value]

        return rewrite(self, value, self.spans(value))[0]

    def _word(self, spelling: str) -> str:
        """The pseudonym of *spelling*, one per spelling."""
        if spelling in self._word_cache:
            return self._word_cache[spelling]
        # A spelling that is all lower case keeps the pseudonym of 0.20.x.
        hex_digest = hmac.new(self._salt.encode(), spelling.encode(), hashlib.sha256).hexdigest()
        replacement = f"word_{hex_digest[:24]}"
        self._word_cache[spelling] = replacement
        return replacement

    def get_mapping(self) -> dict[str, str]:
        """Return the original -> anonymized value mapping."""
        return dict(self._mapping)
