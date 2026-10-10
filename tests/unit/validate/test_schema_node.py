"""Tests for SchemaNode IR and tree utilities."""

from __future__ import annotations

from junoscfg.validate.schema_node import Combinator, SchemaNode, find_all, navigate, walk


def _make_tree() -> SchemaNode:
    """Build a small test tree:
    configuration
    ├── system
    │   ├── host-name (leaf)
    │   └── services
    │       └── ssh (presence)
    └── interfaces
        └── name (leaf, key)
    """
    ssh = SchemaNode(name="ssh", is_presence=True)
    hostname = SchemaNode(name="host-name", is_leaf=True)
    services = SchemaNode(
        name="services",
        children={"ssh": ssh},
        combinator=Combinator.CHOICE,
    )
    system = SchemaNode(
        name="system",
        children={"host-name": hostname, "services": services},
        combinator=Combinator.CHOICE,
    )
    iface_name = SchemaNode(name="name", is_leaf=True, is_key=True)
    interfaces = SchemaNode(
        name="interfaces",
        children={"name": iface_name},
        combinator=Combinator.SEQUENCE,
        is_list=True,
    )
    return SchemaNode(
        name="configuration",
        children={"system": system, "interfaces": interfaces},
        combinator=Combinator.CHOICE,
    )


class TestSchemaNode:
    def test_repr_basic(self):
        node = SchemaNode(name="test")
        assert "SchemaNode('test')" in repr(node)

    def test_repr_with_attrs(self):
        node = SchemaNode(name="x", is_leaf=True, is_key=True, is_list=True)
        r = repr(node)
        assert "leaf" in r
        assert "key" in r
        assert "list" in r

    def test_combinator_values(self):
        assert Combinator.SEQUENCE.value == "sequence"
        assert Combinator.CHOICE.value == "choice"
        assert Combinator.SEQ_CHOICE.value == "seq_choice"

    def test_defaults(self):
        node = SchemaNode(name="test")
        assert node.children == {}
        assert node.combinator == Combinator.CHOICE
        assert node.is_key is False
        assert node.is_list is False
        assert node.is_mandatory is False
        assert node.is_leaf is False
        assert node.is_presence is False
        assert node.enums is None
        assert node.pattern is None
        assert node.pattern_negated is False
        assert node.type_ref is None
        assert node.flags == set()


class TestNavigate:
    def test_navigate_to_leaf(self):
        tree = _make_tree()
        node = navigate(tree, "system", "host-name")
        assert node is not None
        assert node.name == "host-name"
        assert node.is_leaf is True

    def test_navigate_to_presence(self):
        tree = _make_tree()
        node = navigate(tree, "system", "services", "ssh")
        assert node is not None
        assert node.is_presence is True

    def test_navigate_missing(self):
        tree = _make_tree()
        assert navigate(tree, "system", "nonexistent") is None

    def test_navigate_empty_path(self):
        tree = _make_tree()
        assert navigate(tree) is tree


class TestFindAll:
    def test_find_existing(self):
        tree = _make_tree()
        results = find_all(tree, "name")
        assert len(results) == 1
        assert results[0].is_key is True

    def test_find_none(self):
        tree = _make_tree()
        assert find_all(tree, "nonexistent") == []

    def test_find_multiple(self):
        # Add another "name" somewhere
        tree = _make_tree()
        tree.children["system"].children["name"] = SchemaNode(name="name", is_leaf=True)
        results = find_all(tree, "name")
        assert len(results) == 2


class TestWalk:
    def test_walk_visits_all(self):
        tree = _make_tree()
        visited: list[str] = []
        walk(tree, lambda node, path: visited.append(node.name))
        # Should visit: configuration, system, host-name, services, ssh, interfaces, name
        assert "configuration" in visited
        assert "host-name" in visited
        assert "ssh" in visited
        assert len(visited) == 7

    def test_walk_provides_path(self):
        tree = _make_tree()
        paths: dict[str, list[str]] = {}
        walk(tree, lambda node, path: paths.update({node.name: list(path)}))
        assert paths["configuration"] == []
        assert paths["host-name"] == ["system", "host-name"]
        assert paths["ssh"] == ["system", "services", "ssh"]
