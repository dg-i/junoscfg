"""find_unused against the bundled registry.

Every reportable type in the curated registry
(src/junoscfg/audit/data/unused-types.yaml) gets a scenario with a
definition, a real reference position, and the expected definition path,
run through the standard rules: unused, used, unknown position
(probably-unused) and duplicate definition. The rules themselves, with inline
registries, are in ``test_engine.py``. The classes after the scenarios pin
reference positions the adversarial review of the audit found unseen.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple

import pytest

from junoscfg.audit import find_unused, load_registry
from junoscfg.convert import to_dict

if TYPE_CHECKING:
    from junoscfg.audit import AuditResult, Finding

TARGET = "aud-target"


class TypeScenario(NamedTuple):
    """One reportable registry type with its definition and reference lines.

    Attributes:
        type_name: Registry type key.
        def_lines: Set commands defining an object named ``aud-target``.
        ref_lines: Set commands referencing ``aud-target`` at a real
            registry reference position.
        expected_def_path: ``Finding.path`` expected for the unused case.
        alt_refs: Additional reference variants as (id-suffix, lines) pairs;
            each variant must also count as a use.
        duplicate_ok: False for types where the groups-based duplicate
            scenario does not apply (config groups share one namespace).
    """

    type_name: str
    def_lines: tuple[str, ...]
    ref_lines: tuple[str, ...]
    expected_def_path: tuple[str, ...]
    alt_refs: tuple[tuple[str, tuple[str, ...]], ...] = ()
    duplicate_ok: bool = True


TYPE_SCENARIOS: list[TypeScenario] = [
    TypeScenario(
        type_name="policy-statement",
        def_lines=(f"set policy-options policy-statement {TARGET} term 1 then accept",),
        ref_lines=(f"set protocols bgp group ebgp import {TARGET}",),
        expected_def_path=("policy-options", "policy-statement", TARGET),
    ),
    TypeScenario(
        type_name="prefix-list",
        def_lines=(f"set policy-options prefix-list {TARGET} 10.0.0.0/8",),
        ref_lines=(f"set policy-options policy-statement p1 term 1 from prefix-list {TARGET}",),
        expected_def_path=("policy-options", "prefix-list", TARGET),
        alt_refs=(
            (
                "firewall-from",
                (f"set firewall family inet filter f1 term t1 from source-prefix-list {TARGET}",),
            ),
        ),
    ),
    TypeScenario(
        type_name="community",
        def_lines=(f"set policy-options community {TARGET} members 64496:100",),
        ref_lines=(f"set policy-options policy-statement p1 term 1 from community {TARGET}",),
        expected_def_path=("policy-options", "community", TARGET),
        alt_refs=(
            (
                "then-community",
                (f"set policy-options policy-statement p1 term 1 then community add {TARGET}",),
            ),
        ),
    ),
    TypeScenario(
        type_name="as-path",
        def_lines=(f'set policy-options as-path {TARGET} "^64496"',),
        ref_lines=(f"set policy-options policy-statement p1 term 1 from as-path {TARGET}",),
        expected_def_path=("policy-options", "as-path", TARGET),
    ),
    TypeScenario(
        type_name="as-path-group",
        def_lines=(f'set policy-options as-path-group {TARGET} as-path a1 "^64497"',),
        ref_lines=(f"set policy-options policy-statement p1 term 1 from as-path-group {TARGET}",),
        expected_def_path=("policy-options", "as-path-group", TARGET),
    ),
    TypeScenario(
        type_name="as-list",
        def_lines=(f"set policy-options as-list {TARGET} members 64496",),
        ref_lines=(
            f"set policy-options policy-statement p1 term 1 from as-path-neighbors as-list "
            f"{TARGET}",
        ),
        expected_def_path=("policy-options", "as-list", TARGET),
    ),
    TypeScenario(
        type_name="as-list-group",
        def_lines=(f"set policy-options as-list-group {TARGET} as-list a1 members 64498",),
        ref_lines=(
            f"set policy-options policy-statement p1 term 1 from as-path-origins as-list-group "
            f"{TARGET}",
        ),
        expected_def_path=("policy-options", "as-list-group", TARGET),
    ),
    TypeScenario(
        type_name="condition",
        def_lines=(f"set policy-options condition {TARGET} if-route-exists 10.0.0.0/8",),
        ref_lines=(f"set policy-options policy-statement p1 term 1 from condition {TARGET}",),
        expected_def_path=("policy-options", "condition", TARGET),
    ),
    TypeScenario(
        type_name="damping",
        def_lines=(f"set policy-options damping {TARGET} half-life 15",),
        ref_lines=(f"set policy-options policy-statement p1 term 1 then damping {TARGET}",),
        expected_def_path=("policy-options", "damping", TARGET),
    ),
    TypeScenario(
        type_name="route-filter-list",
        def_lines=(f"set policy-options route-filter-list {TARGET} 10.0.0.0/8 exact",),
        ref_lines=(
            f"set policy-options policy-statement p1 term 1 from route-filter-list {TARGET}",
        ),
        expected_def_path=("policy-options", "route-filter-list", TARGET),
    ),
    TypeScenario(
        type_name="firewall-filter",
        def_lines=(f"set firewall family inet filter {TARGET} term t1 then accept",),
        ref_lines=(f"set interfaces ge-0/0/0 unit 0 family inet filter input {TARGET}",),
        expected_def_path=("firewall", "family", "inet", "filter", TARGET),
        alt_refs=(
            (
                "input-list",
                (f"set interfaces ge-0/0/0 unit 0 family inet filter input-list {TARGET}",),
            ),
        ),
    ),
    TypeScenario(
        type_name="policer",
        def_lines=(f"set firewall policer {TARGET} then discard",),
        ref_lines=(f"set firewall family inet filter f1 term t1 then policer {TARGET}",),
        expected_def_path=("firewall", "policer", TARGET),
    ),
    # rib-group was missing from the registry until the adversarial review.
    TypeScenario(
        type_name="rib-group",
        def_lines=(f"set routing-options rib-groups {TARGET} import-rib inet.0",),
        ref_lines=(f"set protocols bgp group g family inet unicast rib-group {TARGET}",),
        expected_def_path=("routing-options", "rib-groups", TARGET),
        alt_refs=(
            (
                "interface-routes",
                (f"set routing-options interface-routes rib-group inet {TARGET}",),
            ),
        ),
    ),
    TypeScenario(
        type_name="config-group",
        def_lines=(f"set groups {TARGET} system host-name router1",),
        ref_lines=(f"set apply-groups {TARGET}",),
        expected_def_path=("groups", TARGET),
        alt_refs=(
            (
                "apply-groups-except",
                (f"set interfaces ge-0/0/0 apply-groups-except {TARGET}",),
            ),
        ),
        duplicate_ok=False,
    ),
    TypeScenario(
        type_name="login-class",
        def_lines=(f"set system login class {TARGET} permissions view",),
        ref_lines=(f"set system login user operator1 class {TARGET}",),
        expected_def_path=("system", "login", "class", TARGET),
    ),
    TypeScenario(
        type_name="snmp-view",
        def_lines=(f"set snmp view {TARGET} oid 1.3.6.1 include",),
        ref_lines=(f"set snmp community comm1 view {TARGET}",),
        expected_def_path=("snmp", "view", TARGET),
    ),
]

SCENARIO_IDS = [scenario.type_name for scenario in TYPE_SCENARIOS]

# All (scenario, reference-variant) pairs: primary ref plus alt_refs.
REF_CASES = [
    pytest.param(scenario, scenario.ref_lines, id=scenario.type_name) for scenario in TYPE_SCENARIOS
] + [
    pytest.param(scenario, ref_lines, id=f"{scenario.type_name}-{suffix}")
    for scenario in TYPE_SCENARIOS
    for suffix, ref_lines in scenario.alt_refs
]

DUPLICATE_SCENARIOS = [scenario for scenario in TYPE_SCENARIOS if scenario.duplicate_ok]
DUPLICATE_IDS = [scenario.type_name for scenario in DUPLICATE_SCENARIOS]


def audit(make_ir: Any, lines: tuple[str, ...]) -> AuditResult:
    """Run the bundled-registry audit over the given set commands."""
    return find_unused(make_ir("\n".join(lines)))


def target_findings(result: AuditResult, type_name: str) -> list[Finding]:
    """Findings for (type_name, aud-target)."""
    return [f for f in result.findings if f.type_name == type_name and f.name == TARGET]


class TestTheScenariosCoverTheRegistry:
    def test_every_reportable_type_has_a_scenario(self) -> None:
        """A type added to the registry without a scenario would go untested."""
        assert sorted(SCENARIO_IDS) == sorted(load_registry().reportable())


@pytest.mark.parametrize("scenario", TYPE_SCENARIOS, ids=SCENARIO_IDS)
class TestUnused:
    def test_definition_only_is_unused(self, make_ir: Any, scenario: TypeScenario) -> None:
        result = audit(make_ir, scenario.def_lines)
        findings = target_findings(result, scenario.type_name)
        assert len(findings) == 1
        finding = findings[0]
        assert finding.confidence == "unused"
        assert finding.path == scenario.expected_def_path
        assert finding.unresolved == ()
        assert not finding.duplicate_definition
        # No collateral findings: nested member entries (as-path-group
        # as-path a1, as-list-group as-list a1) are report:false anchors
        # and must never surface.
        assert [f.name for f in result.findings] == [TARGET]


@pytest.mark.parametrize(("scenario", "ref_lines"), REF_CASES)
class TestUsed:
    def test_reference_removes_finding(
        self, make_ir: Any, scenario: TypeScenario, ref_lines: tuple[str, ...]
    ) -> None:
        result = audit(make_ir, scenario.def_lines + ref_lines)
        assert target_findings(result, scenario.type_name) == []


@pytest.mark.parametrize("scenario", TYPE_SCENARIOS, ids=SCENARIO_IDS)
class TestUnknownPosition:
    def test_unknown_occurrence_downgrades_to_probably_unused(
        self, make_ir: Any, scenario: TypeScenario
    ) -> None:
        lines = scenario.def_lines + (f"set interfaces ge-0/0/0 description {TARGET}",)
        result = audit(make_ir, lines)
        findings = target_findings(result, scenario.type_name)
        assert len(findings) == 1
        finding = findings[0]
        assert finding.confidence == "probably-unused"
        assert len(finding.unresolved) > 0
        assert all(occurrence.value == TARGET for occurrence in finding.unresolved)


@pytest.mark.parametrize("scenario", DUPLICATE_SCENARIOS, ids=DUPLICATE_IDS)
class TestDuplicateDefinition:
    def test_same_definition_in_group_reports_both(
        self, make_ir: Any, scenario: TypeScenario
    ) -> None:
        grouped = tuple(line.replace("set ", "set groups g1 ", 1) for line in scenario.def_lines)
        result = audit(make_ir, scenario.def_lines + grouped)
        findings = target_findings(result, scenario.type_name)
        assert len(findings) == 2
        assert all(f.duplicate_definition for f in findings)
        assert all(f.confidence == "unused" for f in findings)
        assert {f.path for f in findings} == {
            scenario.expected_def_path,
            ("groups", "g1", *scenario.expected_def_path),
        }


def audit_names(set_text: str, **kwargs: Any) -> set[str]:
    """Names of every finding for the set text, with the bundled registry."""
    return {f.name for f in find_unused(to_dict(set_text.strip(), "set"), **kwargs).findings}


class TestEveryLeafListItemIsAUse:
    """Each item of a repeated leaf-list reference counts, not only the first."""

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


class TestReferencesBesideATransparentList:
    """The siblings of a transparent list's entries are walked as well."""

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


class TestANumericNameMatchesANumericReference:
    """A name the IR holds as a number is matched as one on both sides."""

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


class TestAPolicyNameWithSpacesIsReferenced:
    """A quoted policy name is one name in a policy-algebra leaf, alone or in an
    expression. Its tokenizing is in ``test_algebra.py``."""

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


class TestABareLeafFilterFamilyIsAReference:
    """A filter family whose filter is a bare leaf (ethernet-switching, mpls, ...)."""

    def test_ethernet_switching_filter(self) -> None:
        cfg = """
        set firewall family ethernet-switching filter ESW term 1 then accept
        set interfaces ge-0/0/5 unit 0 family ethernet-switching filter input ESW
        """
        assert audit_names(cfg, types=["firewall-filter"]) == set()


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
