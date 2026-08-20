"""Per-registry-type tests for find_unused against the BUNDLED registry.

Each reportable type in the curated registry
(src/junoscfg/audit/data/unused-types.yaml) gets a scenario with a
definition, a real reference position, and the expected definition path.
The scenarios are exercised through the standard rules: unused,
used, unknown-position (probably-unused), and duplicate definition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

import pytest

from junoscfg.audit import find_unused

if TYPE_CHECKING:
    from typing import Any

    from junoscfg.audit.model import AuditResult, Finding

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
            f"set policy-options policy-statement p1 term 1 from as-path-neighbors {TARGET}",
        ),
        expected_def_path=("policy-options", "as-list", TARGET),
    ),
    TypeScenario(
        type_name="as-list-group",
        def_lines=(f"set policy-options as-list-group {TARGET} as-list a1 members 64498",),
        ref_lines=(f"set policy-options policy-statement p1 term 1 from as-path-origins {TARGET}",),
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


class TestCollision:
    def test_prefix_list_position_is_not_a_policy_statement_reference(self, make_ir: Any) -> None:
        # "aud-col" appears only at a position owned by prefix-list, so the
        # policy-statement finding must stay a strict "unused".
        result = audit(
            make_ir,
            (
                "set policy-options policy-statement aud-col term 1 then accept",
                "set policy-options policy-statement other term 1 from prefix-list aud-col",
            ),
        )
        findings = [
            f for f in result.findings if f.type_name == "policy-statement" and f.name == "aud-col"
        ]
        assert len(findings) == 1
        finding = findings[0]
        assert finding.confidence == "unused"
        assert finding.unresolved == ()


class TestConfigGroupImplicit:
    def test_implicit_group_re0_is_never_reported(self, make_ir: Any) -> None:
        result = audit(make_ir, ("set groups re0 system host-name router1",))
        assert result.findings == ()
        assert result.definitions_checked == 0
