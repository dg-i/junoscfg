"""SchemaNode: condensed intermediate representation of the Junos XSD schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class Combinator(Enum):
    """How child elements combine."""

    SEQUENCE = "sequence"  # s() - all optional in order
    CHOICE = "choice"  # c() - pick one
    SEQ_CHOICE = "seq_choice"  # sc() - pick multiple, any order


@dataclass
class SchemaNode:
    """A node in the condensed schema tree."""

    name: str
    children: dict[str, SchemaNode] = field(default_factory=dict)
    combinator: Combinator = Combinator.CHOICE
    is_key: bool = False
    is_list: bool = False
    is_mandatory: bool = False
    is_leaf: bool = False
    is_presence: bool = False
    enums: list[str] | None = None
    pattern: str | None = None
    pattern_negated: bool = False
    type_ref: str | None = None
    flags: set[str] = field(default_factory=set)

    def __repr__(self) -> str:
        parts = [f"SchemaNode({self.name!r}"]
        if self.children:
            parts.append(f", children={len(self.children)}")
        if self.combinator != Combinator.CHOICE:
            parts.append(f", {self.combinator.value}")
        if self.is_key:
            parts.append(", key")
        if self.is_list:
            parts.append(", list")
        if self.is_mandatory:
            parts.append(", mandatory")
        if self.is_leaf:
            parts.append(", leaf")
        if self.is_presence:
            parts.append(", presence")
        if self.enums:
            parts.append(f", enums={len(self.enums)}")
        if self.type_ref:
            parts.append(f", type={self.type_ref}")
        parts.append(")")
        return "".join(parts)


def navigate(root: SchemaNode, *path: str) -> SchemaNode | None:
    """Navigate to a descendant node by path components.

    Returns None if any path component is not found.
    """
    node = root
    for name in path:
        child = node.children.get(name)
        if child is None:
            return None
        node = child
    return node


def find_all(root: SchemaNode, name: str) -> list[SchemaNode]:
    """Find all descendant nodes with the given name (breadth-first)."""
    results: list[SchemaNode] = []
    queue = list(root.children.values())
    while queue:
        node = queue.pop(0)
        if node.name == name:
            results.append(node)
        queue.extend(node.children.values())
    return results


def walk(root: SchemaNode, visitor: Callable[[SchemaNode, list[str]], None]) -> None:
    """Walk the tree depth-first, calling visitor(node, path) for each node."""
    _walk_impl(root, [], visitor)


def _walk_impl(
    node: SchemaNode, path: list[str], visitor: Callable[[SchemaNode, list[str]], None]
) -> None:
    visitor(node, path)
    for child in node.children.values():
        path.append(child.name)
        _walk_impl(child, path, visitor)
        path.pop()
