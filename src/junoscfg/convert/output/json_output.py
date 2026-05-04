"""Convert JSON dict IR to JSON string output."""

from __future__ import annotations

import json
from typing import Any

from junoscfg.convert.ir import wrap_configuration


def dict_to_json(config: dict[str, Any]) -> str:
    """Render the IR dict as a Junos JSON string.

    Wraps the config in ``{"configuration": ...}`` and serializes
    with 4-space indentation.  Applies native-format normalization
    so the output can be loaded on a Junos device.
    """
    config = _native_groups(config)
    _normalize_presence_flags(config)
    config = _ensure_name_first(config)
    return json.dumps(wrap_configuration(config), indent=4) + "\n"


def _ensure_name_first(obj: Any) -> Any:
    """Walk the IR and move 'name' to be the first non-@ key in each list-entry dict.

    Junos JSON requires the identifier key to appear first in named-list
    array entries. Operational-attribute keys (starting with '@') may precede it.
    """
    if isinstance(obj, list):
        return [_ensure_name_first(item) for item in obj]
    if isinstance(obj, dict):
        if "name" in obj:
            non_at_keys = [k for k in obj if not k.startswith("@")]
            if non_at_keys and non_at_keys[0] != "name":
                at_keys = {k: v for k, v in obj.items() if k.startswith("@")}
                rest = {k: v for k, v in obj.items() if not k.startswith("@") and k != "name"}
                reordered = {**at_keys, "name": obj["name"], **rest}
                return {k: _ensure_name_first(v) for k, v in reordered.items()}
        return {k: _ensure_name_first(v) for k, v in obj.items()}
    return obj


def _native_groups(config: dict[str, Any]) -> dict[str, Any]:
    """Unwrap the ``groups`` transparent container for native Junos JSON.

    The set/structured parsers produce ``"groups": {"group": [...]}``,
    but native Junos JSON uses ``"groups": [...]`` directly.  All other
    transparent containers (interfaces, routing-instances, vlans) keep
    their wrapper keys — ``groups`` is the only exception.
    """
    if "groups" in config and isinstance(config["groups"], dict):
        inner = config["groups"].get("group")
        if isinstance(inner, list):
            config = {**config, "groups": inner}
    return config


def _normalize_presence_flags(obj: Any) -> None:
    """Walk the IR and normalize presence flags to ``[null]``.

    Native Junos JSON uses ``[null]`` for presence flags.  Some input
    paths produce ``true`` or ``{}`` instead — normalize them.

    Keys starting with ``@`` are operational attributes (inactive,
    replace, etc.) and are skipped — their ``true`` values are
    legitimate booleans, not presence flags.
    """
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if key.startswith("@"):
                continue
            value = obj[key]
            if value is True or (isinstance(value, dict) and not value):
                obj[key] = [None]
            elif isinstance(value, (dict, list)):
                _normalize_presence_flags(value)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if item is True:
                obj[i] = [None]
            elif isinstance(item, dict):
                _normalize_presence_flags(item)
