"""Conservative schema relevance backed by native successful generation evidence."""

import argparse
import ast
import fnmatch
import hashlib
import json
import subprocess
from pathlib import Path

import tomllib

from tools.schema_dependencies import check_dependencies, fingerprint_text

CONSUMERS = (
    "src/junoscfg/convert/",
    "src/junoscfg/anonymize/",
    "src/junoscfg/audit/",
    "src/junoscfg/edityaml/",
)
VALIDATORS = {
    f"src/junoscfg/validate/{name}.py"
    for name in (
        "validator",
        "json_yaml_validator",
        "xml_validator",
        "set_validator",
        "structured_validator",
    )
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
            before, after = tomllib.loads(old), tomllib.loads(new)
            for value in (before, after):
                version = value["project"].pop("version")
                if not isinstance(version, str) or not version:
                    return True
            return before != after
        except (SyntaxError, TypeError, ValueError, KeyError):
            return True
    if any(fnmatch.fnmatch(path, pattern) for pattern in patterns):
        return True
    if path.startswith(CONSUMERS) or path in VALIDATORS:
        try:
            return old is None or new is None or import_shape(old) != import_shape(new)
        except (SyntaxError, TypeError, ValueError):
            return True
    if path.startswith("tests/tooling/") and path.endswith(".py"):
        return False
    if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")):
        return False
    if path.endswith(".md") and (
        path.startswith(("docs/", "openspec/", "changelog.d/"))
        or path in {"README.md", "AGENTS.md"}
    ):
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


def established_context(root, base, patterns):
    """Require native successful generation proof for unchanged inputs and engine.

    This classifies work; it never publishes, copies or admits a reused receipt.
    Native execution remains the sole authority for whole-tier reuse.
    """
    from agent_ready_checks import verification

    from tools.schema_verification import verify_versions

    try:
        declared = next(
            tier for tier in declarations(root) if tier["name"] == "schema-25.2-generation"
        )
        if not declared.get("runtime-command"):
            return False
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
            return False
        for path in directory.glob("*.json"):
            try:
                if path.is_symlink():
                    continue
                record = verification.read_json(path)
                identity = record["identity"]
                if path.stem != record["id"] or identity["declaration"] != declared:
                    continue
                if identity.get("tier_runtime") != current_engine or identity["root"] != str(
                    root.resolve()
                ):
                    continue
                if not verification.valid(root, identity, record):
                    continue
                recorded = identity["files"]
                if any(recorded.get(name) != value for name, value in explicit_hashes.items()):
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
                        safe = False
                        break
                if safe:
                    return True
            except (OSError, ValueError, KeyError, TypeError):
                continue
    except (
        ImportError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        StopIteration,
        subprocess.SubprocessError,
    ):
        return False
    return False


def select(root, base):
    """Select relevant changes or uncertain context; never refresh preparation."""
    check_dependencies(root)
    patterns = [pattern for tier in declarations(root) for pattern in tier["paths"]]
    changed = git_text(root, "diff", "--name-only", "--no-renames", base + "...HEAD").splitlines()
    if any(
        classify(path, patterns, old_text(root, base, path), new_text(root, path))
        for path in changed
    ):
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
