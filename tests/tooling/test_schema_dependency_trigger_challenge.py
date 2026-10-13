"""Independent probes for the entire-lock dependency trigger boundary."""

from __future__ import annotations

import importlib
import json
import os
import subprocess

import pytest
from agent_ready_checks import verification

from tests.support.paths import PROJECT_ROOT
from tests.tooling.test_schema_verification import commit_fixture, git

LOCK = """version = 1
revision = 3
requires-python = ">=3.10"
resolution-markers = ["python_full_version >= '3.11'"]
[[package]]
name = "junoscfg"
version = "0.28.3"
source = { editable = "." }
dependencies = [{ name = "lxml" }]
[package.metadata]
requires-dist = [{ name = "lxml", specifier = ">=1" }]
[[package]]
name = "lxml"
version = "1.0"
source = { registry = "https://example.invalid/simple" }
wheels = [{ url = "https://example.invalid/pkg.whl", hash = "sha256:abc", size = 10 }]
"""
MANIFEST = "tools/schema-verification/dependencies.json"
RESULT = ".agent-ready/schema/dependencies-result.json"


@pytest.fixture(autouse=True)
def isolated_git_environment(monkeypatch):
    """Native wrapper inspection must remain inside each tiny fixture repository."""
    selectors = {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_PREFIX",
        "GIT_CEILING_DIRECTORIES",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    }
    for key in tuple(os.environ):
        if key in selectors or key.startswith("GIT_CONFIG"):
            monkeypatch.delenv(key)


def dependency_module():
    return importlib.import_module("tools.schema_dependencies")


def lock_repository(tmp_path):
    (tmp_path / "uv.lock").write_text(LOCK)
    (tmp_path / "tools/schema-verification").mkdir(parents=True)
    return tmp_path


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("revision = 3", "revision = 4"),
        ('requires-python = ">=3.10"', 'requires-python = ">=3.11"'),
        ("python_full_version >= '3.11'", "python_full_version >= '3.12'"),
        ('dependencies = [{ name = "lxml" }]', 'dependencies = [{ name = "other" }]'),
        ('specifier = ">=1"', 'specifier = ">=2"'),
        ('version = "1.0"', 'version = "2.0"'),
        ('registry = "https://example.invalid/simple"', 'registry = "https://other.invalid"'),
        ('hash = "sha256:abc"', 'hash = "sha256:def"'),
        ("size = 10", "size = 11"),
        ("pkg.whl", "other.whl"),
    ],
)
def test_every_nonroot_version_field_affects_projection(tmp_path, before, after):
    root = lock_repository(tmp_path)
    module = dependency_module()
    original = module.fingerprint(root)
    assert LOCK.count(before) == 1
    (root / "uv.lock").write_text(LOCK.replace(before, after))
    assert module.fingerprint(root) != original


@pytest.mark.parametrize(
    "lock",
    [
        LOCK.replace('version = "0.28.3"\n', ""),
        LOCK.replace('version = "0.28.3"', 'version = ""'),
        LOCK.replace('version = "0.28.3"', "version = 42"),
        LOCK.replace('name = "junoscfg"', 'name = "other"'),
        LOCK.replace('source = { editable = "." }', 'source = { editable = "../junoscfg" }'),
        LOCK.replace('source = { editable = "." }', 'source = { editable = ".", extra = true }'),
        LOCK + '\n[[package]]\nname = "junoscfg"\nversion = "2"\nsource = { editable = "." }\n',
        "[[package]\n",
    ],
)
def test_invalid_root_never_produces_projection(tmp_path, lock):
    root = lock_repository(tmp_path)
    (root / "uv.lock").write_text(lock)
    with pytest.raises(ValueError):
        dependency_module().fingerprint(root)


@pytest.mark.parametrize("fault", ["missing", "malformed", "stale"])
def test_guard_failure_removes_previous_success(tmp_path, fault):
    root = lock_repository(tmp_path)
    module = dependency_module()
    module.write_dependencies(root)
    # Seed exactly the declaration's real completion record, never guessed IDs.
    required = PROJECT_ROOT / "tools/schema-verification/dependencies.required.json"
    (root / required.relative_to(PROJECT_ROOT)).write_bytes(required.read_bytes())
    assert module.run_guard(root) == 0
    assert (root / RESULT).is_file()
    if fault == "missing":
        (root / MANIFEST).unlink()
    elif fault == "malformed":
        (root / MANIFEST).write_text('{"invalid":')
    else:
        (root / "uv.lock").write_text(LOCK.replace('version = "1.0"', 'version = "2.0"'))
    with pytest.raises((ValueError, OSError)):
        module.run_guard(root)
    assert not (root / RESULT).exists()


def test_native_selection_distinguishes_version_only_from_dependencies(tmp_path, monkeypatch):
    """Native tier routing uses real lock classification with explicit context state.

    Receipt integrity belongs to the native-context tests; this fixture has no
    installed project interpreter or schema products. Bridge only the selector
    process and expose both valid-context and uncertain-context decisions.
    """
    selection = importlib.import_module("tools.schema_selection")
    context = {"valid": True}
    consulted = []

    def established(root, base, patterns):
        consulted.append((root, base))
        return context["valid"]

    monkeypatch.setattr(selection, "established_context", established)
    original_run = subprocess.run

    def selector_process(command, *args, **kwargs):
        if "tools.schema_selection" in command:
            compared_base = command[command.index("--base") + 1]
            selected = selection.select(kwargs["cwd"], compared_base)
            return subprocess.CompletedProcess(command, 0, json.dumps({"selected": selected}), "")
        return original_run(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", selector_process)
    root = lock_repository(tmp_path)
    module = dependency_module()
    (root / "pyproject.toml").write_bytes((PROJECT_ROOT / "pyproject.toml").read_bytes())
    module.write_dependencies(root)
    git(root, "init", "-q")
    commit_fixture(root)
    base = git(root, "rev-parse", "HEAD").strip()
    (root / "uv.lock").write_text(LOCK.replace('version = "0.28.3"', 'version = "0.28.4"'))
    module.check_dependencies(root)
    commit_fixture(root)
    selected = verification.tiers(root, base, selection=True)
    assert len(selected) == 1
    assert "tools.schema_dependencies" in selected[0]["command"]
    guard = selected[0]["name"]
    assert consulted and all(compared == (root, base) for compared in consulted)
    context["valid"] = False
    assert [tier["name"] for tier in verification.tiers(root, base, selection=True)] == [
        guard,
        "schema-25.2",
        "schema-25.2-generation",
    ]
    context["valid"] = True
    (root / "uv.lock").write_text(LOCK.replace('version = "1.0"', 'version = "2.0"'))
    with pytest.raises(ValueError):
        module.check_dependencies(root)
    module.write_dependencies(root)
    commit_fixture(root)
    assert [tier["name"] for tier in verification.tiers(root, base, selection=True)] == [
        guard,
        "schema-25.2",
        "schema-25.2-generation",
    ]
