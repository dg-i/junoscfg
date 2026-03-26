"""Convert Junos JSON/XML configurations to standard YAML format.

The output is a 1:1 structural mapping of Junos JSON — arrays with ``name``
fields, ``@`` attribute keys, and ``[null]`` presence markers are all preserved
exactly as they appear in the JSON representation.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, TextIO

import yaml

if TYPE_CHECKING:
    from lxml import etree


def json_to_yaml(source: str | TextIO) -> str:
    """Convert Junos JSON configuration to standard YAML format."""
    text = source.read() if hasattr(source, "read") else str(source)  # type: ignore[union-attr]

    data = json.loads(text)
    if not data:
        return ""
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


def xml_to_yaml(source: str | TextIO) -> str:
    """Convert Junos XML configuration to standard YAML format.

    Requires the ``lxml`` package (install via ``pip install junoscfg[xml]``).
    """
    from junoscfg.display.xml_helpers import find_xml_configuration

    _ensure_xml_imports()

    text = source.read() if hasattr(source, "read") else str(source)  # type: ignore[union-attr]

    root = _etree_mod.fromstring(text.encode())  # noqa: S320
    config_el = find_xml_configuration(root)
    if config_el is None:
        return ""

    result = {"configuration": _xml_element_to_dict(config_el)}
    return yaml.dump(result, default_flow_style=False, allow_unicode=True, sort_keys=False)


# ------------------------------------------------------------------
# Lazy XML imports — loaded once on first xml_to_yaml() call
# ------------------------------------------------------------------

_etree_mod: Any = None
_local_name: Any = None
_filtered_children: Any = None
_FLAT_ENTRY_ELEMENTS: Any = None


def _ensure_xml_imports() -> None:
    """Lazily import lxml and XML helpers on first use."""
    global _etree_mod, _local_name, _filtered_children, _FLAT_ENTRY_ELEMENTS  # noqa: PLW0603
    if _etree_mod is not None:
        return
    from lxml import etree as _etree

    from junoscfg.display.constants import FLAT_ENTRY_ELEMENTS
    from junoscfg.display.xml_helpers import filtered_children, local_name

    _etree_mod = _etree
    _local_name = local_name
    _filtered_children = filtered_children
    _FLAT_ENTRY_ELEMENTS = FLAT_ENTRY_ELEMENTS


# ------------------------------------------------------------------
# XML → JSON-equivalent dict internals
# ------------------------------------------------------------------


def _get_inactive_attrs(element: etree._Element) -> dict[str, Any] | None:
    """Check if element has inactive attribute, return @ dict if so."""
    if element.get("inactive") == "inactive":
        return {"inactive": True}
    for attr_name, attr_value in element.attrib.items():
        if attr_name.endswith("}inactive") and attr_value == "inactive":
            return {"inactive": True}
    return None


def _xml_element_to_dict(element: etree._Element) -> dict[str, Any]:
    """Convert an XML element and its children to a Junos JSON-equivalent dict."""
    children = _filtered_children(element)
    if not children:
        return {}

    # Group children by tag name to detect lists
    groups: dict[str, list[etree._Element]] = {}
    order: list[str] = []
    for child in children:
        name = _local_name(child)
        if name == "undocumented":
            for undoc_child in child:
                uname = _local_name(undoc_child)
                if uname != "comment":
                    if uname not in groups:
                        groups[uname] = []
                        order.append(uname)
                    groups[uname].append(undoc_child)
            continue
        if name not in groups:
            groups[name] = []
            order.append(name)
        groups[name].append(child)

    result: dict[str, Any] = {}
    for name in order:
        elements = groups[name]
        if len(elements) == 1:
            if _should_be_array(elements[0]):
                result[name] = _xml_single_as_array(elements[0])
            else:
                result[name] = _xml_single_element(elements[0])
        else:
            result[name] = _xml_multi_elements(name, elements)

    return result


def _should_be_array(element: etree._Element) -> bool:
    """Check if a single XML element should be wrapped in a JSON array.

    In Junos JSON, list-type elements are always arrays even with a single
    entry. Without YANG schema, we detect these by heuristics:
    - Has a ``name`` child → named entry (keyed list)
    - Tag is a known flat entry element (route-filter, prefix-list-filter)
    - Has a ``community-name`` child → community action entry
    """
    children = _filtered_children(element)
    tag = _local_name(element)

    if tag in _FLAT_ENTRY_ELEMENTS:
        return True

    if children:
        child_names = {_local_name(c) for c in children}
        if "name" in child_names:
            return True
        if "community-name" in child_names:
            return True

    return False


def _xml_single_as_array(element: etree._Element) -> list[dict[str, Any]]:
    """Convert a single XML element to a 1-element array of dicts."""
    children = _filtered_children(element)
    inactive_attrs = _get_inactive_attrs(element)
    entry = _xml_children_to_dict(children) if children else {}
    if inactive_attrs:
        entry["@"] = inactive_attrs
    return [entry]


def _xml_single_element(element: etree._Element) -> Any:
    """Convert a single XML element to a Junos JSON-equivalent value."""
    children = _filtered_children(element)
    inactive_attrs = _get_inactive_attrs(element)

    if not children:
        # Leaf element
        text = (element.text or "").strip()
        if text:
            value = _coerce_value(text)
            if inactive_attrs:
                return {_local_name(element): [value], "@": inactive_attrs}
            return value
        # Empty element → presence flag [null]
        if inactive_attrs:
            return {"@": inactive_attrs}
        return [None]

    # Has sub-elements — it's a container or named entry
    child_dict = _xml_children_to_dict(children)
    if inactive_attrs:
        child_dict["@"] = inactive_attrs
    return child_dict


def _xml_multi_elements(tag_name: str, elements: list[etree._Element]) -> Any:
    """Convert multiple same-tag XML elements to a Junos JSON-equivalent value.

    Multiple same-tag siblings become a JSON array. Each element becomes
    a dict entry in the array.
    """
    # Check if these are leaf elements (no children, just text)
    all_leaf = all(not _filtered_children(el) for el in elements)

    if all_leaf:
        # Check if all are empty (presence) or all have text
        values: list[Any] = []
        for el in elements:
            text = (el.text or "").strip()
            inactive_attrs = _get_inactive_attrs(el)
            if text:
                val = _coerce_value(text)
                if inactive_attrs:
                    values.append({tag_name: [val], "@": inactive_attrs})
                else:
                    values.append(val)
            else:
                if inactive_attrs:
                    values.append({"@": inactive_attrs})
                else:
                    values.append(None)
        return values

    # Container elements → array of dicts
    result: list[dict[str, Any]] = []
    for el in elements:
        children = _filtered_children(el)
        inactive_attrs = _get_inactive_attrs(el)
        entry = _xml_children_to_dict(children) if children else {}
        if inactive_attrs:
            entry["@"] = inactive_attrs
        result.append(entry)
    return result


def _xml_children_to_dict(children: list[etree._Element]) -> dict[str, Any]:
    """Convert a list of XML child elements to a dict."""
    groups: dict[str, list[etree._Element]] = {}
    order: list[str] = []
    for child in children:
        name = _local_name(child)
        if name == "undocumented":
            for undoc_child in child:
                uname = _local_name(undoc_child)
                if uname != "comment":
                    if uname not in groups:
                        groups[uname] = []
                        order.append(uname)
                    groups[uname].append(undoc_child)
            continue
        if name not in groups:
            groups[name] = []
            order.append(name)
        groups[name].append(child)

    result: dict[str, Any] = {}
    for name in order:
        elements = groups[name]
        if len(elements) == 1:
            if _should_be_array(elements[0]):
                result[name] = _xml_single_as_array(elements[0])
            else:
                result[name] = _xml_single_element(elements[0])
        else:
            result[name] = _xml_multi_elements(name, elements)
    return result


def filter_yaml_by_path(text: str, path_tokens: list[str], *, relative: bool = False) -> str:
    """Filter YAML output to the subtree at the given path.

    Args:
        text: YAML text with ``configuration`` as the top-level key.
        path_tokens: Path components to navigate (e.g. ["system", "syslog"]).
        relative: If True, return just the subtree dict.
                  If False, wrap the subtree in the full path hierarchy.

    Returns:
        Filtered YAML text, or empty string if path not found.
    """
    from junoscfg.display.path_filter import filter_dict_by_path

    if not path_tokens:
        return text

    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        return ""

    result = filter_dict_by_path(data, path_tokens, relative=relative)
    if result is None:
        return ""

    return yaml.dump(result, default_flow_style=False, allow_unicode=True, sort_keys=False)


def _coerce_value(text: str) -> Any:
    """Coerce string to int/float if possible, for cleaner YAML output."""
    try:
        return int(text)
    except ValueError:
        pass
    try:
        f = float(text)
        if "." in text and str(f) == text:
            return f
    except ValueError:
        pass
    return text
