"""Input converters: parse various formats into the JSON dict IR."""

from __future__ import annotations

from typing import Any


def to_dict(source: str, fmt: str) -> dict[str, Any]:
    """Dispatch to the appropriate input converter.

    Args:
        source: Configuration text.
        fmt: Format name (``"json"``, ``"yaml"``, ``"xml"``, ``"set"``,
             ``"structured"``).

    Returns:
        The configuration content dict (without the ``"configuration"``
        wrapper — i.e. the value inside ``{"configuration": ...}``).
    """
    if fmt == "json":
        from junoscfg.convert.input.json_input import json_to_dict

        return json_to_dict(source)
    elif fmt == "yaml":
        from junoscfg.convert.input.yaml_input import yaml_to_dict

        return yaml_to_dict(source)
    elif fmt == "xml":
        from junoscfg.convert.input.xml_input import xml_to_dict

        return xml_to_dict(source)
    elif fmt == "set":
        from junoscfg.convert.input.set_input import set_to_dict

        return set_to_dict(source)
    elif fmt == "structured":
        from junoscfg.convert.input.structured_input import structured_to_dict

        return structured_to_dict(source)
    else:
        raise ValueError(f"Unknown input format: {fmt}")
