"""Fast acceptance probes for separated schema assertion and generation work."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from junoscfg.validate import ArtifactBuilder
from tests.tooling.test_schema_verification import (
    PRODUCTS,
    SHARD,
    adapter,
    commit_fixture,
    small_repository,
    write_products,
)


def generation_repository(tmp_path):
    """A tiny genuine assertion run followed by a bound generation recipe."""
    root, required, policy = small_repository(tmp_path)
    recipe = policy["shards"][SHARD]
    for key, suffix in (("generation-required", "required"), ("generation-stability", "stability")):
        recipe[key] = f"tools/schema-verification/{SHARD}-generation.{suffix}.json"
    recipe["generation-result"] = f".agent-ready/schema/{SHARD}/generation-result.json"
    recipe["generation-outcomes"] = f".agent-ready/schema/{SHARD}/generation-outcomes.json"
    recipe["generation-artifacts"] = f".agent-ready/schema/{SHARD}/generation-artifacts"
    generation = {
        "tests": ["public-build", "artifact-integrity"],
        "shards": [f"{SHARD}-generation"],
    }
    (root / recipe["generation-required"]).write_text(json.dumps(generation))
    (root / recipe["generation-stability"]).write_text(
        json.dumps(
            [
                f"{recipe['generation-artifacts']}/{name}"
                for name in (*PRODUCTS, "junos-schema-meta.normalized.json")
            ]
        )
    )
    (root / "tools/schema-verification/policy.json").write_text(json.dumps(policy))
    commit_fixture(root)
    assert adapter().run_shard(root, SHARD) == 0
    return root, recipe, required, generation


class TestTimingEvidence:
    def test_executed_phase_durations_are_recorded(self, tmp_path):
        root, required, policy = small_repository(tmp_path)
        assert adapter().run_shard(root, SHARD) == 0
        outcomes = json.loads((root / policy["shards"][SHARD]["outcomes"]).read_text())
        assert set(outcomes["durations"]) == set(required["tests"])
        for phases in outcomes["durations"].values():
            assert set(phases) == {"setup", "call", "teardown"}
            assert all(isinstance(value, float) and value >= 0 for value in phases.values())


class TestGenerationQualification:
    def test_fresh_build_exports_integrity_without_pytest(self, tmp_path, monkeypatch):
        root, recipe, required, generation = generation_repository(tmp_path)
        calls = []

        def build(self, source, output):
            calls.append(Path(output))
            write_products(Path(output))

        monkeypatch.setattr(ArtifactBuilder, "build", build)
        assert adapter().run_generation(root, SHARD) == 0
        assert adapter().run_generation(root, SHARD) == 0
        assert len(calls) == 2 and calls[0] != calls[1]
        assert json.loads((root / recipe["result"]).read_text()) == required
        assert json.loads((root / recipe["generation-result"]).read_text()) == generation
        outcomes = json.loads((root / recipe["generation-outcomes"]).read_text())
        assert outcomes["durations"]["public-build"] >= 0
        assert len(list((root / recipe["generation-artifacts"]).iterdir())) == 6

    @pytest.mark.parametrize("fault", ["missing-assertions", "builder", "mutation", "artifact"])
    def test_failure_clears_completion(self, tmp_path, monkeypatch, fault):
        root, recipe, _, generation = generation_repository(tmp_path)
        result = root / recipe["generation-result"]
        result.write_text(json.dumps(generation))
        calls = []
        if fault == "missing-assertions":
            (root / recipe["result"]).unlink()

        def build(self, source, output):
            calls.append(Path(output))
            if fault == "builder":
                raise RuntimeError("generation failed")
            write_products(
                Path(output),
                payload=b"different" if fault == "artifact" else b"generated artifact\n",
            )
            if fault == "mutation":
                source.write_text("changed")

        monkeypatch.setattr(ArtifactBuilder, "build", build)
        with pytest.raises((OSError, ValueError, RuntimeError)):
            adapter().run_generation(root, SHARD)
        assert not result.exists()
        if fault == "missing-assertions":
            assert not calls


class TestExplicitQualification:
    def test_parked_policy_refuses_before_execution(self, tmp_path, monkeypatch):
        from agent_ready_checks import lane, readiness, verification

        monkeypatch.setattr(readiness, "config", lambda root: {"enabled": True})
        monkeypatch.setattr(lane, "snapshot_problem", lambda root: None)
        monkeypatch.setattr(lane, "selected_change_for_base", lambda root, base: None)
        monkeypatch.setattr(readiness, "problems", lambda root, folder, base: ["branch is parked"])

        def forbidden(*args, **kwargs):
            pytest.fail("execution attempted before admission")

        monkeypatch.setattr(verification, "execute", forbidden)
        with pytest.raises(ValueError, match="parked"):
            adapter().qualify(tmp_path, SHARD)


def test_bundled_conversion_preflight(monkeypatch):
    """Exercise the identical real-schema conversion assertions without rebuilding."""
    from tests.corpus.test_schema_data import TestConversionAgainstRealArtifacts
    from tests.support.paths import ARTIFACT_DIR

    checks = TestConversionAgainstRealArtifacts()
    checks.test_roundtrip_against_this_release(ARTIFACT_DIR, monkeypatch)
    checks.test_json_and_set_agree_on_real_artifacts(ARTIFACT_DIR, monkeypatch)


@pytest.mark.parametrize("manifest", ["generation-required", "generation-stability"])
@pytest.mark.parametrize("prefix", ["", "./"])
def test_generation_manifest_is_not_an_exempt_record(tmp_path, monkeypatch, manifest, prefix):
    root, recipe, _, _ = generation_repository(tmp_path)
    policy_path = root / "tools/schema-verification/policy.json"
    policy = json.loads(policy_path.read_text())
    path = root / "openspec/changes/probe/review.md"
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    policy["shards"][SHARD][manifest] = prefix + str(path.relative_to(root))
    policy_path.write_text(json.dumps(policy))
    commit_fixture(root)
    path.write_text((root / recipe[manifest]).read_text())

    def forbidden(*args, **kwargs):
        pytest.fail("public build executed with dirty explicit manifest")

    monkeypatch.setattr(ArtifactBuilder, "build", forbidden)
    with pytest.raises(ValueError, match="committed clean candidate"):
        adapter().run_generation(root, SHARD)


def test_explicit_qualification_isolates_and_restores_hook_environment(tmp_path, monkeypatch):
    import os

    from agent_ready_checks import readiness, verification

    from tests.tooling.test_schema_verification import git

    parent = tmp_path / "parent"
    parent.mkdir()
    git(parent, "init", "-q")
    (parent / "parent-only").write_text("parent candidate")
    commit_fixture(parent)
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    root, _, _, _ = generation_repository(candidate)
    for key, value in {
        "GIT_DIR": str(parent / ".git"),
        "GIT_WORK_TREE": str(parent),
        "GIT_INDEX_FILE": str(parent / ".git/index"),
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.bare",
        "GIT_CONFIG_VALUE_0": "true",
        "GIT_ALLOW_PROTOCOL": "file",
    }.items():
        monkeypatch.setenv(key, value)
    before = dict(os.environ)
    calls = []

    def observe(root, command, base, declaration, *, reuse):
        assert Path(readiness.git(root, "rev-parse", "--show-toplevel")) == root
        assert os.environ["GIT_ALLOW_PROTOCOL"] == "file"
        calls.append(command[-2])
        return 0

    monkeypatch.setattr(verification, "execute", observe)
    assert adapter().qualify(root, SHARD) == 0
    assert calls == ["run", "generation"]
    assert dict(os.environ) == before
