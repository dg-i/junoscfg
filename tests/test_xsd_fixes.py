"""Tests for XSD structural fixes."""

from __future__ import annotations

from junoscfg.validate.schema_node import Combinator, SchemaNode
from junoscfg.validate.xsd_fixes import (
    ALL_FIXES,
    apply_all_fixes,
    get_fix_count,
)


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
        fix = next(f for f in ALL_FIXES if f.id == "groups-structure")
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
        fix = next(f for f in ALL_FIXES if f.id == "literal-equal")
        fix.apply(root)
        assert "=" in root.children
        assert "equal-literal" not in root.children

    def test_plus_literal_renamed(self):
        root = _make_root(("plus-literal", SchemaNode(name="plus-literal", is_leaf=True)))
        fix = next(f for f in ALL_FIXES if f.id == "literal-plus")
        fix.apply(root)
        assert "+" in root.children

    def test_minus_literal_renamed(self):
        root = _make_root(("minus-literal", SchemaNode(name="minus-literal", is_leaf=True)))
        fix = next(f for f in ALL_FIXES if f.id == "literal-minus")
        fix.apply(root)
        assert "-" in root.children


class TestGroupDMissingElements:
    def test_dhcp_added_as_sibling(self):
        dhcp_service = SchemaNode(name="dhcp-service", is_presence=True)
        processes = SchemaNode(name="processes", children={"dhcp-service": dhcp_service})
        system = SchemaNode(name="system", children={"processes": processes})
        root = _make_root(("system", system))

        fix = next(f for f in ALL_FIXES if f.id == "missing-dhcp")
        fix.apply(root)

        procs = root.children["system"].children["processes"]
        assert "dhcp" in procs.children

    def test_members_accepts_bracket(self):
        members = SchemaNode(name="members", is_leaf=True)
        root = _make_root(("members", members))

        fix = next(f for f in ALL_FIXES if f.id == "members-bracket")
        fix.apply(root)

        assert "accepts-bracket" in root.children["members"].flags

    def test_800g_speed_added(self):
        speed = SchemaNode(name="speed", enums=["100g", "400g"], is_leaf=True)
        root = _make_root(("speed", speed))

        fix = next(f for f in ALL_FIXES if f.id == "800g-speed")
        fix.apply(root)

        assert "800g" in root.children["speed"].enums


class TestGroupEWrongNames:
    def test_end_range_to(self):
        end_range = SchemaNode(name="end-range", is_leaf=True)
        member_range = SchemaNode(name="member-range", children={"end-range": end_range})
        root = _make_root(("member-range", member_range))

        fix = next(f for f in ALL_FIXES if f.id == "end-range-to")
        fix.apply(root)

        assert "to" in root.children["member-range"].children
        assert "end-range" not in root.children["member-range"].children

    def test_ieee_802_3ad(self):
        node = SchemaNode(name="ieee-802.3ad", is_leaf=True)
        root = _make_root(("ieee-802.3ad", node))

        fix = next(f for f in ALL_FIXES if f.id == "ieee-802.3ad")
        fix.apply(root)

        assert "802.3ad" in root.children

    def test_nat_rule_match(self):
        for old_name in ("dest-nat-rule-match", "src-nat-rule-match", "static-nat-rule-match"):
            node = SchemaNode(name=old_name, is_leaf=True)
            root = _make_root((old_name, node))

            fix = next(f for f in ALL_FIXES if f.id == "nat-rule-match")
            fix.apply(root)

            assert "match" in root.children

    def test_system_name_in_snmp(self):
        sys_name = SchemaNode(name="system-name", is_leaf=True)
        snmp = SchemaNode(name="snmp", children={"system-name": sys_name})
        root = _make_root(("snmp", snmp))

        fix = next(f for f in ALL_FIXES if f.id == "system-name")
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

        fix = next(f for f in ALL_FIXES if f.id == "ethernet-speed-prefix")
        fix.apply(root)

        assert "10g" in root.children["speed"].children
        assert "100g" in root.children["speed"].children
        assert "other" in root.children["speed"].children


class TestGroupFNokeyword:
    def test_vlan_name_freeform(self):
        vlan_name = SchemaNode(name="vlan-name", is_leaf=False)
        root = _make_root(("vlan-name", vlan_name))

        fix = next(f for f in ALL_FIXES if f.id == "vlan-name-freeform")
        fix.apply(root)

        assert root.children["vlan-name"].is_leaf is True
        assert "nokeyword" in root.children["vlan-name"].flags

    def test_vlan_id_freeform(self):
        vlan_id = SchemaNode(name="vlan-id", is_leaf=False)
        root = _make_root(("vlan-id", vlan_id))

        fix = next(f for f in ALL_FIXES if f.id == "vlan-id-freeform")
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

        fix = next(f for f in ALL_FIXES if f.id == "archive-seqchoice")
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

        fix = next(f for f in ALL_FIXES if f.id == "term-seqchoice")
        fix.apply(root)

        assert root.children["term"].combinator == Combinator.SEQ_CHOICE

    def test_exact_longer_presence(self):
        exact = SchemaNode(name="exact", is_leaf=True)
        longer = SchemaNode(name="longer", is_leaf=True)
        orlonger = SchemaNode(name="orlonger", is_leaf=True)
        root = _make_root(("exact", exact), ("longer", longer), ("orlonger", orlonger))

        fix = next(f for f in ALL_FIXES if f.id == "exact-longer-presence")
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

        fix = next(f for f in ALL_FIXES if f.id == "login-user-seqchoice")
        fix.apply(root)

        user_node = root.children["system"].children["login"].children["user"]
        assert user_node.combinator == Combinator.SEQ_CHOICE
