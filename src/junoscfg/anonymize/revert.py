"""Revert dictionary: export, import, and apply anonymization mappings.

The revert dictionary is a JSON file that maps rule names to
``{original: anonymized}`` pairs.  To *revert* an already-anonymized
config, the mapping is inverted (``{anonymized: original}``) and every
replacement in the IR's values and keys is undone once.
"""

from __future__ import annotations

import json
import re
from typing import Any

from junoscfg.anonymize.rules import wildcard_text


def export_mapping(mapping: dict[str, dict[str, str]], path: str) -> None:
    """Write an anonymization mapping to a JSON file.

    Args:
        mapping: The mapping dict from :class:`AnonymizeResult` —
            ``{rule_name: {original: anonymized}}``.
        path: Destination file path.
    """
    with open(path, "w") as f:
        json.dump(mapping, f, indent=2, sort_keys=True)
        f.write("\n")


def load_mapping(path: str) -> dict[str, dict[str, str]]:
    """Load an anonymization mapping from a JSON file.

    Args:
        path: Path to the mapping JSON file previously exported by
            :func:`export_mapping`.

    Returns:
        The mapping dict — ``{rule_name: {original: anonymized}}``.
    """
    with open(path) as f:
        return json.load(f)  # type: ignore[no-any-return]


def apply_revert(ir: dict[str, Any], mapping: dict[str, dict[str, str]]) -> dict[str, Any]:
    """Walk an IR dict and replace anonymized values with their originals.

    Each string value and each key is restored: a whole value a rule recorded
    first, then every other replacement the mapping records, once, in one pass
    over the text -- the longest first, a number only between non-digits and
    never inside an address -- and every address last, as the forward chain
    replaced it first (spec anonymization/embedded-values).

    Args:
        ir: The anonymized IR dict.
        mapping: The mapping dict — ``{rule_name: {original: anonymized}}``.

    Returns:
        The same *ir* dict (mutated in place) with anonymized values restored.
    """
    reverse = _Reverse(mapping)
    if not reverse.others and not reverse.addresses:
        return ir
    _walk_revert(ir, reverse)
    return ir


class _Reverse:
    """The inverted mapping: the addresses, and every other replacement."""

    def __init__(self, mapping: dict[str, dict[str, str]]) -> None:
        self.addresses = {
            anonymized: original for original, anonymized in mapping.get("ip", {}).items()
        }
        self.others = {
            anonymized: original
            for rule, pairs in mapping.items()
            if rule != "ip"
            for original, anonymized in pairs.items()
        }
        self._longest = sorted(self.others, key=len, reverse=True)
        self._patterns: dict[tuple[str, ...], re.Pattern[str]] = {}

    def addresses_in(self, text: str) -> str:
        """*text* with each address token a replacement spells restored."""
        from junoscfg.anonymize.rules import ipv4_inside, replace_addresses

        def original(token: str) -> str:
            if token in self.addresses:
                return self.addresses[token]
            inside = ipv4_inside(token.split("/", 1)[0])
            if inside is not None and inside[1] in self.addresses:
                head, quad = inside
                return head + self.addresses[quad] + token[len(head) + len(quad) :]
            return token

        return replace_addresses(text, original)

    def text(self, value: str) -> str:
        """*value* restored: a whole value, then the other replacements once, then addresses."""
        if value in self.addresses:
            return self.addresses[value]
        value = self.others[value] if value in self.others else self._replacements(value)
        if value in self.addresses:
            return self.addresses[value]
        return self.patterns_in(self.addresses_in(value))

    def patterns_in(self, text: str) -> str:
        """*text* with each pattern of whole octets a prefix's replacement spells
        restored (`peer-203.211.226.*`, an `apply-path`'s `<203.211.226.*>`)."""
        from junoscfg.anonymize.rules import ADDRESS_FRAGMENT

        return ADDRESS_FRAGMENT.sub(
            lambda match: self.octets(match.group(0)) or match.group(0), text
        )

    def octets(self, pattern: str) -> str | None:
        """*pattern*, a pattern of whole octets, through its prefix's mapping, or ``None``."""
        from junoscfg.anonymize.rules import address_pattern_prefix, prefix_pattern

        prefix = address_pattern_prefix(pattern)
        if prefix is None or prefix not in self.addresses:
            return None
        return prefix_pattern(self.addresses[prefix], pattern)

    def _replacements(self, text: str) -> str:
        """*text* with every replacement but an address's undone, in one pass."""
        found = tuple(anonymized for anonymized in self._longest if anonymized in text)
        if not found:
            return text
        pattern = self._patterns.get(found)
        if pattern is None:
            pattern = re.compile(
                "|".join(
                    rf"(?<!\d){re.escape(item)}(?!\d)" if item.isdigit() else re.escape(item)
                    for item in found
                )
            )
            self._patterns[found] = pattern
        from junoscfg.anonymize.rules import address_tokens

        addresses = [(start, end) for start, end, _ in address_tokens(text)]

        def undo(match: re.Match[str]) -> str:
            if match.group().isdigit() and any(
                start < match.end() and match.start() < end for start, end in addresses
            ):
                return match.group()
            return self.others[match.group()]

        return pattern.sub(undo, text)


def _walk_revert(obj: Any, reverse: _Reverse) -> None:
    """Recursively walk the IR and restore values and keys.

    Content the anonymizer cannot place -- an unknown key, a 0.16.1 joined
    key, a statement kept whole -- has the shapes in its keys replaced (spec
    anonymization/placed-values), so a key is restored as a value is. A key the
    schema names is never a replacement.
    """
    if isinstance(obj, dict):
        items = []
        for key, value in obj.items():
            if isinstance(value, str):
                value = _revert_value(value, reverse)
            elif isinstance(value, (dict, list)):
                _walk_revert(value, reverse)
            items.append((reverse.text(key), value))
        obj.clear()
        obj.update(items)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str):
                obj[i] = _revert_value(item, reverse)
            elif isinstance(item, (dict, list)):
                _walk_revert(item, reverse)


def _revert_value(value: str, reverse: _Reverse) -> str:
    """Revert a single string value; a wildcard name's text inside its brackets."""
    text = wildcard_text(value)
    if text is not None and value not in reverse.others:
        return f"<{_revert_wildcard(text, reverse)}>"
    return reverse.text(value)


def _revert_wildcard(text: str, reverse: _Reverse) -> str:
    """The text of a wildcard name as written: a pattern of whole octets through
    its prefix's mapping (`203.211.226.*` by `203.211.226.0/24`), alone or
    inside the text (`peer-203.211.226.*`), the rest as a value."""
    whole = reverse.octets(text)
    return whole if whole is not None else reverse.text(text)
