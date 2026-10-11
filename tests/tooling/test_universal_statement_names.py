"""No module keeps the universal statements' names: the tree declares them.

`apply-groups`, `apply-groups-except`, `apply-flags` and `apply-macro` are valid
at every hierarchy level. The schema fix declares them once, on the structure
tree's root, flagged `u`, and `junoscfg.display.schema_child` resolves them
below it (`tests/unit/display/test_universal_statements.py`). Before change
universal-statements-from-tree, field validation and the JSON-schema generator
read the kernel tuple, the set reader, the structured writer and the set writer
compared tokens with the names, and the Group-H flag helpers fell back to six
tables of element names where a universal statement below the root met no node
(ARCH-C06, ARCH-C08). Spec: schema-pipeline/universal-statements.

The names may appear where they are declared or given a meaning the tree does
not hold: the kernel's compatibility floor, the schema fix that declares them,
and the anonymize and audit walkers, which read `apply-groups` as a reference
to a group (their traversal is change 5's). The scan reads string constants
whole: a name, or a prefix of one (`startswith("apply-")`, the literal part of
`f"apply-{kind}"`). A name hidden inside a regular expression or assembled
from parts that are no prefix is beyond it.
"""

from __future__ import annotations

import ast

from tests.support.paths import PACKAGE_SRC

NAMES = frozenset({"apply-groups", "apply-groups-except", "apply-flags", "apply-macro"})
RETIRED_TABLES = frozenset(
    {
        "TRANSPARENT_CONTAINERS",
        "TRANSPARENT_LIST_KEYS",
        "POSITIONAL_KEY_ELEMENTS",
        "NON_NESTING_POSITIONAL_KEYS",
        "ALL_POSITIONAL_KEYS",
        "_FLAT_DICT_ELEMENTS",
    }
)
FLOOR = "UNIVERSAL_STATEMENTS"

# Where a name may stand, by path under the package.
DECLARED = ("display/constants.py", "validate/xsd_fixes.py")
GIVEN_A_MEANING = ("anonymize/", "audit/")
# Where the floor may be read: the kernel that holds it and its door.
FLOOR_READERS = ("display/constants.py", "display/__init__.py")


def _docstrings(tree: ast.AST) -> set[int]:
    """The ids of every docstring node in *tree*: naming a statement there explains it."""
    return {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    }


def _readings(tree: ast.AST, where: str) -> list[tuple[int, str]]:
    """Every place *tree*, the module at *where*, reads a name it may not."""
    docstrings = _docstrings(tree)
    names_allowed = where.startswith(DECLARED + GIVEN_A_MEANING)
    floor_allowed = where.startswith(FLOOR_READERS)
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            # A name, or a prefix of one: `startswith("apply-")`, and the
            # literal part of `f"apply-{kind}"`, which the walk visits too.
            text = node.value
            names_one = text in NAMES or (
                text.startswith("apply") and any(name.startswith(text) for name in NAMES)
            )
            if id(node) not in docstrings and names_one and not names_allowed:
                found.append((node.lineno, repr(text)))
        elif isinstance(node, (ast.Name, ast.Attribute, ast.alias)):
            name = (
                node.id
                if isinstance(node, ast.Name)
                else node.attr
                if isinstance(node, ast.Attribute)
                else node.name
            )
            if name in RETIRED_TABLES or (name == FLOOR and not floor_allowed):
                found.append((node.lineno, name))
    return found


class TestUniversalStatementsComeFromTheTree:
    """The source reads the four names only where they are declared or given a meaning."""

    def test_no_module_keeps_their_names(self) -> None:
        """Read from the syntax tree, so a comment or a docstring that names a
        statement to explain it is not a reading of it."""
        files = sorted(PACKAGE_SRC.rglob("*.py"))
        assert len(files) > 60, "the scan found too little source to mean anything"
        found = [
            f"{path.relative_to(PACKAGE_SRC)}:{line} {what}"
            for path in files
            for line, what in _readings(
                ast.parse(path.read_text(encoding="utf-8")),
                path.relative_to(PACKAGE_SRC).as_posix(),
            )
        ]
        assert found == [], found

    def test_the_scan_sees_each_retired_reading(self) -> None:
        """A scan that finds nothing must be able to find something."""
        source = (
            "'''A docstring naming apply-groups is not a reading.'''\n"
            "from junoscfg.display import UNIVERSAL_STATEMENTS\n"
            "a = token == 'apply-macro'\nb = ('apply-groups', 'apply-groups-except')\n"
            "c = key in UNIVERSAL_STATEMENTS\nd = TRANSPARENT_CONTAINERS.get(key)\n"
            "e = m.ALL_POSITIONAL_KEYS\nf = {'apply-flags': 1}\n"
            "g = key.startswith('apply-')\nh = f'apply-{kind}'\ni = 'an apply-groups message'\n"
        )
        found = {what for _, what in _readings(ast.parse(source), "convert/example.py")}
        assert found == {
            "UNIVERSAL_STATEMENTS",
            "'apply-macro'",
            "'apply-groups'",
            "'apply-groups-except'",
            "TRANSPARENT_CONTAINERS",
            "ALL_POSITIONAL_KEYS",
            "'apply-flags'",
            "'apply-'",
        }
        allowed = _readings(ast.parse(source), "audit/example.py")
        assert {what for _, what in allowed} == {
            "UNIVERSAL_STATEMENTS",
            "TRANSPARENT_CONTAINERS",
            "ALL_POSITIONAL_KEYS",
        }
