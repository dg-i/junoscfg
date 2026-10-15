"""YAML documents that share a block through an alias, loop through one, or explode.

Every yaml-new door reads them (reader, writer, validation, CLI); the expected
outcomes are in spec conversion/junos-json-yaml, "A block shared through an
alias is written out, a cycle and an alias bomb are refused". Synthetic values
only (AGENTS.md).
"""

from __future__ import annotations

import signal
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

#: Two syslog hosts sharing one `contents` list through an alias.
SHARED_BLOCK = (
    "configuration:\n"
    "  system:\n"
    "    syslog:\n"
    "      host:\n"
    "      - name: 198.51.100.9\n"
    "        contents: &c\n"
    "        - name: any\n"
    "          any: [null]\n"
    "      - name: 198.51.100.10\n"
    "        contents: *c\n"
)

#: The same document with the shared block written out.
SHARED_BLOCK_WRITTEN_OUT = SHARED_BLOCK.replace("contents: &c\n", "contents:\n").replace(
    "        contents: *c\n",
    "        contents:\n        - name: any\n          any: [null]\n",
)

#: A mapping that holds itself.
CYCLE = "configuration: &a\n  system:\n    x: *a\n"


def alias_bomb_yaml(levels: int = 9, fan: int = 10, word: str = "lol") -> str:
    """Billion laughs: *levels* lists of *fan* aliases of the level below, the
    last under `configuration` (``fan ** levels`` values written out)."""
    lines = [f"{word}0: &{word}0 [" + ", ".join([word] * fan) + "]"]
    for level in range(1, levels):
        below = f"*{word}{level - 1}"
        lines.append(f"{word}{level}: &{word}{level} [" + ", ".join([below] * fan) + "]")
    lines.append(f"configuration:\n  system:\n    {word}: *{word}{levels - 1}")
    return "\n".join(lines) + "\n"


def alias_bomb(levels: int = 64, fan: int = 2) -> dict[str, Any]:
    """An IR whose *levels* nested lists each hold one list *fan* times
    (``fan ** levels`` values written out), as a caller sharing objects builds it."""
    node: Any = ["lol"]
    for _ in range(levels):
        node = [node] * fan
    return {"system": {"lol": node}}


def alias_chain_yaml(segments: int = 4, depth: int = 300, pad: int = 2500) -> str:
    """Shallow text, deep document: *segments* flow lists each *depth* deep,
    the innermost of each an alias of the one before, plus *pad* nulls so the
    written-out size stays within twice the parsed size. Written out, it nests
    ``segments * depth`` deep, past Python's recursion limit (Test/Challenge
    finding 3 of yaml-new-alias-cycles)."""
    lines = []
    for segment in range(segments):
        inner = f"*s{segment - 1}" if segment else "x"
        lines.append(f"s{segment}: &s{segment} " + "[" * depth + inner + "]" * depth)
    lines.append("pad: [" + ", ".join(["null"] * pad) + "]")
    lines.append(f"configuration:\n  system:\n    x: *s{segments - 1}")
    return "\n".join(lines) + "\n"


#: Two hosts sharing one host entry's `contents`, a third reaching the host
#: itself: each anchor aliased once, `contents` reached three times written out.
NESTED_ONCE = (
    "configuration:\n"
    "  system:\n"
    "    syslog:\n"
    "      host:\n"
    "      - name: 198.51.100.9\n"
    "        contents: &c\n"
    "        - name: any\n"
    "          any: [null]\n"
    "      - &h\n"
    "        name: 198.51.100.10\n"
    "        contents: *c\n"
    "      file:\n"
    "      - name: messages\n"
    "        contents: *h\n"
)


def shared_containers(value: Any) -> list[str]:
    """The paths at which a mapping or list already met is met again."""
    seen: set[int] = set()
    again: list[str] = []
    pending: list[tuple[Any, str]] = [(value, "")]
    while pending:
        node, path = pending.pop()
        if not isinstance(node, (dict, list)):
            continue
        if id(node) in seen:
            again.append(path)
            continue
        seen.add(id(node))
        steps = node.items() if isinstance(node, dict) else enumerate(node)
        pending.extend((child, f"{path}.{step}" if path else str(step)) for step, child in steps)
    return again


@contextmanager
def within(seconds: float) -> Iterator[None]:
    """Fail, instead of hanging, when the block runs longer than *seconds*: an
    unbounded expansion would otherwise never return (POSIX timer)."""

    def expire(_signal: int, _frame: object) -> None:
        raise AssertionError(f"still running after {seconds} s: an unbounded expansion")

    previous = signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
