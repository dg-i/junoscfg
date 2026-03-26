"""Shared value formatting for Junos set command converters."""

from __future__ import annotations

import re
from typing import Any


def policy_expression(s: str) -> bool:
    """Check if a string looks like a Junos policy expression."""
    return bool(re.match(r"\A\s*\(", s)) and ("&&" in s or "||" in s or "!" in s)


def needs_quoting(s: str) -> bool:
    """Check if a value string needs quoting for set command output."""
    return bool(re.search(r'[\s";&|@\[\]{}#$^\\]', s)) or s == ""


def format_value(value: Any) -> str:
    """Format a value for set command output, with quoting as needed."""
    s = str(value)
    if policy_expression(s):
        return s
    return f'"{s}"' if needs_quoting(s) else s
