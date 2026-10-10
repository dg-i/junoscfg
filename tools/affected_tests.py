"""The tests a change to some files must run, read from the layout.

One rule, no hand-kept map: a change to package ``P`` of ``src/junoscfg/``
runs ``tests/unit/<Q>/`` for ``P`` and for every package that imports ``P``,
directly or through another, plus ``tests/contract/``. Who imports whom is
read from the source, so the kernel (``display``, ``input``), which every
package imports, selects every unit directory. A change to a test file runs
that file; to a ``conftest.py``, its directory; to ``tests/support/``,
``tests/conftest.py``, the shipped artifacts or the lock, the whole default
suite. Anything else selects nothing.

``uv run python tools/affected_tests.py FILE...`` prints the selection;
``--run`` runs it with pytest, which is what the pre-commit hook does.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "junoscfg"
TESTS = ROOT / "tests"
EVERYTHING = ("tests/",)
RUNS_EVERYTHING = (
    "tests/conftest.py",
    "tests/support/",
    "src/junoscfg/validate/data/",
    "pyproject.toml",
    "uv.lock",
)


def package_of(path: Path) -> str | None:
    """``display`` for ``src/junoscfg/display/x.py``, ``cli`` for ``src/junoscfg/cli.py``."""
    rel = path.relative_to(SRC)
    if len(rel.parts) == 1:
        return None if rel.name == "__init__.py" else rel.stem
    return rel.parts[0]


def importers() -> dict[str, set[str]]:
    """Package -> the packages whose source imports it."""
    graph: dict[str, set[str]] = {}
    for path in SRC.rglob("*.py"):
        own = package_of(path)
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            elif isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            else:
                continue
            for name in names:
                parts = name.split(".")
                if parts[0] != "junoscfg":
                    continue
                # "" is the top-level package: `from junoscfg import x` reaches
                # every package its __init__ imports.
                target = parts[1] if len(parts) > 1 else ""
                if target != (own or ""):
                    graph.setdefault(target, set()).add(own or "")
    return graph


def dependents(package: str, graph: dict[str, set[str]]) -> set[str]:
    """*package* and everything that imports it, transitively."""
    seen, todo = {package}, [package]
    while todo:
        for user in graph.get(todo.pop(), ()):
            if user not in seen:
                seen.add(user)
                todo.append(user)
    return seen


def select(files: list[str]) -> list[str]:
    """The pytest paths *files* select, in a stable order."""
    chosen: set[str] = set()
    graph = None
    for name in files:
        rel = Path(name).as_posix()
        if rel.startswith(RUNS_EVERYTHING) or rel == "src/junoscfg/__init__.py":
            return list(EVERYTHING)
        path = ROOT / rel
        if rel.startswith("src/junoscfg/") and rel.endswith(".py"):
            graph = graph if graph is not None else importers()
            for package in dependents(package_of(path), graph):
                if package and (TESTS / "unit" / package).is_dir():
                    chosen.add(f"tests/unit/{package}/")
            chosen.add("tests/contract/")
        elif rel.startswith("tests/") and rel.endswith(".py") and path.exists():
            chosen.add(f"{Path(rel).parent.as_posix()}/" if path.name == "conftest.py" else rel)
    return sorted(chosen)


def main(argv: list[str]) -> int:
    """Print the selection, or with ``--run`` run it."""
    run = "--run" in argv
    selection = select([a for a in argv if a != "--run"])
    if not run:
        print("\n".join(selection))
        return 0
    if not selection:
        return 0
    command = [sys.executable, "-m", "pytest", "-q", "--no-header", *selection]
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
