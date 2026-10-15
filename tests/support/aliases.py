"""YAML documents that share a block through an alias, loop through one, or nest deep.

Every yaml-new door reads them (reader, writer, validation, CLI), and the
`yaml` reader the cycles and deep ones; the expected outcomes are in spec
conversion/junos-json-yaml, "A block shared through an alias is written out, a
cycle and nesting past 64 levels are refused". Synthetic values only (AGENTS.md).
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


#: The common YAML idiom: a block anchored beside `configuration`, aliased under it.
ANCHORED_BESIDE = (
    "x-contents: &c\n"
    "- name: any\n"
    "  any: [null]\n"
    "configuration:\n"
    "  system:\n"
    "    syslog:\n"
    "      host:\n"
    "      - name: 198.51.100.9\n"
    "        contents: *c\n"
)

#: `ANCHORED_BESIDE` with the block written out at its alias.
ANCHORED_BESIDE_WRITTEN_OUT = ANCHORED_BESIDE.replace(
    "        contents: *c\n", "        contents:\n        - name: any\n          any: [null]\n"
)


def hosts_sharing_contents(hosts: int) -> str:
    """*hosts* syslog hosts, the first anchoring a `contents` the others alias."""
    text = (
        "configuration:\n  system:\n    syslog:\n      host:\n"
        "      - name: h0\n        contents: &c\n        - name: any\n          any: [null]\n"
    )
    return text + "".join(f"      - name: h{i}\n        contents: *c\n" for i in range(1, hosts))


def alias_bomb_yaml(levels: int = 9, fan: int = 10, word: str = "lol") -> str:
    """Billion laughs: *levels* lists of *fan* aliases of the level below, the
    last under `configuration` (``fan ** levels`` values written out)."""
    lines = [f"{word}0: &{word}0 [" + ", ".join([word] * fan) + "]"]
    for level in range(1, levels):
        below = f"*{word}{level - 1}"
        lines.append(f"{word}{level}: &{word}{level} [" + ", ".join([below] * fan) + "]")
    lines.append(f"configuration:\n  system:\n    {word}: *{word}{levels - 1}")
    return "\n".join(lines) + "\n"


def alias_chain_yaml(segments: int = 4, depth: int = 20) -> str:
    """Shallow text, deep document: *segments* flow lists each *depth* deep, the
    innermost of each an alias of the one before. Written out, segment ``s``
    holds its value ``1 + depth * (s + 1)`` steps deep, while no line of the
    text nests deeper than ``depth``."""
    lines = []
    for segment in range(segments):
        inner = f"*s{segment - 1}" if segment else "x"
        lines.append(f"s{segment}: &s{segment} " + "[" * depth + inner + "]" * depth)
    lines.append(f"configuration:\n  system:\n    x: *s{segments - 1}")
    return "\n".join(lines) + "\n"


def nested_yaml(lists: int, value: str = "acme") -> str:
    """`configuration.system.x` holding *lists* nested flow lists around *value*:
    the value sits ``3 + lists`` path steps below the document's root."""
    return "configuration:\n  system:\n    x: " + "[" * lists + value + "]" * lists + "\n"


def nested_ir(steps: int, value: Any = "acme") -> dict[str, Any]:
    """An IR whose *value* sits *steps* path steps below its own root, as
    mappings `{"a": ...}`: ``steps + 1`` below `{"configuration": ir}`."""
    node: Any = value
    for _ in range(steps):
        node = {"a": node}
    return node


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
