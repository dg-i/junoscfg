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
    return json.dumps(wrap_configuration(config), indent=4) + "\n"
