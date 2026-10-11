"""Lex Junos structured (curly-brace) configuration into statements.

One token lexer reads the text: `{`, `}`, `;` and a bracket list are tokens
wherever they stand outside quotes, and a comment is never part of a token, so
a configuration means the same whatever its layout. What the text holds but
yields no statement is reported (`SetConverter.notes`), and malformed text
raises `ValueError` naming the fault and its line.
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from typing import NoReturn, TextIO

# One alternative per token kind, tried in order at each position. A word
# starts with anything but a quote and runs to whitespace, a delimiter, `#` or
# `/*`; a quote inside a word is part of it, as the set reader's tokenizer
# reads one. `[` opens a list only where a token starts (`<[gx]e-*>` is one
# word), and `]` closes one only inside a list (see `_Lexer._word`).
_TOKEN = re.compile(
    r"""
      (?P<space>\s+)
    | (?P<line_comment>\#[^\n]*)
    | (?P<block_comment>/\*(?P<comment_text>.*?)\*/)
    | (?P<open_comment>/\*)
    | (?P<quoted>"(?:[^"\\]|\\.)*")
    | (?P<open_quote>")
    | (?P<delimiter>[{};\[])
    | (?P<word>(?:[^\s{};\#"/]|/(?!\*))(?:[^\s{};\#/]|/(?!\*))*)
    """,
    re.VERBOSE | re.DOTALL,
)

_OMITTED = "OMITTED"


@dataclass
class _Block:
    """An open block: its opener, where it opened, and what it has held."""

    text: str
    position: int
    holds: bool = False
    omitted: bool = False


@dataclass
class _Lexed:
    """What one pass over the text read."""

    statements: list[tuple[list[str], str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class SetConverter:
    """Lex structured Junos configuration into statements.

    Usage::

        converter = SetConverter('interfaces { ge-0/0/0 { description uplink; } }')
        converter.statements()
        # [[('interfaces', frozenset()), ('ge-0/0/0', frozenset()),
        #   ('description uplink', frozenset())]]
    """

    _PREFIX_TAGS = ("replace: ", "protect: ", "inactive: ", "delete: ")

    def __init__(self, source: str | TextIO) -> None:
        """Lex *source*, a string or a readable text stream."""
        self._input = source
        self._lexed: _Lexed | None = None

    def to_set(self) -> str:
        """Convert structured config to display set format. Deprecated.

        A tag becomes a `deactivate`/`protect`/`delete` line for the whole of
        the statement it leads, which is right for a block opener and wrong
        for a one-line entry: `inactive: route 0.0.0.0/0 next-hop 10.0.0.1;`
        marks the route, and `deactivate … route 0.0.0.0/0 next-hop 10.0.0.1`
        marks `next-hop`. Where an entry ends is the schema's to say;
        `convert_config(..., from_format=Format.STRUCTURED, to_format=Format.SET)`
        reads `statements()` through the schema instead.
        """
        warnings.warn(
            "SetConverter.to_set() is deprecated and will be removed in the next minor "
            "release: it tags a one-line statement's last node. Use junoscfg.convert_config"
            "(..., from_format=Format.STRUCTURED, to_format=Format.SET).",
            DeprecationWarning,
            stacklevel=2,
        )
        result = [self._transform_line(stack, text) for stack, text in self._lex().statements]
        return "\n".join(result) + "\n" if result else ""

    def statements(self) -> list[list[tuple[str, frozenset[str]]]]:
        """Each statement as its levels: the block openers above it, then itself.

        A level is its text and the tags that lead it (``inactive``,
        ``protect``, ``replace``, ``delete``). Which node a tag marks is the
        schema's question, not this lexer's: the set reader's schema walk
        answers it for set and structured input alike.
        """
        return [
            [self._split_tags(level) for level in [*stack, text]]
            for stack, text in self._lex().statements
        ]

    def notes(self) -> tuple[str, ...]:
        """What the text holds that yields no statement, one warning per block.

        The device's `{ /* OMITTED */ }` placeholder, its curly rendering of a
        statement under `apply-flags omit`, and a block with nothing in it.
        Each note starts with the block's path, its tags left out.
        """
        return tuple(self._lex().notes)

    @classmethod
    def _split_tags(cls, text: str) -> tuple[str, frozenset[str]]:
        stripped, tags = cls._strip_prefixes(text)
        return stripped, frozenset(tags)

    def _lex(self) -> _Lexed:
        if self._lexed is None:
            text = self._input.read() if hasattr(self._input, "read") else str(self._input)
            self._lexed = _Lexer(re.sub(r"\r\n?", "\n", text)).run()
        return self._lexed

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
        equivalents; ``replace:`` has none.
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

        for stack_entry in current_stack:
            entry, tags = self._strip_prefixes(stack_entry)
            emit_meta(tags, f"{current_statement}{entry}")
            current_statement += f"{entry} "

        text, tags = self._strip_prefixes(text)
        emit_meta(tags, f"{current_statement}{text}")

        statements.insert(0, f"set {current_statement}{text}")
        return "\n".join(statements)


class _Lexer:
    """One pass over structured text: tokens, then statements and notes."""

    def __init__(self, text: str) -> None:
        self._text = text
        self._out = _Lexed()
        self._blocks: list[_Block] = []
        self._pending: list[str] = []
        self._pending_position = 0
        self._items: list[str] | None = None  # the open bracket list
        self._list_position = 0
        self._after_list = False  # a list closed; only `;` may follow

    def run(self) -> _Lexed:
        for match in _TOKEN.finditer(self._text):
            kind = match.lastgroup
            if kind == "comment_text":  # `lastgroup` names the innermost group
                kind = "block_comment"
            position = match.start()
            if kind in ("space", "line_comment"):
                continue
            if kind == "block_comment":
                if self._blocks and match.group("comment_text").strip() == _OMITTED:
                    self._blocks[-1].omitted = True
                continue
            if kind == "open_comment":
                self._fail(position, "a comment is never closed")
            if kind == "open_quote":
                self._fail(position, "a quoted value is never closed")
            token = match.group()
            if kind == "quoted":
                self._value(token, position)
            elif kind == "word":
                self._word(token, position)
            elif token == "[":
                self._open_list(position)
            elif token == ";":
                self._end_statement(position)
            elif token == "{":
                self._open_block(position)
            else:
                self._close_block(position)
        if self._in_list:
            self._fail(self._list_position, "'[' is never closed by ']'")
        if self._pending:
            self._unterminated()
        if self._blocks:
            block = self._blocks[-1]
            self._fail(block.position, f"block '{block.text}' is never closed")
        return self._out

    # ── tokens ──

    @property
    def _in_list(self) -> bool:
        return self._items is not None and not self._after_list

    def _word(self, word: str, position: int) -> None:
        items = self._items
        if items is not None and not self._after_list and "]" in word:
            head, _, rest = word.partition("]")
            if head:
                items.append(head)
            self._close_list(position)
            if rest:
                self._value(rest, position)
            return
        self._value(word, position)

    def _value(self, token: str, position: int) -> None:
        if self._items is not None and self._in_list:
            self._items.append(token)
            return
        if self._after_list:
            self._fail(position, f"'{token}' after a bracket list; only ';' may follow")
        if not self._pending:
            self._pending_position = position
        self._pending.append(token)

    def _open_list(self, position: int) -> None:
        if self._in_list:
            self._fail(position, "'[' inside a bracket list")
        if not self._pending or self._after_list:
            self._fail(position, "'[' opens a list with no statement")
        self._items = []
        self._list_position = position

    def _close_list(self, position: int) -> None:
        if not self._items:
            self._fail(position, "an empty bracket list")
        self._after_list = True

    def _end_statement(self, position: int) -> None:
        if self._in_list:
            self._fail(position, "'[' is never closed by ']'")
        if not self._pending:
            return  # an empty statement, as the device's `};` after a placeholder
        stack = [block.text for block in self._blocks]
        statement = " ".join(self._pending)
        if self._after_list and self._items is not None:
            for item in self._items:
                self._out.statements.append((list(stack), f"{statement} {item}"))
        else:
            self._out.statements.append((stack, statement))
        for block in self._blocks:
            block.holds = True
        self._reset()

    def _open_block(self, position: int) -> None:
        if self._items is not None:
            self._fail(
                position,
                "'{' after a bracket list" if self._after_list else "'{' inside a bracket list",
            )
        if not self._pending:
            self._fail(position, "'{' opens a block with no name")
        if self._blocks:
            self._blocks[-1].holds = True
        self._blocks.append(_Block(" ".join(self._pending), self._pending_position))
        self._reset()

    def _close_block(self, position: int) -> None:
        if self._in_list:
            self._fail(position, "'}' inside a bracket list")
        if self._pending:
            self._unterminated()
        if not self._blocks:
            self._fail(position, "'}' closes no block")
        block = self._blocks.pop()
        if not block.holds:
            path = " ".join(SetConverter._split_tags(b.text)[0] for b in [*self._blocks, block])
            if block.omitted:
                self._out.notes.append(
                    f"{path}: `apply-flags omit` hides this block's content (the device's "
                    "`/* OMITTED */` placeholder); nothing of it is converted"
                )
            else:
                self._out.notes.append(f"{path}: an empty block; it holds no statement")

    # ── helpers ──

    def _reset(self) -> None:
        self._pending = []
        self._items = None
        self._after_list = False

    def _unterminated(self) -> NoReturn:
        statement = " ".join(self._pending)
        self._fail(self._pending_position, f"statement '{statement}' has no ';'")

    def _fail(self, position: int, fault: str) -> NoReturn:
        line = self._text.count("\n", 0, position) + 1
        raise ValueError(f"Invalid structured input on line {line}: {fault}")
