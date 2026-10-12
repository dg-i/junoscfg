"""Hidden list hints follow keyed structure; synthetic names prevent name tables.

These minimal schema policy tests do not assert that invented paths load on Junos.
Device-backed syntax is separately pinned in convert/test_hidden_list_names.py.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from junoscfg.display import entry_keys, is_transparent_list_key
from junoscfg.validate import SchemaNode, apply_all_fixes, write_structure_tree

if TYPE_CHECKING:
    from pathlib import Path


class TestHiddenHintsFollowTheDeclaredKey:
    @pytest.mark.parametrize("keys", [("name",), ("address", ("exact", "upto"))])
    def test_a_hidden_key_needs_no_name_mapping(self, tmp_path: Path, keys: tuple) -> None:
        children = {}
        for key in keys:
            for name in key if isinstance(key, tuple) else (key,):
                children[name] = SchemaNode(
                    name=name, is_leaf=True, is_key=True, flags={"nokeyword"}
                )
        node = SchemaNode(
            name="synthetic-hidden-entry",
            is_list=True,
            flags={"nokeyword"},
            children=children,
            key_fields=keys,
        )
        root = SchemaNode(name="configuration", children={node.name: node})
        apply_all_fixes(root)
        output = tmp_path / "minimal-tree.json"
        write_structure_tree(root, str(output))
        generated = json.loads(output.read_text())["c"][node.name]
        assert is_transparent_list_key(generated)
        assert entry_keys(generated) == keys

    @pytest.mark.parametrize("kind", ["keyworded", "leaf", "unkeyed"])
    def test_nonmatching_models_receive_no_hidden_hint(self, tmp_path: Path, kind: str) -> None:
        node = SchemaNode(
            name="synthetic-ordinary-entry",
            is_list=kind != "leaf",
            is_leaf=kind == "leaf",
            flags=set() if kind == "keyworded" else {"nokeyword"},
            children={}
            if kind != "keyworded"
            else {
                "name": SchemaNode(name="name", is_leaf=True, is_key=True, flags={"nokeyword"}),
            },
        )
        root = SchemaNode(name="configuration", children={node.name: node})
        apply_all_fixes(root)
        output = tmp_path / "minimal-tree.json"
        write_structure_tree(root, str(output))
        generated = json.loads(output.read_text())["c"][node.name]
        assert not is_transparent_list_key(generated)
