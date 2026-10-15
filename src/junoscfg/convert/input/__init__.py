"""Input converters: parse various formats into the JSON dict IR."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

_JCMD_PREFIX = "junos-configuration-metadata:"


def to_dict(
    source: str, fmt: str, diagnostic_sink: Callable[[str, str], None] | None = None
) -> dict[str, Any]:
    """Dispatch to the appropriate input converter.

    Args:
        source: Configuration text.
        fmt: Format name, a key of
             :data:`~junoscfg.convert.formats.FORMAT_IMPLEMENTATIONS`
             (``"json"``, ``"yaml"``, ``"yaml-new"``, ``"xml"``, ``"set"``,
             ``"structured"``).
        diagnostic_sink: Receives each reader warning as the path it concerns
            and its message: what structured text holds that yields no
            statement. Without one, nothing is reported.

    Returns:
        The configuration content dict (without the ``"configuration"``
        wrapper — i.e. the value inside ``{"configuration": ...}``).
        Documented variant annotation spellings are normalized to the
        canonical forms (see :func:`_normalize_annotation`).
    """
    from junoscfg.convert.formats import implementation

    implemented = implementation(fmt, "input")
    if implemented == "junos-json":
        from junoscfg.convert.input.json_input import json_to_dict

        ir = json_to_dict(source)
    elif implemented == "junos-yaml":
        from junoscfg.convert.input.json_input import junos_yaml_to_dict

        ir = junos_yaml_to_dict(source)
    elif implemented == "ir-yaml":
        from junoscfg.convert.input.yaml_input import yaml_to_dict

        ir = yaml_to_dict(source)
    elif implemented == "xml":
        from junoscfg.convert.input.xml_input import xml_to_dict

        ir = xml_to_dict(source)
    elif implemented == "set":
        from junoscfg.convert.input.set_input import set_to_dict

        ir = set_to_dict(source)
    elif implemented == "structured":
        from junoscfg.convert.input.structured_input import structured_to_dict

        ir = structured_to_dict(source, diagnostic_sink)
    else:
        raise ValueError(f"Unknown implementation {implemented!r} for input format {fmt}")

    if implemented in {"ir-yaml", "xml"}:
        from junoscfg.convert.input.normalization import normalize_leaf_lists

        normalize_leaf_lists(ir)
    _normalize_annotations(ir)
    _refuse_malformed_records(ir)
    return ir


def _refuse_malformed_records(node: Any) -> None:
    """Refuse a record of kept statements no writer could print as it stands.

    JSON and YAML can carry the record (`UNPLACED_STATEMENTS`) as written by
    junoscfg or by hand; the writers print its statements verbatim, so one
    with a line break or an unquoted brace would write lines or blocks the
    input never held. The message names no statement.
    """
    from junoscfg.display import UNPLACED_STATEMENTS, unplaced_record_problem

    if isinstance(node, dict):
        for key, value in node.items():
            if key == UNPLACED_STATEMENTS:
                problem = unplaced_record_problem(value)
                if problem is not None:
                    raise ValueError(f"Invalid input: {problem}")
            else:
                _refuse_malformed_records(value)
    elif isinstance(node, list):
        for item in node:
            _refuse_malformed_records(item)


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
