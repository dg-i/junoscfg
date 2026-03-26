"""Convert JSON configuration to the JSON dict IR."""

from __future__ import annotations

import json
from typing import Any

from junoscfg.convert.ir import find_configuration


def json_to_dict(source: str) -> dict[str, Any]:
    """Parse a JSON configuration string into the IR dict.

    Returns the configuration content dict (the value inside
    ``{"configuration": ...}``).

    Raises:
        ValueError: If the JSON does not contain a configuration dict.
    """
    data = json.loads(source)
    config = find_configuration(data)
    if config is None:
        raise ValueError("No 'configuration' key found in JSON input.")
    return config
