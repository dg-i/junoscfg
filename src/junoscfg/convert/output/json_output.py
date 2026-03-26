"""Convert JSON dict IR to JSON string output."""

from __future__ import annotations

import json
from typing import Any

from junoscfg.convert.ir import wrap_configuration


def dict_to_json(config: dict[str, Any]) -> str:
    """Render the IR dict as a Junos JSON string.

    Wraps the config in ``{"configuration": ...}`` and serializes
    with 4-space indentation.
    """
    config = _native_groups(config)
    return json.dumps(wrap_configuration(config), indent=4) + "\n"


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
