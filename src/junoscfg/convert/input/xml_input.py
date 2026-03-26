"""Convert XML configuration to the JSON dict IR via XML→YAML bridge."""

from __future__ import annotations

from typing import Any


def xml_to_dict(source: str) -> dict[str, Any]:
    """Parse an XML configuration string into the IR dict.

    Uses the XML→YAML bridge (``xml_to_yaml()``) to convert to YAML first,
    then parses the YAML into the dict IR via ``yaml_to_dict()``.

    Returns the configuration content dict (the value inside
    ``{"configuration": ...}``).

    Raises:
        ValueError: If the XML does not contain a configuration element.
    """
    from junoscfg.convert.input.yaml_input import yaml_to_dict
    from junoscfg.display.to_yaml import xml_to_yaml

    yaml_content = xml_to_yaml(source)
    if not yaml_content:
        raise ValueError("No 'configuration' element found in XML input.")
    return yaml_to_dict(yaml_content)
