"""Revert dictionary: export, import, and apply anonymization mappings.

The revert dictionary is a JSON file that maps rule names to
``{original: anonymized}`` pairs.  To *revert* an already-anonymized
config, the mapping is inverted (``{anonymized: original}``) and every
matching string value in the IR is replaced.
"""

from __future__ import annotations

import json
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
    _walk_revert(ir, reverse)
    return ir


def _walk_revert(obj: Any, reverse: dict[str, str]) -> None:
    """Recursively walk the IR and replace anonymized values."""
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            value = obj[key]
            if isinstance(value, str):
                obj[key] = _revert_value(value, reverse)
            elif isinstance(value, (dict, list)):
                _walk_revert(value, reverse)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str):
                obj[i] = _revert_value(item, reverse)
            elif isinstance(item, (dict, list)):
                _walk_revert(item, reverse)


def _revert_value(value: str, reverse: dict[str, str]) -> str:
    """Revert a single string value.

    First checks for an exact match in the reverse map.  If not found,
    checks whether any anonymized token appears as a substring (handles
    sensitive-word replacements embedded in larger strings).
    """
    # Exact match — covers most rules (IP, password, identity, group, etc.)
    if value in reverse:
        return reverse[value]

    # Substring match — covers sensitive_word partial replacements
    result = value
    for anonymized, original in reverse.items():
        if anonymized in result:
            result = result.replace(anonymized, original)
    return result
