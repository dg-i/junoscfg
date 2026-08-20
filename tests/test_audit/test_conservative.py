"""Safety-property tests for the conservative classification rule (d).

An object whose name occurs at a position the registry does not know
must NEVER be reported as strict ``unused``: the verdict degrades to
``probably-unused`` and the blocking occurrence is surfaced in the
finding's ``unresolved`` tuple. An incomplete registry may reduce
precision but never produces a confident delete suggestion for an
object that is actually referenced.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from junoscfg.audit.engine import run_audit
from junoscfg.audit.walker import collect_occurrences
from junoscfg.display.constants import load_schema_tree
from tests.test_audit.conftest import POLICY_STATEMENT, make_registry

if TYPE_CHECKING:
    from collections.abc import Callable

    from junoscfg.audit.model import AuditResult, Finding, OccurrenceKind

    MakeIr = Callable[[str], dict[str, Any]]

NAME = "pol-unref"

BASE_DEFINITION = f"set policy-options policy-statement {NAME} then accept"

# (case id, extra display-set lines, extra top-level IR keys, expected occurrence kind)
UNKNOWN_POSITION_CASES: list[tuple[str, str | None, dict[str, Any] | None, OccurrenceKind]] = [
    (
        "unknown-leaf-value",
        f"set interfaces ge-0/0/0 description {NAME}",
        None,
        "leaf",
    ),
    (
        "leaf-list-item",
        f"set system domain-search {NAME}",
        None,
        "leaf",
    ),
    (
        "unknown-key-subtree",
        None,
        {"custom-automation": {"target-policy": {"value": NAME}}},
        "unknown",
    ),
    (
        "apply-macro-data-value",
        f"set policy-options policy-statement other apply-macro m1 param {NAME}",
        None,
        "unknown",
    ),
]


def _finding_for(result: AuditResult, name: str) -> Finding:
    """Return the single finding for *name* (fails the test otherwise)."""
    matches = [f for f in result.findings if f.name == name]
    assert len(matches) == 1
    return matches[0]


class TestConservativeClassification:
    """Occurrences at unregistered positions block the strict verdict."""

    @pytest.mark.parametrize(
        ("extra_set", "extra_ir", "expected_kind"),
        [case[1:] for case in UNKNOWN_POSITION_CASES],
        ids=[case[0] for case in UNKNOWN_POSITION_CASES],
    )
    def test_unknown_position_is_never_strict_unused(
        self,
        make_ir: MakeIr,
        extra_set: str | None,
        extra_ir: dict[str, Any] | None,
        expected_kind: OccurrenceKind,
    ) -> None:
        set_text = BASE_DEFINITION if extra_set is None else f"{BASE_DEFINITION}\n{extra_set}"
        config = make_ir(set_text)
        if extra_ir is not None:
            config.update(extra_ir)

        result = run_audit(config, make_registry(POLICY_STATEMENT))
        finding = _finding_for(result, NAME)

        # The safety property: never a strict "unused" verdict here.
        assert finding.confidence != "unused"
        assert finding.confidence == "probably-unused"
        # The blocking occurrence is surfaced in unresolved.
        assert any(occ.value == NAME and occ.kind == expected_kind for occ in finding.unresolved)

    def test_negative_control_without_occurrence_is_strict_unused(self, make_ir: MakeIr) -> None:
        """Same object, no stray occurrence: the strict verdict IS reachable."""
        config = make_ir(BASE_DEFINITION)

        result = run_audit(config, make_registry(POLICY_STATEMENT))
        finding = _finding_for(result, NAME)

        assert finding.confidence == "unused"
        assert finding.unresolved == ()
        assert result.n_unused == 1
        assert result.n_probably_unused == 0


class TestLeafListOccurrenceKind:
    """The leaf-list case really exercises a walker ``leaf`` occurrence."""

    def test_domain_search_yields_leaf_occurrence(self, make_ir: MakeIr) -> None:
        schema = load_schema_tree()
        assert schema is not None
        schema_root = schema.get("c", {}).get("configuration", schema)

        config = make_ir(f"set system domain-search {NAME}")
        kinds = [occ.kind for occ in collect_occurrences(config, schema_root) if occ.value == NAME]

        assert kinds == ["leaf"]
