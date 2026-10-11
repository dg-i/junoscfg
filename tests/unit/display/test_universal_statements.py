"""Statements valid at every level come from the tree: `schema_child`, `universal_statements`.

Junos accepts `apply-groups`, `apply-groups-except`, `apply-flags` and
`apply-macro` at every hierarchy level, and no NETCONF XSD models them. The
schema fix declares them once, on the structure tree's root, flagged `u`; one
kernel helper resolves a key a node's children do not name against them, so no
reader, writer or validator keeps its own copy (ARCH-C06, ARCH-C08, change
universal-statements-from-tree). A tree that declares none -- artifacts built
before 0.8.0 -- runs on the kernel's floor, which retires when the loader
refuses such a tree. Spec: schema-pipeline/universal-statements. That no module
keeps the names is the source scan in
`tests/tooling/test_universal_statement_names.py`.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import pytest

import junoscfg.display as display
from junoscfg import Format, convert_config
from junoscfg.display import UNIVERSAL_STATEMENTS, schema_child, universal_statements
from tests.support.artifacts import using_tree
from tests.support.shapes import BY_NAME, WRITERS, read_ir

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

NAMES = ("apply-groups", "apply-groups-except", "apply-flags", "apply-macro")

#: A tree as `junoscfg schema generate` wrote it before 0.8.0: no node at the
#: root for any of the four statements, and no `u` flag anywhere.
OLD_TREE: dict[str, Any] = {
    "c": {
        "system": {"c": {"host-name": {"l": True}, "location": {"c": {"building": {"l": True}}}}},
    }
}


class TestOneHelperResolvesThem:
    """`schema_child` answers a node's child, else the root's universal statement."""

    def test_a_nested_statement_resolves_to_the_roots_node(self, bundled_tree: dict) -> None:
        system = bundled_tree["c"]["system"]
        bgp_group = bundled_tree["c"]["protocols"]["c"]["bgp"]["c"]["group"]
        for name in NAMES:
            assert name not in system["c"], name
            assert schema_child(system, name, bundled_tree) is bundled_tree["c"][name], name
            assert schema_child(bgp_group, name, bundled_tree) is bundled_tree["c"][name], name
        # Below unplaced content too: a universal statement is valid at every level.
        assert schema_child(None, "apply-groups", bundled_tree) is bundled_tree["c"]["apply-groups"]

    def test_nothing_resolves_inside_a_universal_statement(self, bundled_tree: dict) -> None:
        """`apply-flags` holds its flags, `apply-macro` its pairs: a universal
        statement is never resolved inside one (Reviewer finding 1)."""
        flags = bundled_tree["c"]["apply-flags"]
        data = bundled_tree["c"]["apply-macro"]["c"]["data"]
        for node in (flags, data, bundled_tree["c"]["apply-macro"]):
            for name in NAMES:
                assert schema_child(node, name, bundled_tree) is None, name
        assert schema_child(flags, "omit", bundled_tree) is flags["c"]["omit"]
        floor_flags = UNIVERSAL_STATEMENTS["apply-flags"]
        assert schema_child(floor_flags, "apply-groups", OLD_TREE) is None

    def test_the_nodes_own_child_comes_first(self, bundled_tree: dict) -> None:
        system = bundled_tree["c"]["system"]
        assert schema_child(system, "host-name", bundled_tree) is system["c"]["host-name"]
        own = {"c": {"apply-flags": {"l": True}}}
        assert schema_child(own, "apply-flags", bundled_tree) is own["c"]["apply-flags"]

    def test_a_key_nothing_declares_resolves_to_nothing(self, bundled_tree: dict) -> None:
        system = bundled_tree["c"]["system"]
        assert schema_child(system, "bogus-statement", bundled_tree) is None
        assert schema_child(None, "bogus-statement", bundled_tree) is None
        assert schema_child(system, "bogus-statement", None) is None
        # Only a universal statement: no other child of the root is valid below it.
        assert schema_child(system, "interfaces", bundled_tree) is None
        assert schema_child(None, "system", bundled_tree) is None

    def test_a_nodes_own_statement_wins_in_every_reader(self, tmp_path: Path) -> None:
        """A tree whose `system` declares its own `apply-macro` leaf reads it as
        that leaf from every door, and writes it back: no reader looks the
        universal statement up before the node's own child."""
        tree = {
            "c": {
                **{name: copy.deepcopy(dict(node)) for name, node in UNIVERSAL_STATEMENTS.items()},
                "system": {"c": {"apply-macro": {"l": True}, "host-name": {"l": True}}},
            }
        }
        sources = {
            Format.SET: "set system apply-macro M1\n",
            Format.STRUCTURED: "system {\n    apply-macro M1;\n}\n",
            Format.JSON: '{"configuration": {"system": {"apply-macro": "M1"}}}',
            Format.YAML: "configuration:\n  system:\n    apply-macro: M1\n",
            Format.XML: "<configuration><system><apply-macro>M1</apply-macro></system>"
            "</configuration>",
        }
        with using_tree(tmp_path, tree):
            for fmt, source in sources.items():
                ir = json.loads(convert_config(source, from_format=fmt, to_format=Format.JSON))
                assert ir["configuration"] == {"system": {"apply-macro": "M1"}}, fmt
                out = convert_config(source, from_format=fmt, to_format=Format.SET, strict=True)
                assert out == "set system apply-macro M1\n", fmt

    def test_the_helper_is_a_kernel_door(self) -> None:
        """Usable from every package above the kernel: conversion, validation and
        the anonymizer's walker (change 5) import it through the door."""
        for name in ("schema_child", "universal_statements", "UNIVERSAL_STATEMENTS"):
            assert name in display.__all__, name


class TestTheFloorIsForATreeThatDeclaresNone:
    """The tree is authoritative; the floor stands in only where it declares nothing."""

    def test_a_tree_declaring_none_gets_the_floor(self) -> None:
        got = universal_statements(OLD_TREE)
        assert tuple(got) == tuple(UNIVERSAL_STATEMENTS) == NAMES
        assert schema_child(OLD_TREE["c"]["system"], "apply-flags", OLD_TREE) == {
            "u": True,
            "c": {"omit": {"p": True}, "replace": {"p": True}},
        }

    def test_a_tree_declaring_some_gets_only_those(self) -> None:
        """The flag decides, not the name: a fifth flagged statement counts, an
        `apply-flags` the tree does not flag is no universal statement."""
        tree = {
            "c": {
                "apply-groups": {"l": True, "ll": True, "u": True},
                "apply-x": {"l": True, "u": True},
                "apply-flags": {"c": {"omit": {"p": True}}},
                "system": {"c": {}},
            }
        }
        assert set(universal_statements(tree)) == {"apply-groups", "apply-x"}
        assert schema_child(tree["c"]["system"], "apply-flags", tree) is None
        assert schema_child(tree["c"]["system"], "apply-x", tree) is tree["c"]["apply-x"]

    def test_the_bundled_tree_never_runs_on_the_floor(self, bundled_tree: dict) -> None:
        """The tripwire. The floor is what the bundled tree declares, so an old
        tree reads as the bundled one does; and the bundled tree is answered
        from its own nodes, never the floor. A shipped tree without the four
        nodes fails here before it runs anywhere on the floor. Retirement
        trigger: the artifact loader refuses a tree whose root declares no
        universal statement (after one minor release that warns); then the
        floor and this test go."""
        got = universal_statements(bundled_tree)
        assert tuple(got) == NAMES
        for name, node in got.items():
            assert node is bundled_tree["c"][name], name
            assert node == UNIVERSAL_STATEMENTS[name], name

    def test_conversion_never_answers_from_the_floor(self, monkeypatch: Any) -> None:
        """The runtime tripwire: with the floor poisoned, both catalogue rows still
        read, write and validate on the bundled tree. A walker that resolves
        against the wrong root -- the current node, a subtree, nothing -- would
        be answered by the floor, which equals the bundled nodes, and no output
        test could see it; here it raises."""

        class Poisoned(Mapping):
            def __getitem__(self, key: str) -> Any:
                raise AssertionError("answered from the floor")

            def __iter__(self) -> Iterator[str]:
                raise AssertionError("answered from the floor")

            def __len__(self) -> int:
                raise AssertionError("answered from the floor")

        # An old tree asked first: the floor is never kept, so the poison below
        # trips whatever ran before it (Reviewer finding 3).
        assert tuple(universal_statements(OLD_TREE)) == NAMES
        monkeypatch.setattr("junoscfg.display.constants.UNIVERSAL_STATEMENTS", Poisoned())
        with pytest.raises(AssertionError, match="answered from the floor"):
            universal_statements(OLD_TREE)
        for name in (
            "apply-flags-omit-as-the-device-writes-it",
            "universal-statements-below-the-root",
        ):
            shape = BY_NAME[name]
            for reader, source in shape.sources.items():
                assert read_ir(source, reader) == shape.expected_ir(), (name, reader)
                for writer in WRITERS:
                    output = convert_config(
                        source, from_format=reader, to_format=writer, strict=True
                    )
                    assert read_ir(output, writer) == shape.expected_ir(), (name, reader, writer)

    def test_an_old_tree_reads_and_writes_them(self, tmp_path: Path) -> None:
        source = (
            "set system apply-groups G1\n"
            "set system apply-macro M1 k1 v1\n"
            "set system apply-flags omit\n"
            "set system host-name router1\n"
        )
        with using_tree(tmp_path, copy.deepcopy(OLD_TREE)):
            ir = json.loads(convert_config(source, from_format=Format.SET, to_format=Format.JSON))
            back = convert_config(source, from_format=Format.SET, to_format=Format.SET)
        assert ir["configuration"]["system"] == {
            "apply-groups": ["G1"],
            "apply-macro": [{"name": "M1", "data": [{"name": "k1", "value": "v1"}]}],
            "apply-flags": {"omit": [None]},
            "host-name": "router1",
        }
        assert sorted(back.splitlines()) == sorted(source.splitlines())
