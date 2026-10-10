"""Tests for the audit type-registry loader and pattern matching."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from junoscfg.audit.registry import (
    RegistryError,
    default_registry_path,
    load_registry,
    tail_match,
)

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
        registry = load_registry()
        assert registry.types
        assert all(entry.source in {"curated", "generated"} for entry in registry.types.values())
        # Reportable types all declare at least one reference mechanism.
        for name in registry.reportable():
            entry = registry.types[name]
            assert entry.reference_paths or entry.reference_schema_types

    def test_bundled_registry_path_exists(self) -> None:
        assert default_registry_path().is_file()

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


class TestTailMatch:
    def test_exact(self) -> None:
        path = ("policy-options", "policy-statement")
        assert tail_match(path, ("policy-options", "policy-statement"))

    def test_tail_anchored(self) -> None:
        path = ("groups", "group", "policy-options", "policy-statement")
        assert tail_match(path, ("policy-options", "policy-statement"))
        assert not tail_match(path, ("groups", "policy-statement"))

    def test_pattern_longer_than_path(self) -> None:
        assert not tail_match(("policy-statement",), ("policy-options", "policy-statement"))

    def test_glob_segments(self) -> None:
        pattern = ("family", "inet*", "filter")
        assert tail_match(("firewall", "family", "inet6", "filter"), pattern)
        assert not tail_match(("firewall", "family", "mpls", "filter"), pattern)

    def test_empty_pattern_never_matches(self) -> None:
        assert not tail_match(("a",), ())
