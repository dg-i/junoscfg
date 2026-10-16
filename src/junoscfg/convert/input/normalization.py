"""Canonical normalization for input adapters that require schema guidance."""

from __future__ import annotations

from typing import Any

from junoscfg.display import load_schema_tree, schema_child, statement_key


def normalize_names(config: dict[str, Any], *, leaf_lists: bool = False) -> None:
    """Key the IR as the structure tree does, in place; with *leaf_lists*, also
    promote scalar leaf-list values to the IR's canonical array form.

    JSON, yaml-new and YAML may carry the element name the device writes in
    XML and JSON where the tree's key is the CLI keyword (`ieee-802.3ad` for
    `802.3ad`, `end-range` for `to`): the IR holds the keyword, as the set,
    curly and XML readers give it, so one configuration has one IR (spec
    schema-pipeline/conversion-hints).
    """
    tree = load_schema_tree()
    _normalize(config, tree, tree, leaf_lists)


def _normalize(
    obj: Any, schema_node: dict[str, Any] | None, root: dict[str, Any] | None, leaf_lists: bool
) -> None:
    """Walk the IR: rename keys to the tree's, then descend; wrap leaf-list scalars.

    Already-array values, dicts, None, and True are left as they are.
    ``@``-prefixed operational keys are skipped; a statement's own ``@<key>``
    follows its rename. A universal statement below the root -- `apply-groups`
    in `system` -- is its root node's leaf-list. A transparent container held
    as its child's list (`groups` in the Junos JSON object) is read as that
    child's entries.
    """
    if not isinstance(obj, dict):
        return
    if schema_node is not None:
        _rename_keys(obj, schema_node.get("c") or {})
    for key, value in obj.items():
        if key.startswith("@"):
            continue
        child = schema_child(schema_node, key, root)
        if isinstance(value, list):
            item_schema = child
            if child is not None and "t" in child and "L" not in child and "l" not in child:
                item_schema = child.get("c", {}).get(child["t"], child)
            for item in value:
                if isinstance(item, dict):
                    _normalize(item, item_schema, root, leaf_lists)
        elif isinstance(value, dict):
            _normalize(value, child, root, leaf_lists)
        elif leaf_lists and value is not None and value is not True and child and child.get("ll"):
            obj[key] = [value]


def _rename_keys(obj: dict[str, Any], children: dict[str, Any]) -> None:
    """Rename *obj*'s element names to the tree's keys, keeping key order."""
    renamed = {
        key: name
        for key in obj
        if not key.startswith("@")
        and (name := statement_key(children, key)) != key
        and name not in obj
    }
    if not renamed:
        return
    items = list(obj.items())
    obj.clear()
    for key, value in items:
        if key in renamed:
            key = renamed[key]
        elif key.startswith("@") and key[1:] in renamed:
            key = "@" + renamed[key[1:]]
        obj[key] = value
