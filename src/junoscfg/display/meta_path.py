"""What a verb line names: the one walk the set reader and set validation share.

A `deactivate`, `protect`, `activate` or `delete` line names a statement by its
path. `meta_target` walks the path's tokens through the structure tree, read
only, and says where the walk ends: at a container, at a list entry after its
whole key, at a leaf, leaf-list or flag before its value, at a list's keyword
(a homogeneous list is tagged whole, another needs its entry's name), at a
leaf's value, inside an entry's key, or nowhere the tree places. The set
reader places the tag where the walk says (`junoscfg.convert.input.set_input`);
set validation refuses a line the device cannot tag
(`junoscfg.validate.SetValidator`). The QFX5120 25.2R2-S1.5 refuses a
verb before a list's name and on one value of a leaf-list (probe D5 and A2,
`tests/data/device/probes/qfx5120-25.2R2-S1.5/2026-10-16.json`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from junoscfg.display.constants import (
    entry_keys,
    is_transparent_list_key,
    key_is_positional,
    passes_tag_to_child,
    schema_child,
    statement_children,
    statement_key,
)
from junoscfg.input import set_token_value

#: Where a walk ends. `container`, `entry`, `leaf`, `whole-list`: a statement
#: the device can tag (a leaf here is a leaf, a leaf-list or a flag before its
#: value; a whole list is one the XSD marks `homogeneous`, as port-mirroring's
#: `routing-instance`, which the device deactivates whole, deactivate6.txt).
#: `list`: another list's keyword without its entry's name (the device refuses
#: `protect policy-options policy-statement`, probe D5); `merged`: a container
#: Junos writes merged with each child and never tags (`family`, which the
#: device refuses, "missing argument"; `passes_tag_to_child`); `value`: a
#: leaf's value; `partial-key`: inside an entry's key. `unplaced`: nowhere the
#: tree places, from token `at` on, which the reader keeps whole.
MetaKind = Literal[
    "container",
    "entry",
    "leaf",
    "whole-list",
    "list",
    "merged",
    "value",
    "partial-key",
    "unplaced",
]


@dataclass(frozen=True)
class MetaStep:
    """One step of a verb line's path, as the reader places it.

    `key` is the IR key the step descends into: a container's own key, or the
    key of the list the entry sits in. `entry` is the entry's key fields; a
    container step has none. `under` is the container a hidden list sits in
    (the list a child's `t` names), whose key is not in the line.
    """

    key: str
    entry: dict[str, Any] | None = None
    under: str | None = None


@dataclass(frozen=True)
class MetaTarget:
    """Where a verb line's path ends: its `kind`, the `steps` to it, and the
    statement's `key` and tree `node` where the walk stopped. `at` is the
    first token the walk did not place, for a `value`, `partial-key` or
    `unplaced` end; `node` there is the level the walk stood at, the leaf's
    level for a `value`."""

    kind: MetaKind
    steps: tuple[MetaStep, ...]
    key: str | None = None
    node: dict[str, Any] | None = None
    at: int = 0


def read_entry_key(
    list_node: dict[str, Any], tokens: list[str], j: int
) -> tuple[dict[str, Any], int] | None:
    """The key of an entry of *list_node* read from ``tokens[j:]``, and where it ends.

    One token per positional field, in declared order; a field whose leaf is
    not `nokeyword` as `keyword value`, those fields in any order among
    themselves after the positional ones; a choice of identifiers as one of
    its keywords, with its value where the alternative is a leaf, before or
    after all of them. The device accepts `then community SAMPLE-COMM add`,
    `route-filter exact 198.51.100.0/24` and `virtual-link transit-area
    0.0.0.3 neighbor-id 10.255.255.2`, and rejects a keyword field given
    without its keyword or left out (device probe, vMX 23.2R2-S7.5). The key
    comes back in declared order, the device's. None when the tokens run out
    first, or a token is not the keyword a field needs: a statement the
    device rejects.
    """
    children = list_node.get("c", {})
    fields = list(entry_keys(list_node))
    choices = [field for field in fields if isinstance(field, tuple)]
    keyworded = [
        field
        for field in fields
        if not isinstance(field, tuple) and not key_is_positional(children.get(field))
    ]
    positional = [f for f in fields if not isinstance(f, tuple) and f not in keyworded]
    found: dict[str | tuple[str, ...], tuple[str, Any]] = {}

    def read_choices(j: int) -> int | None:
        for field in choices:
            if j >= len(tokens) or statement_key(children, tokens[j]) not in field:
                return None
            token = statement_key(children, tokens[j])
            if children.get(token, {}).get("l"):
                if j + 1 >= len(tokens):
                    return None
                found[field] = (token, set_token_value(tokens[j + 1]))
                j += 2
            else:
                found[field] = (token, [None])
                j += 1
        return j

    leads = j < len(tokens) and any(statement_key(children, tokens[j]) in c for c in choices)
    if leads and (j := read_choices(j)) is None:
        return None
    for field in positional:
        if j >= len(tokens):
            return None
        found[field] = (field, set_token_value(tokens[j]))
        j += 1
    pending = list(keyworded)
    while pending:
        if j + 1 >= len(tokens) or tokens[j] not in pending:
            return None
        pending.remove(tokens[j])
        found[tokens[j]] = (tokens[j], set_token_value(tokens[j + 1]))
        j += 2
    if not leads and (j := read_choices(j)) is None:
        return None
    return dict(found[field] for field in fields), j


def meta_target(tokens: list[str], root: dict[str, Any]) -> MetaTarget:
    """Where the verb line whose path is *tokens* ends, walked through *root*.

    Read only: the reader creates the entries the steps name and places the
    tag; the validator judges the kind. The walk resolves a token as the set
    reader always has: a statement of the level (a renamed element read as its
    keyword, a universal statement); else an entry of the level's hidden list
    (`interfaces ge-0/0/0`), of a hidden key list, or of a child's hidden list
    that the next token is a statement of; else it is unplaced.
    """
    steps: list[MetaStep] = []
    current: dict[str, Any] = root
    i = 0

    def ended(kind: MetaKind, **fields: Any) -> MetaTarget:
        return MetaTarget(kind, tuple(steps), **fields)

    while i < len(tokens):
        token = tokens[i]
        children = statement_children(current)
        schema_key = statement_key(children, token)
        if schema_key not in children:
            found = schema_child(current, schema_key, root)
            if found is not None and found.get("u"):
                children = {**children, schema_key: found}

        if schema_key not in children:
            transparent = current.get("t")
            if transparent and transparent in children:
                steps.append(MetaStep(transparent, {"name": set_token_value(token)}))
                i += 1
                if i >= len(tokens):
                    return ended("entry")
                current = children[transparent]
                continue

            hidden = _hidden_key_entry(children, tokens, i)
            if hidden is not None:
                name, cnode, key, after = hidden
                steps.append(MetaStep(name, key))
                i = after
                if i >= len(tokens):
                    return ended("entry")
                current = cnode
                continue

            if i + 1 < len(tokens):
                inner = _child_hidden_list(children, tokens[i + 1])
                if inner is not None:
                    parent_key, tc_name, tc_node = inner
                    steps.append(
                        MetaStep(tc_name, {"name": set_token_value(token)}, under=parent_key)
                    )
                    i += 1
                    current = tc_node
                    continue

            return ended("unplaced", node=current, at=i)

        child = children[schema_key]

        if i == len(tokens) - 1:
            if child.get("L"):
                return ended("whole-list" if child.get("h") else "list", key=token, node=child)
            if child.get("l") or child.get("p"):
                return ended("leaf", key=token, node=child)
            if passes_tag_to_child(child):
                return ended("merged", key=token, node=child)
            return ended("container", key=token, node=child)

        if child.get("L"):
            read = read_entry_key(child, tokens, i + 1)
            if read is None:
                return ended("partial-key", key=token, node=child, at=i)
            key, end = read
            if end < len(tokens) and not statement_children(child):
                return ended("unplaced", node=current, at=i)
            steps.append(MetaStep(token, key))
            i = end
            if i >= len(tokens):
                return ended("entry", node=child)
            current = child
            continue

        if child.get("c"):
            steps.append(MetaStep(token))
            current = child
            i += 1
            continue

        if child.get("l"):
            return ended("value", key=token, node=current, at=i + 1)

        return ended("unplaced", node=current, at=i)

    return ended("unplaced", node=current, at=i)


def _hidden_key_entry(
    children: dict[str, Any], tokens: list[str], i: int
) -> tuple[str, dict[str, Any], dict[str, Any], int] | None:
    """The entry of a hidden key list among *children* that ``tokens[i:]`` start."""
    for name, node in children.items():
        if not isinstance(node, dict) or not is_transparent_list_key(node):
            continue
        read = read_entry_key(node, tokens, i)
        if read is None:
            continue
        key, after = read
        if after < len(tokens) and not statement_children(node):
            continue
        return name, node, key, after
    return None


def _child_hidden_list(
    children: dict[str, Any], next_token: str
) -> tuple[str, str, dict[str, Any]] | None:
    """The child whose hidden list has a statement *next_token* names, if any."""
    for parent_key, parent_node in children.items():
        if not isinstance(parent_node, dict):
            continue
        tc_name = parent_node.get("t")
        if not tc_name:
            continue
        tc_node = parent_node.get("c", {}).get(tc_name)
        if not tc_node or not tc_node.get("L"):
            continue
        tc_children = statement_children(tc_node)
        if statement_key(tc_children, next_token) in tc_children:
            return parent_key, tc_name, tc_node
    return None
