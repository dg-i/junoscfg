"""Input converters: parse various formats into the JSON dict IR."""

from __future__ import annotations

from typing import Any

_JCMD_PREFIX = "junos-configuration-metadata:"


def to_dict(source: str, fmt: str) -> dict[str, Any]:
    """Dispatch to the appropriate input converter.

    Args:
        source: Configuration text.
        fmt: Format name (``"json"``, ``"yaml"``, ``"xml"``, ``"set"``,
             ``"structured"``).

    Returns:
        The configuration content dict (without the ``"configuration"``
        wrapper — i.e. the value inside ``{"configuration": ...}``).
        Documented variant annotation spellings are normalized to the
        canonical forms (see :func:`_normalize_annotation`).
    """
    if fmt == "json":
        from junoscfg.convert.input.json_input import json_to_dict

        ir = json_to_dict(source)
    elif fmt == "yaml":
        from junoscfg.convert.input.yaml_input import yaml_to_dict

        ir = yaml_to_dict(source)
    elif fmt == "xml":
        from junoscfg.convert.input.xml_input import xml_to_dict

        ir = xml_to_dict(source)
    elif fmt == "set":
        from junoscfg.convert.input.set_input import set_to_dict

        ir = set_to_dict(source)
    elif fmt == "structured":
        from junoscfg.convert.input.structured_input import structured_to_dict

        ir = structured_to_dict(source)
    else:
        raise ValueError(f"Unknown input format: {fmt}")

    _normalize_annotations(ir)
    return ir


def _normalize_annotation(attrs: dict[str, Any]) -> None:
    """Canonicalize documented variant spellings inside one annotation dict.

    Junos documentation and devices use several encodings for the same
    operations. Normalizing at parse time means every downstream consumer
    (and every output format) sees the canonical spellings:

    - ``"inactive": "inactive"``          -> ``"inactive": true``
    - ``"protect": true/false``           -> ``"protect": "protect"`` / removed
    - ``"active": true/false``            -> ``"active": "active"`` / ``"inactive": true``
    - ``"junos-configuration-metadata:*"``-> folded into the plain key

    Unknown attributes (``operation: create/merge``, ``junos:*`` metadata,
    ``comment`` content, ...) are left untouched.
    """
    # Fold YANG (jcmd module) metadata keys into their plain equivalents;
    # an existing plain key wins over the jcmd spelling.
    for plain in ("active", "protect", "comment"):
        jcmd_key = f"{_JCMD_PREFIX}{plain}"
        if jcmd_key in attrs:
            attrs.setdefault(plain, attrs.pop(jcmd_key))

    if attrs.get("inactive") == "inactive":
        attrs["inactive"] = True

    if attrs.get("protect") is True:
        attrs["protect"] = "protect"
    elif attrs.get("protect") is False:
        del attrs["protect"]

    active = attrs.get("active")
    if active is True:
        attrs["active"] = "active"
    elif active is False:
        del attrs["active"]
        attrs.setdefault("inactive", True)


def _normalize_annotations(node: Any) -> None:
    """Recursively normalize all annotation dicts (``"@"`` / ``"@leaf"``) in the IR."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key.startswith("@") and isinstance(value, dict):
                _normalize_annotation(value)
            else:
                _normalize_annotations(value)
    elif isinstance(node, list):
        for item in node:
            _normalize_annotations(item)
