"""Input normalization for Junos configuration text.

Handles comment removal, carriage return normalization, and
multi-line bracket unification.
"""

from __future__ import annotations

__all__ = [
    "META_KEY_PREFIXES",
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


#: The key prefixes of the Ansible inventory artefacts the ``yaml`` format leaves
#: unread: its reader drops them unwalked, and its schema admits them unread.
META_KEY_PREFIXES = ("_ansible", "_meta_")

#: The Python types of a JSON document's scalars.
_JSON_SCALARS = (str, int, float, bool, type(None))

#: How deep a document may nest: path steps from its root to any value. The
#: owner's figure (2026-10-15); no Junos configuration comes near it, and
#: junoscfg's own recursive stages then never walk a YAML document deeper.
_CEILING = 64

#: Why a value, a key or a cycle is refused.
_NO_SPELLING = "has no JSON spelling"
#: Why a value is refused that sits past the ceiling.
_TOO_DEEP = f"is nested deeper than {_CEILING} levels"


class NonJsonValue(NamedTuple):
    """Where a loaded document stops being a JSON document junoscfg can walk, and why.

    ``kind`` is a value's type (``date``, ``bytes``, ``set``, ``tuple``, ...),
    ``<type> key`` for a mapping key that is not a string (``null`` for
    ``None``), ``cycle``, or ``value`` for a value nested too deep; ``path`` is
    dotted keys and list indexes from the document root, ``""`` for the
    document itself; ``reason`` says why in words every door prints. None of
    them holds a value or a key.
    """

    kind: str
    path: str
    reason: str

    @property
    def where(self) -> str:
        """``at <path>``, or ``at the top level`` for the document itself."""
        return f"at {self.path}" if self.path else "at the top level"

    def read_refusal(self, label: str) -> str:
        """The message a reader of *label* text (``YAML``, ``JSON``, ``XML``) refuses it with."""
        article = "an" if label == "XML" else "a"
        return f"Invalid input: {article} {label} {self.kind} {self.where} {self.reason}"


def find_non_json_value(
    data: Any, *, scalars: bool = True, unwalked: tuple[str, ...] = ()
) -> NonJsonValue | None:
    """The first place, in document order, a loaded document stops being a JSON
    document junoscfg can walk.

    yaml-new is the Junos JSON object spelled in YAML (spec
    conversion/junos-json-yaml); its conversion, its writer and its validation
    all refuse a document that holds anything else. JSON has no aliases, so a
    mapping or list reached again, through a YAML alias or a caller sharing one
    object, stands for a copy of itself and is walked at every place it is
    reached, however often. Refused:

    - a mapping or list reached inside itself, kind ``cycle``, at the path where
      it is reached again;
    - a value more than 64 path steps below *data*, kind ``value``, at its own
      path: the walk never goes deeper, nor does any stage after it;
    - a mapping key that is not a string, kind ``<type> key``, at its mapping's
      path, before what it holds is walked: every stage after a reader takes a
      key as a statement name;
    - with *scalars* true, a value of a type JSON lacks.

    The ``yaml`` reader and its validation pass *scalars* false, since its IR
    holds YAML's dates and other scalars, and in *unwalked* the key prefixes
    whose values they leave unread: there only what junoscfg's own walks would
    take is refused. junoscfg assumes its input is not hostile: an alias bomb is
    walked written out, at the cost of its expansion, and a caller handling
    untrusted YAML bounds it first (decision
    2026-10-15-yaml-nests-at-most-64-levels). Returns ``None`` when nothing is
    refused.
    """
    return _visit(data, 0, set(), scalars, unwalked)


def _visit(
    data: Any, depth: int, open_: set[int], scalars: bool, unwalked: tuple[str, ...]
) -> NonJsonValue | None:
    container = isinstance(data, (dict, list))
    if container and id(data) in open_:
        return NonJsonValue("cycle", "", _NO_SPELLING)
    if depth > _CEILING:
        return NonJsonValue("value", "", _TOO_DEEP)
    if not container:
        if not scalars or isinstance(data, _JSON_SCALARS):
            return None
        return NonJsonValue(_kind(data), "", _NO_SPELLING)
    open_.add(id(data))
    try:
        steps = data.items() if isinstance(data, dict) else enumerate(data)
        for step, value in steps:
            if isinstance(data, dict):
                if not isinstance(step, str):
                    return NonJsonValue(f"{_kind(step)} key", "", _NO_SPELLING)
                if unwalked and step.startswith(unwalked):
                    continue
            found = _visit(value, depth + 1, open_, scalars, unwalked)
            if found is not None:
                return found._replace(path=f"{step}.{found.path}" if found.path else str(step))
        return None
    finally:
        open_.discard(id(data))


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
