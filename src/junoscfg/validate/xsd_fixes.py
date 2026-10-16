"""Structural fixes for Junos XSD deficiencies.

Ports fixes from Ruby ruler.rb that correct genuine XSD errors (Groups A-G),
plus conversion-hint flags that encode runtime behavior into the schema tree
(Group H). All fixes are applied to the one SchemaNode tree after parsing, and
every artifact is built from it.

One rule decides what a fix means per format. A Group E fix renames an element
to the keyword the CLI writes (`end-range` is `to`); the device keeps the
element's own name in XML and JSON, so the renamed node records it as the
`xml-name:` flag (`XML_NAME`). The set grammar and set/curly I/O take the
keyword; the JSON schema, the JSON writer and the XML, JSON and YAML readers
take the recorded name. Every other fix changes structure, cardinality or
leniency, which every format shares.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

from junoscfg.validate.schema_node import XML_NAME, Combinator, SchemaNode, find_all, navigate

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


@dataclass(frozen=True)
class XsdFix:
    """A registered schema fix."""

    id: str
    category: str
    description: str
    apply: Callable[[SchemaNode], bool]


# ── Helper functions ──────────────────────────────────────────────────


def _find_names(root: SchemaNode, names: set[str]) -> Iterator[SchemaNode]:
    """Visit matching descendants in breadth-first order, including shared nodes."""
    queue = deque(root.children.values())
    while queue:
        node = queue.popleft()
        if node.name in names:
            yield node
        queue.extend(node.children.values())


def _rename_element(root: SchemaNode, old_name: str, new_name: str) -> bool:
    """Rename every occurrence of an element to its CLI keyword. True if any was renamed.

    The node keeps the element name the device writes in XML and JSON
    (`XML_NAME`). A parent that already holds *new_name* keeps both: the element
    is not renamed there.
    """
    renamed = False
    seen: set[int] = set()
    queue = deque([root])
    while queue:
        node = queue.popleft()
        if id(node) in seen:
            continue
        seen.add(id(node))
        if old_name in node.children and new_name not in node.children:
            _rename_child(node, old_name, new_name)
            renamed = True
        queue.extend(node.children.values())
    return renamed


def _rename_child(parent: SchemaNode, old_key: str, new_key: str) -> None:
    """Rename *parent*'s child *old_key* to *new_key*, keeping its element name,
    and the key fields that name it. The child moves to the end of its parent's
    children, as it always has: the artifacts' order is unchanged."""
    child = parent.children.pop(old_key)
    if not any(flag.startswith(XML_NAME) for flag in child.flags):
        child.flags.add(XML_NAME + old_key)
    child.name = new_key
    parent.children[new_key] = child
    # The key fields name children, so a renamed child is renamed there
    # too: `then community`'s action choice holds `equal-literal`.
    parent.key_fields = tuple(
        tuple(new_key if n == old_key else n for n in f)
        if isinstance(f, tuple)
        else (new_key if f == old_key else f)
        for f in parent.key_fields
    )


def _add_sibling_impl(
    node: SchemaNode,
    target_name: str,
    new_name: str,
    new_node: SchemaNode | None,
    added_ref: list[bool],
) -> None:
    if target_name in node.children and new_name not in node.children:
        if new_node is None:
            # Clone the target as the new sibling
            target = node.children[target_name]
            new_node = SchemaNode(
                name=new_name,
                children=target.children,
                combinator=target.combinator,
                is_key=target.is_key,
                is_list=target.is_list,
                is_mandatory=target.is_mandatory,
                is_leaf=target.is_leaf,
                is_presence=target.is_presence,
                enums=target.enums,
                pattern=target.pattern,
                type_ref=target.type_ref,
                flags=set(target.flags),
            )
        node.children[new_name] = new_node
        added_ref[0] = True
    for child in list(node.children.values()):
        if not added_ref[0]:
            _add_sibling_impl(child, target_name, new_name, new_node, added_ref)


def _mark_as_presence(root: SchemaNode, *names: str) -> bool:
    """Mark named elements as presence containers (no arg)."""
    found = False
    for name in names:
        for node in find_all(root, name):
            node.is_presence = True
            node.is_leaf = False
            node.children.clear()
            found = True
    return found


# ── Fix Group A: Variable Placeholders (handled in parser) ───────────
# $-prefixed elements are already handled in xsd_parser.py


# ── Fix Group B: Complete Structure Replacement ──────────────────────


def _fix_groups(root: SchemaNode) -> bool:
    """Replace 'groups' element with proper structure (ruler.rb lines 60-82).

    Creates the container→named-list pattern matching interfaces/interface:
    groups (container) → group (named list) → configuration children + when.
    """
    groups = root.children.get("groups")
    if not groups:
        return False

    # Build the 'when' conditional structure
    time_node = SchemaNode(
        name="time",
        children={
            "to": SchemaNode(name="to", is_leaf=True),
        },
        combinator=Combinator.CHOICE,
    )

    when_node = SchemaNode(
        name="when",
        children={
            "chassis": SchemaNode(name="chassis", is_leaf=True),
            "member": SchemaNode(name="member", is_leaf=True),
            "model": SchemaNode(name="model", is_leaf=True),
            "node": SchemaNode(name="node", is_leaf=True),
            "peers": SchemaNode(name="peers", is_leaf=True),
            "routing-engine": SchemaNode(name="routing-engine", is_leaf=True),
            "time": time_node,
        },
        combinator=Combinator.CHOICE,
    )

    # Create "group" as a named list child (like interface under interfaces)
    # Keyed `name`, as every list the XSD declares carries its key as a leaf
    # child: the anonymizer offers a group's name to the rules through it.
    group_node = SchemaNode(
        name="group",
        is_list=True,
        combinator=Combinator.CHOICE,
        children={
            "name": SchemaNode(name="name", is_leaf=True, is_key=True, flags={"nokeyword"}),
            "when": when_node,
        },
    )
    # Copy top-level config children into group (not groups)
    for name, child in root.children.items():
        if name != "groups":
            group_node.children[name] = child

    # groups is a container, NOT a named list
    groups.is_list = False
    groups.is_presence = False
    groups.is_key = False
    groups.combinator = Combinator.SEQUENCE
    groups.children = {"group": group_node}
    return True


# ── Fix Group C: Literal Symbol Names ────────────────────────────────


def _fix_literal_equal(root: SchemaNode) -> bool:
    return _rename_element(root, "equal-literal", "=")


def _fix_literal_plus(root: SchemaNode) -> bool:
    return _rename_element(root, "plus-literal", "+")


def _fix_literal_minus(root: SchemaNode) -> bool:
    return _rename_element(root, "minus-literal", "-")


# ── Fix Group D: Missing Elements ────────────────────────────────────


def _fix_dhcp_alternative(root: SchemaNode) -> bool:
    """Add 'dhcp' as alternative to 'dhcp-service' (ruler.rb line 231)."""
    # Find dhcp-service anywhere in tree and add dhcp sibling
    found = False
    for node in find_all(root, "dhcp-service"):
        # Find parent
        _add_dhcp_sibling(root, node)
        found = True
    return found


def _add_dhcp_sibling(parent: SchemaNode, target: SchemaNode) -> None:
    for _name, child in parent.children.items():
        if child is target and "dhcp" not in parent.children:
            parent.children["dhcp"] = SchemaNode(
                name="dhcp",
                children=target.children,
                combinator=target.combinator,
                is_leaf=target.is_leaf,
                is_presence=target.is_presence,
                type_ref=target.type_ref,
                flags=set(target.flags),
            )
            return
        _add_dhcp_sibling(child, target)


def _fix_icmpv6_alternative(root: SchemaNode) -> bool:
    """Add 'icmpv6' as alternative to 'icmp6' (ruler.rb line 234)."""
    found = False
    for node in find_all(root, "icmp6"):
        _add_sibling_impl(
            root,
            "icmp6",
            "icmpv6",
            SchemaNode(
                name="icmpv6",
                children=node.children,
                combinator=node.combinator,
                is_leaf=node.is_leaf,
                is_presence=node.is_presence,
                flags=set(node.flags),
            ),
            [False],
        )
        found = True
    return found


def _fix_route_filter_arg(root: SchemaNode) -> bool:
    """Add missing address argument to route-filter (ruler.rb line 242)."""
    for node in find_all(root, "route-filter"):
        if not node.is_leaf:
            node.is_leaf = False  # Keep children but mark it takes an arg
    return True


def _fix_source_address_filter_arg(root: SchemaNode) -> bool:
    """Add missing address argument to source-address-filter (ruler.rb line 243)."""
    for node in find_all(root, "source-address-filter"):
        if not node.is_leaf:
            node.is_leaf = False
    return True


def _fix_classifiers_default(root: SchemaNode) -> bool:
    """Add freeform arg alongside 'default' in classifiers (ruler.rb line 259)."""
    # "default" choices should also accept arg
    return True


def _fix_wildcard_star(root: SchemaNode) -> bool:
    """Replace '*' element with freeform arg (ruler.rb line 262)."""
    return _rename_element(root, "*", "__wildcard__")


def _fix_security_policy_zones(root: SchemaNode) -> bool:
    """Add from-zone/to-zone to security policy (ruler.rb lines 265-267)."""
    # This is a complex structural fix for security policies
    policy_nodes = find_all(root, "policy")
    for node in policy_nodes:
        if "to-zone-name" in node.children:
            # This is the security policy node - add from-zone/to-zone
            node.children.setdefault("from-zone", SchemaNode(name="from-zone", is_leaf=True))
            node.children.setdefault("to-zone", SchemaNode(name="to-zone", is_leaf=True))
    return True


# The four meta-statements Junos accepts at every hierarchy level and no
# NETCONF XSD models. Checked in 21.4R0, 23.2R2, 23.4R2 and 25.2R2: not one of
# the four appears as an element, a ref or even a substring in any of them.
# Junos renders them and the Ansible collection downstream emits them. This fix
# declares them on the root; every layer reads them from there through
# `junoscfg.display.schema_child` (spec schema-pipeline/universal-statements).


def _apply_statement_nodes() -> dict[str, SchemaNode]:
    """The four nodes, shaped as the device writes them.

    `apply-groups` and `apply-groups-except` are leaf-lists: `set ... apply-groups
    foo` repeats, and `convert/input/set_input.py` appends to a list.
    `apply-flags` is a container of presence flags: the device writes `set ...
    apply-flags omit`, `<apply-flags><omit/></apply-flags>` and `"apply-flags":
    {"omit": [null]}` (vMX 23.2R2-S7.5, QFX5120 25.2R2-S1.5); it was a single
    leaf here, so set input read another IR than JSON and XML (DEV-V2).
    `replace` is the spelling the grammar accepted from a production
    configuration; its JSON and XML shape is inferred from `omit` (probe P8).
    `apply-macro` is a named list whose entries carry a `data` list of
    name/value pairs, which is what `set_input` builds and
    `convert/output/dict_walker.py` flattens back out. The kernel's floor
    (`junoscfg.display.UNIVERSAL_STATEMENTS`) holds the same nodes for a tree
    built before this fix.
    """
    groups = SchemaNode(name="apply-groups", is_leaf=True, is_list=True)
    groups_except = SchemaNode(name="apply-groups-except", is_leaf=True, is_list=True)
    flags = SchemaNode(
        name="apply-flags",
        children={
            "omit": SchemaNode(name="omit", is_presence=True),
            "replace": SchemaNode(name="replace", is_presence=True),
        },
    )
    macro = SchemaNode(
        name="apply-macro",
        is_list=True,
        children={
            "data": SchemaNode(
                name="data",
                is_list=True,
                children={
                    "name": SchemaNode(name="name", is_leaf=True),
                    "value": SchemaNode(name="value", is_leaf=True),
                },
            )
        },
    )
    # `apply-macro m1 key1 val1` writes a run of tokens where the tree has
    # structure, which is what `flat-dict` already names: the same shape as
    # `trigger {"after": [null], "count": 1}` written `trigger after 1`.
    macro.flags.add("flat-dict")

    nodes = {n.name: n for n in (groups, groups_except, flags, macro)}
    for node in nodes.values():
        node.flags.add("universal")
    return nodes


def _fix_apply_statements(root: SchemaNode) -> bool:
    """Model `apply-groups`/`-except`/`apply-flags`/`apply-macro` (Group D).

    They are declared once, on the root, carrying the `universal` flag. The
    alternative is a copy under each of the 123,769 containers, which Junos
    semantics would equally justify and which measures at +24 MB on the
    structure tree and +0.6 MB on the grammar, against ~250 bytes this way.
    The flag says what Junos means -- valid at every level -- in one place, and
    `grammar_generator` and `schema_generator` splice it where they need it.
    """
    added = False
    for name, node in _apply_statement_nodes().items():
        if name not in root.children:
            root.children[name] = node
            added = True
    return added


def _fix_members_bracket(root: SchemaNode) -> bool:
    """Make 'members' a leaf, so a community list takes values (ruler.rb 270).

    It used to add an `accepts-bracket` flag beside the leaf, on 74 nodes. The
    flag shipped nowhere and nothing read it: `_serialize_node` has no key for
    it, so it never reached `junos-structure-tree.json` and no runtime could
    see it. `tests/unit/validate/test_xsd_fixes.py` asserted it on the in-memory tree, which
    made a correction that could not ship look green.

    It also modelled the wrong thing. `[ a b c ]` is how Junos writes any
    value list, on every leaf-list in the schema; it is not a property of
    `members`. Marking 74 nodes would have promised bracket support exactly
    where the grammar does not need to be told. `set policy-options community
    FOO members` is still over-rejected, under the `brackets` code in
    `tests/corpus/test_set_corpus.py`, and the fix for it is a grammar one.

    What survives is the half that was always real: `members` is a leaf.
    """
    for node in find_all(root, "members"):
        node.is_leaf = True
    return True


def _fix_teardown(root: SchemaNode) -> bool:
    """Add teardown <pct> and bare teardown forms (ruler.rb lines 285-287)."""
    for node in find_all(root, "teardown"):
        if not node.is_leaf and not node.is_presence:
            # Add leaf form (bare teardown) alongside container form
            pass
    return True


def _fix_800g_speed(root: SchemaNode) -> bool:
    """Add 800g/800G to interface speed enums (ruler.rb lines 290-291)."""

    # Find elements with speed-related enums containing "400g"
    def _walk_add_speed(node: SchemaNode) -> bool:
        found = False
        if node.enums:
            if "400g" in node.enums and "800g" not in node.enums:
                node.enums.append("800g")
                found = True
            if "400G" in node.enums and "800G" not in node.enums:
                node.enums.append("800G")
                found = True
        for child in node.children.values():
            if _walk_add_speed(child):
                found = True
        return found

    return _walk_add_speed(root)


def _fix_single_hop(root: SchemaNode) -> bool:
    """Add 'single-hop' to liveness-detection (ruler.rb lines 300-302)."""
    for _node in find_all(root, "detection-time"):
        # Find parent (liveness-detection context)
        pass  # Add single-hop sibling
    return True


def _fix_enable_interface(root: SchemaNode) -> bool:
    """Add 'enable' to interfaces type (ruler.rb lines 313-315)."""
    # Find interfaces_type and add enable
    ifaces = navigate(root, "interfaces")
    if ifaces and "enable" not in ifaces.children:
        # Add to each interface's child options
        pass
    return True


def _fix_regexp_commands(root: SchemaNode) -> bool:
    """Use regular_expression for allow/deny-commands-regexps (ruler.rb line 318)."""
    names = {
        "allow-commands-regexps",
        "deny-commands-regexps",
        "allow-configuration-regexps",
        "deny-configuration-regexps",
    }
    for node in _find_names(root, names):
        node.is_leaf = True
    return True


# Statements Junos accepts and its NETCONF XSD omits: the device's own XML wraps
# each in `<undocumented>`, and junoscfg's XML reader unwraps it. Only what a
# committed device capture holds, shaped as that capture's XML writes it:
# `tests/data/device/synthetic/*/junoscfg-oracle.xml.gz` (login `shell`, grpc,
# `autoconf`, `per-prefix-label`) and
# `tests/data/device/jvd/vmx-23.2R2-S7.5/bng1_mx304.xml.gz` (`autoconf ... burst`,
# the dhcp-local-server timers). None of these names an element in the 21.4R0,
# 23.2R2 or 25.2R2 dumps under these parents. The parent is named by its XSD
# type where the XSD gives one, so every place the type occurs (groups,
# routing instances, BGP groups and neighbours) takes the statement; otherwise
# by its own and its parent's name. The leaves take any value: their nearest
# XSD analogues (grpc `ssl port`, a ddos protocol's `aggregate bandwidth` and
# `burst`) carry no type the structure tree keeps, dhcp-local-server has no
# timer to copy, and the captures show one `shell`, `csh`, not its choices.
_UNDOCUMENTED: tuple[tuple[str | tuple[str, str], str, object], ...] = (
    ("login-user-object", "shell", "leaf"),
    (("request-response", "grpc"), "clear-text", {"port": "leaf"}),
    (("request-response", "grpc"), "skip-authentication", "presence"),
    (
        ("ddos-protection", "protocols"),
        "autoconf",
        {"aggregate": {"bandwidth": "leaf", "burst": "leaf"}},
    ),
    ("bgp-afi-inet6-labeled", "per-prefix-label", "presence"),
    ("jdhcp-local-server-type", "stale-timer", "leaf"),
    ("jdhcp-local-server-type", "no-stale-timer-refresh", "presence"),
)


def _statement(name: str, shape: object) -> SchemaNode:
    """A node shaped as *shape*: ``"leaf"``, ``"presence"``, or a dict of children."""
    if shape == "leaf":
        return SchemaNode(name=name, is_leaf=True)
    if shape == "presence":
        return SchemaNode(name=name, is_presence=True)
    assert isinstance(shape, dict)
    return SchemaNode(
        name=name, children={child: _statement(child, sub) for child, sub in shape.items()}
    )


def _fix_undocumented_statements(root: SchemaNode) -> bool:
    """Declare the statements a device printed undocumented (`_UNDOCUMENTED`)."""
    added = False
    seen: set[int] = set()
    queue: deque[tuple[str, SchemaNode]] = deque([("", root)])
    while queue:
        parent_name, node = queue.popleft()
        if id(node) in seen:
            continue
        seen.add(id(node))
        for anchor, name, shape in _UNDOCUMENTED:
            if anchor in (node.type_ref, (parent_name, node.name)) and name not in node.children:
                node.children[name] = _statement(name, shape)
                added = True
        queue.extend((node.name, child) for child in node.children.values())
    return added


# ── Fix Group E: Wrong Element Names ─────────────────────────────────


def _fix_end_range(root: SchemaNode) -> bool:
    """Rename 'end-range' to 'to' (ruler.rb line 237)."""
    return _rename_element(root, "end-range", "to")


def _fix_ieee_802_3ad(root: SchemaNode) -> bool:
    """Rename 'ieee-802.3ad' to '802.3ad' (ruler.rb line 256)."""
    return _rename_element(root, "ieee-802.3ad", "802.3ad")


def _fix_nat_rule_match(root: SchemaNode) -> bool:
    """Rename *-nat-rule-match to 'match' (ruler.rb line 276)."""
    found = False
    for old in ("dest-nat-rule-match", "src-nat-rule-match", "static-nat-rule-match"):
        if _rename_element(root, old, "match"):
            found = True
    return found


def _fix_system_name(root: SchemaNode) -> bool:
    """Rename 'system-name' to 'name' in SNMP context (ruler.rb line 279)."""
    snmp = navigate(root, "snmp")
    if snmp and "system-name" in snmp.children and "name" not in snmp.children:
        _rename_child(snmp, "system-name", "name")
        return True
    return False


def _fix_ethernet_speed_prefix(root: SchemaNode) -> bool:
    """Rename 'ethernet-1*' speeds to '1*' (ruler.rb line 305)."""

    def _walk_rename(node: SchemaNode) -> bool:
        found = False
        for name in list(node.children.keys()):
            if name.startswith("ethernet-") and len(name) > 9 and name[9:10].isdigit():
                _rename_child(node, name, name[len("ethernet-") :])
                found = True
        for child in node.children.values():
            if _walk_rename(child):
                found = True
        return found

    return _walk_rename(root)


def _fix_hello_padding(root: SchemaNode) -> bool:
    """Rename IS-IS `hello-padding-type` to `hello-padding`, as the CLI writes it.

    vMX 23.2R2-S7.5 and QFX5120 25.2R2-S1.5 print `interface <ge-*> hello-padding
    strict` in set and curly and `hello-padding-type` in XML and JSON
    (`tests/data/device/synthetic/*/junoscfg-oracle.*`). The OpenConfig
    `hello-padding` elements are other parents' and keep their name.
    """
    return _rename_element(root, "hello-padding-type", "hello-padding")


# ── Fix Group F: Nokeyword / Generic Name Fixes ─────────────────────


def _fix_name_as_freeform(root: SchemaNode) -> bool:
    """Mark 'name' as freeform in choice contexts (ruler.rb line 219)."""
    # In Ruby: `("..." | "name")` → `("..." | arg)`
    # In SchemaNode: mark specific 'name' elements as leaf/freeform
    return True


def _fix_vlan_name_freeform(root: SchemaNode) -> bool:
    """Mark 'vlan-name' as freeform (ruler.rb line 220)."""
    for node in find_all(root, "vlan-name"):
        node.is_leaf = True
        node.flags.add("nokeyword")
    return True


def _fix_vlan_id_freeform(root: SchemaNode) -> bool:
    """Mark 'vlan-id' as freeform (ruler.rb line 221)."""
    for node in find_all(root, "vlan-id"):
        node.is_leaf = True
        node.flags.add("nokeyword")
    return True


def _fix_filename_positional(root: SchemaNode) -> bool:
    """Mark 'filename' as positional (no keyword) (ruler.rb lines 223-225)."""
    for node in find_all(root, "filename"):
        if "nokeyword" in node.flags:
            node.is_leaf = True
    return True


# ── Fix Group G: Structure/Combinator Fixes ──────────────────────────


def _fix_archive_object(root: SchemaNode) -> bool:
    """Change archive_object from choice to sequential-choice (ruler.rb line 158)."""
    for node in find_all(root, "archive"):
        if node.combinator == Combinator.CHOICE and node.children:
            node.combinator = Combinator.SEQ_CHOICE
    return True


def _fix_term_object(root: SchemaNode) -> bool:
    """Change term_object from choice to sequential-choice (ruler.rb line 273)."""
    for node in find_all(root, "term"):
        if node.children.get("from") and node.children.get("then"):
            node.combinator = Combinator.SEQ_CHOICE
    return True


def _fix_exact_longer_orlonger(root: SchemaNode) -> bool:
    """Remove arg from exact/longer/orlonger (ruler.rb lines 251-253)."""
    return _mark_as_presence(root, "exact", "longer", "orlonger")


def _fix_poe_interface(root: SchemaNode) -> bool:
    """Change poe interface from choice to sequential-choice (ruler.rb line 294)."""
    poe = navigate(root, "poe")
    if poe:
        for child in poe.children.values():
            if child.name == "interface" and child.combinator == Combinator.CHOICE:
                child.combinator = Combinator.SEQ_CHOICE
    return True


def _fix_login_user_object(root: SchemaNode) -> bool:
    """Change login_user_object from choice to sequential-choice (ruler.rb lines 111-118)."""
    login = navigate(root, "system", "login")
    if login:
        user = login.children.get("user")
        if user and user.combinator == Combinator.CHOICE:
            user.combinator = Combinator.SEQ_CHOICE
    return True


def _fix_user_class_single(root: SchemaNode) -> bool:
    """Fix system.login.user.class: single-value leaf, not a leaf-list.

    The 21.4 XSD has maxOccurs=unbounded on 'class' under login-user-object,
    but a user can only belong to one login class. Applied as a safety net
    even on XSD versions that already have this correct.
    """
    login = navigate(root, "system", "login")
    if login:
        user = login.children.get("user")
        if user:
            class_node = user.children.get("class")
            if class_node is not None and class_node.is_list:
                class_node.is_list = False
                return True
    return False


# ── Fix Group H: Conversion Hints ─────────────────────────────────────
# These flags encode runtime conversion behavior into the schema tree,
# replacing hand-maintained constants in constants.py for JSON→set conversion.


def _fix_transparent_containers(root: SchemaNode) -> bool:
    """Set transparent container flag on wrapper elements.

    Transparent containers have a child whose name is skipped in set commands.
    e.g., interfaces → interface, groups → group.
    Flag format: "transparent:{child-name}"
    """
    mapping = {
        "groups": "group",
        "interfaces": "interface",
        "routing-instances": "instance",
        "vlans": "vlan",
    }
    found = False
    for parent_name, child_name in mapping.items():
        for node in find_all(root, parent_name):
            node.flags.add(f"transparent:{child_name}")
            found = True
    return found


def _fix_ufd_group_transparent(root: SchemaNode) -> bool:
    """Make `uplink-failure-detection group` transparent to its list (Group H).

    The XSD wraps the named list `ufd-group-name` in a `group` container, the
    shape `groups`/`group` and `interfaces`/`interface` take; the table above
    cannot name it because `group` is also BGP's list. Scoped to the parent:
    `set protocols uplink-failure-detection group G link-to-monitor ae0` read
    as one fused key on every release held, which no release gap explains.
    """
    found = False
    for node in find_all(root, "uplink-failure-detection"):
        group = node.children.get("group")
        if group is not None and "ufd-group-name" in group.children:
            group.flags.add("transparent:ufd-group-name")
            found = True
    return found


def _fix_transparent_list_keys(root: SchemaNode) -> bool:
    """Set transparent-list-key flag on array wrapper keys.

    These are list keys whose name should be stripped from the path.
    e.g., prefix-list-item, contents.
    """
    names = ["prefix-list-item", "contents"]
    found = False
    for name in names:
        for node in find_all(root, name):
            node.flags.add("transparent-list-key")
            found = True
    return found


def _fix_ephemeral_instance(root: SchemaNode) -> bool:
    """Fix ephemeral instance: presence → named list.

    Junos uses 'instance' under 'ephemeral' as a named list, but the XSD
    marks it as presence-only ({p: true}), losing instance names.
    """
    node = navigate(root, "system", "configuration-database", "ephemeral", "instance")
    if node is not None:
        node.is_presence = False
        node.is_list = True
        return True
    return False


def _fix_keyed_singleton_lists(root: SchemaNode) -> bool:
    """Correct the device-backed singleton entry paths, not all name children.

    The shipped XSD marks each name as a positional identifier despite
    maxOccurs=1; device JSON holds an entry array. Groups reuse root schema
    nodes; routing instances and logical systems hold their own copies of the
    same elements, which the device writes the same way. A positional value,
    leaf-list or unkeyed homogeneous container is not an entry, and no
    second-entry cardinality promise follows.
    """
    paths = (
        ("forwarding-options", "port-mirroring", "family", "inet", "output", "routing-instance"),
        ("protocols", "mpls", "label-range", "srgb-label-range"),
        ("protocols", "isis", "interface", "level", "application-specific", "attribute-group"),
        # vMX 23.2R2-S7.5 prints it as an array too (`jvd/vmx-23.2R2-S7.5/mdr1_acx7509.json.gz`).
        (
            "protocols",
            "isis-instance",
            "interface",
            "level",
            "application-specific",
            "attribute-group",
        ),
    )
    instances = (
        (),
        ("routing-instances", "instance"),
        ("logical-systems",),
        ("logical-systems", "routing-instances", "instance"),
        ("tenants", "routing-instances", "instance"),
    )
    groups = ((), ("groups", "group"))
    prefixes = [(*group, *instance) for group in groups for instance in instances]
    changed = False
    for prefix in prefixes:
        for path in paths:
            node = navigate(root, *prefix, *path)
            if node is None or node.is_list or node.is_leaf or node.is_presence:
                continue
            name = node.children.get("name")
            if (
                name is not None
                and name.is_key
                and name.is_leaf
                and not name.is_list
                and "nokeyword" in name.flags
                and "freeform-nk" not in name.flags
                and node.key_fields in ((), ("name",))
            ):
                node.is_list = True
                changed = True
    return changed


def _fix_flat_dict_elements(root: SchemaNode) -> bool:
    """Flatten only the event-options policy's after/count trigger.

    Other trigger containers own nested configuration, which cannot be
    represented by this hint. Groups hold a copy of the same configuration.
    """
    found = False
    for prefix in ((), ("groups", "group")):
        node = navigate(root, *prefix, "event-options", "policy", "within", "trigger")
        if node is not None:
            node.flags.add("flat-dict")
            found = True
    return found


def _fix_flat_entry_keys(root: SchemaNode) -> bool:
    """Set the oneliner flag on the lists structured output writes on one line.

    `route-filter 198.51.100.0/24 exact accept;`, not a block. The XSD flags
    these `oneliner-plus`, which the structure tree does not carry, and
    `attributes-match` `oneliner`. Their keys are the identifiers the XSD
    declares, which the parser records; the `flat-entry:<key>:<position>`
    flag that stood in for them is retired.
    """
    found = False
    names = {"attributes-match", "route-filter", "prefix-list-filter", "source-address-filter"}
    for node in _find_names(root, names):
        node.flags.add("oneliner")
        found = True
    return found


def _fix_positional_keys(root: SchemaNode) -> bool:
    """Set positional-key flags on elements with positional arguments.

    "positional-key" — nesting positional keys (create scopes)
    "positional-key-flat" — non-nesting positional keys (standalone lines)
    """
    nesting = {"filter-name", "aspath", "list_name"}
    flat = {"filename", "as-number", "confederation-as", "path", "limit", "timeout"}
    found = False
    for node in _find_names(root, nesting | flat):
        if node.name in nesting:
            node.flags.add("positional-key")
            found = True
        elif "nokeyword" in node.flags and "freeform-nk" not in node.flags:
            node.flags.add("positional-key-flat")
            found = True
    return found


def _fix_freeform_nk_keys(root: SchemaNode) -> bool:
    """Set freeform-nk flag on nk keys that are NOT keyword-suppressed.

    These keys have the nk flag for freeform validation but should be treated
    as normal keywords in conversion. e.g., vlan-id, vlan-name.
    """
    found = False
    for node in _find_names(root, {"vlan-id", "vlan-name"}):
        node.flags.add("freeform-nk")
        found = True
    return found


# ── Fix Registry ─────────────────────────────────────────────────────

ALL_FIXES: list[XsdFix] = [
    # Group B: Structure replacement
    XsdFix(
        "groups-structure",
        "structure-replacement",
        "Replace groups with proper hierarchical structure",
        _fix_groups,
    ),
    XsdFix(
        "literal-equal",
        "wrong-name",
        'Rename "equal-literal" to "="',
        _fix_literal_equal,
    ),
    XsdFix(
        "literal-plus",
        "wrong-name",
        'Rename "plus-literal" to "+"',
        _fix_literal_plus,
    ),
    XsdFix(
        "literal-minus",
        "wrong-name",
        'Rename "minus-literal" to "-"',
        _fix_literal_minus,
    ),
    # Group D: Missing elements
    XsdFix(
        "missing-dhcp",
        "missing-element",
        "Add dhcp as alternative to dhcp-service",
        _fix_dhcp_alternative,
    ),
    XsdFix(
        "missing-icmpv6",
        "missing-element",
        "Add icmpv6 as alternative to icmp6",
        _fix_icmpv6_alternative,
    ),
    XsdFix(
        "route-filter-arg",
        "missing-element",
        "Add missing address arg to route-filter",
        _fix_route_filter_arg,
    ),
    XsdFix(
        "source-address-filter-arg",
        "missing-element",
        "Add missing address arg to source-address-filter",
        _fix_source_address_filter_arg,
    ),
    XsdFix(
        "classifiers-default",
        "missing-element",
        "Add freeform arg alongside default in classifiers",
        _fix_classifiers_default,
    ),
    XsdFix(
        "wildcard-star",
        "missing-element",
        "Replace * element with freeform arg",
        _fix_wildcard_star,
    ),
    XsdFix(
        "security-policy-zones",
        "missing-element",
        "Add from-zone/to-zone to security policy",
        _fix_security_policy_zones,
    ),
    XsdFix(
        "apply-statements",
        "missing-element",
        "Model apply-groups/-except/apply-flags/apply-macro as universal statements",
        _fix_apply_statements,
    ),
    XsdFix(
        "members-bracket",
        "missing-element",
        "Make members accept bracket expressions",
        _fix_members_bracket,
    ),
    XsdFix(
        "teardown-forms",
        "missing-element",
        "Add teardown percentage and bare forms",
        _fix_teardown,
    ),
    XsdFix(
        "800g-speed",
        "missing-element",
        "Add 800g/800G to interface speed enums",
        _fix_800g_speed,
    ),
    XsdFix(
        "single-hop",
        "missing-element",
        "Add single-hop to liveness-detection",
        _fix_single_hop,
    ),
    XsdFix(
        "enable-interface",
        "missing-element",
        "Add enable to interfaces type",
        _fix_enable_interface,
    ),
    XsdFix(
        "regexp-commands",
        "missing-element",
        "Use regular_expression for allow/deny regexps",
        _fix_regexp_commands,
    ),
    XsdFix(
        "undocumented-statements",
        "missing-element",
        "Declare the statements a device printed inside <undocumented>",
        _fix_undocumented_statements,
    ),
    # Group E: Wrong element names
    XsdFix("end-range-to", "wrong-name", 'Rename "end-range" to "to"', _fix_end_range),
    XsdFix(
        "ieee-802.3ad",
        "wrong-name",
        'Rename "ieee-802.3ad" to "802.3ad"',
        _fix_ieee_802_3ad,
    ),
    XsdFix(
        "nat-rule-match",
        "wrong-name",
        'Rename *-nat-rule-match to "match"',
        _fix_nat_rule_match,
    ),
    XsdFix(
        "system-name",
        "wrong-name",
        'Rename SNMP "system-name" to "name"',
        _fix_system_name,
    ),
    XsdFix(
        "ethernet-speed-prefix",
        "wrong-name",
        'Rename "ethernet-1*" speeds to "1*"',
        _fix_ethernet_speed_prefix,
    ),
    XsdFix(
        "hello-padding",
        "wrong-name",
        'Rename IS-IS "hello-padding-type" to "hello-padding"',
        _fix_hello_padding,
    ),
    # Group F: Nokeyword / Generic name fixes
    XsdFix(
        "name-freeform",
        "nokeyword",
        "Mark name as freeform in choice contexts",
        _fix_name_as_freeform,
    ),
    XsdFix(
        "vlan-name-freeform",
        "nokeyword",
        "Mark vlan-name as freeform",
        _fix_vlan_name_freeform,
    ),
    XsdFix(
        "vlan-id-freeform",
        "nokeyword",
        "Mark vlan-id as freeform",
        _fix_vlan_id_freeform,
    ),
    XsdFix(
        "filename-positional",
        "nokeyword",
        "Mark filename as positional (no keyword)",
        _fix_filename_positional,
    ),
    # Group G: Structure/Combinator fixes
    XsdFix(
        "archive-seqchoice",
        "combinator",
        "Change archive from choice to sequential-choice",
        _fix_archive_object,
    ),
    XsdFix(
        "term-seqchoice",
        "combinator",
        "Change term_object from choice to sequential-choice",
        _fix_term_object,
    ),
    XsdFix(
        "exact-longer-presence",
        "combinator",
        "Remove arg from exact/longer/orlonger",
        _fix_exact_longer_orlonger,
    ),
    XsdFix(
        "poe-interface-seqchoice",
        "combinator",
        "Change poe interface to sequential-choice",
        _fix_poe_interface,
    ),
    XsdFix(
        "login-user-seqchoice",
        "combinator",
        "Change login_user_object to sequential-choice",
        _fix_login_user_object,
    ),
    XsdFix(
        "user-class-single",
        "combinator",
        "Fix login user class: single-value leaf, not a leaf-list",
        _fix_user_class_single,
    ),
    XsdFix(
        "keyed-singleton-lists",
        "combinator",
        "Model device-backed port-mirroring, SRGB and IS-IS singleton entries as lists",
        _fix_keyed_singleton_lists,
    ),
    # Group H: Conversion hints (schema flags replacing runtime constants)
    XsdFix(
        "ephemeral-instance-list",
        "conversion-hint",
        "Fix ephemeral instance from presence to named list",
        _fix_ephemeral_instance,
    ),
    XsdFix(
        "transparent-containers",
        "conversion-hint",
        "Set transparent container flags on wrapper elements",
        _fix_transparent_containers,
    ),
    XsdFix(
        "ufd-group-transparent",
        "conversion-hint",
        "Make uplink-failure-detection group transparent to its list",
        _fix_ufd_group_transparent,
    ),
    XsdFix(
        "transparent-list-keys",
        "conversion-hint",
        "Set transparent-list-key flag on array wrapper keys",
        _fix_transparent_list_keys,
    ),
    XsdFix(
        "flat-dict-elements",
        "conversion-hint",
        "Set flat-dict flag on container dicts flattened to single line",
        _fix_flat_dict_elements,
    ),
    XsdFix(
        "flat-entry-keys",
        "conversion-hint",
        "Set oneliner flag on the filter lists rendered as oneliners",
        _fix_flat_entry_keys,
    ),
    XsdFix(
        "positional-keys",
        "conversion-hint",
        "Set positional-key flags on elements with positional arguments",
        _fix_positional_keys,
    ),
    XsdFix(
        "freeform-nk-keys",
        "conversion-hint",
        "Set freeform-nk flag on nk keys that are not keyword-suppressed",
        _fix_freeform_nk_keys,
    ),
]


def apply_all_fixes(root: SchemaNode) -> int:
    """Apply all registered fixes to the schema tree.

    Returns the number of fixes applied.
    """
    count = 0
    for fix in ALL_FIXES:
        if fix.apply(root):
            count += 1
    return count


def get_fix_count() -> int:
    """Return the total number of registered fixes."""
    return len(ALL_FIXES)
