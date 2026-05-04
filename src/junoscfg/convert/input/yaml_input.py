"""Convert YAML configuration to the JSON dict IR."""

from __future__ import annotations

from typing import Any

import yaml

from junoscfg.convert.ir import find_configuration
from junoscfg.display.constants import load_schema_tree

# Meta key prefixes stripped before conversion (Ansible inventory artifacts).
_STRIP_PREFIXES = ("_ansible", "_meta_")


def yaml_to_dict(source: str) -> dict[str, Any]:
    """Parse a YAML configuration string into the IR dict.

    Strips ``_ansible_*`` and ``_meta_*`` meta keys before returning.
    Promotes bare scalars to single-element arrays for leaf-list fields so
    the IR matches the Junos JSON expectation (e.g. ``extended-vni-list``).

    Returns the configuration content dict (the value inside
    ``{"configuration": ...}``).

    Raises:
        ValueError: If the YAML does not contain a configuration dict.
    """
    data = yaml.safe_load(source)
    if not isinstance(data, dict) or not data:
        raise ValueError("YAML input is empty or not a mapping.")
    cleaned = _strip_meta_keys(data)
    config = find_configuration(cleaned)
    if config is None:
        raise ValueError("No 'configuration' key found in YAML input.")
    _promote_leaf_list_scalars(config, load_schema_tree())
    return config


def _promote_leaf_list_scalars(obj: Any, schema_node: dict[str, Any] | None) -> None:
    """Walk the IR and wrap bare scalars in arrays for leaf-list fields.

    YAML may represent a leaf-list value as a plain scalar (e.g.
    ``extended-vni-list: 3001000-3001100``). When the schema marks the field
    as a leaf-list (``ll``), Junos JSON expects an array — wrap it here.

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


def _strip_meta_keys(obj: Any) -> Any:
    """Recursively remove keys matching ``_ansible*`` or ``_meta_*`` prefixes."""
    if isinstance(obj, dict):
        return {
            k: _strip_meta_keys(v)
            for k, v in obj.items()
            if not any(k.startswith(p) for p in _STRIP_PREFIXES)
        }
    if isinstance(obj, list):
        return [_strip_meta_keys(item) for item in obj]
    return obj
