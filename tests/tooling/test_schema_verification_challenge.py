"""Independent counterexamples for the frozen schema evidence requirements."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from junoscfg.validate import ArtifactBuilder
from tests.tooling.test_schema_verification import (
    DUMP,
    SHARD,
    adapter,
    commit_fixture,
    git,
    small_repository,
)


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


class TestQualifiedLifecycleRecordBoundary:
    """Only the provider's five fixed non-executable records may change."""

    @pytest.mark.parametrize(
        "record", ["review.md", "metrics.md", "metrics.json", "events.jsonl", "lifecycle.json"]
    )
    def test_fixed_tracked_record_changes_do_not_block_execution(self, tmp_path, record):
        root, _, policy = small_repository(tmp_path)
        path = root / "openspec/changes/fixture" / record
        path.parent.mkdir(parents=True)
        path.write_text("{}\n" if record.endswith(".json") else "")
        commit_fixture(root)
        path.write_text("updated non-executable evidence\n")
        assert adapter().run_shard(root, SHARD) == 0
        result = root / policy["shards"][SHARD]["result"]
        assert result.is_file()
        assert "openspec/changes/fixture/" + record in git(root, "status", "--porcelain")

    def test_record_update_during_execution_does_not_mutate_the_candidate(self, tmp_path):
        root, _, policy = small_repository(tmp_path)
        path = root / "openspec/changes/fixture/events.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text("")
        suite = root / policy["suite"]
        suite.write_text(
            suite.read_text().replace(
                "assert True",
                "Path('openspec/changes/fixture/events.jsonl').write_text('observed event\\n')",
            )
        )
        commit_fixture(root)
        assert adapter().run_shard(root, SHARD) == 0
        assert path.read_text() == "observed event\n"

    @pytest.mark.parametrize(
        "path",
        [
            "tools/schema_verification.py",
            "openspec/changes/fixture/tasks.md",
            "private_test_data/schemas/21.4R0-ex4600.xsd",
            "openspec/changes/fixture/roles/events.jsonl",
            "openspec/changes/archive/fixture/events.jsonl",
        ],
    )
    def test_nonrecord_or_explicit_input_mutation_remains_a_failure(self, tmp_path, path):
        root, _, policy = small_repository(tmp_path)
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("initial candidate input")
        suite = root / policy["suite"]
        suite.write_text(
            suite.read_text().replace("assert True", f"Path({path!r}).write_text('mutated')")
        )
        commit_fixture(root)
        try:
            status = adapter().run_shard(root, SHARD)
        except (ValueError, OSError):
            status = 1
        assert status != 0
        assert target.read_text() == "mutated"
        assert not (root / policy["shards"][SHARD]["result"]).exists()

    def test_native_tracked_events_allow_the_next_real_wrapper_execution(
        self, tmp_path, monkeypatch
    ):
        from agent_ready_checks import verification

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
        protocol = os.environ.get("GIT_ALLOW_PROTOCOL")
        for key in tuple(os.environ):
            if key in controls or key.startswith("GIT_CONFIG"):
                monkeypatch.delenv(key)
        assert os.environ.get("GIT_ALLOW_PROTOCOL") == protocol
        root, _, policy = small_repository(tmp_path)
        base = git(root, "rev-parse", "HEAD").strip()
        folder = root / "openspec/changes/fixture"
        folder.mkdir(parents=True)
        ledger = folder / "events.jsonl"
        ledger.write_text("")
        (folder / "tasks.md").write_text("- [x] Actual fixture work\n")
        (folder / ".openspec.yaml").write_text("schema: agent-ready\n")
        suite = root / policy["suite"]
        suite.write_text(
            suite.read_text().replace(
                'out = tmp_path_factory.mktemp("actual-generation")',
                """out = tmp_path_factory.mktemp("actual-generation")
    counter = Path('.agent-ready/schema/executions')
    counter.parent.mkdir(parents=True, exist_ok=True)
    number = int(counter.read_text()) + 1 if counter.exists() else 1
    counter.write_text(str(number))""",
            )
        )
        commit_fixture(root)
        recipe = policy["shards"][SHARD]
        declaration = {
            "name": SHARD,
            "inputs": [recipe["dump"], policy["runtime"]],
            "version-files": [policy["runtime"]],
            "required-manifest": recipe["required"],
            "result-manifest": recipe["result"],
            "stability-manifest": recipe["stability"],
        }
        command = [sys.executable, "-B", "-m", "tools.schema_verification", "run", SHARD]
        before = verification.identity(root, command, base, declaration)
        assert verification.execute(root, command, base, declaration, reuse=False) == 0
        events = [json.loads(line) for line in ledger.read_text().splitlines()]
        assert [event["kind"] for event in events] == ["verification", "progress"]
        assert events[0]["payload"]["exit_status"] == 0
        assert (root / ".agent-ready/schema/executions").read_text() == "2"
        assert verification.identity(root, command, base, declaration) == before
        assert verification.execute(root, command, base, declaration, reuse=False) == 0
        assert (root / ".agent-ready/schema/executions").read_text() == "4"
        assert len(ledger.read_text().splitlines()) == 4
        assert os.environ.get("GIT_ALLOW_PROTOCOL") == protocol

    @pytest.mark.parametrize("prefix", ["", "./"])
    @pytest.mark.parametrize("read_input", ["runtime", "required"])
    def test_explicit_read_inputs_override_fixed_record_spelling(
        self, tmp_path, monkeypatch, read_input, prefix
    ):
        root, _, policy = small_repository(tmp_path)
        recipe = policy["shards"][SHARD]
        original = root / (policy["runtime"] if read_input == "runtime" else recipe["required"])
        value = json.loads(original.read_text())
        name = prefix + "openspec/changes/fixture/metrics.json"
        target = root / name
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps(value, indent=2))
        if read_input == "runtime":
            policy["runtime"] = name
        else:
            recipe["required"] = name
        (root / "tools/schema-verification/policy.json").write_text(json.dumps(policy))
        commit_fixture(root)
        target.write_text(json.dumps(value, indent=4))
        assert json.loads(target.read_text()) == value
        original_run = subprocess.run
        launched = []

        def observe(command, *args, **kwargs):
            if any("pytest" in str(part) for part in command):
                launched.append(command)
                raise AssertionError("changed explicit input preceded candidate refusal")
            return original_run(command, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", observe)
        try:
            status = adapter().run_shard(root, SHARD)
        except (ValueError, OSError):
            status = 1
        assert status != 0
        assert launched == []
        assert not (root / recipe["result"]).exists()

    def test_source_renamed_to_a_fixed_record_is_not_evidence_only(self, tmp_path, monkeypatch):
        root, _, policy = small_repository(tmp_path)
        source = root / "candidate.py"
        source.write_text("# tracked candidate source\n")
        destination = root / "openspec/changes/fixture/review.md"
        destination.parent.mkdir(parents=True)
        commit_fixture(root)
        git(root, "mv", "candidate.py", "openspec/changes/fixture/review.md")
        original_run = subprocess.run
        launched = []

        def observe(command, *args, **kwargs):
            if any("pytest" in str(part) for part in command):
                launched.append(command)
                raise AssertionError("source rename preceded candidate refusal")
            return original_run(command, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", observe)
        try:
            status = adapter().run_shard(root, SHARD)
        except (ValueError, OSError):
            status = 1
        assert status != 0
        assert launched == []
        assert not source.exists() and destination.read_text() == "# tracked candidate source\n"
        assert not (root / policy["shards"][SHARD]["result"]).exists()
