"""Convert JSON dict IR to YAML string output."""

from __future__ import annotations

from typing import Any

import yaml

from junoscfg.convert.ir import wrap_configuration


def dict_to_yaml(config: Any, *, wrap: bool = True, below: list[str] | None = None) -> str:
    """Render the IR dict as a YAML string.

    When *wrap* is true, wraps the config in ``{"configuration": ...}``, then
    serializes with default flow style disabled for readable block output.
    With *below*, *config* is the IR along that path and the value at the
    path is written (a relative selection, possibly a scalar or null).
    """
    if below is not None:
        for key in below:
            config = config[key]
        wrap = False
    return yaml.dump(
        wrap_configuration(config) if wrap else config,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
