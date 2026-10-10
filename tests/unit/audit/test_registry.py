"""The audit type registry: loading and validating it, and what a pattern matches."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from junoscfg.audit import Registry, RegistryError, TypeEntry, find_unused, load_registry
from junoscfg.convert import to_dict

if TYPE_CHECKING:
    from pathlib import Path

VALID_MINIMAL = """
version: 1
types:
  policy-statement:
    source: curated
    definition:
      - policy-options policy-statement
    references:
      schema-types: [policy-algebra]
"""


def write_registry(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "registry.yaml"
    path.write_text(content)
    return path


class TestLoadRegistry:
    def test_bundled_registry_loads(self) -> None:
        """With no path, load_registry reads the bundled file."""
        registry = load_registry()
        assert registry.types
        assert all(entry.source in {"curated", "generated"} for entry in registry.types.values())
        # Reportable types all declare at least one reference mechanism.
        for name in registry.reportable():
            entry = registry.types[name]
            assert entry.reference_paths or entry.reference_schema_types

    def test_valid_minimal(self, tmp_path: Path) -> None:
        registry = load_registry(write_registry(tmp_path, VALID_MINIMAL))
        entry = registry.types["policy-statement"]
        assert entry.definition == (("policy-options", "policy-statement"),)
        assert entry.reference_schema_types == frozenset({"policy-algebra"})
        assert entry.report is True
        assert entry.source == "curated"

    def test_insertion_order_preserved(self, tmp_path: Path) -> None:
        content = (
            VALID_MINIMAL
            + """
  config-group:
    source: curated
    definition: [groups group]
    references:
      paths: [apply-groups]
"""
        )
        registry = load_registry(write_registry(tmp_path, content))
        assert list(registry.types) == ["policy-statement", "config-group"]

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(RegistryError, match="cannot read file"):
            load_registry(tmp_path / "nope.yaml")

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        with pytest.raises(RegistryError, match="invalid YAML"):
            load_registry(write_registry(tmp_path, "types: [unclosed"))

    def test_non_mapping_document(self, tmp_path: Path) -> None:
        with pytest.raises(RegistryError, match="top level must be a mapping"):
            load_registry(write_registry(tmp_path, "- just\n- a\n- list\n"))

    def test_missing_version(self, tmp_path: Path) -> None:
        with pytest.raises(RegistryError, match="unsupported or missing 'version'"):
            load_registry(write_registry(tmp_path, "types: {}\n"))

    def test_empty_types(self, tmp_path: Path) -> None:
        with pytest.raises(RegistryError, match="'types' must be a non-empty mapping"):
            load_registry(write_registry(tmp_path, "version: 1\ntypes: {}\n"))

    def test_unknown_type_key(self, tmp_path: Path) -> None:
        content = """
version: 1
types:
  foo:
    source: curated
    definition: [a b]
    references: {paths: [c]}
    surprise: true
"""
        with pytest.raises(RegistryError, match="type 'foo': unknown key.*surprise"):
            load_registry(write_registry(tmp_path, content))

    def test_missing_source(self, tmp_path: Path) -> None:
        content = """
version: 1
types:
  foo:
    definition: [a b]
    references: {paths: [c]}
"""
        with pytest.raises(RegistryError, match="type 'foo': 'source' must be one of"):
            load_registry(write_registry(tmp_path, content))

    def test_missing_definition(self, tmp_path: Path) -> None:
        content = """
version: 1
types:
  foo:
    source: curated
    references: {paths: [c]}
"""
        with pytest.raises(RegistryError, match="'definition' is required"):
            load_registry(write_registry(tmp_path, content))

    def test_reference_less_reportable_type(self, tmp_path: Path) -> None:
        content = """
version: 1
types:
  foo:
    source: curated
    definition: [a b]
"""
        with pytest.raises(RegistryError, match="must declare at least one reference"):
            load_registry(write_registry(tmp_path, content))

    def test_report_false_needs_no_references(self, tmp_path: Path) -> None:
        content = """
version: 1
types:
  foo:
    source: curated
    definition: [a b]
    report: false
"""
        registry = load_registry(write_registry(tmp_path, content))
        assert registry.types["foo"].report is False
        assert registry.reportable() == []

    def test_unknown_reference_key(self, tmp_path: Path) -> None:
        content = """
version: 1
types:
  foo:
    source: curated
    definition: [a b]
    references: {routes: [c]}
"""
        with pytest.raises(RegistryError, match="'references' has unknown key.*routes"):
            load_registry(write_registry(tmp_path, content))

    def test_non_string_pattern(self, tmp_path: Path) -> None:
        content = """
version: 1
types:
  foo:
    source: curated
    definition: [123]
    references: {paths: [c]}
"""
        with pytest.raises(RegistryError, match="only non-empty strings"):
            load_registry(write_registry(tmp_path, content))

    def test_non_bool_report(self, tmp_path: Path) -> None:
        content = """
version: 1
types:
  foo:
    source: curated
    definition: [a b]
    references: {paths: [c]}
    report: "yes please"
"""
        with pytest.raises(RegistryError, match="'report' must be a boolean"):
            load_registry(write_registry(tmp_path, content))


def definitions_found(set_text: str, pattern: tuple[str, ...]) -> list[tuple[str, ...]]:
    """The definition paths a type defined by *pattern* finds in *set_text*."""
    entry = TypeEntry(
        name="probe", source="curated", definition=(pattern,), reference_paths=(("nowhere",),)
    )
    result = find_unused(to_dict(set_text, "set"), registry=Registry(types={"probe": entry}))
    return [finding.path for finding in result.findings]


class TestTailMatch:
    """A pattern matches the tail of a definition's schema path, segment by
    segment with shell globs, so one pattern finds the object inside
    ``groups`` and ``logical-systems`` as well."""

    def test_exact(self) -> None:
        found = definitions_found(
            "set policy-options policy-statement p1 then accept",
            ("policy-options", "policy-statement"),
        )
        assert found == [("policy-options", "policy-statement", "p1")]

    def test_tail_anchored(self) -> None:
        # Schema path: groups group policy-options policy-statement.
        grouped = "set groups g1 policy-options policy-statement p1 then accept"
        assert definitions_found(grouped, ("policy-options", "policy-statement")) == [
            ("groups", "g1", "policy-options", "policy-statement", "p1")
        ]
        assert definitions_found(grouped, ("groups", "policy-statement")) == []

    def test_pattern_longer_than_path(self) -> None:
        # Schema path of the group: groups group.
        found = definitions_found(
            "set groups g1 system host-name router1", ("configuration", "groups", "group")
        )
        assert found == []

    def test_glob_segments(self) -> None:
        pattern = ("family", "inet*", "filter")
        assert definitions_found(
            "set firewall family inet6 filter f6 term t1 then accept", pattern
        ) == [("firewall", "family", "inet6", "filter", "f6")]
        assert (
            definitions_found("set firewall family mpls filter fm term t1 then accept", pattern)
            == []
        )

    def test_empty_pattern_never_matches(self) -> None:
        assert definitions_found("set groups g1 system host-name router1", ()) == []
