"""Output converters: render the JSON dict IR into various formats."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


def from_dict(
    config: Any,
    fmt: str,
    *,
    wrap: bool = True,
    diagnostic_sink: Callable[[str], None] | None = None,
) -> str:
    """Dispatch to the appropriate output converter.

    Args:
        config: The configuration content (without the ``"configuration"``
                wrapper). Relative path filtering may supply a scalar.
        fmt: Format name (``"json"``, ``"yaml"``, ``"xml"``, ``"set"``,
             ``"structured"``).
        wrap: Wrap JSON and YAML output in a top-level ``"configuration"``
              mapping. Ignored by the other renderers.
        diagnostic_sink: Optional receiver for renderer diagnostics. The
            caller owns any terminal or log rendering.

    Returns:
        The rendered configuration as a string.
    """
    if fmt == "json":
        from junoscfg.convert.output.json_output import dict_to_json

        return dict_to_json(config, wrap=wrap)
    elif fmt == "yaml":
        from junoscfg.convert.output.yaml_output import dict_to_yaml

        return dict_to_yaml(config, wrap=wrap)
    elif fmt == "xml":
        raise NotImplementedError("XML output conversion is not yet implemented.")
    elif fmt == "set":
        from junoscfg.convert.output.set_output import dict_to_set

        return dict_to_set(config)
    elif fmt == "structured":
        from junoscfg.convert.output.structured_output import dict_to_structured

        return dict_to_structured(config, diagnostic_sink=diagnostic_sink)
    else:
        raise ValueError(f"Unknown output format: {fmt}")
