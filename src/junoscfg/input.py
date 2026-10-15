"""Input normalization for Junos configuration text.

Handles comment removal, carriage return normalization, and
multi-line bracket unification.
"""

from __future__ import annotations

__all__ = [
    "InputError",
    "find_non_json_value",
    "find_unsupported_set_brackets",
    "find_unsupported_set_commands",
    "iter_visible_set_lines",
    "normalize",
]

import re
from typing import TYPE_CHECKING, Any, TextIO

if TYPE_CHECKING:
    from collections.abc import Iterator


class InputError(ValueError):
    """A refusal to read configuration text, with the line it happened on.

    Its message is the reader's own and may quote the text; ``lineno``
    (1-based, ``None`` when unknown) lets a caller that must not quote it
    still say where (an anonymized conversion), as `json.JSONDecodeError`'s
    ``lineno`` does.
    """

    def __init__(self, message: str, lineno: int | None = None) -> None:
        """Build the refusal from its *message* and the *lineno* it names."""
        super().__init__(message)
        self.lineno = lineno


#: The Python types of a JSON document's scalars.
_JSON_SCALARS = (str, int, float, bool, type(None))


def find_non_json_value(data: Any) -> tuple[str, str] | None:
    """The first value of a loaded document that no JSON document can hold.

    yaml-new is the Junos JSON object spelled in YAML (spec
    conversion/junos-json-yaml); its conversion, its writer and its validation
    all refuse a document that holds anything else. Returns ``(kind, path)``:
    the kind is the value's type (``date``, ``bytes``, ``set``, ``tuple``, ...),
    ``<type> key`` for a mapping key that is not a string (``null`` for
    ``None``), or ``alias`` for a mapping or list met a second time, which only
    a YAML alias, or a caller sharing one object, produces: JSON has neither,
    and a cycle would otherwise never end. The path is dotted keys and list
    indexes from the document root, ``""`` for the document itself, and never
    holds the offending value or key. Returns ``None`` when the document is a
    tree of mappings with string keys, lists, strings, numbers, booleans and
    nulls. The walk visits each mapping and list once.
    """
    return _non_json(data, set())


def _non_json(data: Any, seen: set[int]) -> tuple[str, str] | None:
    if isinstance(data, (dict, list)):
        if id(data) in seen:
            return "alias", ""
        seen.add(id(data))
    if isinstance(data, dict):
        for key, value in data.items():
            if not isinstance(key, str):
                return f"{_kind(key)} key", ""
            found = _non_json(value, seen)
            if found is not None:
                kind, below = found
                return kind, f"{key}.{below}" if below else key
    elif isinstance(data, list):
        for index, item in enumerate(data):
            found = _non_json(item, seen)
            if found is not None:
                kind, below = found
                return kind, f"{index}.{below}" if below else str(index)
    elif not isinstance(data, _JSON_SCALARS):
        return _kind(data), ""
    return None


def _kind(value: Any) -> str:
    return "null" if value is None else type(value).__name__


def find_unsupported_set_brackets(source: str) -> tuple[tuple[int, str], ...]:
    """Return line-numbered diagnostics for unquoted square brackets.

    Raw set input accepts canonical ``display set`` commands, not interactive
    bracket-list shorthand. Full-line ``#`` comments and ``/* ... */`` block
    comments are ignored exactly as they are by :func:`normalize`.
    """
    findings: list[tuple[int, str]] = []
    for lineno, original_line, visible_line in iter_visible_set_lines(source):
        if _has_unquoted_square_bracket(visible_line):
            findings.append(
                (
                    lineno,
                    f"Unsupported bracket syntax in set input on line {lineno}:\n{original_line}",
                )
            )

    return tuple(findings)


def find_unsupported_set_commands(source: str) -> tuple[tuple[int, str], ...]:
    """Return value-free, physical-line diagnostics for unsupported commands.

    Classify the existing raw set reader's command spellings only, not paths
    or values. Every supported command needs a nonempty path after its literal
    space separator. Leading comments are ignored through the same physical
    line view used by bracket detection and validation.
    """
    prefixes = ("set ", "deactivate ", "protect ", "delete ", "activate ")
    findings: list[tuple[int, str]] = []
    for lineno, _original_line, visible_line in iter_visible_set_lines(source):
        line = visible_line.strip()
        if not any(line.startswith(prefix) and line[len(prefix) :].strip() for prefix in prefixes):
            findings.append((lineno, f"Unsupported command in set input on line {lineno}"))
    return tuple(findings)


def iter_visible_set_lines(source: str) -> Iterator[tuple[int, str, str]]:
    """Yield line number, original text, and content outside leading comments.

    Full-line ``#`` comments and leading ``/* ... */`` block comments are
    omitted. Content following a closing block-comment marker remains visible
    on its original physical line. Raw set consumers use this shared view so
    conversion and validation classify comments consistently.
    """
    in_block_comment = False

    for lineno, original_line in enumerate(source.splitlines(), 1):
        visible_line = original_line

        while True:
            if in_block_comment:
                comment_end = visible_line.find("*/")
                if comment_end < 0:
                    visible_line = ""
                    break
                visible_line = visible_line[comment_end + 2 :]
                in_block_comment = False

            stripped = visible_line.lstrip()
            if not stripped or stripped.startswith("#"):
                visible_line = ""
                break
            if stripped.startswith("/*"):
                in_block_comment = True
                visible_line = stripped[2:]
                continue
            visible_line = stripped
            break

        if visible_line:
            yield lineno, original_line, visible_line


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
