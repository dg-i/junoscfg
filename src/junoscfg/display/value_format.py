"""How a value is spelled in a set or curly statement, by its leaf's type.

One answer for every writer and reader (spec conversion/value-quoting). A
value is one token: quoted where it must be, its `"` escaped as `\\"`, its `\\`
written as is, as the device writes `description "uplink to sw1 \\"core\\""`
and `message "...only.\\nAll..."` (vMX 23.2R2-S7.5, QFX5120 25.2R2-S1.5
`junoscfg-oracle.set.gz`). A `policy-algebra` leaf holds the device's own
token instead: an expression `( P-A && P-B )` written bare, or a quoted name
whose text starts with `(`, `"( P-A )"`, which the device keeps quoted in its
XML and JSON (`synthetic-probes`), so that it is never read as an expression.
"""

from __future__ import annotations

import re
from typing import Any

#: The XSD type of a leaf that holds a policy expression or a policy chain.
POLICY_ALGEBRA = "policy-algebra"

#: One quoted token, as every reader reads one: `\\` and the character after
#: it belong to the value (`display/set_converter.py`, the set tokenizer).
_QUOTED_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"')


def needs_quoting(s: str) -> bool:
    """Check if a value string needs quoting for set command output."""
    return bool(re.search(r'[\s";&|@\[\]{}#$^\\]', s)) or s == ""


def is_policy_algebra(node: Any) -> bool:
    """Whether *node*, a structure-tree leaf, takes a policy expression."""
    return isinstance(node, dict) and node.get("tr") == POLICY_ALGEBRA


def is_algebra_token(text: str) -> bool:
    """Whether *text*, a `policy-algebra` value, is the device's token as written.

    An expression starts with `(`; a quoted name that starts with `(` keeps its
    quotes, or it would read as an expression. Readers keep such a token as
    written and writers write it as it is; any other value is an ordinary
    value both ways, so whatever is written reads back as written.
    """
    if text.startswith("("):
        return True
    return text.startswith('"(') and _QUOTED_TOKEN.fullmatch(text) is not None


def format_value(value: Any, node: Any = None) -> str:
    """*value* as one token of a set or curly statement, for the leaf *node*.

    *node* is the leaf's structure-tree node, or None where the caller has
    none (an entry's name, an apply-macro value, an audit path): the leaf's
    type, never the value's look, decides whether a value is the device's
    policy token. Every other value is quoted where it must be, `"` escaped.
    """
    s = str(value)
    if is_policy_algebra(node) and is_algebra_token(s):
        return s
    if not needs_quoting(s):
        return s
    return '"' + s.replace('"', '\\"') + '"'
