"""YAML documents that share a block through an alias, loop through one, or explode.

Every yaml-new door reads them (reader, writer, validation, CLI); the expected
outcomes are in spec conversion/junos-json-yaml, "A block shared through an
alias is written out, a cycle and an alias bomb are refused". Synthetic values
only (AGENTS.md).
"""

from __future__ import annotations

from typing import Any

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
