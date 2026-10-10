"""No module keeps its own entry key: the source holds none of the retired spellings.

Before identifier-key-fields, modules answered an entry's keys for themselves:
a flat-entry table (`fe`, `values-only`, `FLAT_ENTRY_ELEMENTS`), a table of
overrides (`ENTRY_KEY_OVERRIDES`, `get_flat_entry_config`), a hard-coded
`community-name`, and positional `_v0`, `_v1` keys. Now `display.entry_keys`
answers from the tree (`tests/unit/display/test_entry_keys.py`). Spec:
schema-pipeline/entry-key-fields.
"""

from __future__ import annotations

import ast
import re

import pytest

from tests.support.paths import PACKAGE_SRC, PROJECT_ROOT

RETIRED_STRINGS = frozenset({"fe", "values-only", "community-name"})
RETIRED_NAMES = frozenset({"FLAT_ENTRY_ELEMENTS", "ENTRY_KEY_OVERRIDES", "get_flat_entry_config"})
POSITIONAL = re.compile(r"^_v\d+$")

# Development tooling, like the checks it guards: it needs 3.11's tomllib.
tomllib = pytest.importorskip("tomllib")


def _docstrings(tree: ast.AST) -> set[int]:
    """The ids of every docstring node in *tree*: naming a spelling there explains it."""
    return {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    }


def _readings(tree: ast.AST) -> list[tuple[int, str]]:
    """Every place *tree* reads a retired spelling, outside docstrings and comments."""
    docstrings = _docstrings(tree)
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) not in docstrings and (
                node.value in RETIRED_STRINGS or POSITIONAL.match(node.value)
            ):
                found.append((node.lineno, repr(node.value)))
        elif isinstance(node, ast.JoinedStr):
            head = node.values[0] if node.values else None
            if isinstance(head, ast.Constant) and head.value == "_v":
                found.append((node.lineno, "f'_v{...}'"))
        elif isinstance(node, ast.Name) and node.id in RETIRED_NAMES:
            found.append((node.lineno, node.id))
        elif isinstance(node, ast.Attribute) and node.attr in RETIRED_NAMES:
            found.append((node.lineno, node.attr))
        elif isinstance(node, ast.alias) and node.name in RETIRED_NAMES:
            found.append((node.lineno, node.name))
    return found


class TestEntryKeysComeFromTheTree:
    """The source reads no retired spelling, and the retired names are banned."""

    def test_no_module_keeps_its_own_key(self) -> None:
        """Read from the syntax tree, so a comment or a docstring that names a
        spelling to explain its retirement is not a reading of it."""
        files = sorted(PACKAGE_SRC.rglob("*.py"))
        assert len(files) > 60, "the scan found too little source to mean anything"
        found = [
            f"{path.relative_to(PACKAGE_SRC)}:{line} {what}"
            for path in files
            for line, what in _readings(ast.parse(path.read_text(encoding="utf-8")))
        ]
        assert found == [], found

        pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        banned = pyproject["tool"]["ruff"]["lint"]["flake8-tidy-imports"]["banned-api"]
        assert "junoscfg.display.ENTRY_KEY_OVERRIDES" in banned
        assert "junoscfg.display.get_flat_entry_config" in banned

    def test_the_scan_sees_each_retired_spelling(self) -> None:
        """A scan that finds nothing must be able to find something."""
        source = (
            "'''A docstring naming fe and _v0 is not a reading.'''\n"
            "from x import ENTRY_KEY_OVERRIDES\n"
            "a = node['fe']\nb = 'values-only'\nc = 'community-name'\nd = '_v1'\n"
            "e = f'_v{n}'\nf = FLAT_ENTRY_ELEMENTS\ng = m.get_flat_entry_config\n"
        )
        found = {what for _, what in _readings(ast.parse(source))}
        assert found == {
            "ENTRY_KEY_OVERRIDES",
            "'fe'",
            "'values-only'",
            "'community-name'",
            "'_v1'",
            "f'_v{...}'",
            "FLAT_ENTRY_ELEMENTS",
            "get_flat_entry_config",
        }
