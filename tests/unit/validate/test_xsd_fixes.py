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
            assert fix.applies_to, f"Fix {fix.id} missing applies_to"

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
