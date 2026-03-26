"""Convert JSON dict IR to YAML string output."""

from __future__ import annotations

from typing import Any

import yaml

from junoscfg.convert.ir import wrap_configuration


def dict_to_yaml(config: dict[str, Any]) -> str:
    """Render the IR dict as a YAML string.

    Wraps the config in ``{"configuration": ...}`` and serializes
    with default flow style disabled for readable block output.
    """
    return yaml.dump(
        wrap_configuration(config),
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
