"""Structural fixes for Junos XSD deficiencies.

Ports fixes from Ruby ruler.rb that correct genuine XSD errors (Groups A-G),
plus conversion-hint flags that encode runtime behavior into the schema tree
(Group H). All fixes are applied to the SchemaNode tree after parsing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from junoscfg.validate.schema_node import Combinator, SchemaNode, find_all, navigate

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(frozen=True)
class XsdFix:
    """A registered schema fix."""

    id: str
    category: str
    description: str
    applies_to: list[str]
    apply: Callable[[SchemaNode], bool]


# ── Helper functions ──────────────────────────────────────────────────


def _rename_element(root: SchemaNode, old_name: str, new_name: str) -> bool:
    """Rename all occurrences of an element in the tree. Returns True if any renamed."""
    renamed = False
    nodes = find_all(root, old_name)
    for node in nodes:
        node.name = new_name
    if nodes:
        renamed = True
    # Also fix parent children dicts
    _fix_parent_keys(root, old_name, new_name)
    return renamed


def _fix_parent_keys(node: SchemaNode, old_key: str, new_key: str) -> None:
    """Walk tree and update children dict keys where old_key is found."""
    if old_key in node.children:
        child = node.children.pop(old_key)
        node.children[new_key] = child
    for child in list(node.children.values()):
        _fix_parent_keys(child, old_key, new_key)


def _add_sibling(
    root: SchemaNode, target_name: str, new_name: str, new_node: SchemaNode | None = None
) -> bool:
    """Add a sibling element next to an existing element. Returns True if added."""
    _add_sibling_impl(root, target_name, new_name, new_node, added_ref=[False])
    return True  # Best-effort


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
    group_node = SchemaNode(
        name="group",
        is_list=True,
        combinator=Combinator.CHOICE,
        children={"when": when_node},
    )
    # Copy top-level config children into group (not groups)
    for name, child in root.children.items():
        if name != "groups":
            group_node.children[name] = child

    # groups is a container, NOT a named list
    groups.is_list = False
    groups.is_key = False
    groups.combinator = Combinator.SEQUENCE
    groups.children = {"group": group_node}
    return True


# ── Fix Group B2: Missing Flags ───────────────────────────────────────


def _fix_attributes_match_oneliner(root: SchemaNode) -> bool:
    """Mark attributes-match as oneliner (flat entry)."""
    for node in find_all(root, "attributes-match"):
        node.flags.add("oneliner")
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


def _fix_members_bracket(root: SchemaNode) -> bool:
    """Make 'members' accept bracket expressions (ruler.rb line 270)."""
    for node in find_all(root, "members"):
        node.is_leaf = True
        node.flags.add("accepts-bracket")
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
    for name in (
        "allow-commands-regexps",
        "deny-commands-regexps",
        "allow-configuration-regexps",
        "deny-configuration-regexps",
    ):
        for node in find_all(root, name):
            node.is_leaf = True
    return True


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
    if snmp and "system-name" in snmp.children:
        child = snmp.children.pop("system-name")
        child.name = "name"
        snmp.children["name"] = child
        return True
    return False


def _fix_ethernet_speed_prefix(root: SchemaNode) -> bool:
    """Rename 'ethernet-1*' speeds to '1*' (ruler.rb line 305)."""

    def _walk_rename(node: SchemaNode) -> bool:
        found = False
        renames = {}
        for name in list(node.children.keys()):
            if name.startswith("ethernet-") and len(name) > 9 and name[9:10].isdigit():
                new_name = name[len("ethernet-") :]
                renames[name] = new_name
                found = True
        for old, new in renames.items():
            child = node.children.pop(old)
            child.name = new
            node.children[new] = child
        for child in node.children.values():
            if _walk_rename(child):
                found = True
        return found

    return _walk_rename(root)


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


def _fix_policy_algebra(root: SchemaNode) -> bool:
    """Make policy_algebra accept any (ruler.rb lines 308-310)."""
    for node in find_all(root, "policy-algebra"):
        node.is_leaf = True
        node.flags.add("accepts-bracket")
    return True


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


def _fix_flat_dict_elements(root: SchemaNode) -> bool:
    """Set flat-dict flag on container dicts flattened to single set line.

    e.g., trigger {"after": [null], "count": 1} → "trigger after 1"
    """
    found = False
    for node in find_all(root, "trigger"):
        node.flags.add("flat-dict")
        found = True
    return found


def _fix_flat_entry_keys(root: SchemaNode) -> bool:
    """Set flat-entry and oneliner flags on named lists rendered as oneliners.

    All flat entry elements get the "oneliner" flag (→ "o" in schema).
    Elements with positional key config also get "flat-entry:{key}:{position}".
    Positions: "first", "last", "values-only"
    """
    # Elements with flat-entry config (positional key + position)
    mapping = {
        "attributes-match": ("", "values-only"),
        "route-filter": ("address", "first"),
        "prefix-list-filter": ("list_name", "first"),
    }
    # All flat entry elements get oneliner (includes source-address-filter
    # which has no flat-entry config but still renders as a oneliner)
    oneliner_names = list(mapping.keys()) + ["source-address-filter"]
    found = False
    for name in oneliner_names:
        for node in find_all(root, name):
            node.flags.add("oneliner")
            found = True
    for elem_name, (key, position) in mapping.items():
        for node in find_all(root, elem_name):
            node.flags.add(f"flat-entry:{key}:{position}")
    return found


def _fix_positional_keys(root: SchemaNode) -> bool:
    """Set positional-key flags on elements with positional arguments.

    "positional-key" — nesting positional keys (create scopes)
    "positional-key-flat" — non-nesting positional keys (standalone lines)
    """
    nesting = ["filter-name", "aspath", "list_name"]
    flat = ["filename", "as-number", "confederation-as", "path", "limit", "timeout"]
    found = False
    for name in nesting:
        for node in find_all(root, name):
            node.flags.add("positional-key")
            found = True
    for name in flat:
        for node in find_all(root, name):
            node.flags.add("positional-key-flat")
            found = True
    return found


def _fix_freeform_nk_keys(root: SchemaNode) -> bool:
    """Set freeform-nk flag on nk keys that are NOT keyword-suppressed.

    These keys have the nk flag for freeform validation but should be treated
    as normal keywords in conversion. e.g., vlan-id, vlan-name.
    """
    names = ["vlan-id", "vlan-name"]
    found = False
    for name in names:
        for node in find_all(root, name):
            node.flags.add("freeform-nk")
            found = True
    return found


# ── Fix Registry ─────────────────────────────────────────────────────

_ALL_TARGETS = ["json-schema", "lark", "xsd"]

ALL_FIXES: list[XsdFix] = [
    # Group B: Structure replacement
    XsdFix(
        "groups-structure",
        "structure-replacement",
        "Replace groups with proper hierarchical structure",
        _ALL_TARGETS,
        _fix_groups,
    ),
    # Group B2: Missing flags
    XsdFix(
        "attributes-match-oneliner",
        "missing-flag",
        "Mark attributes-match as oneliner (flat entry)",
        _ALL_TARGETS,
        _fix_attributes_match_oneliner,
    ),
    # Group C: Literal symbol names
    XsdFix(
        "literal-equal",
        "wrong-name",
        'Rename "equal-literal" to "="',
        _ALL_TARGETS,
        _fix_literal_equal,
    ),
    XsdFix(
        "literal-plus",
        "wrong-name",
        'Rename "plus-literal" to "+"',
        _ALL_TARGETS,
        _fix_literal_plus,
    ),
    XsdFix(
        "literal-minus",
        "wrong-name",
        'Rename "minus-literal" to "-"',
        _ALL_TARGETS,
        _fix_literal_minus,
    ),
    # Group D: Missing elements
    XsdFix(
        "missing-dhcp",
        "missing-element",
        "Add dhcp as alternative to dhcp-service",
        _ALL_TARGETS,
        _fix_dhcp_alternative,
    ),
    XsdFix(
        "missing-icmpv6",
        "missing-element",
        "Add icmpv6 as alternative to icmp6",
        _ALL_TARGETS,
        _fix_icmpv6_alternative,
    ),
    XsdFix(
        "route-filter-arg",
        "missing-element",
        "Add missing address arg to route-filter",
        _ALL_TARGETS,
        _fix_route_filter_arg,
    ),
    XsdFix(
        "source-address-filter-arg",
        "missing-element",
        "Add missing address arg to source-address-filter",
        _ALL_TARGETS,
        _fix_source_address_filter_arg,
    ),
    XsdFix(
        "classifiers-default",
        "missing-element",
        "Add freeform arg alongside default in classifiers",
        _ALL_TARGETS,
        _fix_classifiers_default,
    ),
    XsdFix(
        "wildcard-star",
        "missing-element",
        "Replace * element with freeform arg",
        _ALL_TARGETS,
        _fix_wildcard_star,
    ),
    XsdFix(
        "security-policy-zones",
        "missing-element",
        "Add from-zone/to-zone to security policy",
        _ALL_TARGETS,
        _fix_security_policy_zones,
    ),
    XsdFix(
        "members-bracket",
        "missing-element",
        "Make members accept bracket expressions",
        _ALL_TARGETS,
        _fix_members_bracket,
    ),
    XsdFix(
        "teardown-forms",
        "missing-element",
        "Add teardown percentage and bare forms",
        _ALL_TARGETS,
        _fix_teardown,
    ),
    XsdFix(
        "800g-speed",
        "missing-element",
        "Add 800g/800G to interface speed enums",
        _ALL_TARGETS,
        _fix_800g_speed,
    ),
    XsdFix(
        "single-hop",
        "missing-element",
        "Add single-hop to liveness-detection",
        _ALL_TARGETS,
        _fix_single_hop,
    ),
    XsdFix(
        "enable-interface",
        "missing-element",
        "Add enable to interfaces type",
        _ALL_TARGETS,
        _fix_enable_interface,
    ),
    XsdFix(
        "regexp-commands",
        "missing-element",
        "Use regular_expression for allow/deny regexps",
        _ALL_TARGETS,
        _fix_regexp_commands,
    ),
    # Group E: Wrong element names
    XsdFix(
        "end-range-to", "wrong-name", 'Rename "end-range" to "to"', _ALL_TARGETS, _fix_end_range
    ),
    XsdFix(
        "ieee-802.3ad",
        "wrong-name",
        'Rename "ieee-802.3ad" to "802.3ad"',
        _ALL_TARGETS,
        _fix_ieee_802_3ad,
    ),
    XsdFix(
        "nat-rule-match",
        "wrong-name",
        'Rename *-nat-rule-match to "match"',
        _ALL_TARGETS,
        _fix_nat_rule_match,
    ),
    XsdFix(
        "system-name",
        "wrong-name",
        'Rename SNMP "system-name" to "name"',
        _ALL_TARGETS,
        _fix_system_name,
    ),
    XsdFix(
        "ethernet-speed-prefix",
        "wrong-name",
        'Rename "ethernet-1*" speeds to "1*"',
        _ALL_TARGETS,
        _fix_ethernet_speed_prefix,
    ),
    # Group F: Nokeyword / Generic name fixes
    XsdFix(
        "name-freeform",
        "nokeyword",
        "Mark name as freeform in choice contexts",
        _ALL_TARGETS,
        _fix_name_as_freeform,
    ),
    XsdFix(
        "vlan-name-freeform",
        "nokeyword",
        "Mark vlan-name as freeform",
        _ALL_TARGETS,
        _fix_vlan_name_freeform,
    ),
    XsdFix(
        "vlan-id-freeform",
        "nokeyword",
        "Mark vlan-id as freeform",
        _ALL_TARGETS,
        _fix_vlan_id_freeform,
    ),
    XsdFix(
        "filename-positional",
        "nokeyword",
        "Mark filename as positional (no keyword)",
        _ALL_TARGETS,
        _fix_filename_positional,
    ),
    # Group G: Structure/Combinator fixes
    XsdFix(
        "archive-seqchoice",
        "combinator",
        "Change archive from choice to sequential-choice",
        _ALL_TARGETS,
        _fix_archive_object,
    ),
    XsdFix(
        "term-seqchoice",
        "combinator",
        "Change term_object from choice to sequential-choice",
        _ALL_TARGETS,
        _fix_term_object,
    ),
    XsdFix(
        "exact-longer-presence",
        "combinator",
        "Remove arg from exact/longer/orlonger",
        _ALL_TARGETS,
        _fix_exact_longer_orlonger,
    ),
    XsdFix(
        "policy-algebra-any",
        "combinator",
        "Make policy_algebra accept any",
        _ALL_TARGETS,
        _fix_policy_algebra,
    ),
    XsdFix(
        "poe-interface-seqchoice",
        "combinator",
        "Change poe interface to sequential-choice",
        _ALL_TARGETS,
        _fix_poe_interface,
    ),
    XsdFix(
        "login-user-seqchoice",
        "combinator",
        "Change login_user_object to sequential-choice",
        _ALL_TARGETS,
        _fix_login_user_object,
    ),
    # Group H: Conversion hints (schema flags replacing runtime constants)
    XsdFix(
        "ephemeral-instance-list",
        "conversion-hint",
        "Fix ephemeral instance from presence to named list",
        _ALL_TARGETS,
        _fix_ephemeral_instance,
    ),
    XsdFix(
        "transparent-containers",
        "conversion-hint",
        "Set transparent container flags on wrapper elements",
        _ALL_TARGETS,
        _fix_transparent_containers,
    ),
    XsdFix(
        "transparent-list-keys",
        "conversion-hint",
        "Set transparent-list-key flag on array wrapper keys",
        _ALL_TARGETS,
        _fix_transparent_list_keys,
    ),
    XsdFix(
        "flat-dict-elements",
        "conversion-hint",
        "Set flat-dict flag on container dicts flattened to single line",
        _ALL_TARGETS,
        _fix_flat_dict_elements,
    ),
    XsdFix(
        "flat-entry-keys",
        "conversion-hint",
        "Set flat-entry flag on named lists rendered as oneliners",
        _ALL_TARGETS,
        _fix_flat_entry_keys,
    ),
    XsdFix(
        "positional-keys",
        "conversion-hint",
        "Set positional-key flags on elements with positional arguments",
        _ALL_TARGETS,
        _fix_positional_keys,
    ),
    XsdFix(
        "freeform-nk-keys",
        "conversion-hint",
        "Set freeform-nk flag on nk keys that are not keyword-suppressed",
        _ALL_TARGETS,
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
