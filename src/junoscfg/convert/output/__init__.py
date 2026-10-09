"""Output converters: render the JSON dict IR into various formats."""

from __future__ import annotations

from typing import Any


def from_dict(config: dict[str, Any], fmt: str) -> str:
    """Dispatch to the appropriate output converter.

    Args:
        config: The configuration content dict (without the
                ``"configuration"`` wrapper).
        fmt: Format name (``"json"``, ``"yaml"``, ``"xml"``, ``"set"``,
             ``"structured"``).

    Returns:
        The rendered configuration as a string.
    """
    if fmt == "json":
        from junoscfg.convert.output.json_output import dict_to_json

        return dict_to_json(config)
    elif fmt == "yaml":
        from junoscfg.convert.output.yaml_output import dict_to_yaml

        return dict_to_yaml(config)
    elif fmt == "xml":
        from junoscfg.convert.output.xml_output import dict_to_xml

        return dict_to_xml(config)
    elif fmt == "set":
        from junoscfg.convert.output.set_output import dict_to_set

        return dict_to_set(config)
    elif fmt == "structured":
        from junoscfg.convert.output.structured_output import dict_to_structured

        return dict_to_structured(config)
    else:
        raise ValueError(f"Unknown output format: {fmt}")
