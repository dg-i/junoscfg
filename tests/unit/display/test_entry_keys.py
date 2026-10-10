"""An entry's keys come from the tree: `entry_keys` and `statement_children`.

One kernel helper in `display/constants.py` answers which fields key a list
entry, and the structure tree carries them (`k`, written from the fields the
XSD declares). Spec: schema-pipeline/entry-key-fields (identifier-key-fields).
That no module keeps its own key is the source scan in
`tests/tooling/test_entry_key_spellings.py`; that the builder writes `k` and
`o` from a dump is `tests/unit/validate/test_artifact_builder.py`.
"""

from __future__ import annotations

from typing import Any

import junoscfg.display as display
from junoscfg.display import entry_keys, statement_children
from junoscfg.validate import SchemaNode


def _lists(tree: dict[str, Any]) -> list[tuple[tuple[str, ...], dict[str, Any]]]:
    """Every list node of *tree*, with its path."""
    found: list[tuple[tuple[str, ...], dict[str, Any]]] = []
    stack: list[tuple[tuple[str, ...], dict[str, Any]]] = [((), tree)]
    while stack:
        path, node = stack.pop()
        for name, child in (node.get("c") or {}).items():
            here = (*path, name)
            if child.get("L"):
                found.append((here, child))
            stack.append((here, child))
    return found


class TestEntryKeys:
    """`entry_keys` answers the key tuple a list node declares, `name` by default."""

    def test_the_helper_answers_the_key_tuple(self) -> None:
        assert "entry_keys" in display.__all__
        assert entry_keys({"L": True, "k": ["list-type", "list-name"]}) == (
            "list-type",
            "list-name",
        )
        assert entry_keys({"L": True, "k": ["address", ["exact", "orlonger"]]}) == (
            "address",
            ("exact", "orlonger"),
        )
        assert entry_keys({"L": True, "k": [["add", "delete"], "community-name"]}) == (
            ("add", "delete"),
            "community-name",
        )
        assert entry_keys({"L": True}) == ("name",)
        assert entry_keys({"L": True, "c": {"name": {"l": True}}}) == ("name",)

    def test_the_bundled_tree_carries_the_declared_keys(self, bundled_tree: dict) -> None:
        """Measured on the shipped tree (25.2R2).

        The as-list references at the root, under logical systems, groups and
        grouped logical systems, with and without a term; `attributes-match`;
        the filter lists keyed by their address or name and a match type; and
        every list declaring an all-identifier action choice before
        `community-name`: 48 on 25.2R2, measured in identifier-key-fields
        phase 5 (owner decision): 8 under `then`, 8 each under route-filter,
        prefix-list-filter, source-address-filter and route-filter-list, 4
        each under rf_list and saf_list.
        """
        lists = _lists(bundled_tree)
        assert len(lists) > 15_000, "the walk reached too few lists to mean anything"

        as_lists = [(p, n) for p, n in lists if n.get("tr") == "control-as-list-type"]
        assert len(as_lists) == 24
        where = set()
        for path, node in as_lists:
            assert node.get("k") == ["list-type", "list-name"], path
            assert list(node["c"])[:2] == ["list-type", "list-name"], path
            assert "p" not in node, path
            where.add((path[-1], "groups" in path, "logical-systems" in path, "term" in path))
        # root, logical systems, groups and grouped logical systems, with and
        # without a term, for each of the three lists: 3 x 8.
        assert len(where) == 24
        assert all(entry_keys(n) == ("list-type", "list-name") for _, n in as_lists)

        matches = [n for p, n in lists if p[-1] == "attributes-match"]
        assert len(matches) == 2
        for node in matches:
            assert node["k"] == ["from-event-attribute", "condition", "to-event-attribute-value"]

        filters = {
            "control-route-filter-type": "address",
            "control-source-address-filter-type": "address",
            "control-prefix-list-filter-type": "list_name",
        }
        for type_ref, first in filters.items():
            found = [(p, n) for p, n in lists if n.get("tr") == type_ref]
            assert len(found) == 8, type_ref
            for path, node in found:
                keys = entry_keys(node)
                assert len(keys) == 2 and keys[0] == first, path
                assert isinstance(keys[1], tuple) and {"exact", "orlonger"} <= set(keys[1])
                assert list(node["c"])[0] == first
            if type_ref != "control-prefix-list-filter-type":
                assert all("accept" in n["c"] for _, n in found), type_ref

        actions = [
            (p, n)
            for p, n in lists
            if "community-name" in n.get("c", {}) and {"add", "delete", "set"} <= set(n["c"])
        ]
        assert len(actions) == 48
        for path, node in actions:
            keys = entry_keys(node)
            assert len(keys) == 2 and keys[-1] == "community-name", path
            # The key order is the declared order: the choice precedes the name.
            assert isinstance(keys[0], tuple) and {"add", "delete", "set"} <= set(keys[0]), path
        definitions = [n for p, n in lists if p[-2:] == ("policy-options", "community")]
        assert len(definitions) == 4
        assert all(entry_keys(n) == ("name",) and "k" not in n for n in definitions)


class TestStatementChildren:
    """The set reader and the grammar ask one helper which children a statement names.

    A list's key fields are its entries' values, never statements; a container
    keeps them all. Provenance: identifier-key-fields, phase-6 review, finding 8.
    """

    def test_statement_children_drop_the_key_fields(self) -> None:
        assert "statement_children" in display.__all__
        leaf = {"l": True}
        children = {"address": leaf, "exact": {"p": True}, "accept": {"p": True}}
        keyed = {"L": True, "k": ["address", ["exact", "orlonger"]], "c": children}
        assert list(statement_children(keyed)) == ["accept"]
        assert list(statement_children({"L": True, "c": {"name": leaf, "then": {}}})) == ["then"]
        assert statement_children({"c": {"name": leaf}}) == {"name": leaf}
        node = SchemaNode(
            name="route-filter",
            is_list=True,
            key_fields=("address", ("exact", "orlonger")),
            children={n: SchemaNode(name=n, is_leaf=True) for n in ("address", "exact", "accept")},
        )
        assert list(statement_children(node)) == ["accept"]
