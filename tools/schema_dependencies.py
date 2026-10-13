"""Execution dependency lock fingerprint and cheap schema dependency consistency guard."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import tomllib

MANIFEST = "tools/schema-verification/dependencies.json"
REQUIRED = "tools/schema-verification/dependencies.required.json"
RESULT = ".agent-ready/schema/dependencies-result.json"
# Audited execution roots: generators/validators, public CLI regeneration and
# the assertion harness. Native runtime identity additionally discovers plugins.
SCHEMA_PACKAGES = (
    "click",
    "jsonschema",
    "lark",
    "lxml",
    "pytest",
    "pytest-cov",
    "pyyaml",
)

OBLIGATIONS = {"tests": ["schema-dependency-consistency"], "shards": []}


def _physical(root: Path, name: str) -> Path:
    path = root / name
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("schema dependency paths must be physical")
    return path


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"schema dependency JSON is missing or invalid: {path.name}") from error


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=path.parent) as directory:
        temporary = Path(directory) / path.name
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(path)


def fingerprint(root: Path) -> dict:
    """Represent the locked transitive execution closure and resolution constraints."""
    try:
        return fingerprint_text(_physical(root, "uv.lock").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError("schema dependency lock is missing or invalid") from error


def fingerprint_text(text: str) -> dict:
    """Apply the same relevance rule to a historical committed lockfile."""
    data = tomllib.loads(text)
    packages = data.get("package")
    if not isinstance(packages, list) or any(not isinstance(item, dict) for item in packages):
        raise ValueError("schema dependency package inventory is invalid")
    roots = [item for item in packages if item.get("name") == "junoscfg"]
    if len(roots) != 1 or roots[0].get("source") != {"editable": "."}:
        raise ValueError("schema dependencies require one unambiguous editable root")
    version = roots[0].get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("schema dependency root version is missing or invalid")
    inventory = {}
    for package in packages:
        name = package.get("name")
        if not isinstance(name, str):
            raise ValueError("schema dependency has no package name")
        inventory.setdefault(name.lower().replace("_", "-"), []).append(package)
    pending = set(SCHEMA_PACKAGES) & set(inventory)
    if not pending:
        raise ValueError("schema execution dependency inventory is empty")
    selected = {}
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        records = inventory.get(name)
        if not records:
            raise ValueError(f"unresolved schema dependency: {name}")
        # Bind all marker/platform variants rather than guessing this machine's
        # branch of a universal lock. All source, wheel and dependency bytes stay.
        selected[name] = records
        for record in records:
            edges = list(record.get("dependencies", []))
            for group in record.get("optional-dependencies", {}).values():
                edges.extend(group)
            for edge in edges:
                dependency = edge.get("name")
                if not isinstance(dependency, str):
                    raise ValueError("invalid schema dependency edge")
                pending.add(dependency.lower().replace("_", "-"))
    root = dict(roots[0])
    del root["version"]
    for key in ("dependencies",):
        root[key] = [edge for edge in root.get(key, []) if edge.get("name") in selected]
    # Only requirements for execution dependencies participate in root metadata.
    # The installed module closure independently binds checks engine code.
    for key in ("optional-dependencies", "dev-dependencies"):
        root.pop(key, None)
    metadata = root.get("metadata", {})
    root["metadata"] = {
        key: [edge for edge in value if edge.get("name") in selected]
        for key, value in metadata.items()
        if key == "requires-dist"
    }
    data["package"] = [root, *[record for name in sorted(selected) for record in selected[name]]]
    try:
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError("schema dependency lock contains unsupported values") from error
    return {"format": 2, "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}


def write_dependencies(root: Path) -> None:
    """Deliberately refresh the tracked projection after a relevant lock change."""
    _write_json(_physical(root, MANIFEST), fingerprint(root))


def check_dependencies(root: Path) -> None:
    """Refuse stale projection without generating or mutating any evidence."""
    actual = _read_json(_physical(root, MANIFEST))
    if (
        not isinstance(actual, dict)
        or type(actual.get("format")) is not int
        or actual != fingerprint(root)
    ):
        raise ValueError(
            "schema dependency fingerprint is stale or malformed; "
            "run tools.schema_dependencies write"
        )


def run_guard(root: Path) -> int:
    """Publish only actual dependency consistency, never schema execution IDs."""
    result = _physical(root, RESULT)
    result.unlink(missing_ok=True)
    if _read_json(_physical(root, REQUIRED)) != OBLIGATIONS:
        raise ValueError("schema dependency guard obligations differ")
    check_dependencies(root)
    _write_json(result, OBLIGATIONS)
    return 0


def main(argv=None) -> int:
    """Refresh the projection deliberately or execute its cheap consistency guard."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("write", "check"))
    args = parser.parse_args(argv)
    try:
        if args.action == "write":
            write_dependencies(Path.cwd())
        else:
            return run_guard(Path.cwd())
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
