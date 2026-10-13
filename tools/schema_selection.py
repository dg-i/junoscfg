"""Conservative schema relevance backed by native successful generation evidence."""

import argparse
import ast
import fnmatch
import hashlib
import json
import subprocess
import sys
from contextlib import suppress
from pathlib import Path

import tomllib

from tools.schema_dependencies import check_dependencies, fingerprint_text

CONSUMERS = (
    "src/junoscfg/anonymize/",
    "src/junoscfg/audit/",
    "src/junoscfg/edityaml/",
)
# These modules execute qualification or supply fixtures/data locations. Other
# tools do not become schema dependencies merely by sharing this directory.
EXECUTION_PATHS = {
    "tools/schema_selection.py",
    "tools/schema_dependencies.py",
    "tools/schema_verification.py",
    "tools/schema_content_worker.py",
    "tests/conftest.py",
    "tests/support/schema_data.py",
    "tests/support/regen.py",
    "tests/support/paths.py",
    "tests/support/artifacts.py",
    "tests/support/devices.py",
    "tests/support/shapes.py",
    "tests/corpus/test_schema_data.py",
}
WORKFLOW_CONFIG = {
    ".pre-commit-config.yaml",
    "mkdocs.yml",
    "tach.toml",
    "ruff.toml",
    ".copier-answers.yml",
    ".gitignore",
    "tools/verification-costs.json",
}


def configuration(text):
    """Bind audited schema readers, not unrelated tool/agent settings."""
    value = tomllib.loads(text)
    project = value.get("project", {})
    tool = value.get("tool", {})
    template = tool.get("template", {})
    return {
        "build-system": value.get("build-system"),
        "requires-python": project.get("requires-python"),
        "scripts": project.get("scripts"),
        "tools": {
            key: item
            for key, item in tool.items()
            if key
            not in {
                "template",
                "uv",
                "ruff",
                "mypy",
                "coverage",
                "towncrier",
                "hatch",
                "deptry",
                "tach",
            }
        },
        "unknown": {
            key: item
            for key, item in value.items()
            if key not in {"project", "tool", "build-system", "dependency-groups"}
        },
        "tiers": template.get("batch", {}).get("expensive-tiers"),
    }


def import_shape(source):
    """Retain import-time AST structure while removing consumer function bodies."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.body = [ast.Pass()]
    # A callback/decorator/metaclass can execute a changed body during import.
    # Decline that exemption rather than assuming the callback is harmless.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            raise ValueError("import-time call requires qualification")
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.decorator_list
        ):
            raise ValueError("decorator requires qualification")
        if isinstance(node, ast.ClassDef) and (node.bases or node.keywords):
            raise ValueError("class construction requires qualification")
    return ast.dump(tree, include_attributes=False)


def version_shape(text):
    """Ignore only the root package's literal release version assignment."""
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == "__version__":
                if not isinstance(node.value, ast.Constant) or not isinstance(
                    node.value.value, str
                ):
                    raise ValueError("unknown package version")
                node.value = ast.Constant(value="release-version")
    return ast.dump(tree, include_attributes=False)


def classify(path, patterns, old=None, new=None):
    """Return true unless a changed path is demonstrably outside schema production."""
    if not path or Path(path).is_absolute() or ".." in Path(path).parts:
        return True
    if path in {"uv.lock", "pyproject.toml", "src/junoscfg/__init__.py"}:
        if old is None or new is None:
            return True
        try:
            if path == "uv.lock":
                return fingerprint_text(old) != fingerprint_text(new)
            if path.endswith("__init__.py"):
                return version_shape(old) != version_shape(new)
            return configuration(old) != configuration(new)
        except (SyntaxError, TypeError, ValueError, KeyError):
            return True
    if any(fnmatch.fnmatch(path, pattern) for pattern in patterns):
        return True
    if path.endswith((".md", ".rst")):
        return False
    if path in EXECUTION_PATHS or path.startswith(
        ("src/junoscfg/validate/", "tools/schema-verification/")
    ):
        return True
    if path.startswith(CONSUMERS):
        try:
            return old is None or new is None or import_shape(old) != import_shape(new)
        except (SyntaxError, TypeError, ValueError):
            return True
    if path in WORKFLOW_CONFIG:
        return False
    if path.startswith("tools/") and path.endswith(".py"):
        return False
    if path.startswith((".agents/", ".claude/", ".codex/")) or path in {
        "CLAUDE.md",
        "CHANGELOG.md",
    }:
        return False
    if path.startswith("tests/tooling/") and path.endswith(".py"):
        return False
    if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")):
        return False
    if path.endswith((".md", ".rst")):
        return False
    if path.startswith("openspec/changes/") and Path(path).name in {
        ".openspec.yaml",
        "metrics.json",
        "events.jsonl",
        "lifecycle.json",
    }:
        return False
    return path != ".agent-ready/activation.json"


def git_text(root, *arguments):
    """Read the candidate repository, failing closed when comparison is unavailable."""
    return subprocess.check_output(["git", *arguments], cwd=root, text=True)


def old_text(root, base, path):
    """Missing/deleted history supplies no consumer-body exemption."""
    result = subprocess.run(["git", "show", base + ":" + path], cwd=root, capture_output=True)
    try:
        return result.stdout.decode() if result.returncode == 0 else None
    except UnicodeError:
        return None


def historical_version_text(root, base, path, expected):
    """Recover only hash-proven release-file bytes from comparison-base ancestry."""
    if path not in {"uv.lock", "pyproject.toml", "src/junoscfg/__init__.py"}:
        return None
    for commit in git_text(root, "log", "--format=%H", base, "--", path).splitlines():
        text = old_text(root, commit, path)
        if text is not None and hashlib.sha256(text.encode()).hexdigest() == expected:
            return text
    return None


def new_text(root, path):
    """Nontext and unavailable content remains uncertain."""
    try:
        return (root / path).read_text()
    except (OSError, UnicodeError):
        return None


def declarations(root):
    """Read the existing authoritative application tier table."""
    config = tomllib.loads((root / "pyproject.toml").read_text())
    return [
        tier
        for tier in config["tool"]["template"]["batch"]["expensive-tiers"]
        if tier["name"] in {"schema-25.2", "schema-25.2-generation"}
    ]


def execution_sources(root, names):
    """Close audited source roots over local imports, including package doors.

    All product sources remain in the reviewed boundary: lazy exports and
    callbacks cannot silently promote an excluded consumer into a producer.
    Local tooling imports are followed so a helper outside tools/schema* stays
    relevant. Changing an audited dynamic import requires a renewed audit.
    """
    modules = {}
    for name in names:
        if not name.endswith(".py"):
            continue
        module = name.removeprefix("src/")[:-3].replace("/", ".")
        if module.endswith(".__init__"):
            module = module[:-9]
        modules[module] = name
    pending = {
        name
        for name in names
        if name.endswith(".py") and (name.startswith("src/junoscfg/") or name in EXECUTION_PATHS)
    }
    selected = set()
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        selected.add(name)
        source = (root / name).read_text()
        module = name.removeprefix("src/")[:-3].replace("/", ".")
        package = module.rsplit(".", 1)[0]
        for node in ast.walk(ast.parse(source)):
            imports = []
            if isinstance(node, ast.Import):
                imports = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom):
                prefix = node.module or ""
                if node.level:
                    parents = package.split(".")
                    prefix = ".".join(
                        parents[: len(parents) - node.level + 1] + ([prefix] if prefix else [])
                    )
                imports = [prefix, *[prefix + "." + item.name for item in node.names]]
            for imported in imports:
                parts = imported.split(".")
                for index in range(1, len(parts) + 1):
                    target = modules.get(".".join(parts[:index]))
                    if target:
                        pending.add(target)
    return selected


def source_boundary(root):
    """Fingerprint the explicitly audited producer/consumer source relationship.

    Qualification success alone cannot audit a newly introduced call dependency.
    Only already-audited isolated consumer bodies and root release versions are
    normalized; every other source byte and relevant lock field remains bound.
    """
    from agent_ready_checks import verification

    patterns = [pattern for tier in declarations(root) for pattern in tier["paths"]]
    result = {}
    names = verification.tracked(root)
    execution = execution_sources(root, names)
    for name in names:
        if not name.endswith(".py") or not (
            name in execution or any(fnmatch.fnmatch(name, pattern) for pattern in patterns)
        ):
            continue
        text = (root / name).read_text()
        normalized = "source\0" + text
        if name == "src/junoscfg/__init__.py":
            normalized = "root-version\0" + version_shape(text)
        elif name.startswith(CONSUMERS) and not any(
            fnmatch.fnmatch(name, pattern) for pattern in patterns
        ):
            # No isolation proof leaves the complete source bytes bound.
            with suppress(SyntaxError, TypeError, ValueError):
                normalized = "consumer-imports\0" + import_shape(text)
        result[name] = hashlib.sha256(normalized.encode()).hexdigest()
    if not result:
        raise ValueError("audited source boundary is empty")
    config = configuration((root / "pyproject.toml").read_text())
    result["pyproject.toml"] = hashlib.sha256(repr(config).encode()).hexdigest()
    result["uv.lock"] = fingerprint_text((root / "uv.lock").read_text())["sha256"]
    return result


def verified_source_boundary(root):
    """Missing or changed audit scope cannot authorize a negative selection."""
    path = root / "tools/schema-verification/consumer-boundary.json"
    try:
        if path.is_symlink():
            return False
        value = json.loads(path.read_text())
        return (
            isinstance(value, dict)
            and set(value) == {"format", "sources"}
            and type(value["format"]) is int
            and value["format"] == 1
            and value["sources"] == source_boundary(root)
        )
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError):
        return False


def established_context(root, base, patterns):
    """Require native successful generation proof for unchanged inputs and engine.

    This classifies work; it never publishes, copies or admits a reused receipt.
    Native execution remains the sole authority for whole-tier reuse.
    """
    from agent_ready_checks import verification

    from tools.schema_verification import verify_versions

    reasons = {"no successful native generation receipt found"}
    try:
        if not verified_source_boundary(root):
            print(
                "schema qualification: audited execution boundary missing or changed",
                file=sys.stderr,
            )
            return False
        declared = next(
            tier for tier in declarations(root) if tier["name"] == "schema-25.2-generation"
        )
        if not declared.get("runtime-command"):
            raise ValueError("generation declaration has no runtime command")
        from agent_ready_checks import verification_runtime

        verify_versions(root / ".agent-ready/schema/runtime.json")
        current_engine = verification_runtime.runtime(root, declared)
        explicit = set(declared.get("inputs", []) + declared.get("version-files", []))
        # Prepared metadata is observed independently; it may change solely because
        # editable root release metadata changed. It is never qualification proof.
        explicit.discard(".agent-ready/schema/runtime.json")
        explicit_hashes = verification.manifest(root, sorted(explicit))
        names = verification.tracked(root)
        current = verification.manifest(root, names)
        directory = root / verification.STORE
        if directory.is_symlink():
            raise ValueError("native evidence directory is a symlink")
        for path in directory.glob("*.json"):
            try:
                if path.is_symlink():
                    reasons.add("native receipt is a symlink")
                    continue
                record = verification.read_json(path)
                identity = record["identity"]
                if path.stem != record["id"] or identity["declaration"] != declared:
                    reasons.add("receipt identity or generation declaration differs")
                    continue
                if identity.get("tier_runtime") != current_engine or identity["root"] != str(
                    root.resolve()
                ):
                    reasons.add("executing runtime or physical worktree differs")
                    continue
                if not verification.valid(root, identity, record):
                    reasons.add("receipt completion, output hashes or provenance is invalid")
                    continue
                recorded = identity["files"]
                if any(recorded.get(name) != value for name, value in explicit_hashes.items()):
                    reasons.add("declared schema input or prerequisite artifact differs")
                    continue
                safe = True
                # Untracked declared input differences have already been checked.
                # Source changes not covered by the caller's comparison base cannot
                # borrow a consumer-body exemption from a different source version.
                for name in set(current) | (set(recorded) - set(declared.get("inputs", []))):
                    if name == ".agent-ready/schema/runtime.json" or current.get(
                        name
                    ) == recorded.get(name):
                        continue
                    previous = old_text(root, base, name)
                    if previous is not None and hashlib.sha256(
                        previous.encode()
                    ).hexdigest() != recorded.get(name):
                        previous = historical_version_text(root, base, name, recorded.get(name))
                    if classify(name, patterns, previous, new_text(root, name)):
                        reasons.add(f"relevant receipt input differs: {name}")
                        safe = False
                        break
                if safe:
                    return True
            except (OSError, ValueError, KeyError, TypeError) as error:
                reasons.add(f"malformed or unreadable native receipt: {error}")
                continue
    except (
        ImportError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        StopIteration,
        subprocess.SubprocessError,
    ) as error:
        reasons.add(str(error))
    print("schema qualification: " + "; ".join(sorted(reasons)), file=sys.stderr)
    return False


def select(root, base):
    """Select relevant changes or uncertain context; never refresh preparation."""
    check_dependencies(root)
    patterns = [pattern for tier in declarations(root) for pattern in tier["paths"]]
    from agent_ready_checks import verification

    patterns.extend(
        execution_sources(root, verification.tracked(root))
        - {name for name in verification.tracked(root) if name.startswith(CONSUMERS)}
    )
    changed = git_text(root, "diff", "--name-only", "--no-renames", base + "...HEAD").splitlines()
    for path in changed:
        if classify(path, patterns, old_text(root, base, path), new_text(root, path)):
            print(
                f"schema qualification: relevant or uncertain execution input changed: {path}",
                file=sys.stderr,
            )
            return True

    return not established_context(root, base, patterns)


def main():
    """Native selection protocol: exact boolean JSON, failures never mean false."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    print(json.dumps({"selected": select(Path.cwd(), args.base)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
