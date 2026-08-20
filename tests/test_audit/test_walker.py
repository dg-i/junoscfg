"""Tests for the schema-guided audit occurrence walker."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest

from junoscfg.audit.walker import collect_occurrences
from junoscfg.convert import to_dict
from junoscfg.display.constants import load_schema_tree

if TYPE_CHECKING:
    from junoscfg.audit.model import Occurrence


def _schema_root() -> dict[str, Any]:
    schema = load_schema_tree()
    assert schema is not None
    return schema.get("c", {}).get("configuration", schema)


SCHEMA_ROOT: dict[str, Any] = _schema_root()


def occs(ir: dict[str, Any]) -> list[Occurrence]:
    """Collect all occurrences from an unwrapped IR dict."""
    return collect_occurrences(ir, SCHEMA_ROOT)


def json_ir(config: dict[str, Any]) -> dict[str, Any]:
    """Build an IR from a native-JSON configuration dict."""
    return to_dict(json.dumps({"configuration": config}), "json")


def by_value(occurrences: list[Occurrence], value: str) -> list[Occurrence]:
    """All occurrences with the given value."""
    return [o for o in occurrences if o.value == value]


def one(occurrences: list[Occurrence], value: str) -> Occurrence:
    """The single occurrence with the given value (asserts uniqueness)."""
    matches = by_value(occurrences, value)
    assert len(matches) == 1, f"expected exactly one occurrence of {value!r}, got {matches}"
    return matches[0]


class TestEntryKeys:
    def test_named_list_entry_key(self, make_ir: Any) -> None:
        ir = make_ir("set policy-options policy-statement FOO then accept")
        occ = one(occs(ir), "FOO")
        assert occ.kind == "entry-key"
        assert occ.schema_path[-2:] == ("policy-options", "policy-statement")
        assert occ.path == ("policy-options", "policy-statement", "FOO")

    def test_native_json_entry_key(self) -> None:
        ir = json_ir(
            {"policy-options": {"policy-statement": [{"name": "FOO", "then": {"accept": [None]}}]}}
        )
        occ = one(occs(ir), "FOO")
        assert occ.kind == "entry-key"
        assert occ.schema_path == ("policy-options", "policy-statement")
        assert occ.path == ("policy-options", "policy-statement", "FOO")


class TestLeaves:
    def test_leaf_occurrence(self, make_ir: Any) -> None:
        ir = make_ir("set system login user alice class operator-class")
        occ = one(occs(ir), "operator-class")
        assert occ.kind == "leaf"
        assert occ.schema_path == ("system", "login", "user", "class")
        assert occ.path == ("system", "login", "user", "alice", "class", "operator-class")

    def test_leaf_list_occurrences(self, make_ir: Any) -> None:
        ir = make_ir(
            "set interfaces ge-0/0/0 unit 0 family inet filter input-list f1\n"
            "set interfaces ge-0/0/0 unit 0 family inet filter input-list f2"
        )
        occurrences = occs(ir)
        for name in ("f1", "f2"):
            occ = one(occurrences, name)
            assert occ.kind == "leaf"
            assert occ.schema_path[-2:] == ("filter", "input-list")
            assert occ.path[-2:] == ("input-list", name)


class TestAlgebra:
    def test_boolean_expression_extracts_names(self, make_ir: Any) -> None:
        ir = make_ir("set protocols bgp group ibgp import ( pol-a && ! pol-b )")
        occurrences = occs(ir)
        algebra = [o for o in occurrences if o.kind == "algebra"]
        assert [o.value for o in algebra] == ["pol-a", "pol-b"]
        for occ in algebra:
            assert occ.schema_types == ("policy-algebra",)
            assert occ.schema_path == ("protocols", "bgp", "group", "import")
            assert occ.path[:4] == ("protocols", "bgp", "group", "ibgp")
        # Operators and negation are never collected as values.
        assert not by_value(occurrences, "&&")
        assert not by_value(occurrences, "!")


APPLY_GROUPS_CASES: list[tuple[str, str, str, tuple[str, ...], tuple[str, ...]]] = [
    (
        "set apply-groups g1",
        "g1",
        "apply-groups",
        ("apply-groups",),
        ("apply-groups", "g1"),
    ),
    (
        "set system apply-groups g2",
        "g2",
        "apply-groups",
        ("system", "apply-groups"),
        ("system", "apply-groups", "g2"),
    ),
    (
        "set system apply-groups-except g3",
        "g3",
        "apply-groups-except",
        ("system", "apply-groups-except"),
        ("system", "apply-groups-except", "g3"),
    ),
]


class TestApplyGroups:
    @pytest.mark.parametrize(
        ("set_text", "value", "kind", "schema_path", "path"), APPLY_GROUPS_CASES
    )
    def test_apply_groups_occurrence(
        self,
        make_ir: Any,
        set_text: str,
        value: str,
        kind: str,
        schema_path: tuple[str, ...],
        path: tuple[str, ...],
    ) -> None:
        occ = one(occs(make_ir(set_text)), value)
        assert occ.kind == kind
        assert occ.schema_path == schema_path
        assert occ.path == path


class TestAnnotationsSkipped:
    def test_deactivated_leaf_value_kept_annotation_skipped(self, make_ir: Any) -> None:
        ir = make_ir("set system host-name router1\ndeactivate system host-name")
        occurrences = occs(ir)
        occ = one(occurrences, "router1")
        assert occ.kind == "leaf"
        assert not any(segment.startswith("@") for o in occurrences for segment in o.schema_path)
        assert not by_value(occurrences, "inactive")
        assert not by_value(occurrences, "delete")

    def test_deactivated_container_yields_nothing(self, make_ir: Any) -> None:
        ir = make_ir("set system services ssh\ndeactivate system services ssh")
        assert occs(ir) == []

    def test_annotation_payload_strings_not_collected(self) -> None:
        ir: dict[str, Any] = {
            "system": {
                "host-name": "router1",
                "@host-name": {"comment": "note-string", "protect": "protect"},
            }
        }
        occurrences = occs(ir)
        assert [o.value for o in occurrences] == ["router1"]


class TestEnumExclusion:
    def test_enum_leaf_value_not_collected(self, make_ir: Any) -> None:
        ir = make_ir("set routing-instances VRF-A instance-type vrf")
        occurrences = occs(ir)
        assert not by_value(occurrences, "vrf")
        occ = one(occurrences, "VRF-A")
        assert occ.kind == "entry-key"
        assert occ.schema_path[-2:] == ("routing-instances", "instance")
        assert occ.path == ("routing-instances", "VRF-A")


class TestTransparentContainers:
    def test_set_parsed_groups_shape(self, make_ir: Any) -> None:
        ir = make_ir("set groups g1 system host-name router1")
        assert ir == {"groups": {"group": [{"name": "g1", "system": {"host-name": "router1"}}]}}
        occ = one(occs(ir), "g1")
        assert occ.kind == "entry-key"
        assert occ.schema_path[-2:] == ("groups", "group")
        assert occ.path == ("groups", "g1")

    def test_native_json_groups_shape(self) -> None:
        ir = json_ir({"groups": [{"name": "g1", "system": {"host-name": "router1"}}]})
        occ = one(occs(ir), "g1")
        assert occ.kind == "entry-key"
        assert occ.schema_path[-2:] == ("groups", "group")
        assert occ.path == ("groups", "g1")

    def test_both_shapes_yield_identical_occurrences(self, make_ir: Any) -> None:
        set_ir = make_ir("set groups g1 system host-name router1")
        native_ir = json_ir({"groups": [{"name": "g1", "system": {"host-name": "router1"}}]})
        assert occs(set_ir) == occs(native_ir)


class TestLogicalSystems:
    def test_nested_policy_statement_entry_key(self, make_ir: Any) -> None:
        ir = make_ir(
            "set logical-systems ls1 policy-options policy-statement foo term 1 then accept"
        )
        occ = one(occs(ir), "foo")
        assert occ.kind == "entry-key"
        assert occ.schema_path == ("logical-systems", "policy-options", "policy-statement")
        assert occ.path == ("logical-systems", "ls1", "policy-options", "policy-statement", "foo")


class TestFlatEntryKeys:
    def test_prefix_list_filter_fe_key(self, make_ir: Any) -> None:
        ir = make_ir(
            "set policy-options policy-statement p1 term 1 from prefix-list-filter plf-a orlonger"
        )
        occ = one(occs(ir), "plf-a")
        assert occ.kind == "entry-key"
        assert occ.schema_path[-2:] == ("from", "prefix-list-filter")
        assert occ.path[-2:] == ("prefix-list-filter", "plf-a")

    def test_community_name_fallback_key(self, make_ir: Any) -> None:
        ir = make_ir("set policy-options policy-statement p1 term 1 then community add comm-a")
        occ = one(occs(ir), "comm-a")
        assert occ.kind == "entry-key"
        assert occ.schema_path[-2:] == ("then", "community")
        assert occ.path[-2:] == ("community", "comm-a")


class TestUnknownPositions:
    def test_unknown_top_level_key_blind_walk(self) -> None:
        ir: dict[str, Any] = {
            "policy-options": {"policy-statement": [{"name": "p1", "then": {"accept": [None]}}]},
            "made-up-extension": {"sub": {"ref": "some-name"}},
        }
        occurrences = occs(ir)
        occ = one(occurrences, "some-name")
        assert occ.kind == "unknown"
        assert occ.schema_path == ("made-up-extension", "sub", "ref")
        # The schema-known part of the tree is still walked normally.
        assert one(occurrences, "p1").kind == "entry-key"

    def test_apply_macro_contents_collected_as_unknown(self, make_ir: Any) -> None:
        ir = make_ir("set policy-options policy-statement p1 apply-macro m1 key1 val1")
        occurrences = occs(ir)
        for value in ("m1", "key1", "val1"):
            assert one(occurrences, value).kind == "unknown"
        # The macro name is never an auditable entry-key occurrence.
        assert not any(
            o.kind == "entry-key" and "apply-macro" in o.schema_path for o in occurrences
        )


class TestNonStringValues:
    def test_int_leaf_value_is_coerced_and_collected(self) -> None:
        # Numeric leaves are collected as strings so numeric-named objects
        # match symmetrically on the definition and reference sides.
        ir: dict[str, Any] = {"protocols": {"bgp": {"hold-time": 90}}}
        occurrences = by_value(occs(ir), "90")
        assert len(occurrences) == 1
        assert occurrences[0].kind == "leaf"

    def test_none_presence_value_not_collected(self) -> None:
        ir: dict[str, Any] = {"protocols": {"bgp": {"damping": None}}}
        assert occs(ir) == []

    def test_bool_presence_value_not_collected(self) -> None:
        ir: dict[str, Any] = {"protocols": {"bgp": {"damping": True}}}
        assert occs(ir) == []
