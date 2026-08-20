"""Tokenizer for Junos policy expressions.

Policy references may be plain names, bracket lists (``[ pol-a pol-b ]``)
or boolean expressions (``( pol-a && ! pol-b )``). The IR stores them as
opaque strings; this module extracts the referenced names as whole
tokens — the audit never does substring matching.
"""

from __future__ import annotations

import re

# Structure characters that mark an expression or bracket list (as opposed
# to a single policy name, which may itself contain spaces when quoted).
_HAS_STRUCTURE = re.compile(r"[()\[\]]|&&|\|\|")

# Everything that separates names inside an expression: whitespace,
# parentheses, brackets, negation, and the boolean operators && / ||.
_SEPARATORS = re.compile(r"(?:&&|\|\||[()\[\]!\s])+")

# A double-quoted span, kept atomic so quoted names with spaces survive.
_QUOTED = re.compile(r'"[^"]*"')


def extract_names(expr: str) -> list[str]:
    """Extract referenced policy names from a policy-expression string.

    Args:
        expr: The raw leaf value, e.g. ``'( "my pol" && ! pol-b )'``,
            ``"[ imp-a imp-b ]"``, or a plain (possibly spaced) name.

    Returns:
        The names in order of appearance, with surrounding double quotes
        stripped.
    """
    stripped = expr.strip()
    if not stripped:
        return []
    if not _HAS_STRUCTURE.search(stripped):
        # A single policy name. It may contain spaces (the set parser
        # strips the surrounding quotes), so it must not be tokenized.
        return [stripped.strip('"')]

    names: list[str] = []
    last = 0
    for match in _QUOTED.finditer(stripped):
        names.extend(t for t in _SEPARATORS.split(stripped[last : match.start()]) if t)
        names.append(match.group()[1:-1])
        last = match.end()
    names.extend(t for t in _SEPARATORS.split(stripped[last:]) if t)
    return names
