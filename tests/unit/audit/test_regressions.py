"""Regression tests for issues found in adversarial review.

Each test pins a fix for a confirmed safety-property or contract bug so it
cannot silently return. See the audit review findings for context.
"""

from __future__ import annotations

from typing import Any

from junoscfg.audit import find_unused
from junoscfg.convert import to_dict


def audit_names(set_text: str, **kwargs: Any) -> set[str]:
    ir = to_dict(set_text.strip(), "set")
    return {f.name for f in find_unused(ir, **kwargs).findings}


def strict_unused(set_text: str, **kwargs: Any) -> set[str]:
    ir = to_dict(set_text.strip(), "set")
    return {f.name for f in find_unused(ir, **kwargs).findings if f.confidence == "unused"}


class TestLeafListReferences:
    """Repeated canonical leaf-list references must all be recognized."""

    def test_from_community_repeated(self) -> None:
        cfg = """
        set policy-options community C1 members 64496:1
        set policy-options community C2 members 64496:2
        set policy-options policy-statement POL term t from community C1
        set policy-options policy-statement POL term t from community C2
        set policy-options policy-statement POL term t then accept
        set protocols bgp group g import POL
        """
        assert "C1" not in audit_names(cfg)
        assert "C2" not in audit_names(cfg)

    def test_filter_input_list_repeated(self) -> None:
        cfg = """
        set firewall family inet filter F1 term t then accept
        set firewall family inet filter F2 term t then accept
        set interfaces ge-0/0/0 unit 0 family inet filter input-list F1
        set interfaces ge-0/0/0 unit 0 family inet filter input-list F2
        """
        assert audit_names(cfg, types=["firewall-filter"]) == set()


class TestTransparentContainerSiblings:
    """Sibling keys of a transparent child must still be walked."""

    def test_apply_groups_under_routing_instances(self) -> None:
        cfg = """
        set groups G1 system host-name r1
        set routing-instances apply-groups G1
        set routing-instances VRF1 instance-type vrf
        """
        assert "G1" not in audit_names(cfg)

    def test_interface_range_filter_reference(self) -> None:
        cfg = """
        set firewall family inet filter RANGE-FILT term 1 then accept
        set interfaces interface-range ACCESS unit 0 family inet filter input RANGE-FILT
        """
        assert "RANGE-FILT" not in audit_names(cfg)


class TestNumericNames:
    """Numeric-named objects referenced via numeric leaves are not unused."""

    def test_numeric_filter_name(self) -> None:
        ir: dict[str, Any] = {
            "configuration": {
                "firewall": {"family": {"inet": {"filter": [{"name": 100}]}}},
                "interfaces": {
                    "interface": [
                        {
                            "name": "lo0",
                            "unit": [
                                {
                                    "name": "0",
                                    "family": {"inet": {"filter": {"input": {"filter-name": 100}}}},
                                }
                            ],
                        }
                    ]
                },
            }
        }
        result = find_unused(ir, types=["firewall-filter"])
        assert [f.name for f in result.findings] == []


class TestQuotedPolicyNames:
    """Policy names with spaces referenced via policy-algebra leaves."""

    def test_single_quoted_name(self) -> None:
        cfg = """
        set policy-options policy-statement "my pol" term 1 then accept
        set protocols ospf import "my pol"
        """
        assert "my pol" not in audit_names(cfg)

    def test_quoted_name_in_expression(self) -> None:
        cfg = """
        set policy-options policy-statement "my pol" term 1 then accept
        set policy-options policy-statement OTHER term 1 then reject
        set protocols bgp group g import ( "my pol" && ! OTHER )
        """
        used = audit_names(cfg)
        assert "my pol" not in used
        assert "OTHER" not in used


class TestBareLeafFilterFamilies:
    """Bare-leaf filter families (ethernet-switching, mpls, ...) count as refs."""

    def test_ethernet_switching_filter(self) -> None:
        cfg = """
        set firewall family ethernet-switching filter ESW term 1 then accept
        set interfaces ge-0/0/5 unit 0 family ethernet-switching filter input ESW
        """
        assert audit_names(cfg, types=["firewall-filter"]) == set()


class TestRibGroup:
    """rib-group objects are audited (regression: type was missing)."""

    def test_unused_rib_group_reported(self) -> None:
        cfg = "set routing-options rib-groups RG-DEAD import-rib inet.0"
        assert "RG-DEAD" in strict_unused(cfg, types=["rib-group"])

    def test_referenced_rib_group_not_reported(self) -> None:
        cfg = """
        set routing-options rib-groups RG-USED import-rib inet.0
        set protocols bgp group g family inet unicast rib-group RG-USED
        """
        assert "RG-USED" not in audit_names(cfg)

    def test_interface_routes_reference(self) -> None:
        cfg = """
        set routing-options rib-groups RG-IR import-rib inet.0
        set routing-options interface-routes rib-group inet RG-IR
        """
        assert "RG-IR" not in audit_names(cfg)


class TestKeyedReferences:
    """An AS list referenced by its key field is used.

    The set reader kept `as-list` as the entry's `name` and dropped the list
    name, so every AS list a policy referenced was reported unused. Spec:
    identifier-key-fields, audit/keyed-references.
    """

    DEFINITIONS = """
        set policy-options as-list AS-LIST-A members 64496
        set policy-options as-list AS-LIST-B members 64497
        set policy-options as-list-group ASG-A as-list A1 members 64498
        set policy-options as-list-group ASG-B as-list B1 members 64499
    """

    def test_an_as_list_used_by_as_path_neighbors_is_not_unused(self) -> None:
        cfg = (
            self.DEFINITIONS
            + """
        set policy-options policy-statement POL term t from as-path-neighbors as-list AS-LIST-A
        set policy-options policy-statement POL term t from as-path-origins as-list-group ASG-A
        set policy-options policy-statement POL term t then accept
        set protocols bgp group g import POL
        """
        )
        names = audit_names(cfg)
        assert "AS-LIST-A" not in names
        assert "ASG-A" not in names
        assert {"AS-LIST-B", "ASG-B"} <= names
        assert "as-list" not in names and "as-list-group" not in names

    def test_a_name_used_by_one_list_type_does_not_use_the_other(self) -> None:
        """`as-list X` and `as-list-group X` are two entries and two objects."""
        cfg = """
        set policy-options as-list SAMPLE-X members 64496
        set policy-options as-list-group SAMPLE-X as-list A1 members 64498
        set policy-options policy-statement POL from as-path-transits as-list SAMPLE-X
        set protocols bgp group g import POL
        """
        result = find_unused(to_dict(cfg.strip(), "set"))
        unused = {(f.type_name, f.name) for f in result.findings}
        assert ("as-list", "SAMPLE-X") not in unused
        assert ("as-list-group", "SAMPLE-X") in unused
