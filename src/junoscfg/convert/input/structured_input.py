"""Convert structured (curly-brace) configuration to the JSON dict IR.

`SetConverter` lexes the braces into statements, each with the tags that
lead its levels, and the set reader's schema walk builds the dict: one walk
for set and structured input, so a tag lands where the schema says the
statement it leads starts. What the text holds but yields no statement (the
device's `/* OMITTED */` placeholder, an empty block) is reported to the
caller's diagnostic sink, never dropped silently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from junoscfg.convert.input.set_input import statements_to_dict
from junoscfg.display import SetConverter

if TYPE_CHECKING:
    from collections.abc import Callable


def structured_to_dict(
    source: str, diagnostic_sink: Callable[[str, str], None] | None = None
) -> dict[str, Any]:
    """Parse structured configuration into the IR dict.

    Each of the lexer's notes (`SetConverter.notes`) goes to *diagnostic_sink*
    as its block's path and its message.
    """
    lexer = SetConverter(source)
    ir = statements_to_dict(lexer.statements())
    if diagnostic_sink is not None:
        for note in lexer.notes():
            diagnostic_sink(note.path, note.message)
    return ir


@dataclass(frozen=True, slots=True)
class StructuredSetLines:
    """The set statements structured text spells, as the conversion walk reads them.

    Attributes:
        lines: One ``set`` line per statement, in the input's own tokens and
            without tags; a one-line statement the walk reads as siblings
            gives one line per sibling.
        incomplete: The lines whose last leaf has no value.
        notes: What the text holds that yields no statement, each as the
            block's path and its message.
    """

    lines: tuple[str, ...]
    incomplete: tuple[str, ...]
    notes: tuple[tuple[str, str], ...]


def structured_set_lines(source: str) -> StructuredSetLines:
    """Read structured text into the set statements the conversion walk reads.

    Validation checks these lines rather than the set writer's output, so it
    judges what the input says: the writer would quote `description a b c`
    into one value and drop the keyword of `overload timeout 300`.

    Raises:
        ValueError: The text is malformed, or a tag sits inside a key or value.
    """
    lexer = SetConverter(source)
    read: list[tuple[str, bool]] = []
    statements_to_dict(lexer.statements(), set_lines=read)
    return StructuredSetLines(
        lines=tuple(f"set {line}" for line, _ in read),
        incomplete=tuple(f"set {line}" for line, whole in read if not whole),
        notes=tuple((note.path, note.message) for note in lexer.notes()),
    )
