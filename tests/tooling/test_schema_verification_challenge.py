"""Independent counterexamples for the frozen schema evidence requirements."""

from __future__ import annotations

import json
import subprocess

import pytest

from junoscfg.validate import ArtifactBuilder
from tests.tooling.test_schema_verification import DUMP, SHARD, adapter, small_repository


class TestPrerequisitesBeforeExecution:
    @pytest.mark.parametrize("fault", ["missing-dump", "missing-runtime", "staged-dump"])
    def test_shard_refuses_before_launching_pytest(self, tmp_path, monkeypatch, fault):
        root, _, policy = small_repository(tmp_path)
        if fault == "missing-dump":
            (root / "private_test_data/schemas" / DUMP).unlink()
        elif fault == "missing-runtime":
            (root / policy["runtime"]).unlink()
        else:
            (root / "private_test_data/schemas/new.xsd").write_text("staged")
        original = subprocess.run
        launched = []

        def observe(command, *args, **kwargs):
            if any("pytest" in str(part) for part in command):
                launched.append(command)
                raise AssertionError("costly execution preceded prerequisite refusal")
            return original(command, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", observe)
        try:
            status = adapter().run_shard(root, SHARD)
        except (ValueError, OSError):
            status = 1
        assert status != 0
        assert launched == []
        if fault == "staged-dump":
            assert (root / "private_test_data/schemas/new.xsd").read_text() == "staged"

    def test_sentinel_refuses_runtime_mismatch_before_generation(self, tmp_path, monkeypatch):
        root, _, policy = small_repository(tmp_path)
        path = root / policy["runtime"]
        values = json.loads(path.read_text())
        values[next(iter(values))] = "changed runtime"
        path.write_text(json.dumps(values))
        launched = []

        def generate(*args, **kwargs):
            launched.append(True)
            raise AssertionError("generator preceded runtime refusal")

        monkeypatch.setattr(ArtifactBuilder, "build", generate)
        try:
            status = adapter().run_sentinel(root)
        except (ValueError, OSError):
            status = 1
        assert status != 0
        assert launched == []


class TestFailureCannotPublishSuccess:
    def test_actual_failed_run_cannot_retain_success_manifests(self, tmp_path):
        root, required, policy = small_repository(tmp_path, fault="failed")
        recipe = policy["shards"][SHARD]
        result = root / recipe["result"]
        outcomes = root / recipe["outcomes"]
        result.parent.mkdir(parents=True, exist_ok=True)
        result.write_text(json.dumps(required))
        old_success = {
            "tests": {node: {"outcome": "passed", "reason": ""} for node in required["tests"]}
        }
        outcomes.write_text(json.dumps(old_success))
        try:
            status = adapter().run_shard(root, SHARD)
        except (ValueError, OSError):
            status = 1
        assert status != 0
        assert not result.exists()
        if outcomes.exists():
            current = json.loads(outcomes.read_text())
            assert current != old_success
            assert any(row["outcome"] != "passed" for row in current["tests"].values())
