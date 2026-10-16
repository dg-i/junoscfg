"""Convert XML configuration directly to the JSON dict IR."""

from __future__ import annotations

from typing import Any


def xml_to_dict(source: str) -> dict[str, Any]:
    """Parse an XML configuration string into the IR dict.

    Returns the configuration content dict (the value inside
    ``{"configuration": ...}``).

    Raises:
        ValueError: If the XML does not contain a configuration element, or if
            its mapping holds a value nested deeper than 64 levels
            (`find_non_json_value`), named by its path, never by its value,
            before junoscfg's own walks meet it: a repeated element is a list
            and its entry, two levels for one of XML.
    """
    from junoscfg.convert.ir import find_configuration
    from junoscfg.display import xml_to_dict as parse_xml
    from junoscfg.input import find_non_json_value

    data = parse_xml(source)
    found = find_non_json_value(data)
    if found is not None:
        raise ValueError(found.read_refusal("XML"))
    config = find_configuration(data)
    if config is None:
        raise ValueError("No 'configuration' element found in XML input.")
    return config
