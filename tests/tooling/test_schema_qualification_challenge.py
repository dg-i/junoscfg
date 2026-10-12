"""Independent adversarial probes for generation evidence integrity."""

from __future__ import annotations

import json
import sys

import pytest
from agent_ready_checks import verification

from tests.tooling.test_schema_verification import (
    PRODUCTS,
    SHARD,
    adapter,
    commit_fixture,
    small_repository,
)


def generation_repository(tmp_path, fault=""):
    """Real tiny assertions plus installed wrapper; controlled public builder seam."""
    root, required, policy = small_repository(tmp_path)
    recipe = policy["shards"][SHARD]
    prefix = f".agent-ready/schema/{SHARD}/generation"
    recipe.update(
        {
            "generation-required": "tools/schema-verification/generation.required.json",
            "generation-result": f"{prefix}/result.json",
            "generation-outcomes": f"{prefix}/outcomes.json",
            "generation-artifacts": f"{prefix}/artifacts",
            "generation-stability": "tools/schema-verification/generation.stability.json",
        }
    )
    obligations = {
        "tests": ["public-build", "artifact-integrity"],
        "shards": [f"{SHARD}-generation"],
    }
    (root / recipe["generation-required"]).write_text(json.dumps(obligations))
    outputs = [f"{prefix}/artifacts/{name}" for name in PRODUCTS]
    outputs.append(f"{prefix}/artifacts/junos-schema-meta.normalized.json")
    (root / recipe["generation-stability"]).write_text(json.dumps(outputs))
    (root / "tools/schema-verification/policy.json").write_text(json.dumps(policy))
    source = f"""import gzip, json
from pathlib import Path
from tools import schema_verification as adapter
root = Path.cwd()
class Builder:
    def build(self, source, output):
        counter = root / '.agent-ready/schema/build-count'
        number = int(counter.read_text()) + 1 if counter.exists() else 1
        counter.write_text(str(number))
        assert not (root / {recipe["generation-result"]!r}).exists(), 'premature success'
        if {fault!r} == 'second-failure' and number == 2:
            raise ValueError('second public build failed')
        for name in {PRODUCTS!r}:
            (output / name).write_bytes(gzip.compress(b'generated artifact\\n', mtime=0))
        meta = {{'junos_version': '21.4R0', 'generated_at': str(number),
                'stats': {{'total_nodes': 3}}}}
        if {fault!r} == 'semantic' and number == 2:
            meta['stats']['total_nodes'] = 4
        compressed = gzip.compress(json.dumps(meta).encode(), mtime=0)
        (output / 'junos-schema-meta.json.gz').write_bytes(compressed)
        if {fault!r} == 'source':
            (root / 'pyproject.toml').write_text('mutated')
        if {fault!r} == 'input':
            source.write_text('mutated')
adapter.ArtifactBuilder = Builder
raise SystemExit(adapter.run_generation(root, {SHARD!r}))
"""
    (root / "generation_probe.py").write_text(source)
    commit_fixture(root)
    assert adapter().run_shard(root, SHARD) == 0
    declaration = {
        "name": f"{SHARD}-generation",
        "inputs": [recipe["dump"], policy["runtime"], recipe["result"]],
        "version-files": [policy["runtime"]],
        "required-manifest": recipe["generation-required"],
        "result-manifest": recipe["generation-result"],
        "stability-manifest": recipe["generation-stability"],
        "paths": ["*"],
    }
    return root, recipe, required, obligations, outputs, declaration


@pytest.mark.parametrize("fault", ["semantic", "second-failure", "source", "input"])
def test_failed_generation_cannot_publish_reusable_success(tmp_path, fault):
    root, recipe, _, _, _, declaration = generation_repository(tmp_path, fault)
    command = [sys.executable, "-B", "generation_probe.py"]
    assert verification.execute(root, command, "HEAD", declaration, reuse=False) != 0
    assert not (root / recipe["generation-result"]).exists()
    assert (root / ".agent-ready/schema/build-count").read_text() == (
        "2" if fault in {"semantic", "second-failure"} else "1"
    )


@pytest.mark.parametrize("missing", [True, False])
def test_unfinished_assertions_refuse_before_public_build(tmp_path, monkeypatch, missing):
    root, recipe, required, _, _, _ = generation_repository(tmp_path)
    result = root / recipe["result"]
    if missing:
        result.unlink()
    else:
        result.write_text(json.dumps({"tests": required["tests"][:-1], "shards": [SHARD]}))

    def forbidden_build(*args, **kwargs):
        pytest.fail("public build executed before assertion prerequisite")

    monkeypatch.setattr(adapter().ArtifactBuilder, "build", forbidden_build)
    with pytest.raises((ValueError, OSError)):
        adapter().run_generation(root, SHARD)
    assert not (root / ".agent-ready/schema/build-count").exists()
    assert not (root / recipe["generation-result"]).exists()


def test_wrapper_reuse_rejects_corrupted_generation_outputs(tmp_path):
    root, recipe, required, obligations, outputs, declaration = generation_repository(tmp_path)
    command = [sys.executable, "-B", "generation_probe.py"]
    assert verification.execute(root, command, "HEAD", declaration, reuse=False) == 0
    count = root / ".agent-ready/schema/build-count"
    assert count.read_text() == "2"
    assert json.loads((root / recipe["result"]).read_text()) == required
    assert json.loads((root / recipe["generation-result"]).read_text()) == obligations
    assert verification.execute(root, command, "HEAD", declaration, reuse=True) == 0
    assert count.read_text() == "2"
    (root / outputs[0]).write_bytes(b"corrupted output")
    assert verification.execute(root, command, "HEAD", declaration, reuse=True) == 0
    assert count.read_text() == "4"
