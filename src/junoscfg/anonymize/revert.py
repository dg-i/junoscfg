"""Revert dictionary: export, import, and apply anonymization mappings.

The revert dictionary is a JSON file that maps rule names to
``{original: anonymized}`` pairs.  To *revert* an already-anonymized
config, the mapping is inverted (``{anonymized: original}``) and every
matching string value in the IR is replaced.
"""

from __future__ import annotations

import json
import re
from typing import Any


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


def _build_reverse_map(mapping: dict[str, dict[str, str]]) -> dict[str, str]:
    """Invert the mapping to ``{anonymized: original}`` for revert."""
    reverse: dict[str, str] = {}
    for _rule_name, pairs in mapping.items():
        for original, anonymized in pairs.items():
            reverse[anonymized] = original
    return reverse


def apply_revert(ir: dict[str, Any], mapping: dict[str, dict[str, str]]) -> dict[str, Any]:
    """Walk an IR dict and replace anonymized values with their originals.

    The mapping is first inverted so that each anonymized value maps back
    to the original.  Then every string value in the IR is checked and
    replaced if it appears in the reverse map.

    For values that contain anonymized substrings (e.g. sensitive-word
    replacements embedded in larger strings), a substring-replacement
    pass is also performed.

    Args:
        ir: The anonymized IR dict.
        mapping: The mapping dict — ``{rule_name: {original: anonymized}}``.

    Returns:
        The same *ir* dict (mutated in place) with anonymized values restored.
    """
    reverse = _build_reverse_map(mapping)
    if not reverse:
        return ir
    addresses = {anonymized: original for original, anonymized in mapping.get("ip", {}).items()}
    _walk_revert(ir, _Reverse(reverse, addresses))
    return ir


class _Reverse:
    """The inverted mapping, and the inverted address mapping alone."""

    def __init__(self, reverse: dict[str, str], addresses: dict[str, str]) -> None:
        self.reverse = reverse
        self.addresses = addresses

    def addresses_in(self, text: str) -> str:
        """*text* with each address token a replacement spells restored."""
        from junoscfg.anonymize.rules import replace_addresses

        return replace_addresses(text, lambda token: self.addresses.get(token, token))

    def word(self, word: str) -> str:
        """Undo the forward chain on one word: a whole-word replacement, then its addresses."""
        if word in self.addresses:
            return self.addresses[word]
        return self.addresses_in(self.reverse.get(word, word))

    def words(self, text: str) -> str:
        """Undo the forward chain word by word, as the walk splits a word."""
        return _WORD.sub(lambda match: self.word(match.group()), text)


def _walk_revert(obj: Any, reverse: _Reverse) -> None:
    """Recursively walk the IR and replace anonymized values, and the words of keys.

    Content the anonymizer cannot place -- an unknown key, a 0.16.1 joined
    key, a statement kept whole -- has the addresses, hashes and sensitive
    words of its keys replaced word by word (spec anonymization/placed-values),
    so revert restores a key the same way, with the same split. A key the
    schema names is never a replacement.
    """
    if isinstance(obj, dict):
        items = []
        for key, value in obj.items():
            if isinstance(value, str):
                value = _revert_value(value, reverse)
            elif isinstance(value, (dict, list)):
                _walk_revert(value, reverse)
            items.append((reverse.words(key), value))
        obj.clear()
        obj.update(items)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str):
                obj[i] = _revert_value(item, reverse)
            elif isinstance(item, (dict, list)):
                _walk_revert(item, reverse)


#: A word as the anonymize walker splits text it cannot place.
_WORD = re.compile(r'[^\s"]+')


def _revert_value(value: str, reverse: _Reverse) -> str:
    """Revert a single string value.

    An exact match first: a whole value a rule replaced, with any address the
    chain replaced before it. Then word by word, as the walk rewrote content
    it cannot place and the strings pass an embedded address; then any
    anonymized token left as a substring (an AS number inside a word).
    """
    if value in reverse.addresses:
        return reverse.addresses[value]
    if value in reverse.reverse:
        return reverse.addresses_in(reverse.reverse[value])
    # Word by word, then any token left as a substring -- an AS number inside
    # a word, which the strings pass replaces beside an address.
    result = reverse.words(value)
    for anonymized, original in reverse.reverse.items():
        if anonymized in result:
            result = result.replace(anonymized, original)
    return result
