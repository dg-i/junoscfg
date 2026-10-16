"""Tests for XSD structural fixes."""

from __future__ import annotations

import pytest

from junoscfg.validate import (
    ALL_FIXES,
    Combinator,
    SchemaNode,
    XsdFix,
    apply_all_fixes,
    get_fix_count,
)


def registered(fix_id: str) -> XsdFix:
    """The registered fix *fix_id*; a renamed or dropped fix fails here by name."""
    found = [f for f in ALL_FIXES if f.id == fix_id]
    assert len(found) == 1, f"{fix_id!r} is registered {len(found)} times"
    return found[0]


def _make_root(*children_items: tuple[str, SchemaNode]) -> SchemaNode:
    """Create a minimal root node with given children."""
    return SchemaNode(
        name="configuration",
        children=dict(children_items),
        combinator=Combinator.CHOICE,
    )


class TestFixRegistry:
    def test_fix_count(self):
        assert get_fix_count() == len(ALL_FIXES)
        # All fixes have unique IDs
        ids = [f.id for f in ALL_FIXES]
        assert len(ids) == len(set(ids))

    def test_all_fixes_have_metadata(self):
        for fix in ALL_FIXES:
            assert fix.id, "Fix missing id"
            assert fix.category, f"Fix {fix.id} missing category"
            assert fix.description, f"Fix {fix.id} missing description"

    def test_apply_all_fixes_returns_count(self):
        root = _make_root()
        count = apply_all_fixes(root)
        # On an empty root, most fixes won't match — count reflects actual applications
        assert count <= get_fix_count()

    def test_apply_all_fixes_counts_actual_applications(self):
        """Verify return reflects actual successes, not total attempts."""
        # With a root that has 'equal-literal', at least the literal rename should succeed
        root = _make_root(("equal-literal", SchemaNode(name="equal-literal", is_leaf=True)))
        count = apply_all_fixes(root)
        # Should count only fixes that actually applied, not all fixes
        assert count < get_fix_count()


class TestGroupBGroupsFix:
    def test_groups_structure_replaced(self):
        groups = SchemaNode(name="groups", is_list=True, combinator=Combinator.SEQUENCE)
        system = SchemaNode(
            name="system", children={"host-name": SchemaNode(name="host-name", is_leaf=True)}
        )
        root = _make_root(("groups", groups), ("system", system))

        # Apply just the groups fix
        fix = registered("groups-structure")
        fix.apply(root)

        # groups is a container (not a named list)
        assert not root.children["groups"].is_list
        assert root.children["groups"].combinator == Combinator.SEQUENCE

        # group is a named list child under groups (like interface under interfaces)
        assert "group" in root.children["groups"].children
        group = root.children["groups"].children["group"]
        assert group.is_list

        # Verify group has when and config children
        assert "when" in group.children
        when = group.children["when"]
        assert "chassis" in when.children
        assert "routing-engine" in when.children
        assert "time" in when.children

        # Config children copied into group
        assert "system" in group.children


class TestGroupCLiteralNames:
    def test_equal_literal_renamed(self):
        root = _make_root(("equal-literal", SchemaNode(name="equal-literal", is_leaf=True)))
        fix = registered("literal-equal")
        fix.apply(root)
        assert "=" in root.children
        assert "equal-literal" not in root.children

    def test_plus_literal_renamed(self):
        root = _make_root(("plus-literal", SchemaNode(name="plus-literal", is_leaf=True)))
        fix = registered("literal-plus")
        fix.apply(root)
        assert "+" in root.children

    def test_minus_literal_renamed(self):
        root = _make_root(("minus-literal", SchemaNode(name="minus-literal", is_leaf=True)))
        fix = registered("literal-minus")
        fix.apply(root)
        assert "-" in root.children


class TestGroupDMissingElements:
    def test_dhcp_added_as_sibling(self):
        dhcp_service = SchemaNode(name="dhcp-service", is_presence=True)
        processes = SchemaNode(name="processes", children={"dhcp-service": dhcp_service})
        system = SchemaNode(name="system", children={"processes": processes})
        root = _make_root(("system", system))

        fix = registered("missing-dhcp")
        fix.apply(root)

        procs = root.children["system"].children["processes"]
        assert "dhcp" in procs.children

    def test_apply_statements_are_modelled_once_on_the_root(self):
        """The four meta-statements no NETCONF XSD carries.

        Checked in 21.4R0, 23.2R2, 23.4R2 and 25.2R2: not one of them appears
        as an element or a ref in any of them, so six modules in this package
        each compensated for their absence in a different way.
        """
        root = _make_root(("system", SchemaNode(name="system")))

        fix = registered("apply-statements")
        assert fix.apply(root)

        for name in (
            "apply-groups",
            "apply-groups-except",
            "apply-flags",
            "apply-macro",
        ):
            assert name in root.children, name
            assert "universal" in root.children[name].flags, name

        assert root.children["apply-groups"].is_leaf
        assert root.children["apply-groups"].is_list
        # `apply-macro m1 key1 val1` writes a run where the tree has structure.
        assert "flat-dict" in root.children["apply-macro"].flags

    def test_apply_flags_is_the_devices_container_of_flags(self):
        """`apply-flags` holds presence flags, as the device writes it.

        The device prints `set groups GR-OMIT system apply-flags omit`, XML
        `<apply-flags><omit/></apply-flags>` and JSON `"apply-flags": {"omit":
        [null]}` (vMX 23.2R2-S7.5 and QFX5120 25.2R2-S1.5,
        `tests/data/device/synthetic/*/junoscfg-oracle.{set,xml,json}.gz`).
        This fix modelled it as a single leaf, so set and curly `apply-flags
        omit` read as another IR than JSON and XML did (DEV-V2). `replace` is
        the spelling the grammar accepted from a production configuration;
        its JSON and XML shape is inferred from `omit` (probe P8). Change
        universal-statements-from-tree.
        """
        root = _make_root(("system", SchemaNode(name="system")))
        registered("apply-statements").apply(root)

        flags = root.children["apply-flags"]
        assert not flags.is_leaf
        assert not flags.is_list
        assert set(flags.children) == {"omit", "replace"}
        for name, flag in flags.children.items():
            assert flag.is_presence, name
            assert not flag.is_leaf, name

    def test_apply_statements_do_not_land_below_the_root(self):
        """Declared once, not copied under each of 123,769 containers.

        A copy per container is equally true of Junos and costs +24 MB on the
        structure tree; the `universal` flag says the same thing in 242 bytes
        and the generators splice it.
        """
        system = SchemaNode(name="system")
        root = _make_root(("system", system))

        registered("apply-statements").apply(root)

        assert "apply-groups" not in system.children

    def test_members_is_made_a_leaf(self):
        """What the fix achieves, not what it used to claim.

        It also set an `accepts-bracket` flag that `_serialize_node` had no key
        for, so the flag never reached an artifact and nothing ever read it.
        This assertion passed on an in-memory tree while the correction could
        not ship.
        """
        members = SchemaNode(name="members")
        root = _make_root(("members", members))

        fix = registered("members-bracket")
        fix.apply(root)

        assert root.children["members"].is_leaf
        assert not root.children["members"].flags

    def test_800g_speed_added(self):
        speed = SchemaNode(name="speed", enums=["100g", "400g"], is_leaf=True)
        root = _make_root(("speed", speed))

        fix = registered("800g-speed")
        fix.apply(root)

        assert "800g" in root.children["speed"].enums


class TestGroupEWrongNames:
    def test_end_range_to(self):
        end_range = SchemaNode(name="end-range", is_leaf=True)
        member_range = SchemaNode(name="member-range", children={"end-range": end_range})
        root = _make_root(("member-range", member_range))

        fix = registered("end-range-to")
        fix.apply(root)

        assert "to" in root.children["member-range"].children
        assert "end-range" not in root.children["member-range"].children

    def test_ieee_802_3ad(self):
        node = SchemaNode(name="ieee-802.3ad", is_leaf=True)
        root = _make_root(("ieee-802.3ad", node))

        fix = registered("ieee-802.3ad")
        fix.apply(root)

        assert "802.3ad" in root.children

    def test_nat_rule_match(self):
        for old_name in ("dest-nat-rule-match", "src-nat-rule-match", "static-nat-rule-match"):
            node = SchemaNode(name=old_name, is_leaf=True)
            root = _make_root((old_name, node))

            fix = registered("nat-rule-match")
            fix.apply(root)

            assert "match" in root.children

    def test_system_name_in_snmp(self):
        sys_name = SchemaNode(name="system-name", is_leaf=True)
        snmp = SchemaNode(name="snmp", children={"system-name": sys_name})
        root = _make_root(("snmp", snmp))

        fix = registered("system-name")
        fix.apply(root)

        assert "name" in root.children["snmp"].children
        assert "system-name" not in root.children["snmp"].children

    def test_ethernet_speed_prefix(self):
        speeds = SchemaNode(
            name="speed",
            children={
                "ethernet-10g": SchemaNode(name="ethernet-10g", is_presence=True),
                "ethernet-100g": SchemaNode(name="ethernet-100g", is_presence=True),
                "other": SchemaNode(name="other", is_presence=True),
            },
        )
        root = _make_root(("speed", speeds))

        fix = registered("ethernet-speed-prefix")
        fix.apply(root)

        assert "10g" in root.children["speed"].children
        assert "100g" in root.children["speed"].children
        assert "other" in root.children["speed"].children


class TestGroupFNokeyword:
    def test_vlan_name_freeform(self):
        vlan_name = SchemaNode(name="vlan-name", is_leaf=False)
        root = _make_root(("vlan-name", vlan_name))

        fix = registered("vlan-name-freeform")
        fix.apply(root)

        assert root.children["vlan-name"].is_leaf is True
        assert "nokeyword" in root.children["vlan-name"].flags

    def test_vlan_id_freeform(self):
        vlan_id = SchemaNode(name="vlan-id", is_leaf=False)
        root = _make_root(("vlan-id", vlan_id))

        fix = registered("vlan-id-freeform")
        fix.apply(root)

        assert root.children["vlan-id"].is_leaf is True


class TestGroupGCombinator:
    def test_archive_seqchoice(self):
        archive = SchemaNode(
            name="archive",
            children={"a": SchemaNode(name="a"), "b": SchemaNode(name="b")},
            combinator=Combinator.CHOICE,
        )
        root = _make_root(("archive", archive))

        fix = registered("archive-seqchoice")
        fix.apply(root)

        assert root.children["archive"].combinator == Combinator.SEQ_CHOICE

    def test_term_seqchoice(self):
        term = SchemaNode(
            name="term",
            children={
                "from": SchemaNode(name="from"),
                "then": SchemaNode(name="then"),
            },
            combinator=Combinator.CHOICE,
        )
        root = _make_root(("term", term))

        fix = registered("term-seqchoice")
        fix.apply(root)

        assert root.children["term"].combinator == Combinator.SEQ_CHOICE

    def test_exact_longer_presence(self):
        exact = SchemaNode(name="exact", is_leaf=True)
        longer = SchemaNode(name="longer", is_leaf=True)
        orlonger = SchemaNode(name="orlonger", is_leaf=True)
        root = _make_root(("exact", exact), ("longer", longer), ("orlonger", orlonger))

        fix = registered("exact-longer-presence")
        fix.apply(root)

        for name in ("exact", "longer", "orlonger"):
            assert root.children[name].is_presence is True

    def test_login_user_seqchoice(self):
        user = SchemaNode(
            name="user",
            children={"full-name": SchemaNode(name="full-name", is_leaf=True)},
            combinator=Combinator.CHOICE,
        )
        login = SchemaNode(name="login", children={"user": user})
        system = SchemaNode(name="system", children={"login": login})
        root = _make_root(("system", system))

        fix = registered("login-user-seqchoice")
        fix.apply(root)

        user_node = root.children["system"].children["login"].children["user"]
        assert user_node.combinator == Combinator.SEQ_CHOICE

    def test_user_class_single(self):
        class_node = SchemaNode(name="class", is_leaf=True, is_list=True)
        user = SchemaNode(name="user", is_list=True, children={"class": class_node})
        login = SchemaNode(name="login", children={"user": user})
        system = SchemaNode(name="system", children={"login": login})
        root = _make_root(("system", system))

        fix = registered("user-class-single")
        applied = fix.apply(root)

        assert applied is True
        fixed = root.children["system"].children["login"].children["user"].children["class"]
        assert fixed.is_leaf is True
        assert fixed.is_list is False

    def test_user_class_single_noop_when_already_fixed(self):
        class_node = SchemaNode(name="class", is_leaf=True, is_list=False)
        user = SchemaNode(name="user", is_list=True, children={"class": class_node})
        login = SchemaNode(name="login", children={"user": user})
        system = SchemaNode(name="system", children={"login": login})
        root = _make_root(("system", system))

        fix = registered("user-class-single")
        applied = fix.apply(root)

        assert applied is False


class TestGroupHUfdGroupTransparent:
    """`uplink-failure-detection group` is transparent to `ufd-group-name`.

    The name-keyed transparent table cannot say so, because `group` is also
    BGP's list; this fix is scoped to the parent and leaves every other
    `group` alone.
    """

    @staticmethod
    def _fix():
        return registered("ufd-group-transparent")

    @staticmethod
    def _tree() -> SchemaNode:
        ufd_list = SchemaNode(
            name="ufd-group-name",
            is_list=True,
            children={"link-to-monitor": SchemaNode(name="link-to-monitor", is_list=True)},
        )
        ufd = SchemaNode(
            name="uplink-failure-detection",
            children={"group": SchemaNode(name="group", children={"ufd-group-name": ufd_list})},
        )
        bgp = SchemaNode(
            name="bgp",
            children={"group": SchemaNode(name="group", is_list=True)},
        )
        return _make_root(
            (
                "protocols",
                SchemaNode(
                    name="protocols", children={"uplink-failure-detection": ufd, "bgp": bgp}
                ),
            )
        )

    def test_the_wrapper_is_flagged(self) -> None:
        tree = self._tree()
        assert self._fix().apply(tree) is True
        group = tree.children["protocols"].children["uplink-failure-detection"].children["group"]
        assert "transparent:ufd-group-name" in group.flags

    def test_bgps_group_is_left_alone(self) -> None:
        tree = self._tree()
        self._fix().apply(tree)
        assert not tree.children["protocols"].children["bgp"].children["group"].flags

    def test_a_tree_without_the_statement_reports_nothing_applied(self) -> None:
        assert self._fix().apply(_make_root()) is False


class TestFlatPositionalHints:
    @pytest.mark.parametrize(
        "name", ["filename", "as-number", "confederation-as", "path", "limit", "timeout"]
    )
    @pytest.mark.parametrize(
        "flags",
        [set(), {"nokeyword"}, {"nokeyword", "freeform-nk"}],
        ids=["keyworded", "positional", "freeform-keyworded"],
    )
    def test_only_a_positional_leaf_receives_the_hint(self, name: str, flags: set[str]) -> None:
        """NEW-A-S1: a name cannot turn a keyworded leaf into an argument."""
        leaf = SchemaNode(name=name, is_leaf=True, flags=flags.copy())
        root = _make_root((name, leaf))
        registered("positional-keys").apply(root)
        assert ("positional-key-flat" in leaf.flags) == (flags == {"nokeyword"})


class TestTriggerFlattening:
    def test_only_event_options_trigger_is_flattened(self) -> None:
        """NEW-B3: same-named trigger nodes outside event-options are hierarchical."""
        trigger = SchemaNode(
            name="trigger",
            children={"count": SchemaNode(name="count", is_leaf=True, flags={"nokeyword"})},
        )
        within = SchemaNode(name="within", children={"trigger": trigger})
        policy = SchemaNode(name="policy", children={"within": within})
        event = SchemaNode(name="event-options", children={"policy": policy})
        optical = SchemaNode(name="trigger", children={"oc-los": SchemaNode(name="oc-los")})
        unrelated = SchemaNode(name="trigger")
        group_trigger = SchemaNode(name="trigger")
        group = SchemaNode(
            name="group",
            children={
                "event-options": SchemaNode(
                    name="event-options",
                    children={
                        "policy": SchemaNode(
                            name="policy",
                            children={
                                "within": SchemaNode(
                                    name="within", children={"trigger": group_trigger}
                                )
                            },
                        )
                    },
                )
            },
        )
        root = _make_root(
            ("event-options", event),
            ("interfaces", SchemaNode(name="interfaces", children={"trigger": optical})),
            ("other", SchemaNode(name="other", children={"trigger": unrelated})),
            ("groups", SchemaNode(name="groups", children={"group": group})),
        )
        registered("flat-dict-elements").apply(root)
        assert "flat-dict" in trigger.flags
        assert "flat-dict" in group_trigger.flags
        assert "flat-dict" not in optical.flags
        assert "flat-dict" not in unrelated.flags


class TestKeyedSingletonLists:
    """Only admitted source-qualified paths change; copied references stay consistent."""

    PATHS = (
        ("forwarding-options", "port-mirroring", "family", "inet", "output", "routing-instance"),
        ("protocols", "mpls", "label-range", "srgb-label-range"),
        ("protocols", "isis", "interface", "level", "application-specific", "attribute-group"),
        (
            "protocols",
            "isis-instance",
            "interface",
            "level",
            "application-specific",
            "attribute-group",
        ),
    )
    #: The copies of the same elements: root and groups, each bare, in a
    #: routing instance, a logical system and a tenant (change device-validation).
    PREFIXES = [
        (*group, *instance)
        for group in ((), ("groups", "group"))
        for instance in (
            (),
            ("routing-instances", "instance"),
            ("logical-systems",),
            ("logical-systems", "routing-instances", "instance"),
            ("tenants", "routing-instances", "instance"),
        )
    ]

    @staticmethod
    def entry(**overrides) -> SchemaNode:
        fields = dict(
            name="entry",
            children={
                "name": SchemaNode(name="name", is_leaf=True, is_key=True, flags={"nokeyword"}),
                "child": SchemaNode(name="child", is_leaf=True),
            },
            combinator=Combinator.SEQ_CHOICE,
            key_fields=("name",),
        )
        fields.update(overrides)
        return SchemaNode(**fields)

    @staticmethod
    def at_path(root: SchemaNode, path: tuple[str, ...], entry: SchemaNode) -> None:
        node = root
        for name in path[:-1]:
            node = node.children.setdefault(name, SchemaNode(name=name))
        entry.name = path[-1]
        node.children[path[-1]] = entry

    @pytest.mark.parametrize("path", PATHS)
    @pytest.mark.parametrize("prefix", PREFIXES)
    def test_a_declared_positional_identifier_makes_the_named_entry_a_list(self, path, prefix):
        root = _make_root()
        entry = self.entry()
        self.at_path(root, prefix + path, entry)
        children = tuple(entry.children.items())
        keys = entry.key_fields
        combinator = entry.combinator
        fix = registered("keyed-singleton-lists")
        assert fix.apply(root)
        assert entry.is_list
        assert tuple(entry.children.items()) == children
        assert entry.key_fields == keys
        assert entry.combinator is combinator
        assert not fix.apply(root)

    @pytest.mark.parametrize(
        "case",
        [
            "value",
            "keyworded",
            "freeform",
            "key-leaf-list",
            "leaf",
            "leaf-list",
            "presence",
            "unkeyed",
            "other-key-order",
            "other-path",
        ],
    )
    def test_a_name_or_homogeneous_flag_does_not_promote_a_non_entry(self, case):
        root = _make_root()
        entry = self.entry(flags={"homogeneous"})
        key = entry.children["name"]
        path = self.PATHS[0]
        if case == "value":
            key.is_key = False
        elif case == "keyworded":
            key.flags.clear()
        elif case == "freeform":
            key.flags.add("freeform-nk")
        elif case == "key-leaf-list":
            key.is_list = True
        elif case == "leaf":
            entry.is_leaf = True
        elif case == "leaf-list":
            entry.is_leaf = True
            entry.is_list = True
        elif case == "presence":
            entry.is_presence = True
        elif case == "unkeyed":
            del entry.children["name"]
        elif case == "other-key-order":
            entry.key_fields = ("name", "child")
        elif case == "other-path":
            path = ("access", "securid-server")
        self.at_path(root, path, entry)
        before = entry.is_list
        assert not registered("keyed-singleton-lists").apply(root)
        assert entry.is_list is before

    def test_root_and_group_shared_entry_is_changed_once(self):
        root = _make_root()
        entry = self.entry()
        for prefix in ((), ("groups", "group")):
            self.at_path(root, prefix + self.PATHS[0], entry)
        assert registered("keyed-singleton-lists").apply(root)
        assert entry.is_list


class TestARenameKeepsTheDevicesName:
    """A Group E fix renames an element to its CLI keyword; the device writes the
    element's own name in XML and JSON (`"ieee-802.3ad"`, `"end-range"` in every
    `junoscfg-oracle.json.gz`), so the node records it (`xml-name:`) for the JSON
    schema, the JSON writer and the readers (change device-validation)."""

    CASES = [
        ("end-range-to", ("member-range",), "end-range", "to"),
        ("ieee-802.3ad", ("ether-options",), "ieee-802.3ad", "802.3ad"),
        ("nat-rule-match", ("rule",), "src-nat-rule-match", "match"),
        ("system-name", ("snmp",), "system-name", "name"),
        ("ethernet-speed-prefix", ("speed",), "ethernet-1g", "1g"),
        ("literal-equal", ("community",), "equal-literal", "="),
        ("literal-plus", ("community",), "plus-literal", "+"),
        ("literal-minus", ("community",), "minus-literal", "-"),
        ("hello-padding", ("isis", "interface"), "hello-padding-type", "hello-padding"),
    ]

    @pytest.mark.parametrize(("fix_id", "parents", "element", "keyword"), CASES)
    def test_every_rename_records_the_element_name(self, fix_id, parents, element, keyword):
        node = SchemaNode(name=element, is_leaf=True)
        parent = SchemaNode(name=parents[-1], children={element: node})
        for name in reversed(parents[:-1]):
            parent = SchemaNode(name=name, children={parent.name: parent})
        root = _make_root((parent.name, parent))

        assert registered(fix_id).apply(root)

        holder = root
        for name in parents:
            holder = holder.children[name]
        assert list(holder.children) == [keyword]
        assert holder.children[keyword] is node
        assert node.name == keyword
        assert f"xml-name:{element}" in node.flags

    def test_every_wrong_name_fix_is_a_case(self):
        assert {f.id for f in ALL_FIXES if f.category == "wrong-name"} == {
            fix_id for fix_id, *_ in self.CASES
        }


#: The statements a committed capture holds inside the device's `<undocumented>`,
#: each at a path of the shipped tree where its parent's XSD type occurs, with the
#: shape the capture's XML gives it: `l` a leaf, `p` a presence flag, a dict its
#: children. Evidence: `tests/data/device/synthetic/*/junoscfg-oracle.xml.gz` and
#: `tests/data/device/jvd/vmx-23.2R2-S7.5/bng1_mx304.xml.gz`.
UNDOCUMENTED = [
    (("system", "login", "user"), "shell", "l"),
    # The QFX5120 25.2R2-S1.5 takes `clear-text address` beside `port`, and the
    # flags below, inside `<undocumented>` (probe D4, P4; change device-probe-fixes).
    (
        ("system", "services", "extension-service", "request-response", "grpc"),
        "clear-text",
        {"address": "l", "port": "l"},
    ),
    # `system dump-on-panic` prints as an open and close tag, a container's
    # shape (`<dump-on-panic>\n</dump-on-panic>`); the others print as `<x/>`.
    *(
        row
        for prefix in ((), ("groups", "group"))
        for row in (
            ((*prefix, "system"), "dump-on-panic", {}),
            ((*prefix, "system"), "debugger-on-break", "p"),
            ((*prefix, "system"), "debugger-on-panic", "p"),
            ((*prefix, "chassis"), "dump-on-panic", "p"),
            (
                (*prefix, "system", "services", "extension-service", "request-response", "grpc"),
                "clear-text",
                {"address": "l", "port": "l"},
            ),
        )
    ),
    (
        ("system", "services", "extension-service", "request-response", "grpc"),
        "skip-authentication",
        "p",
    ),
    (
        ("system", "ddos-protection", "protocols"),
        "autoconf",
        {"aggregate": {"bandwidth": "l", "burst": "l"}},
    ),
    (("protocols", "bgp", "group", "family", "inet6", "labeled-unicast"), "per-prefix-label", "p"),
    (
        ("protocols", "bgp", "group", "neighbor", "family", "inet6", "labeled-unicast"),
        "per-prefix-label",
        "p",
    ),
    (
        (
            "routing-instances",
            "instance",
            "protocols",
            "bgp",
            "group",
            "family",
            "inet6",
            "labeled-unicast",
        ),
        "per-prefix-label",
        "p",
    ),
    (("system", "services", "dhcp-local-server"), "stale-timer", "l"),
    (("system", "services", "dhcp-local-server"), "no-stale-timer-refresh", "p"),
    (
        ("routing-instances", "instance", "system", "services", "dhcp-local-server"),
        "stale-timer",
        "l",
    ),
    (
        ("routing-instances", "instance", "system", "services", "dhcp-local-server"),
        "no-stale-timer-refresh",
        "p",
    ),
    (("groups", "group", "system", "login", "user"), "shell", "l"),
]


def _shape(node: dict) -> object:
    if node.get("l"):
        return "l"
    if node.get("p"):
        assert not node.get("c"), "a flag holds no statement"
        return "p"
    return {name: _shape(child) for name, child in node.get("c", {}).items()}


class TestUndocumentedStatementsAreModelled:
    """Juniper's XSD omits what the device's own XML wraps in `<undocumented>`; a
    device loaded and printed each of these, so the schema model declares them
    as the capture shapes them, wherever the parent's XSD type occurs (change
    device-validation)."""

    @pytest.mark.parametrize(
        ("path", "statement", "shape"),
        UNDOCUMENTED,
        ids=[f"{'/'.join(path)}/{statement}" for path, statement, _ in UNDOCUMENTED],
    )
    def test_the_statement_is_declared_where_its_parent_type_occurs(
        self, bundled_tree, path, statement, shape
    ):
        node = bundled_tree["c"]
        for name in path:
            node = node[name]["c"]
        assert statement in node
        assert _shape(node[statement]) == shape


class TestKeyedSingletonListsOfTheDevicesArrays:
    """The vMX 23.2R2-S7.5 prints `protocols isis-instance ... application-specific
    attribute-group` as an array (`jvd/vmx-23.2R2-S7.5/mdr1_acx7509.json.gz`), as it
    does under `protocols isis`; the JSON schema rejected it (change
    device-validation)."""

    PATH = (
        "protocols",
        "isis-instance",
        "interface",
        "level",
        "application-specific",
        "attribute-group",
    )

    @pytest.mark.parametrize("prefix", [(), ("groups", "group")])
    def test_the_isis_instance_attribute_group_is_a_list(self, bundled_tree, prefix):
        node = bundled_tree["c"]
        for name in (*prefix, *self.PATH[:-1]):
            node = node[name]["c"]
        assert node[self.PATH[-1]].get("L")
