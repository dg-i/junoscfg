"""Input normalization for Junos configuration text.

Handles comment removal, carriage return normalization, and
multi-line bracket unification.
"""

from __future__ import annotations

__all__ = [
    "InputError",
    "NonJsonValue",
    "find_non_json_value",
    "find_unsupported_set_brackets",
    "find_unsupported_set_commands",
    "iter_visible_set_lines",
    "normalize",
]

import re
from typing import TYPE_CHECKING, Any, NamedTuple, TextIO

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

#: Why a value, a key or a cycle is refused.
_NO_SPELLING = "has no JSON spelling"
#: Why an alias is refused whose copies pass the size bound.
_TOO_LARGE = "expands the document past twice its size"
#: Why an alias is refused whose copies nest deeper than the document is written.
_TOO_DEEP = "nests the document deeper than it is written"
_BOUNDS = (_TOO_LARGE, _TOO_DEEP)


class NonJsonValue(NamedTuple):
    """Where a loaded document stops being a JSON document, and why.

    ``kind`` is a value's type (``date``, ``bytes``, ``set``, ``tuple``, ...),
    ``<type> key`` for a mapping key that is not a string (``null`` for
    ``None``), ``cycle`` or ``alias``; ``path`` is dotted keys and list indexes
    from the document root, ``""`` for the document itself; ``reason`` says why
    in words every door prints. None of them holds a value or a key.
    """

    kind: str
    path: str
    reason: str


def find_non_json_value(data: Any) -> NonJsonValue | None:
    """The first place a loaded document stops being a JSON document.

    yaml-new is the Junos JSON object spelled in YAML (spec
    conversion/junos-json-yaml); its conversion, its writer and its validation
    all refuse a document that holds anything else. JSON has no aliases, so a
    mapping or list reached again, through a YAML alias or a caller sharing one
    object, stands for a copy of itself and is checked at every place it is
    reached. Refused, in document order:

    - a value of a type JSON lacks, or a mapping key that is not a string;
    - a mapping or list reached inside itself, kind ``cycle``, at the path where
      it is reached again;
    - an alias whose copies would make the document, written out, hold more
      than twice the values it holds as parsed (mappings, lists and scalars; a
      mapping or list reached again counted once), kind ``alias``, at the path
      of the outermost alias being written out when that size is passed.

    Every document that reaches each value at most twice passes the bound; one
    without aliases never reaches it. The walk stops within twice the parsed
    size, so it, and every stage after it, stays linear in the parsed document
    (decision 2026-10-15-yaml-new-expands-aliases-within-a-bound; the factor is
    interim, pending the owner). Returns ``None`` for a JSON document.
    """
    size, depth = _as_parsed(data)
    return _Walk(2 * size, depth).visit(data, 0, inside_copy=False)


def _as_parsed(data: Any) -> tuple[int, int]:
    """The values *data* holds as parsed (each mapping and list once, with its
    scalars) and its deepest nesting, where a mapping or list reached again is
    a leaf, as an alias is in the text. Iterative: it never recurses."""
    seen: set[int] = set()
    count = deepest = 0
    pending = [(data, 0)]
    while pending:
        value, depth = pending.pop()
        deepest = max(deepest, depth)
        if isinstance(value, (dict, list)):
            if id(value) in seen:
                continue
            seen.add(id(value))
            children = list(value.values() if isinstance(value, dict) else value)
            # Reversed, so the walk meets each value in document order and an
            # anchor before its aliases, as the text holds them.
            pending.extend((child, depth + 1) for child in reversed(children))
        count += 1
    return count, deepest


class _Walk:
    """The written-out walk, with the bound's remaining steps and the open containers."""

    def __init__(self, budget: int, deepest: int) -> None:
        self.left = budget
        self.deepest = deepest
        self.seen: set[int] = set()
        self.open: set[int] = set()

    def visit(self, data: Any, depth: int, *, inside_copy: bool) -> NonJsonValue | None:
        self.left -= 1
        if self.left < 0:
            return NonJsonValue("alias", "", _TOO_LARGE)
        if depth > self.deepest:
            return NonJsonValue("alias", "", _TOO_DEEP)
        if not isinstance(data, (dict, list)):
            if isinstance(data, _JSON_SCALARS):
                return None
            return NonJsonValue(_kind(data), "", _NO_SPELLING)
        key = id(data)
        if key in self.open:
            return NonJsonValue("cycle", "", _NO_SPELLING)
        again = key in self.seen
        self.seen.add(key)
        self.open.add(key)
        found = self._children(data, depth + 1, inside_copy=inside_copy or again)
        self.open.discard(key)
        if found is not None and found.reason in _BOUNDS and again and not inside_copy:
            # This is the alias being written out: name its place.
            return found._replace(path="")
        return found

    def _children(self, data: dict | list, depth: int, *, inside_copy: bool) -> NonJsonValue | None:
        if isinstance(data, dict):
            for step, value in data.items():
                if not isinstance(step, str):
                    return NonJsonValue(f"{_kind(step)} key", "", _NO_SPELLING)
                found = self.visit(value, depth, inside_copy=inside_copy)
                if found is not None:
                    return found._replace(path=f"{step}.{found.path}" if found.path else step)
            return None
        for index, item in enumerate(data):
            found = self.visit(item, depth, inside_copy=inside_copy)
            if found is not None:
                place = str(index)
                return found._replace(path=f"{place}.{found.path}" if found.path else place)
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
