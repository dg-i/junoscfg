"""Shared configuration format detection with caller-specific policies."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from collections.abc import Collection

CONVERSION_FORMATS = frozenset({"json", "xml", "yaml", "set", "structured"})
AUDIT_FORMATS = CONVERSION_FORMATS
VALIDATION_FORMATS = frozenset({"set", "structured"})


def is_display_set(text: str) -> bool:
    """Return whether every visible line is a supported display-set command."""
    for line in text.strip().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not re.match(r"^(set|deactivate|protect|activate|delete)\s", stripped):
            return False
    return True


def detect_format(source: str, *, accepted_formats: Collection[str]) -> str:
    """Detect configuration format within a caller's accepted-format policy.

    Args:
        source: Configuration text to classify.
        accepted_formats: Formats the caller permits automatic detection to
            return. Validation deliberately supplies only ``set`` and
            ``structured``; conversion and audit supply all five formats.

    Returns:
        One of the accepted format names.

    Raises:
        ValueError: If the input is empty, the policy is empty or unknown, or
            the detected format is outside the policy.
    """
    stripped = source.strip()
    if not stripped:
        raise ValueError("Cannot detect format from empty input.")

    accepted = frozenset(name.lower() for name in accepted_formats)
    if not accepted:
        raise ValueError("accepted_formats must not be empty.")
    unknown = accepted - CONVERSION_FORMATS
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"Unknown accepted format(s): {names}")

    # Validation's public auto-detection contract is intentionally narrower
    # than the classifier's knowledge: it distinguishes set from structured.
    if accepted == VALIDATION_FORMATS:
        return "set" if is_display_set(stripped) else "structured"

    detected = _detect_full_policy(stripped)
    if detected not in accepted:
        raise ValueError(f"Detected format {detected!r} is not accepted by this caller.")
    return detected


def _detect_full_policy(stripped: str) -> str:
    """Classify non-empty input under the five-format policy."""
    if stripped.startswith("<"):
        # Preserve the existing XML parser door for malformed XML so its
        # format-specific error remains the one callers receive.
        return "xml"

    if is_display_set(stripped):
        return "set"

    if stripped.startswith(("{", "[")):
        try:
            json.loads(stripped)
        except json.JSONDecodeError:
            yaml_value = _load_yaml_collection(stripped)
            if yaml_value is not None:
                return "yaml"
            # Preserve the existing JSON parser door for malformed
            # brace/bracket-prefixed input.
            return "json"
        return "json"

    if not _opens_a_block(stripped) and _load_yaml_collection(stripped) is not None:
        return "yaml"
    return "structured"


# A curly statement that opens a block: tags, then words, then `{`. A word may
# hold a colon (`2001:db8::/32`) but not a YAML key's `: `, and the first word
# is no YAML sequence's `- ` and no document marker (`---`, `...`), so no YAML
# document matches.
_TAGS = r"(?:(?:inactive|protect|replace|delete):\s+)*"
_WORD = r'(?:"[^"\n]*"|(?:[^\s{};#":]|:(?!\s|$))+)'
_OPENER = re.compile(
    rf"^{_TAGS}(?!-\s|---(?:\s|$)|\.\.\.(?:\s|$)){_WORD}(?:[ \t]+{_WORD})*[ \t]*\{{"
)


def _opens_a_block(stripped: str) -> bool:
    """Whether the first line that is not a comment opens a curly block.

    A one-line curly statement with a tag, `system { inactive: host-name r1; }`,
    is also a YAML mapping (`system { inactive` to `host-name r1; }`).
    """
    for line in stripped.splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "/*")):
            return _OPENER.match(line) is not None
    return False


def _load_yaml_collection(source: str) -> dict[object, object] | list[object] | None:
    """Return a parsed YAML mapping/list, excluding scalar documents."""
    try:
        value = yaml.safe_load(source)
    except yaml.YAMLError:
        return None
    return value if isinstance(value, (dict, list)) else None
