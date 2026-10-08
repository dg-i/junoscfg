"""Input normalization for Junos configuration text.

Handles comment removal, carriage return normalization, and
multi-line bracket unification.
"""

from __future__ import annotations

__all__ = ["find_unsupported_set_brackets", "normalize"]

import re
from typing import TextIO


def find_unsupported_set_brackets(source: str) -> tuple[tuple[int, str], ...]:
    """Return line-numbered diagnostics for unquoted square brackets.

    Raw set input accepts canonical ``display set`` commands, not interactive
    bracket-list shorthand. Full-line ``#`` comments and ``/* ... */`` block
    comments are ignored exactly as they are by :func:`normalize`.
    """
    findings: list[tuple[int, str]] = []
    in_block_comment = False

    for lineno, original_line in enumerate(source.splitlines(), 1):
        scan = original_line

        while True:
            if in_block_comment:
                comment_end = scan.find("*/")
                if comment_end < 0:
                    scan = ""
                    break
                scan = scan[comment_end + 2 :]
                in_block_comment = False

            stripped = scan.lstrip()
            if not stripped or stripped.startswith("#"):
                scan = ""
                break
            if stripped.startswith("/*"):
                in_block_comment = True
                scan = stripped[2:]
                continue
            scan = stripped
            break

        if scan and _has_unquoted_square_bracket(scan):
            findings.append(
                (
                    lineno,
                    f"Unsupported bracket syntax in set input on line {lineno}:\n{original_line}",
                )
            )

    return tuple(findings)


def _has_unquoted_square_bracket(line: str) -> bool:
    """Return whether *line* contains ``[`` or ``]`` outside double quotes."""
    in_quote = False
    preceding_backslashes = 0

    for char in line:
        if char == '"' and preceding_backslashes % 2 == 0:
            in_quote = not in_quote
        elif char in "[]" and not in_quote:
            return True

        if char == "\\":
            preceding_backslashes += 1
        else:
            preceding_backslashes = 0

    return False


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
