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

    def __init__(self, config: AnonymizeConfig) -> None:
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
