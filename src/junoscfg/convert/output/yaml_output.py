"""Convert JSON dict IR to YAML string output."""

from __future__ import annotations

from typing import Any

import yaml

from junoscfg.convert.ir import wrap_configuration


def dict_to_yaml(config: Any, *, wrap: bool = True) -> str:
    """Render the IR dict as a YAML string.

    When *wrap* is true, wraps the config in ``{"configuration": ...}``, then
    serializes with default flow style disabled for readable block output.
    Relative path filtering may pass a scalar.
    """
    return yaml.dump(
        wrap_configuration(config) if wrap else config,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
