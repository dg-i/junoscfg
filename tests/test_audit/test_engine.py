"""Tests for the audit classification engine (run_audit / find_unused)."""

from __future__ import annotations

from typing import Any

import pytest

from junoscfg.audit import find_unused
from junoscfg.audit.engine import run_audit
from junoscfg.audit.registry import TypeEntry
from tests.test_audit.conftest import (
    CONFIG_GROUP,
    POLICY_STATEMENT,
    PREFIX_LIST,
    make_registry,
)

POLICY_DEF = "set policy-options policy-statement pol-a term 1 then accept"

# Namespace-only entry (report: false) that anchors collision classification.
AS_PATH_NAMESPACE = TypeEntry(
    name="as-path",
    source="curated",
    definition=(("policy-options", "as-path"),),
    report=False,
)


class TestConfidence:
    def test_unused_when_no_external_occurrence(self, make_ir: Any) -> None:
        config = make_ir(POLICY_DEF)
        result = run_audit(config, make_registry(POLICY_STATEMENT))
        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.type_name == "policy-statement"
        assert finding.name == "pol-a"
        assert finding.path == ("policy-options", "policy-statement", "pol-a")
        assert finding.confidence == "unused"
        assert finding.unresolved == ()
        assert not finding.duplicate_definition
        assert result.n_unused == 1
        assert result.n_probably_unused == 0

    def test_probably_unused_on_unknown_leaf_position(self, make_ir: Any) -> None:
        config = make_ir(
            f"""
            {POLICY_DEF}
            set interfaces ge-0/0/0 description pol-a
            """
        )
        result = run_audit(config, make_registry(POLICY_STATEMENT))
        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.confidence == "probably-unused"
        assert len(finding.unresolved) == 1
        occurrence = finding.unresolved[0]
        assert occurrence.value == "pol-a"
        assert occurrence.path == ("interfaces", "ge-0/0/0", "description", "pol-a")
        assert result.n_unused == 0
        assert result.n_probably_unused == 1

    def test_used_produces_no_finding(self, make_ir: Any) -> None:
        config = make_ir(
            f"""
            {POLICY_DEF}
            set protocols bgp group ebgp-peers import pol-a
            """
        )
        result = run_audit(config, make_registry(POLICY_STATEMENT))
        assert result.findings == ()
        assert result.definitions_checked == 1


class TestCollisionRule:
    def test_position_owned_by_other_type_is_not_a_reference(self, make_ir: Any) -> None:
        config = make_ir(
            """
            set policy-options policy-statement shared term 1 then accept
            set policy-options policy-statement referrer term 1 from prefix-list shared
            """
        )
        result = run_audit(config, make_registry(POLICY_STATEMENT, PREFIX_LIST))
        by_key = {(f.type_name, f.name): f for f in result.findings}
        shared = by_key[("policy-statement", "shared")]
        assert shared.confidence == "unused"
        assert shared.unresolved == ()
        assert not shared.duplicate_definition

    def test_same_named_prefix_list_is_used(self, make_ir: Any) -> None:
        config = make_ir(
            """
            set policy-options policy-statement shared term 1 then accept
            set policy-options policy-statement referrer term 1 from prefix-list shared
            set policy-options prefix-list shared 10.0.0.0/8
            """
        )
        result = run_audit(config, make_registry(POLICY_STATEMENT, PREFIX_LIST))
        keys = {(f.type_name, f.name) for f in result.findings}
        assert ("prefix-list", "shared") not in keys
        assert ("policy-statement", "shared") in keys
        by_key = {(f.type_name, f.name): f for f in result.findings}
        assert by_key[("policy-statement", "shared")].confidence == "unused"


class TestDuplicateRule:
    def test_duplicate_definitions_reported_for_both_paths(self, make_ir: Any) -> None:
        config = make_ir(
            """
            set policy-options policy-statement dup term 1 then accept
            set groups g1 policy-options policy-statement dup term 1 then reject
            """
        )
        result = run_audit(config, make_registry(POLICY_STATEMENT))
        assert len(result.findings) == 2
        assert all(f.name == "dup" for f in result.findings)
        assert all(f.duplicate_definition for f in result.findings)
        assert all(f.confidence == "unused" for f in result.findings)
        assert {f.path for f in result.findings} == {
            ("policy-options", "policy-statement", "dup"),
            ("groups", "g1", "policy-options", "policy-statement", "dup"),
        }
        assert result.definitions_checked == 2


IMPLICIT_GROUP_CASES: list[tuple[str, bool]] = [
    ("re0", False),
    ("member0", False),
    ("memberx", False),
    ("other-name", True),
]


class TestImplicitGroups:
    @pytest.mark.parametrize(("group_name", "reported"), IMPLICIT_GROUP_CASES)
    def test_implicit_globs(self, make_ir: Any, group_name: str, reported: bool) -> None:
        config = make_ir(f"set groups {group_name} system host-name router1")
        result = run_audit(config, make_registry(CONFIG_GROUP))
        assert (group_name in [f.name for f in result.findings]) is reported
        assert result.definitions_checked == (1 if reported else 0)


class TestApplyGroups:
    def test_apply_groups_except_counts_as_use(self, make_ir: Any) -> None:
        config = make_ir(
            """
            set groups g-exc system host-name router1
            set interfaces ge-0/0/0 apply-groups-except g-exc
            """
        )
        result = run_audit(config, make_registry(CONFIG_GROUP))
        assert result.findings == ()
        assert result.definitions_checked == 1


class TestSelfReference:
    def test_self_reference_does_not_count_as_use(self, make_ir: Any) -> None:
        config = make_ir("set policy-options policy-statement foo term 1 from policy foo")
        result = run_audit(config, make_registry(POLICY_STATEMENT))
        assert len(result.findings) == 1
        finding = result.findings[0]
        assert finding.name == "foo"
        assert finding.confidence == "unused"
        assert finding.unresolved == ()

    def test_reference_from_other_policy_counts_as_use(self, make_ir: Any) -> None:
        config = make_ir(
            """
            set policy-options policy-statement foo term 1 from policy foo
            set policy-options policy-statement referrer term 1 from policy foo
            """
        )
        result = run_audit(config, make_registry(POLICY_STATEMENT))
        assert [f.name for f in result.findings] == ["referrer"]


class TestDeadGroupReference:
    def test_reference_inside_unapplied_group_counts(self, make_ir: Any) -> None:
        config = make_ir(
            f"""
            {POLICY_DEF}
            set groups g-dead protocols bgp group ebgp-peers import pol-a
            """
        )
        result = run_audit(config, make_registry(POLICY_STATEMENT, CONFIG_GROUP))
        assert [(f.type_name, f.name) for f in result.findings] == [("config-group", "g-dead")]
        assert result.findings[0].confidence == "unused"


class TestMatchFilter:
    def test_match_filters_definitions_but_corpus_stays_whole(self, make_ir: Any) -> None:
        config = make_ir(
            """
            set policy-options policy-statement old-pol term 1 then accept
            set policy-options policy-statement old-used term 1 then accept
            set policy-options policy-statement new-pol term 1 then accept
            set protocols bgp group ebgp-peers import old-used
            """
        )
        result = run_audit(config, make_registry(POLICY_STATEMENT), match="^old-")
        # new-pol is unused but filtered out; old-used is referenced from a
        # position outside the match filter — the corpus is never filtered.
        assert [f.name for f in result.findings] == ["old-pol"]
        assert result.definitions_checked == 2

    def test_invalid_regex_raises_value_error(self, make_ir: Any) -> None:
        config = make_ir(POLICY_DEF)
        with pytest.raises(ValueError, match="invalid match regex"):
            run_audit(config, make_registry(POLICY_STATEMENT), match="[")


class TestTypesFilter:
    def test_types_restricts_audited_definitions(self, make_ir: Any) -> None:
        config = make_ir(
            f"""
            {POLICY_DEF}
            set groups other-grp system host-name router1
            """
        )
        registry = make_registry(POLICY_STATEMENT, CONFIG_GROUP)
        result = run_audit(config, registry, types=["policy-statement"])
        assert result.types_audited == ("policy-statement",)
        assert [(f.type_name, f.name) for f in result.findings] == [
            ("policy-statement", "pol-a"),
        ]
        assert result.definitions_checked == 1

    def test_unknown_type_raises_value_error_listing_valid_names(self, make_ir: Any) -> None:
        config = make_ir(POLICY_DEF)
        registry = make_registry(POLICY_STATEMENT, CONFIG_GROUP)
        with pytest.raises(ValueError) as exc_info:
            run_audit(config, registry, types=["bogus-type"])
        message = str(exc_info.value)
        assert "unknown audit type(s): bogus-type" in message
        assert "policy-statement" in message
        assert "config-group" in message

    def test_report_false_type_rejected_in_types(self, make_ir: Any) -> None:
        config = make_ir(POLICY_DEF)
        registry = make_registry(POLICY_STATEMENT, AS_PATH_NAMESPACE)
        with pytest.raises(ValueError, match="unknown audit type"):
            run_audit(config, registry, types=["as-path"])


class TestFindUnused:
    def test_accepts_wrapped_ir(self, make_ir: Any) -> None:
        ir = {"configuration": make_ir(POLICY_DEF)}
        result = find_unused(ir, registry=make_registry(POLICY_STATEMENT))
        assert [f.name for f in result.findings] == ["pol-a"]

    def test_accepts_bare_policy_options_dict(self) -> None:
        ir: dict[str, Any] = {"policy-options": {"policy-statement": [{"name": "pol-a"}]}}
        result = find_unused(ir, registry=make_registry(POLICY_STATEMENT))
        assert [f.name for f in result.findings] == ["pol-a"]
        assert result.findings[0].confidence == "unused"


class TestResultMetadata:
    def test_definitions_checked_and_types_audited(self, make_ir: Any) -> None:
        config = make_ir(
            """
            set policy-options policy-statement pol-a term 1 then accept
            set policy-options policy-statement pol-b term 1 then accept
            set groups re0 system host-name router1
            set groups other-grp system host-name r1
            """
        )
        registry = make_registry(POLICY_STATEMENT, CONFIG_GROUP)
        result = run_audit(config, registry)
        # pol-a, pol-b and other-grp are checked; re0 is implicit.
        assert result.definitions_checked == 3
        assert result.types_audited == ("policy-statement", "config-group")


class TestOrdering:
    def test_findings_sorted_by_registry_order_then_name(self, make_ir: Any) -> None:
        config = make_ir(
            """
            set policy-options policy-statement zz-pol term 1 then accept
            set policy-options policy-statement aa-pol term 1 then accept
            set policy-options prefix-list pl-b 192.168.1.0/24
            set policy-options prefix-list pl-a 10.0.0.0/8
            set groups other-grp system host-name router1
            """
        )
        registry = make_registry(POLICY_STATEMENT, PREFIX_LIST, CONFIG_GROUP)
        result = run_audit(config, registry)
        assert [(f.type_name, f.name) for f in result.findings] == [
            ("policy-statement", "aa-pol"),
            ("policy-statement", "zz-pol"),
            ("prefix-list", "pl-a"),
            ("prefix-list", "pl-b"),
            ("config-group", "other-grp"),
        ]
