"""Convert XML configuration directly to the JSON dict IR."""

from __future__ import annotations

from typing import Any


def xml_to_dict(source: str) -> dict[str, Any]:
    """Parse an XML configuration string into the IR dict.

    Returns the configuration content dict (the value inside
    ``{"configuration": ...}``).

    Raises:
        ValueError: If the XML does not contain a configuration element.
    """
    from junoscfg.convert.ir import find_configuration
    from junoscfg.display import xml_to_dict as parse_xml

    config = find_configuration(parse_xml(source))
    if config is None:
        raise ValueError("No 'configuration' element found in XML input.")
    return config
