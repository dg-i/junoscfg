"""The tests a change to some files must run, read from the layout.

One rule, no hand-kept map: a change to package ``P`` of ``src/junoscfg/``
runs ``tests/unit/<Q>/`` for ``P`` and for every package that imports ``P``,
directly or through another, plus ``tests/contract/``. Who imports whom is
read from the source, so the kernel (``display``, ``input``), which every
package imports, selects every unit directory. A change to a test file runs
that file; to a ``conftest.py``, its directory; to ``tests/support/``,
``tests/conftest.py``, the shipped artifacts or the lock, the whole default
suite. Tooling modules select transitive test consumers; uncertain discovery selects
the full suite, and unmapped tools or tooling configuration select the tooling
suite. Shared test data
selects everything. Deleted tests select their nearest existing test directory.
Anything else selects nothing; selected ancestors subsume their descendants.

``uv run python tools/affected_tests.py FILE...`` prints the selection;
``--run`` runs it with pytest. With no files it reads the change from git: the
staged files on a commit, or, with nothing staged (``pre-commit run
--all-files``, as the agent-ready check sets run it), the branch's diff
against its base plus the working tree. That is what the pre-commit hook does.
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
    "tests/data/",
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


# These are the only file loaders the graph understands. Compare their ASTs,
# not just their names: a changed mechanism invalidates the audited exception.
_FILE_LOADERS = {
    "tests/tooling/test_affected_tests.py": """
def _tool(name: str):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
""",
    "tests/tooling/test_compare_device_outputs.py": """
def comparison_tool():
    spec = importlib.util.spec_from_file_location("compare_device_outputs", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
""",
}
_WORKER_PATHS = {
    "tests/conftest.py": 'PROJECT_ROOT / "tools/schema_content_worker.py"',
    "tools/schema_verification.py": 'root / "tools/schema_content_worker.py"',
}


def _shape(source: str) -> str:
    return ast.dump(ast.parse(source).body[0])


def _qualified(node: ast.AST, aliases: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        return f"{_qualified(node.value, aliases)}.{node.attr}"
    return ""


def tooling_importers() -> dict[str, set[str]]:
    """Reverse imports across tools AND tests; reject opaque import mechanisms.

    No code is executed and no graph survives the selection call. The small
    audited file-loader/worker exceptions below are intentionally not a Python
    expression evaluator. Unknown mechanisms or unreadable files raise, causing
    full-suite selection because the hidden consumer might be a shared fixture.
    """
    paths = sorted([*(ROOT / "tools").rglob("*.py"), *TESTS.rglob("*.py")])
    modules = {
        ".".join(path.relative_to(ROOT).with_suffix("").parts).removesuffix(
            ".__init__"
        ): path.relative_to(ROOT).as_posix()
        for path in paths
    }
    graph: dict[str, set[str]] = {}

    def edge(module: str, owner: str) -> None:
        # Importing a submodule also executes every package initializer.
        pieces = module.split(".")
        for size in range(1, len(pieces) + 1):
            target = modules.get(".".join(pieces[:size]))
            if target:
                graph.setdefault(target, set()).add(owner)

    for path in paths:
        owner = path.relative_to(ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        nodes = list(ast.walk(tree))
        aliases: dict[str, str] = {}
        for node in nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    edge(alias.name, owner)
                    aliases[alias.asname or alias.name.split(".")[0]] = (
                        alias.name if alias.asname else alias.name.split(".")[0]
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level:
                    package = owner.removesuffix(".py").split("/")[:-1]
                    module = ".".join(
                        package[: len(package) - node.level + 1] + ([module] if module else [])
                    )
                edge(module, owner)
                for alias in node.names:
                    target = f"{module}.{alias.name}"
                    edge(target, owner)
                    aliases[alias.asname or alias.name] = target

        audited: set[ast.AST] = set()
        if owner in _FILE_LOADERS:
            expected = _shape(_FILE_LOADERS[owner])
            match = next((node for node in tree.body if ast.dump(node) == expected), None)
            if match is None:
                raise ValueError(f"file loader changed: {owner}")
            audited.update(ast.walk(match))
            if owner.endswith("test_compare_device_outputs.py"):
                expected_path = _shape(
                    'TOOL = PROJECT_ROOT / "tools" / "compare_device_outputs.py"'
                )
                if not any(ast.dump(node) == expected_path for node in tree.body):
                    raise ValueError("comparison loader path changed")
                edge("tools.compare_device_outputs", owner)
        if owner in _WORKER_PATHS:
            expected_path = ast.dump(ast.parse(_WORKER_PATHS[owner], mode="eval").body)
            if not any(ast.dump(node) == expected_path for node in nodes):
                raise ValueError(f"worker path changed: {owner}")
            edge("tools.schema_content_worker", owner)

        for node in nodes:
            if not isinstance(node, ast.Call) or node in audited:
                continue
            called = _qualified(node.func, aliases)
            if called in {"importlib.import_module", "__import__", "_tool"}:
                if (
                    not node.args
                    or not isinstance(node.args[0], ast.Constant)
                    or not isinstance(node.args[0].value, str)
                ):
                    raise ValueError(f"nonliteral import: {owner}")
                target = node.args[0].value
                if called == "_tool":
                    if owner != "tests/tooling/test_affected_tests.py":
                        raise ValueError(f"unknown file loader: {owner}")
                    target = f"tools.{target}"
                if target.startswith("."):
                    raise ValueError(f"relative dynamic import: {owner}")
                edge(target, owner)
            elif called in {
                "importlib.util.spec_from_file_location",
                "importlib.machinery.SourceFileLoader",
                "runpy.run_path",
                "runpy.run_module",
            } or called.endswith(".exec_module"):
                if (
                    owner == "tests/tooling/test_compare_device_outputs.py"
                    and called == "runpy.run_path"
                    and node.args
                    and ast.dump(node.args[0]) == ast.dump(ast.parse("str(TOOL)", mode="eval").body)
                ):
                    continue
                raise ValueError(f"opaque loader: {owner}")
    return graph


def tooling_selection(rel: str, graph: dict[str, set[str]]) -> set[str]:
    """Map reachable consumers to pytest paths, with broad unmapped fallback."""
    selected: set[str] = set()
    for consumer in dependents(rel, graph):
        if consumer.startswith(("tests/support/", "tests/conftest.py")):
            return set(EVERYTHING)
        if consumer.startswith("tests/"):
            path = Path(consumer)
            if path.name in {"conftest.py", "__init__.py"}:
                selected.add(f"{path.parent.as_posix()}/")
            elif path.name.startswith("test_"):
                selected.add(consumer)
    return selected or {"tests/tooling/"}


def select(files: list[str]) -> list[str]:
    """The pytest paths *files* select, in a stable order."""
    chosen: set[str] = set()
    graph = None
    tool_graph = None
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
        elif rel in {".pre-commit-config.yaml", "tach.toml"} or (
            rel.startswith("tools/") and path.suffix != ".md"
        ):
            if rel.startswith("tools/") and path.suffix == ".py" and path.is_file():
                try:
                    if tool_graph is None:
                        tool_graph = tooling_importers()
                    chosen.update(tooling_selection(rel, tool_graph))
                except (OSError, UnicodeError, SyntaxError, ValueError):
                    return list(EVERYTHING)
            else:
                chosen.add("tests/tooling/")
        elif rel.startswith("tests/") and rel.endswith(".py"):
            if path.is_file() and path.name != "conftest.py":
                chosen.add(rel)
            else:
                directory = path.parent
                while not directory.is_dir() and directory != TESTS:
                    directory = directory.parent
                chosen.add(f"{directory.relative_to(ROOT).as_posix()}/")
    return [
        target
        for target in sorted(chosen)
        if not any(
            target != parent and target.startswith(parent)
            for parent in chosen
            if parent.endswith("/")
        )
    ]


def _git(*args: str) -> list[str]:
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    return [line for line in out.stdout.splitlines() if line]


def changed_files() -> list[str]:
    """The staged files; with none staged, the branch's change and the working tree."""
    staged = _git("diff", "--cached", "--name-only")
    if staged:
        return staged
    import tomllib

    with open(ROOT / "pyproject.toml", "rb") as handle:
        base = tomllib.load(handle).get("tool", {}).get("template", {}).get("base", "master")
    fork = _git("merge-base", "HEAD", base)
    branch = _git("diff", "--name-only", f"{fork[0]}...HEAD") if fork else []
    working = [line[3:] for line in _git("status", "--porcelain")]
    return sorted(set(branch) | set(working))


def main(argv: list[str]) -> int:
    """Print the selection, or with ``--run`` run it."""
    run = "--run" in argv
    files = [a for a in argv if a != "--run"]
    selection = select(files or changed_files())
    if not run:
        print("\n".join(selection))
        return 0
    if not selection:
        return 0
    command = [sys.executable, "-m", "pytest", "-q", "--no-header", *selection]
    from agent_ready_checks import readiness, verification

    if readiness.config(ROOT).get("enabled", False):
        try:
            return verification.execute(
                ROOT,
                command,
                None,
                {"name": "affected-tests", "runtime-command": [sys.executable]},
            )
        except (OSError, ValueError) as error:
            # A deleted tracked input or unavailable identity cannot prove reuse.
            # Running the selected tests still satisfies the ordinary obligation.
            print(f"affected-test evidence unavailable; executing tests: {error}", file=sys.stderr)
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
