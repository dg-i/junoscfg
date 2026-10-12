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
