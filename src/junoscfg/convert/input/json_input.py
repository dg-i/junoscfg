"""Read the Junos JSON object, from JSON text or from YAML text, into the IR.

`ir_from_junos_json_object` is the reader's object stage. The format ``json``
parses JSON text into it (`json_to_dict`), ``yaml-new`` parses YAML text
(`junos_yaml_to_dict`); both then read the same object the same way, with none
of the ``yaml`` reader's metadata cleanup or leaf-list promotion
(spec conversion/junos-json-yaml).
"""

from __future__ import annotations

import json
from typing import Any

import yaml

from junoscfg.convert.ir import find_configuration, unshared
from junoscfg.input import find_non_json_value


def ir_from_junos_json_object(data: Any, *, label: str) -> dict[str, Any]:
    """The IR of a parsed Junos JSON object: its ``configuration`` content.

    Accepts the wrappers `find_configuration` does (``rpc-reply``, bare content).

    Raises:
        ValueError: If *data* holds no configuration dict; *label* names the
            input's text format in the message.
    """
    config = find_configuration(data)
    if config is None:
        raise ValueError(f"No 'configuration' key found in {label} input.")
    return config


def json_to_dict(source: str) -> dict[str, Any]:
    """Parse a JSON configuration string into the IR dict.

    Returns the configuration content dict (the value inside
    ``{"configuration": ...}``).

    Raises:
        ValueError: If the JSON holds a value nested deeper than 64 levels
            (`find_non_json_value`), named by its path, never by its value,
            before junoscfg's own walks meet it; or if it does not contain a
            configuration dict.
    """
    data = json.loads(source)
    found = find_non_json_value(data)
    if found is not None:
        raise ValueError(found.read_refusal("JSON"))
    return ir_from_junos_json_object(data, label="JSON")


def junos_yaml_to_dict(source: str) -> dict[str, Any]:
    """Parse a yaml-new configuration string, the Junos JSON object in YAML, into the IR.

    The text is read with PyYAML's ``safe_load`` (YAML 1.1 implicit types, as
    the ``yaml`` format reads it): an unquoted ``on`` is a boolean, ``010`` the
    number 8, as the writer's quoting expects.

    Raises:
        yaml.YAMLError: If the text is not YAML.
        ValueError: If the document holds a value no JSON document can hold
            (a timestamp, a key that is not a string, binary data, a set), a
            cycle, or a value nested deeper than 64 levels
            (`find_non_json_value`), named by its kind and path, never by its
            value; or if it holds no configuration dict.

    A mapping or list shared through an alias is read written out, as JSON
    spells it, however often it is reused: the IR holds no object twice.
    """
    data = yaml.safe_load(source)
    found = find_non_json_value(data)
    if found is not None:
        raise ValueError(found.read_refusal("YAML"))
    return ir_from_junos_json_object(unshared(data), label="YAML")
