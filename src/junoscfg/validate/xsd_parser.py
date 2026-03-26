"""Parse XSD schema into a SchemaNode tree.

Two-pass approach:
1. Collect all named xsd:complexType definitions into a lookup dict
2. Walk from <xsd:element name="configuration">, building SchemaNode tree
"""

from __future__ import annotations

from lxml import etree

from junoscfg.validate.schema_node import Combinator, SchemaNode

XSD_NS = "http://www.w3.org/2001/XMLSchema"
JUNOS_NS = "http://xml.juniper.net/junos/21.4R0/junos"

# Elements to skip during parsing
_SKIP_REFS = {"undocumented", f"{{{JUNOS_NS}}}comment", "junos:comment"}
_SKIP_NAMES = {"undocumented", "apply-advanced", "junos:comment"}

# Named types that are simple string wrappers (leaf types)
_STRING_BASE_TYPES = {
    "xsd:string",
    "xsd:int",
    "xsd:unsignedInt",
    "xsd:unsignedLong",
    "xsd:long",
    "xsd:boolean",
}


def _xsd(tag: str) -> str:
    """Create a fully qualified XSD tag name."""
    return f"{{{XSD_NS}}}{tag}"


def parse_xsd(xsd_text: str) -> SchemaNode:
    """Parse XSD text into a SchemaNode tree rooted at 'configuration'.

    Args:
        xsd_text: The XSD schema XML as a string.

    Returns:
        SchemaNode tree rooted at the 'configuration' element.

    Raises:
        ValueError: If 'configuration' element is not found.
    """
    root_el = etree.fromstring(xsd_text.encode("utf-8"))

    # Pass 1: collect named complexType definitions
    type_map: dict[str, etree._Element] = {}
    for ct in root_el.iter(_xsd("complexType")):
        name = ct.get("name")
        if name:
            type_map[name] = ct

    # Also collect named simpleType definitions
    simple_type_map: dict[str, etree._Element] = {}
    for st in root_el.iter(_xsd("simpleType")):
        name = st.get("name")
        if name:
            simple_type_map[name] = st

    # Pass 2: find configuration element and build tree
    config_el = None
    for el in root_el.iter(_xsd("element")):
        if el.get("name") == "configuration":
            config_el = el
            break

    if config_el is None:
        raise ValueError("No <xsd:element name='configuration'> found in XSD")

    return _build_node(config_el, type_map, simple_type_map, set())


def _build_node(
    element: etree._Element,
    type_map: dict[str, etree._Element],
    simple_type_map: dict[str, etree._Element],
    seen_types: set[str],
) -> SchemaNode:
    """Build a SchemaNode from an xsd:element."""
    name = element.get("name", "")

    # Extract flags and metadata from annotation/appinfo
    flags = set()
    is_key = False
    is_mandatory = False
    pattern = None
    pattern_negated = False

    appinfo = element.find(f"{_xsd('annotation')}/{_xsd('appinfo')}")
    if appinfo is not None:
        for flag_el in appinfo.iter("flag"):
            flag_text = (flag_el.text or "").strip()
            if flag_text:
                flags.add(flag_text)
            if flag_text == "identifier":
                is_key = True
            elif flag_text == "mandatory":
                is_mandatory = True

        # Also check for <identifier/> element
        if appinfo.find("identifier") is not None:
            is_key = True

        # Check for match/pattern
        match_el = appinfo.find("match")
        if match_el is not None:
            pattern_el = match_el.find("pattern")
            if pattern_el is not None and pattern_el.text:
                pattern = pattern_el.text.strip()
                if pattern.startswith("!"):
                    pattern_negated = True
                    pattern = pattern[1:]

    # Determine cardinality
    is_list = element.get("maxOccurs") == "unbounded"

    # Determine type
    type_attr = element.get("type", "")

    # Check for $-prefixed names (freeform leaf)
    if name.startswith("$"):
        return SchemaNode(
            name=name,
            is_leaf=True,
            is_key=is_key,
            is_list=is_list,
            is_mandatory=is_mandatory,
            flags=flags,
            pattern=pattern,
            pattern_negated=pattern_negated,
        )

    # Check if it's a simple XSD type (leaf)
    if type_attr in _STRING_BASE_TYPES:
        enums = _extract_enums_from_element(element)
        return SchemaNode(
            name=name,
            is_leaf=True,
            is_key=is_key,
            is_list=is_list,
            is_mandatory=is_mandatory,
            flags=flags,
            type_ref=type_attr,
            enums=enums or None,
            pattern=pattern,
            pattern_negated=pattern_negated,
        )

    # Resolve named type reference
    if type_attr and type_attr not in _STRING_BASE_TYPES:
        # Check if it's a simple string-wrapper type (like filename, hostname, etc.)
        if type_attr in simple_type_map:
            return SchemaNode(
                name=name,
                is_leaf=True,
                is_key=is_key,
                is_list=is_list,
                is_mandatory=is_mandatory,
                flags=flags,
                type_ref=type_attr,
                pattern=pattern,
                pattern_negated=pattern_negated,
            )

        ct = type_map.get(type_attr)
        if ct is not None:
            # Guard against infinite recursion
            if type_attr in seen_types:
                return SchemaNode(
                    name=name,
                    is_leaf=True,
                    is_key=is_key,
                    is_list=is_list,
                    flags=flags,
                    type_ref=type_attr,
                )
            seen_types = seen_types | {type_attr}
            return _build_from_complex_type(
                name,
                ct,
                type_map,
                simple_type_map,
                seen_types,
                is_key=is_key,
                is_list=is_list,
                is_mandatory=is_mandatory,
                flags=flags,
                type_ref=type_attr,
                pattern=pattern,
                pattern_negated=pattern_negated,
            )
        else:
            # Named type is a string wrapper (e.g., key-attribute-string-type)
            return SchemaNode(
                name=name,
                is_leaf=True,
                is_key=is_key,
                is_list=is_list,
                is_mandatory=is_mandatory,
                flags=flags,
                type_ref=type_attr,
                pattern=pattern,
                pattern_negated=pattern_negated,
            )

    # Inline complexType
    inline_ct = element.find(_xsd("complexType"))
    if inline_ct is not None:
        return _build_from_complex_type(
            name,
            inline_ct,
            type_map,
            simple_type_map,
            seen_types,
            is_key=is_key,
            is_list=is_list,
            is_mandatory=is_mandatory,
            flags=flags,
            pattern=pattern,
            pattern_negated=pattern_negated,
        )

    # Inline simpleType (leaf with restrictions)
    inline_st = element.find(_xsd("simpleType"))
    if inline_st is not None:
        enums = _extract_enums(inline_st)
        st_pattern = pattern
        st_negated = pattern_negated
        if not st_pattern:
            st_pattern, st_negated = _extract_pattern_from_simple_type(inline_st)
        return SchemaNode(
            name=name,
            is_leaf=True,
            is_key=is_key,
            is_list=is_list,
            is_mandatory=is_mandatory,
            flags=flags,
            enums=enums or None,
            pattern=st_pattern,
            pattern_negated=st_negated,
        )

    # No type info at all - treat as leaf
    return SchemaNode(
        name=name,
        is_leaf=True,
        is_key=is_key,
        is_list=is_list,
        is_mandatory=is_mandatory,
        flags=flags,
        pattern=pattern,
        pattern_negated=pattern_negated,
    )


def _build_from_complex_type(
    name: str,
    ct: etree._Element,
    type_map: dict[str, etree._Element],
    simple_type_map: dict[str, etree._Element],
    seen_types: set[str],
    *,
    is_key: bool = False,
    is_list: bool = False,
    is_mandatory: bool = False,
    flags: set[str] | None = None,
    type_ref: str | None = None,
    pattern: str | None = None,
    pattern_negated: bool = False,
) -> SchemaNode:
    """Build a SchemaNode from an xsd:complexType element."""
    if flags is None:
        flags = set()

    # Merge flags from the complexType's own annotation/appinfo.
    # Named types (e.g., control-route-filter-type) carry flags like
    # oneliner-plus that the element reference doesn't duplicate.
    ct_appinfo = ct.find(f"{_xsd('annotation')}/{_xsd('appinfo')}")
    if ct_appinfo is not None:
        for flag_el in ct_appinfo.iter("flag"):
            flag_text = (flag_el.text or "").strip()
            if flag_text:
                flags.add(flag_text)

    # Check for simpleContent (text node with attributes - it's a leaf)
    simple_content = ct.find(_xsd("simpleContent"))
    if simple_content is not None:
        enums = _extract_enums(ct)
        return SchemaNode(
            name=name,
            is_leaf=True,
            is_key=is_key,
            is_list=is_list,
            is_mandatory=is_mandatory,
            flags=flags,
            type_ref=type_ref,
            enums=enums or None,
            pattern=pattern,
            pattern_negated=pattern_negated,
        )

    # Check for empty complexType (presence container)
    has_child_elements = False
    for child in ct:
        tag = etree.QName(child.tag).localname if isinstance(child.tag, str) else ""
        if tag in ("sequence", "choice", "all"):
            has_child_elements = True
            break

    if not has_child_elements:
        # Could be truly empty or have only annotation
        return SchemaNode(
            name=name,
            is_presence=True,
            is_key=is_key,
            is_list=is_list,
            is_mandatory=is_mandatory,
            flags=flags,
            type_ref=type_ref,
        )

    # Parse children from sequence/choice
    children: dict[str, SchemaNode] = {}
    combinator = Combinator.CHOICE

    seq = ct.find(_xsd("sequence"))
    if seq is not None:
        # Check if the sequence contains a single choice (dominant Junos pattern)
        choice = seq.find(_xsd("choice"))
        if choice is not None:
            combinator = Combinator.CHOICE
            _collect_children(choice, children, type_map, simple_type_map, seen_types)
        else:
            # Pure sequence
            combinator = Combinator.SEQUENCE
            _collect_children(seq, children, type_map, simple_type_map, seen_types)

    choice_direct = ct.find(_xsd("choice"))
    if choice_direct is not None and seq is None:
        combinator = Combinator.CHOICE
        _collect_children(choice_direct, children, type_map, simple_type_map, seen_types)

    if not children:
        return SchemaNode(
            name=name,
            is_presence=True,
            is_key=is_key,
            is_list=is_list,
            is_mandatory=is_mandatory,
            flags=flags,
            type_ref=type_ref,
        )

    return SchemaNode(
        name=name,
        children=children,
        combinator=combinator,
        is_key=is_key,
        is_list=is_list,
        is_mandatory=is_mandatory,
        flags=flags,
        type_ref=type_ref,
    )


def _collect_children(
    container: etree._Element,
    children: dict[str, SchemaNode],
    type_map: dict[str, etree._Element],
    simple_type_map: dict[str, etree._Element],
    seen_types: set[str],
) -> None:
    """Collect child elements from a sequence or choice container."""
    for child in container:
        if not isinstance(child.tag, str):
            continue

        local = etree.QName(child.tag).localname

        if local == "element":
            child_name = child.get("name", "")
            ref = child.get("ref", "")

            # Skip undocumented/comment refs
            if ref and (ref in _SKIP_REFS or ref.split("}")[-1] in _SKIP_REFS):
                continue
            if child_name in _SKIP_NAMES:
                continue

            # Handle ref= (resolve element reference)
            if ref and not child_name:
                # For our purposes, skip external refs we can't resolve
                continue

            if child_name:
                node = _build_node(child, type_map, simple_type_map, seen_types)
                children[child_name] = node

        elif local in ("sequence", "choice"):
            # Nested sequence/choice - recurse into it
            _collect_children(child, children, type_map, simple_type_map, seen_types)


def _extract_enums(type_el: etree._Element) -> list[str]:
    """Extract enumeration values from a type element."""
    enums = []
    for enum_el in type_el.iter(_xsd("enumeration")):
        val = enum_el.get("value")
        if val is not None:
            enums.append(val)
    return enums


def _extract_enums_from_element(element: etree._Element) -> list[str]:
    """Extract enums from inline simpleType within an element."""
    st = element.find(_xsd("simpleType"))
    if st is not None:
        return _extract_enums(st)
    return []


def _extract_pattern_from_simple_type(st: etree._Element) -> tuple[str | None, bool]:
    """Extract pattern from a simpleType restriction."""
    for restriction in st.iter(_xsd("restriction")):
        for pat_el in restriction.iter(_xsd("pattern")):
            val = pat_el.get("value", "")
            if val:
                if val.startswith("!"):
                    return val[1:], True
                return val, False
    return None, False
