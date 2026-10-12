"""Acceptance tests for lock-aware schema scheduling, without real schema work."""

from __future__ import annotations

import importlib
import json

import pytest

from tests.support.paths import PROJECT_ROOT
from tests.tooling.test_schema_qualification import generation_repository
from tests.tooling.test_schema_verification import SHARD, adapter

LOCK = """version = 1
requires-python = ">=3.10"
[[package]]
name = "junoscfg"
version = "0.28.3"
source = { editable = "." }
dependencies = [{ name = "lxml" }]
[[package]]
name = "lxml"
version = "6.0.2"
source = { registry = "https://pypi.org/simple" }
wheels = [{ url = "https://example.invalid/wheel", hash = "sha256:abcd" }]
"""
MANIFEST = "tools/schema-verification/dependencies.json"
RESULT = ".agent-ready/schema/dependencies-result.json"
OBLIGATIONS = {"tests": ["schema-dependency-consistency"], "shards": []}


def dependency_tool():
    return importlib.import_module("tools.schema_dependencies")


def lock_repository(tmp_path):
    (tmp_path / "uv.lock").write_text(LOCK)
    manifests = tmp_path / "tools/schema-verification"
    manifests.mkdir(parents=True)
    (manifests / "dependencies.required.json").write_text(json.dumps(OBLIGATIONS))
    return tmp_path


def test_only_root_version_is_ignored(tmp_path):
    root = lock_repository(tmp_path)
    before = dependency_tool().fingerprint(root)
    (root / "uv.lock").write_text(LOCK.replace('version = "0.28.3"', 'version = "0.28.4"'))
    assert dependency_tool().fingerprint(root) == before
    (root / "uv.lock").write_text(LOCK.replace('version = "6.0.2"', 'version = "6.0.3"'))
    assert dependency_tool().fingerprint(root) != before


@pytest.mark.parametrize("fault", ["malformed", "missing", "duplicate", "source", "version"])
def test_ambiguous_or_invalid_root_refuses(tmp_path, fault):
    root = lock_repository(tmp_path)
    text = LOCK
    if fault == "malformed":
        text = "[[package]"
    elif fault == "missing":
        text = text.replace('name = "junoscfg"', 'name = "other"')
    elif fault == "duplicate":
        text += '\n[[package]]\nname = "junoscfg"\nversion = "1"\nsource = { editable = "." }\n'
    elif fault == "source":
        text = text.replace('editable = "."', 'editable = "../other"')
    else:
        text = text.replace('version = "0.28.3"', 'version = ""')
    (root / "uv.lock").write_text(text)
    with pytest.raises((ValueError, OSError)):
        dependency_tool().fingerprint(root)


def test_guard_publishes_only_consistency(tmp_path):
    root = lock_repository(tmp_path)
    tool = dependency_tool()
    tool.write_dependencies(root)
    assert tool.run_guard(root) == 0
    result = root / RESULT
    assert json.loads(result.read_text()) == OBLIGATIONS
    (root / "uv.lock").write_text(LOCK.replace("sha256:abcd", "sha256:changed"))
    with pytest.raises(ValueError):
        tool.run_guard(root)
    assert not result.exists()


def test_committed_fingerprint_is_current():
    dependency_tool().check_dependencies(PROJECT_ROOT)


@pytest.mark.parametrize("action", ["run", "generation", "sentinel", "qualify"])
def test_schema_preflight_refuses_stale_dependencies(tmp_path, monkeypatch, action):
    root, _, _, _ = generation_repository(tmp_path)
    manifest = root / MANIFEST
    manifest.write_text('{"format":1,"sha256":"stale"}')
    # A stale committed projection must fail as a dependency invariant, not
    # merely because the candidate is dirty or a later schema input is absent.
    from tests.tooling.test_schema_verification import commit_fixture

    commit_fixture(root)
    module = adapter()

    def forbidden(*args, **kwargs):
        pytest.fail("costly execution started with stale dependency fingerprint")

    monkeypatch.setattr(module.ArtifactBuilder, "build", forbidden)
    monkeypatch.setattr(module.subprocess, "run", forbidden)
    calls = {
        "run": lambda: module.run_shard(root, SHARD),
        "generation": lambda: module.run_generation(root, SHARD),
        "sentinel": lambda: module.run_sentinel(root),
        "qualify": lambda: module.qualify(root, SHARD),
    }
    with pytest.raises(ValueError, match="dependenc"):
        calls[action]()
