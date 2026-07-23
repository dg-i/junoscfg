"""Convert Junos structured (curly-brace) configuration to display set commands."""

from __future__ import annotations

import re
from typing import TextIO

from junoscfg.input import normalize


class SetConverter:
    """Convert structured Junos config to 'set' commands.

    Usage::

        converter = SetConverter('interfaces { ge-0/0/0 { description uplink; } }')
        print(converter.to_set())
        # set interfaces ge-0/0/0 description uplink
    """

    _PREFIX_TAGS = ("replace: ", "protect: ", "inactive: ", "delete: ")

    def __init__(self, source: str | TextIO, *, emit_replace: bool = False) -> None:
        self._input = source
        self._emit_replace = emit_replace

    def to_set(self) -> str:
        """Convert structured config to display set format."""
        result: list[str] = []

        for stack, text in self._process():
            result.append(self._transform_line(stack, text))

        return "\n".join(result) + "\n" if result else ""

    def _process(self) -> list[tuple[list[str], str]]:
        """Parse structured config into (stack, statement) pairs."""
        stack: list[str] = []
        results: list[tuple[list[str], str]] = []

        content = normalize(self._input)
        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            # Strip inline comments (respecting quoted strings)
            clean = self._strip_inline_comments(stripped)

            # Line ending with opening brace
            if clean.endswith("{"):
                stack.append(clean[:-1].strip())
                continue

            # Line ending with closing brace
            if clean.endswith("}"):
                if stack:
                    stack.pop()
                continue

            # Bracket expansion: text [items];
            bracket = _parse_bracket_expansion(clean)
            if bracket:
                prefix, items = bracket
                for item in items:
                    results.append((list(stack), f"{prefix} {item}"))
                continue

            # Simple statement ending with ;
            m_stmt = re.match(r"(.*);", line)
            if m_stmt:
                results.append((list(stack), m_stmt.group(1)))
                continue

            raise ValueError(f"Unknown statement: {line}")

        return results

    @staticmethod
    def _strip_inline_comments(line: str) -> str:
        """Strip inline comments (/* */ and #) while respecting quoted strings."""
        result: list[str] = []
        i = 0
        n = len(line)
        while i < n:
            if line[i] == '"':
                # Quoted string — keep everything including quotes
                j = i + 1
                while j < n and line[j] != '"':
                    if line[j] == "\\" and j + 1 < n:
                        j += 2
                    else:
                        j += 1
                if j < n:
                    j += 1  # include closing quote
                result.append(line[i:j])
                i = j
            elif line[i : i + 2] == "/*":
                # Block comment — skip to */
                end = line.find("*/", i + 2)
                i = end + 2 if end >= 0 else n
            elif line[i] == "#":
                # Line comment — skip rest of line
                break
            else:
                result.append(line[i])
                i += 1
        return "".join(result).strip()

    @classmethod
    def _strip_prefixes(cls, text: str) -> tuple[str, set[str]]:
        """Strip leading operational tags and report which were found.

        Junos operational tags (``replace:``, ``protect:``, ``inactive:``,
        ``delete:``) only ever lead a statement, possibly stacked. Anything
        past the first non-tag token — including quoted values that happen
        to contain tag text — is left untouched.
        """
        found: set[str] = set()
        while True:
            for tag in cls._PREFIX_TAGS:
                if text.startswith(tag):
                    found.add(tag[:-2])
                    text = text[len(tag) :]
                    break
            else:
                return text, found

    def _transform_line(self, current_stack: list[str], text: str) -> str:
        """Build set/deactivate/protect lines from stack context and statement.

        Strips operational prefixes (replace:, protect:, inactive:, delete:)
        and emits corresponding commands for prefixes that have set
        equivalents. When ``emit_replace`` is set, ``replace:`` additionally
        emits a pseudo ``replace <path>`` line for the structured-input
        bridge (not part of the display-set format).
        """
        statements: list[str] = []
        current_statement = ""

        def emit_meta(tags: set[str], path: str) -> None:
            if "protect" in tags:
                statements.append(f"protect {path}")
            if "inactive" in tags:
                statements.append(f"deactivate {path}")
            if "delete" in tags:
                statements.append(f"delete {path}")
            if "replace" in tags and self._emit_replace:
                statements.append(f"replace {path}")

        for stack_entry in current_stack:
            entry, tags = self._strip_prefixes(stack_entry)
            emit_meta(tags, f"{current_statement}{entry}")
            current_statement += f"{entry} "

        text, tags = self._strip_prefixes(text)
        emit_meta(tags, f"{current_statement}{text}")

        statements.insert(0, f"set {current_statement}{text}")
        return "\n".join(statements)


def _parse_bracket_expansion(line: str) -> tuple[str, list[str]] | None:
    """Parse a bracket expansion like ``prefix [item1 item2];``.

    Handles ``[`` and ``]`` inside quoted strings correctly.
    Returns ``(prefix, [items])`` or ``None`` if no bracket expansion found.
    """
    if not line.endswith(";"):
        return None

    # Find first unquoted '['
    in_quote = False
    bracket_start = -1
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if ch == '"':
            in_quote = not in_quote
        elif ch == "[" and not in_quote:
            bracket_start = i
            break
        i += 1

    if bracket_start < 0:
        return None

    # Find matching unquoted ']'
    in_quote = False
    bracket_end = -1
    i = bracket_start + 1
    while i < n:
        ch = line[i]
        if ch == '"':
            in_quote = not in_quote
        elif ch == "]" and not in_quote:
            bracket_end = i
            break
        i += 1

    if bracket_end < 0:
        return None

    prefix = line[:bracket_start].strip()
    inner = line[bracket_start + 1 : bracket_end].strip()

    # Split inner on whitespace, respecting quoted strings
    items: list[str] = []
    i = 0
    m = len(inner)
    while i < m:
        while i < m and inner[i] == " ":
            i += 1
        if i >= m:
            break
        if inner[i] == '"':
            j = i + 1
            while j < m and inner[j] != '"':
                if inner[j] == "\\" and j + 1 < m:
                    j += 2
                else:
                    j += 1
            if j < m:
                j += 1
            items.append(inner[i:j])
            i = j
        else:
            j = i
            while j < m and inner[j] != " ":
                j += 1
            items.append(inner[i:j])
            i = j

    return (prefix, items) if items else None
