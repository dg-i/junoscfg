"""Canonical normalization shared by every input adapter."""

from __future__ import annotations

from typing import Any

from junoscfg.display import load_schema_tree


def normalize_leaf_lists(config: dict[str, Any]) -> None:
    """Promote scalar leaf-list values to the IR's canonical array form."""
    _promote_leaf_list_scalars(config, load_schema_tree())


def _promote_leaf_list_scalars(obj: Any, schema_node: dict[str, Any] | None) -> None:
    """Walk the IR and wrap bare scalars in arrays for leaf-list fields.

    Already-array values, dicts, None, and True are left untouched.
    ``@``-prefixed operational keys are skipped.
    """
    if not isinstance(obj, dict):
        return
    children = schema_node.get("c", {}) if schema_node else {}
    for key, value in obj.items():
        if key.startswith("@"):
            continue
        child = children.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _promote_leaf_list_scalars(item, child)
        elif isinstance(value, dict):
            _promote_leaf_list_scalars(value, child)
        elif value is not None and value is not True and child and child.get("ll"):
            obj[key] = [value]
