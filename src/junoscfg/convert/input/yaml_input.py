"""Convert YAML configuration to the JSON dict IR."""

from __future__ import annotations

from typing import Any

import yaml

from junoscfg.convert.ir import find_configuration

# Meta key prefixes stripped before conversion (Ansible inventory artifacts).
_STRIP_PREFIXES = ("_ansible", "_meta_")


def yaml_to_dict(source: str) -> dict[str, Any]:
    """Parse a YAML configuration string into the IR dict.

    Strips ``_ansible_*`` and ``_meta_*`` meta keys before returning.

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
