"""Canonical normalization for input adapters that require schema guidance."""

from __future__ import annotations

from typing import Any

from junoscfg.display import load_schema_tree, schema_child


def normalize_leaf_lists(config: dict[str, Any]) -> None:
    """Promote scalar leaf-list values to the IR's canonical array form."""
    tree = load_schema_tree()
    _promote_leaf_list_scalars(config, tree, tree)


def _promote_leaf_list_scalars(
    obj: Any, schema_node: dict[str, Any] | None, root: dict[str, Any] | None
) -> None:
    """Walk the IR and wrap bare scalars in arrays for leaf-list fields.

    Already-array values, dicts, None, and True are left untouched.
    ``@``-prefixed operational keys are skipped. A universal statement below
    the root -- `apply-groups` in `system` -- is its root node's leaf-list.
    """
    if not isinstance(obj, dict):
        return
    for key, value in obj.items():
        if key.startswith("@"):
            continue
        child = schema_child(schema_node, key, root)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _promote_leaf_list_scalars(item, child, root)
        elif isinstance(value, dict):
            _promote_leaf_list_scalars(value, child, root)
        elif value is not None and value is not True and child and child.get("ll"):
            obj[key] = [value]
