"""Non-timestamp metadata participates in genuine wrapper stability execution."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from agent_ready_checks import verification

from tests.support.paths import PROJECT_ROOT
from tests.tooling.test_schema_verification import SHARD, commit_fixture, git, small_repository


class TestMetadataStabilityAcrossExecutedPasses:
    """The actual second generation preserves all non-timestamp metadata."""

    @pytest.mark.parametrize("shard", ["schema-21.4", "schema-23.2"])
    @pytest.mark.parametrize("change", ["semantic", "generated_at"])
    def test_only_generated_at_may_change(self, tmp_path, monkeypatch, shard, change):
        """Reject semantic drift while allowing the established timestamp exception."""
        parent = tmp_path / "hook-parent"
        parent.mkdir()
        git(parent, "init", "-q")
        (parent / "tracked").write_text("parent candidate")
        commit_fixture(parent)
        before = {
            str(path.relative_to(parent)): path.read_bytes()
            for path in parent.rglob("*")
            if path.is_file()
        }
        protocol = os.environ.get("GIT_ALLOW_PROTOCOL")
        for key, value in {
            "GIT_DIR": str(parent / ".git"),
            "GIT_WORK_TREE": str(parent),
            "GIT_COMMON_DIR": str(parent / ".git"),
            "GIT_INDEX_FILE": str(parent / ".git/index"),
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.bare",
            "GIT_CONFIG_VALUE_0": "true",
        }.items():
            monkeypatch.setenv(key, value)
        controls = {
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
        # The installed wrapper is called by this test, outside the adapter child.
        for key in tuple(os.environ):
            if key in controls or key.startswith("GIT_CONFIG"):
                monkeypatch.delenv(key)
        assert os.environ.get("GIT_ALLOW_PROTOCOL") == protocol
        root, _, policy = small_repository(tmp_path)
        recipe = policy["shards"].pop(SHARD)
        policy["shards"][shard] = recipe
        # Exercise the same nonshipped branch as both production older-release tiers.
        policy["shipped"] = "schema-25.2"
        required_path = root / recipe["required"]
        required = json.loads(required_path.read_text())
        required["shards"] = [shard]
        required_path.write_text(json.dumps(required))
        (root / "tools/schema-verification/policy.json").write_text(json.dumps(policy))
        production = json.loads(
            (PROJECT_ROOT / f"tools/schema-verification/{shard}.stability.json").read_text()
        )
        stable = [f"{recipe['artifacts']}/{Path(name).name}" for name in production]
        (root / recipe["stability"]).write_text(json.dumps(stable))
        suite = root / policy["suite"]
        source = suite.read_text().replace(
            'out = tmp_path_factory.mktemp("actual-generation")',
            """out = tmp_path_factory.mktemp("actual-generation")
    counter = Path('.agent-ready/schema/executions')
    counter.parent.mkdir(parents=True, exist_ok=True)
    number = int(counter.read_text()) + 1 if counter.exists() else 1
    counter.write_text(str(number))""",
        )
        source = source.replace('"generated_at": "actual"', '"generated_at": f"pass-{number}"')
        if change == "semantic":
            source = source.replace('"total_nodes": 3', '"total_nodes": number + 2')
        source = source.replace(
            "return out",
            """history = Path('.agent-ready/schema/metadata-history.json')
    previous = json.loads(history.read_text()) if history.exists() else []
    previous.append(meta)
    history.write_text(json.dumps(previous))
    return out""",
        )
        suite.write_text(source)
        commit_fixture(root)
        declaration = {
            "name": shard,
            "inputs": [recipe["dump"], policy["runtime"]],
            "version-files": [policy["runtime"]],
            "required-manifest": recipe["required"],
            "result-manifest": recipe["result"],
            "stability-manifest": recipe["stability"],
            "paths": ["*"],
        }
        command = [sys.executable, "-B", "-m", "tools.schema_verification", "run", shard]
        status = verification.execute(root, command, "HEAD", declaration, reuse=False)
        assert (root / ".agent-ready/schema/executions").read_text() == "2"
        history = json.loads((root / ".agent-ready/schema/metadata-history.json").read_text())
        assert len(history) == 2 and history[0]["generated_at"] != history[1]["generated_at"]
        identity = verification.identity(root, command, "HEAD", declaration)
        native_path = root / verification.STORE / (verification.digest(identity) + ".json")
        native = json.loads(native_path.read_text())
        if change == "semantic":
            assert history[0]["stats"] != history[1]["stats"]
            assert status != 0 and native["exit_status"] != 0
            assert not verification.valid(root, identity, native)
        else:
            for metadata in history:
                metadata.pop("generated_at")
            assert history[0] == history[1]
            assert status == native["exit_status"] == 0
            assert verification.valid(root, identity, native)
        after = {
            str(path.relative_to(parent)): path.read_bytes()
            for path in parent.rglob("*")
            if path.is_file()
        }
        assert after == before
        assert os.environ.get("GIT_ALLOW_PROTOCOL") == protocol
