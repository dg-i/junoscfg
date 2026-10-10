"""Refuse a test that reaches past a package door.

The doors are the module paths `tach.toml` declares, read from there so the
two never disagree. A test imports names from a door, never from a submodule,
never an underscore name, and reaches no underscore attribute on anything but
``self`` or ``cls``; ``monkeypatch.setattr("junoscfg....")`` targets count as
imports. Contract and corpus tests are held to the named surfaces only:
``junoscfg`` and ``junoscfg.cli``.

`tach check` excludes ``tests/`` (its boundaries are the product's), so this is
the check that holds the tests to the same doors. A test that must pin an
internal is listed in ``EXCEPTIONS`` with the reason; nothing else passes.

Run: ``uv run python tools/check_test_doors.py`` (exit 1 on a violation).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
SURFACES = frozenset({"junoscfg", "junoscfg.cli"})
SURFACE_ONLY = ("contract", "corpus")

#: (test file relative to tests/, the module or ``module.attribute`` it reaches) -> why.
EXCEPTIONS: dict[tuple[str, str], str] = {}


def doors() -> frozenset[str]:
    """The door modules, as `tach.toml` declares them."""
    with open(ROOT / "tach.toml", "rb") as handle:
        return frozenset(module["path"] for module in tomllib.load(handle)["modules"])


def _private(name: str) -> bool:
    return name.startswith("_") and not (name.startswith("__") and name.endswith("__"))


class _Visitor(ast.NodeVisitor):
    def __init__(self, allowed: frozenset[str], known: frozenset[str]) -> None:
        self.allowed = allowed
        self.known = known
        self.found: list[tuple[int, str, str]] = []

    def _module(self, lineno: int, module: str) -> None:
        if module.split(".")[0] != "junoscfg":
            return
        if module not in self.allowed:
            why = "a named surface only" if self.allowed <= SURFACES else "a submodule"
            self.found.append((lineno, module, f"imports {module}: {why}"))

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._module(node.lineno, alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level or not node.module:
            return
        self._module(node.lineno, node.module)
        if node.module.split(".")[0] == "junoscfg":
            for alias in node.names:
                if _private(alias.name):
                    self.found.append(
                        (node.lineno, f"{node.module}.{alias.name}", "imports a private name")
                    )
                elif f"{node.module}.{alias.name}" in self.known:
                    self.found.append(
                        (
                            node.lineno,
                            f"{node.module}.{alias.name}",
                            "imports a submodule as a name",
                        )
                    )

    def visit_Attribute(self, node: ast.Attribute) -> None:
        base = node.value
        if _private(node.attr) and not (isinstance(base, ast.Name) and base.id in {"self", "cls"}):
            self.found.append(
                (node.lineno, f"{ast.unparse(base)}.{node.attr}", "reaches a private attribute")
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in {"setattr", "delattr"} and node.args:
            target = node.args[0]
            if isinstance(target, ast.Constant) and isinstance(target.value, str):
                module, _, name = target.value.rpartition(".")
                if module.startswith("junoscfg"):
                    self._module(node.lineno, module)
                    if _private(name):
                        self.found.append((node.lineno, target.value, "patches a private name"))
        self.generic_visit(node)


def _modules_in_src() -> frozenset[str]:
    src = ROOT / "src"
    names = set()
    for path in src.rglob("*.py"):
        parts = path.relative_to(src).with_suffix("").parts
        names.add(".".join(parts[:-1] if parts[-1] == "__init__" else parts))
    return frozenset(names)


def violations(paths: list[Path] | None = None) -> list[str]:
    """Every reach past a door in *paths* (default: all of tests/), less the exceptions."""
    every_door = doors()
    known = _modules_in_src()
    report = []
    for path in sorted(paths or TESTS.rglob("*.py")):
        rel = path.relative_to(TESTS).as_posix()
        allowed = SURFACES if rel.split("/")[0] in SURFACE_ONLY else every_door
        visitor = _Visitor(allowed, known)
        visitor.visit(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
        for lineno, what, why in visitor.found:
            if (rel, what) not in EXCEPTIONS:
                report.append(f"tests/{rel}:{lineno}: {why}: {what}")
    return report


def stale_exceptions() -> list[str]:
    """An exception nothing needs any more is removed, not kept 'just in case'."""
    seen = set()
    for path in TESTS.rglob("*.py"):
        rel = path.relative_to(TESTS).as_posix()
        allowed = SURFACES if rel.split("/")[0] in SURFACE_ONLY else doors()
        visitor = _Visitor(allowed, _modules_in_src())
        visitor.visit(ast.parse(path.read_text(encoding="utf-8")))
        seen.update((rel, what) for _, what, _ in visitor.found)
    return [
        f"stale exception: tests/{rel}: {what}"
        for rel, what in EXCEPTIONS
        if (rel, what) not in seen
    ]


def main() -> int:
    """Print the violations and stale exceptions; 1 if there are any."""
    found = violations() + stale_exceptions()
    for line in found:
        print(line)
    if found:
        print(f"\n{len(found)} door violation(s); see tests/CONTRACT.md", file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
