"""Convert YAML configuration to the JSON dict IR."""

from __future__ import annotations

from typing import Any

import yaml

from junoscfg.convert.ir import find_configuration
from junoscfg.input import find_non_json_value

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
        ValueError: If the YAML does not contain a configuration dict, or if
            what the meta-key cleanup walks holds a cycle or a value nested
            deeper than 64 levels (`find_non_json_value`), named by its kind
            and path, never by its value: junoscfg's own recursion stops there.
    """
    data = yaml.safe_load(source)
    if not isinstance(data, dict) or not data:
        raise ValueError("YAML input is empty or not a mapping.")
    found = find_non_json_value(data, scalars=False, unwalked=_STRIP_PREFIXES)
    if found is not None:
        raise ValueError(f"Invalid input: a YAML {found.kind} {found.where} {found.reason}")
    cleaned = _strip_meta_keys(data)
    config = find_configuration(cleaned)
    if config is None:
        raise ValueError("No 'configuration' key found in YAML input.")
    return config


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
