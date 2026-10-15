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
Package data selects its package. A file outside ``src``, ``tests`` and ``tools``
selects the tests of every module reading it by a path anchored in the
repository, and of every module that may read any file; other configuration also
selects the tooling suite, while documents and change records select nothing
more. Selected ancestors subsume their descendants.

``uv run python tools/affected_tests.py FILE...`` prints the selection;
``--run`` runs it with pytest. With no files it reads the change from git: the
staged files on a commit, or, with nothing staged (``pre-commit run
--all-files``, as the agent-ready check sets run it), the branch's diff
against its base plus the working tree. That is what the pre-commit hook does.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "junoscfg"
TESTS = ROOT / "tests"
EVERYTHING = ("tests/",)
# Files that configure every pytest run.
PYTEST_CONFIGURATION = (
    "pytest.ini",
    ".pytest.ini",
    "pytest.toml",
    ".pytest.toml",
    "tox.ini",
    "setup.cfg",
)
# Where an untracked file can change what pytest collects or imports.
UNTRACKED_INPUTS = ("tests", "src", "tools", "conftest.py")
RUNS_EVERYTHING = (
    *PYTEST_CONFIGURATION,
    "conftest.py",
    "tests/conftest.py",
    "tests/support/",
    "tests/data/",
    "src/junoscfg/validate/data/",
    "pyproject.toml",
    "uv.lock",
)
# Checked by the repository gates, not pytest. A test that reads one names it
# from the project root, which makes it a reader below like any other file.
DOCUMENTS = (".md", ".rst", ".txt")
RECORDS = (
    "openspec/",
    "changelog.d/",
    ".agent-ready/",
    ".agents/",
    ".claude/",
    ".github/",
    "docs/",
    "mkdocs.yml",
    "LICENSE",
    ".copier-answers.yml",
)
TOOLING = ("tools/", "tests/tooling/")
# Gitignored operator data; the evidence refusal below guards it, and its tracked
# README and ignore file are documentation.
PRIVATE = "private_test_data/"
# The selector's assertions about this repository's real import and reader graph.
SELECTOR_TESTS = "tests/tooling/test_affected_tests.py"


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


_EXTENDS = {"joinpath", "glob", "rglob", "resolve", "absolute"}


def _file_path(node: ast.AST, path: Path) -> Path | None:
    """The directory ``Path(__file__)`` with ``.resolve()``/``.parent``/``.parents[N]``
    stands for in the module at *path*."""
    if isinstance(node, ast.Call) and not node.keywords:
        func = node.func
        if (
            (
                isinstance(func, ast.Name)
                and func.id == "Path"
                or isinstance(func, ast.Attribute)
                and func.attr == "Path"
            )
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "__file__"
        ):
            return path
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"resolve", "absolute"}:
            return _file_path(node.func.value, path) if not node.args else None
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        base = _file_path(node.value, path)
        return base.parent if base else None
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "parents"
        and isinstance(node.slice, ast.Constant)
        and isinstance(node.slice.value, int)
    ):
        base = _file_path(node.value.value, path)
        if base and node.slice.value < len(base.parents):
            return base.parents[node.slice.value]
    return None


def _join(prefix: str, part: str) -> str:
    return "/".join(filter(None, (prefix, part.strip("/"))))


def _locate(node: ast.AST, path: Path, bases, modules) -> tuple[str, bool] | None:
    """``("docs/x.md", True)`` for ``ROOT / "docs" / "x.md"``: the repository path an
    expression names; False once a part is computed, keeping the constant prefix;
    None when it is not anchored in the repository. *bases* maps local names, and
    *modules* local module aliases, to the paths their constants name."""
    if isinstance(node, ast.Name):
        return (bases[node.id], True) if node.id in bases else None
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        known = modules.get(node.value.id, {})
        if node.attr in known:
            return known[node.attr], True
    found = _file_path(node, path)
    if found is not None:
        try:
            name = found.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            return None
        return ("" if name == "." else name), True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        parts, base = [node.right], node.left
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr not in _EXTENDS or node.keywords:
            return None
        parts, base = node.args, node.func.value
    else:
        return None
    left = _locate(base, path, bases, modules)
    if left is None or not left[1]:
        return left
    name = left[0]
    glob = isinstance(node, ast.Call) and node.func.attr in {"glob", "rglob"}
    for part in parts:
        if not (isinstance(part, ast.Constant) and isinstance(part.value, str)):
            return name, False
        text = part.value
        if glob:  # the constant directories before the first wildcard
            text = "/".join(piece for piece in text.split("*")[0].split("[")[0].split("/")[:-1])
        name = _join(name, text)
    return name, True


def _module_bases(path: Path, nodes: list[ast.AST], imported) -> dict[str, str]:
    """Names assigned an anchored constant path, plus names imported from modules
    whose own such names *imported* maps."""
    bases: dict[str, str] = {}
    for node in nodes:
        if isinstance(node, ast.ImportFrom) and node.module in imported:
            for alias in node.names:
                if alias.name in imported[node.module]:
                    bases[alias.asname or alias.name] = imported[node.module][alias.name]
    modules = _module_aliases(nodes, imported)
    grown = True
    while grown:
        grown = False
        for node in nodes:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                target = node.target
            else:
                continue
            if isinstance(target, ast.Name) and target.id not in bases:
                found = _locate(node.value, path, bases, modules)
                if found and found[1]:
                    bases[target.id] = found[0]
                    grown = True
    return bases


def _module_aliases(nodes: list[ast.AST], imported) -> dict[str, dict[str, str]]:
    aliases: dict[str, dict[str, str]] = {}
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname and alias.name in imported:
                    aliases[alias.asname] = imported[alias.name]
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                module = f"{node.module}.{alias.name}"
                if module in imported:
                    aliases[alias.asname or alias.name] = imported[module]
    return aliases


def _named_paths(owner, path, nodes, imported) -> tuple[dict[str, str], bool]:
    """Repository paths the module names, each with the consumer it reaches, and
    whether it may read any file: an expression naming the root itself, or a
    computed path below it, outside tooling. A path named only inside a test
    function is that module's alone, since importers reach a module's helpers,
    not its tests; its consumer carries the ``::`` that stops the walk."""
    bases = _module_bases(path, nodes, imported)
    modules = _module_aliases(nodes, imported)
    parents = {id(child): node for node in nodes for child in ast.iter_child_nodes(node)}
    located = {id(node): _locate(node, path, bases, modules) for node in nodes}
    located = {key: value for key, value in located.items() if value is not None}

    def extended(node: ast.AST) -> bool:
        parent = parents.get(id(node))
        if parent is None:
            return False
        if id(parent) in located:
            return True
        grand = parents.get(id(parent))
        return isinstance(parent, ast.Attribute) and grand is not None and id(grand) in located

    def harmless(node: ast.AST) -> bool:
        parent = parents.get(id(node))
        if isinstance(parent, (ast.Assign, ast.AnnAssign)):
            # A name for a constant path; its uses are what read, except in shared
            # support, where declaring a directory makes it shared test input. An
            # attribute, a subscript or a computed path keeps no name to follow.
            targets = parent.targets if isinstance(parent, ast.Assign) else [parent.target]
            followed = (
                len(targets) == 1 and isinstance(targets[0], ast.Name) and located[id(node)][1]
            )
            return followed and not (owner.startswith("tests/support/") and located[id(node)][0])
        if isinstance(parent, ast.Compare):
            return True
        return (
            isinstance(parent, ast.Call)
            and isinstance(parent.func, ast.Attribute)
            and parent.func.attr in {"relative_to", "is_relative_to"}
            and node in parent.args
        )

    in_tests = (
        {
            id(child)
            for node in nodes
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for child in ast.walk(node)
        }
        if path.name.startswith("test_")
        else set()
    )
    named: dict[str, str] = {}
    anything = False
    for node in nodes:
        if id(node) not in located or extended(node) or harmless(node):
            continue
        name, complete = located[id(node)]
        if not name:
            anything = anything or not owner.startswith(TOOLING)
            continue
        if named.get(name) != owner:
            named[name] = f"{owner}::" if id(node) in in_tests else owner
    return named, anything


# Graph keys that are not paths: modules that may read any repository file, and
# modules whose imports the graph cannot follow.
ANYTHING = "*"
UNFOLLOWED = "!"


def tooling_importers() -> dict[str, set[str]]:
    """Reverse imports and named repository paths across tools AND tests.

    No code is executed and no graph survives the selection call. The small
    audited file-loader/worker exceptions below are intentionally not a Python
    expression evaluator. A module with an unknown import mechanism, or one that
    cannot be read, is listed under UNFOLLOWED: a tool change then selects the full
    suite, because the hidden consumer might be a shared fixture. Such a module,
    and one that may read any file, is also listed under ANYTHING.
    """
    paths = sorted([*(ROOT / "tools").rglob("*.py"), *TESTS.rglob("*.py")])
    modules = {
        ".".join(path.relative_to(ROOT).with_suffix("").parts).removesuffix(
            ".__init__"
        ): path.relative_to(ROOT).as_posix()
        for path in paths
    }
    graph: dict[str, set[str]] = {}
    parsed: dict[str, tuple[Path, ast.AST, list[ast.AST]]] = {}
    for path in paths:
        owner = path.relative_to(ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, SyntaxError, ValueError):
            graph.setdefault(UNFOLLOWED, set()).add(owner)
            graph.setdefault(ANYTHING, set()).add(owner)
            continue
        parsed[owner] = (path, tree, list(ast.walk(tree)))

    # Path constants a module defines or imports, until no import adds one.
    imported: dict[str, dict[str, str]] = {}
    grown = True
    while grown:
        grown = False
        for module, owner in modules.items():
            if owner in parsed:
                path, _, nodes = parsed[owner]
                found = _module_bases(path, nodes, imported)
                if found != imported.get(module, {}):
                    imported[module] = found
                    grown = True
    # A module whose tests another runs is no longer the only consumer of them.
    shared_tests = {
        node.module
        for _, _, nodes in parsed.values()
        for node in nodes
        if isinstance(node, ast.ImportFrom)
        and any(alias.name.startswith(("Test", "test_")) for alias in node.names)
    }

    def edge(module: str, owner: str) -> None:
        # Importing a submodule also executes every package initializer.
        pieces = module.split(".")
        for size in range(1, len(pieces) + 1):
            target = modules.get(".".join(pieces[:size]))
            if target:
                graph.setdefault(target, set()).add(owner)
            elif pieces[0] in {"tools", "tests"}:
                # A deleted module keeps its importers under the path it had.
                missing = "/".join(pieces[:size])
                graph.setdefault(f"{missing}.py", set()).add(owner)
                graph.setdefault(f"{missing}/__init__.py", set()).add(owner)

    for owner, (path, tree, nodes) in parsed.items():
        try:
            _follow(owner, path, tree, nodes, imported, shared_tests, graph, edge)
        except ValueError:
            graph.setdefault(UNFOLLOWED, set()).add(owner)
            graph.setdefault(ANYTHING, set()).add(owner)
    return graph


def _follow(owner, path, tree, nodes, imported, shared_tests, graph, edge) -> None:
    """Add one module's imports and named paths to *graph*; raise when its imports
    cannot be followed."""
    named, anything = _named_paths(owner, path, nodes, imported)
    module = ".".join(Path(owner).with_suffix("").parts)
    for name, consumer in named.items():
        if module in shared_tests:
            consumer = consumer.removesuffix("::")
        graph.setdefault(name, set()).add(consumer)
    if anything:
        graph.setdefault(ANYTHING, set()).add(owner)
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

    # A module or script named in a string: a subprocess, importorskip, a loader.
    for node in nodes:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value.removeprefix("./")
            if text.startswith(("tools/", "tests/")) and text.endswith(".py"):
                graph.setdefault(text, set()).add(owner)
            elif text.startswith(("tools.", "tests.")) and all(
                piece.isidentifier() for piece in text.split(".")
            ):
                edge(text, owner)

    audited: set[ast.AST] = set()
    if owner in _FILE_LOADERS:
        expected = _shape(_FILE_LOADERS[owner])
        match = next((node for node in tree.body if ast.dump(node) == expected), None)
        if match is None:
            raise ValueError(f"file loader changed: {owner}")
        audited.update(ast.walk(match))
        if owner.endswith("test_compare_device_outputs.py"):
            expected_path = _shape('TOOL = PROJECT_ROOT / "tools" / "compare_device_outputs.py"')
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


def tooling_selection(
    rel: str, graph: dict[str, set[str]], fallback: tuple[str, ...] = ("tests/tooling/",)
) -> set[str]:
    """Map reachable consumers to existing pytest paths, or *fallback* when none."""
    selected: set[str] = set()
    for consumer in dependents(rel, graph):
        if consumer.endswith("::"):
            selected.add(consumer.removesuffix("::"))
            continue
        if consumer.startswith(("tests/support/", "tests/conftest.py")):
            return set(EVERYTHING)
        if consumer.startswith("tests/"):
            path = Path(consumer)
            if path.name in {"conftest.py", "__init__.py"}:
                selected.add(f"{path.parent.as_posix()}/")
            elif path.name.startswith("test_") and (ROOT / consumer).is_file():
                selected.add(consumer)
    return selected or set(fallback)


def reader_selection(rel: str, graph: dict[str, set[str]], anything: bool = True) -> set[str]:
    """The tests of every module that names *rel*, a directory above it, or, with
    *anything*, may read any file."""
    selected: set[str] = set()
    for name, owners in graph.items():
        if (anything and name == ANYTHING) or rel == name or rel.startswith(f"{name}/"):
            for owner in owners:
                selected.update(tooling_selection(owner, graph))
    return selected


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
        if rel.startswith("src/junoscfg/") and path.suffix != ".md":
            if "/" not in rel.removeprefix("src/junoscfg/") and path.suffix != ".py":
                return list(EVERYTHING)  # a package marker such as py.typed
            graph = graph if graph is not None else importers()
            for package in dependents(package_of(path), graph):
                if package and (TESTS / "unit" / package).is_dir():
                    chosen.add(f"tests/unit/{package}/")
            chosen.add("tests/contract/")
        elif rel in {".pre-commit-config.yaml", "tach.toml"} or (
            rel.startswith("tools/") and path.suffix != ".md"
        ):
            if rel.startswith("tools/") and path.suffix == ".py":
                tool_graph = tool_graph if tool_graph is not None else tooling_importers()
                if tool_graph.get(UNFOLLOWED):
                    return list(EVERYTHING)
                chosen.update(tooling_selection(rel, tool_graph))
                # Readers of a directory above it; a deleted tool's remaining
                # importers and readers fail without it.
                chosen.update(reader_selection(rel, tool_graph, anything=not path.is_file()))
                if not path.is_file():
                    chosen.add("tests/tooling/")
            else:
                chosen.add("tests/tooling/")
        elif rel.startswith("tests/") and path.suffix != ".md":
            if path.suffix == ".py":
                # Other test modules import its helpers and tests, also after
                # it is deleted, and tools read the directories above it.
                tool_graph = tool_graph if tool_graph is not None else tooling_importers()
                if tool_graph.get(UNFOLLOWED):
                    return list(EVERYTHING)
                if path.name != "conftest.py":
                    chosen.update(tooling_selection(rel, tool_graph, fallback=()))
                chosen.update(reader_selection(rel, tool_graph, anything=not path.is_file()))
            if path.suffix == ".py" and path.is_file() and path.name != "conftest.py":
                chosen.add(rel)
            else:
                directory = path.parent
                while not directory.is_dir() and directory != TESTS:
                    directory = directory.parent
                chosen.add(f"{directory.relative_to(ROOT).as_posix()}/")
        elif not rel.startswith(("src/", "tests/", "tools/", PRIVATE)):
            tool_graph = tool_graph if tool_graph is not None else tooling_importers()
            chosen.update(reader_selection(rel, tool_graph))
            if not rel.endswith(DOCUMENTS) and not rel.startswith(RECORDS):
                chosen.add("tests/tooling/")
        # Any source, tests or tools edit, including one that removes a read or
        # an import, can change the graphs the selector's real-tree assertions pin.
        if (
            rel.startswith(("src/", "tests/", "tools/"))
            and path.suffix == ".py"
            and (ROOT / SELECTOR_TESTS).is_file()
        ):
            chosen.add(SELECTOR_TESTS)
    return [
        target
        for target in sorted(chosen)
        if not any(
            target != parent
            and (
                parent.endswith("/")
                and target.startswith(parent)
                or target.startswith(f"{parent}::")
            )
            for parent in chosen
        )
    ]


def _git(*args: str) -> list[str]:
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    return [line for line in out.stdout.splitlines() if line]


def changed_files() -> list[str]:
    """The staged files; with none staged, the branch's change and the working tree."""
    # Without rename detection a moved file also lists its old path, whose
    # readers and deletion rules still apply.
    staged = _git("diff", "--cached", "--name-only", "--no-renames")
    if staged:
        return staged
    import tomllib

    with open(ROOT / "pyproject.toml", "rb") as handle:
        base = tomllib.load(handle).get("tool", {}).get("template", {}).get("base", "master")
    fork = _git("merge-base", "HEAD", base)
    branch = _git("diff", "--name-only", "--no-renames", f"{fork[0]}...HEAD") if fork else []
    working = [line[3:] for line in _git("status", "--porcelain", "--no-renames")]
    return sorted(set(branch) | set(working))


def reuse_blocker() -> str | None:
    """Refuse reuse when pytest may read undeclared external/private inputs."""
    import tomllib

    if any(value and key.startswith(("PYTEST_", "JUNOSCFG_")) for key, value in os.environ.items()):
        return "pytest or Junoscfg environment overrides"
    for name in PYTEST_CONFIGURATION:
        if (ROOT / name).exists():
            return "alternate pytest configuration"
    # Evidence identity binds tracked bytes only. pytest also collects a module
    # that .gitignore hides, and a listing git cannot produce proves nothing.
    listings = [
        subprocess.run(
            ["git", "ls-files", "--others", *flags, "--exclude-standard", "--", *paths],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        for flags, paths in (
            ((), UNTRACKED_INPUTS),
            (
                ("--ignored",),
                (*(f":(glob){top}/**/*.py" for top in UNTRACKED_INPUTS[:3]), "conftest.py"),
            ),
        )
    ]
    if any(listing.returncode for listing in listings):
        return "untracked files cannot be listed"
    if any(listing.stdout.strip() for listing in listings):
        return "untracked files beside the tested code"
    for name in ("captures", "schemas"):
        path = ROOT / "private_test_data" / name
        if path.exists() or path.is_symlink():
            return "private corpus or schema discovery inputs"
    try:
        config = tomllib.loads((ROOT / "pyproject.toml").read_text())
        options = config["tool"]["pytest"]["ini_options"]["addopts"]
    except (OSError, ValueError, KeyError):
        return "unclassified pytest configuration"
    if options != ["--strict-markers", "--strict-config", "-ra"]:
        return "unclassified pytest options"
    return None


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

    blocker = reuse_blocker()
    if blocker:
        print(f"affected-test evidence unavailable; executing tests: {blocker}", file=sys.stderr)
    if not blocker and readiness.config(ROOT).get("enabled", False):
        try:
            return verification.execute(
                ROOT,
                command,
                None,
                {"name": "affected-tests"},
            )
        except (OSError, ValueError) as error:
            # A deleted tracked input or unavailable identity cannot prove reuse.
            # Running the selected tests still satisfies the ordinary obligation.
            print(f"affected-test evidence unavailable; executing tests: {error}", file=sys.stderr)
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
