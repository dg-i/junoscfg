"""Input normalization for Junos configuration text.

Handles comment removal, carriage return normalization, and
multi-line bracket unification.
"""

from __future__ import annotations

import re
from typing import TextIO


def normalize(io_or_string: str | TextIO) -> str:
    """Read and normalize Junos configuration input.

    - Removes blank lines, # comments, and /* */ block comments
    - Normalizes carriage returns
    - Joins lines split across [ ] brackets
    """
    content = io_or_string.read() if hasattr(io_or_string, "read") else str(io_or_string)  # type: ignore[union-attr]

    content = _remove_blank_and_comment_lines(content)
    content = _unify_carriage_return(content)
    content = _unify_square_brackets(content)
    return content


def _remove_blank_and_comment_lines(text: str) -> str:
    """Remove blank lines, # comment lines, and /* */ block comments."""
    # Remove # comment lines
    text = re.sub(r"^\s*#.*", "", text, flags=re.MULTILINE)
    # Remove /* */ block comments (non-greedy, may span lines)
    text = re.sub(r"^\s*/\*((?!\*/).)*\*/", "", text, flags=re.MULTILINE | re.DOTALL)
    # Collapse whitespace-only newlines
    text = re.sub(r"\n\s*", "\n", text)
    return text.strip()


def _unify_carriage_return(text: str) -> str:
    """Normalize \\r\\n and \\r to \\n."""
    return re.sub(r"\r\n?", "\n", text)


def _unify_square_brackets(text: str) -> str:
    """Join lines split across [ ] brackets into single lines."""
    lines: list[str] = []
    open_brackets = 0

    for line in text.split("\n"):
        if open_brackets < 0:
            raise ValueError(f"Invalid statement: {line}")

        if open_brackets == 0:
            lines.append(line)
        else:
            lines[-1] += " " + line

        open_brackets += _count_unquoted_brackets(line)

    if open_brackets > 0:
        raise ValueError("Unclosed bracket")

    return "\n".join(lines)


def _count_unquoted_brackets(line: str) -> int:
    """Count net unquoted brackets (opens minus closes) in a line."""
    count = 0
    in_quote = False
    for i, ch in enumerate(line):
        if ch == '"' and (i == 0 or line[i - 1] != "\\"):
            in_quote = not in_quote
        elif not in_quote:
            if ch == "[":
                count += 1
            elif ch == "]":
                count -= 1
    return count
