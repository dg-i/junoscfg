"""Shared XML helper functions for Junos configuration converters."""

from __future__ import annotations

from lxml import etree


def local_name(element: etree._Element) -> str:
    """Get element name without namespace prefix."""
    return etree.QName(element).localname


def filtered_children(element: etree._Element) -> list[etree._Element]:
    """Get child elements, filtering out comments."""
    return [c for c in element if local_name(c) != "comment"]


def find_xml_configuration(root: etree._Element) -> etree._Element | None:
    """Locate the <configuration> element, handling rpc-reply wrappers."""
    if local_name(root) == "configuration":
        return root
    for el in root.iter():
        if local_name(el) == "configuration":
            return el
    return None
