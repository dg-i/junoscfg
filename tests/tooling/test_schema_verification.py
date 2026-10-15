"""Schema evidence reports execution and preserves the immutable candidate."""

from __future__ import annotations

import gzip
import importlib
import json
import os
import shutil
import subprocess
from functools import cache
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import tomllib

from junoscfg.validate import ArtifactBuilder
from tests.support.paths import PROJECT_ROOT

PRODUCTS = (
    "junos-json-schema.json.gz",
    "junos-yaml-schema.json.gz",
    "junos-structure-tree.json.gz",
    "junos-set.lark.gz",
)
DUMP = "21.4R0-ex4600.xsd"
SHARD = "schema-21.4"
SUITE = "tests/corpus/test_schema_data.py"


def adapter():
    """A missing new behaviour is an executed failure, never a skip."""
    return importlib.import_module("tools.schema_verification")


def reports_for(nodeid, outcome="passed", reason=""):
    return [
        {"nodeid": nodeid, "when": "setup", "outcome": "passed", "reason": ""},
        {"nodeid": nodeid, "when": "call", "outcome": outcome, "reason": reason},
        {"nodeid": nodeid, "when": "teardown", "outcome": "passed", "reason": ""},
    ]


def write_products(directory, *, payload=b"generated artifact\n", generated_at="later"):
    directory.mkdir(parents=True, exist_ok=True)
    for name in PRODUCTS:
        (directory / name).write_bytes(gzip.compress(payload, mtime=0))
    meta = {"junos_version": "21.4R0", "generated_at": generated_at, "stats": {"total_nodes": 3}}
    (directory / "junos-schema-meta.json.gz").write_bytes(
        gzip.compress(json.dumps(meta, sort_keys=True).encode(), mtime=0)
    )


def git(root, *arguments):
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
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in controls and not key.startswith("GIT_CONFIG")
    }
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True, env=environment
    ).stdout


def commit_fixture(root):
    git(root, "add", ".")
    git(
        root,
        "-c",
        "maintenance.auto=false",
        "-c",
        "user.name=Schema Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-m",
        "fixture",
    )


@cache
def prepared_runtime_input():
    """Share immutable preparation bytes, never successful execution evidence.

    Snapshot the installed runtime once as test input. Every production preflight
    still observes it afresh and rejects a changed runtime. Returning bytes keeps
    each caller's deliberately corrupted input independent of other tests.
    """
    with TemporaryDirectory(prefix="schema-runtime-input-") as directory:
        root = Path(directory).resolve()
        manifests = root / "tools/schema-verification"
        manifests.mkdir(parents=True)
        policy = {"runtime": "runtime.json", "shards": {SHARD: {}}}
        (manifests / "policy.json").write_text(json.dumps(policy))
        adapter().prepare_runtime(root)
        return (root / "runtime.json").read_bytes()


def small_repository(tmp_path, *, fault=""):
    """Exercise genuine small pytest sessions with immutable synthetic inputs."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    for package in ("tools", "tests", "tests/corpus", "tests/support"):
        (root / package).mkdir(parents=True, exist_ok=True)
        (root / package / "__init__.py").write_text("")
    shutil.copyfile(
        PROJECT_ROOT / "tools/schema_verification.py", root / "tools/schema_verification.py"
    )
    shutil.copyfile(
        PROJECT_ROOT / "tools/schema_dependencies.py", root / "tools/schema_dependencies.py"
    )
    (root / "uv.lock").write_text(
        'version = 1\n[[package]]\nname = "junoscfg"\n'
        'version = "0.28.3"\nsource = { editable = "." }\n'
        '[[package]]\nname = "lxml"\nversion = "1"\nsource = {registry = "https://example.invalid"}\n'
    )
    from tools.schema_dependencies import write_dependencies

    write_dependencies(root)
    for name in ("paths.py", "schema_data.py"):
        shutil.copyfile(PROJECT_ROOT / "tests/support" / name, root / "tests/support" / name)
    dump = root / "private_test_data/schemas" / DUMP
    dump.parent.mkdir(parents=True)
    dump.write_text('<schema xmlns:junos="http://xml.juniper.net/junos/21.4R0/junos"/>')
    nodeids = [
        f"{SUITE}::test_generated[{DUMP}]",
        f"{SUITE}::test_pass[{DUMP}]",
        f"{SUITE}::TestIdentifierCounts::test_the_counts_are_the_proposals[{DUMP}]",
    ]
    required = {"tests": nodeids, "shards": [SHARD]}
    manifests = root / "tools/schema-verification"
    manifests.mkdir(exist_ok=True)
    (manifests / "schema-21.4.required.json").write_text(json.dumps(required))
    stable = [f".agent-ready/schema/{SHARD}/artifacts/{name}" for name in PRODUCTS]
    stable.append(f".agent-ready/schema/{SHARD}/artifacts/junos-schema-meta.normalized.json")
    (manifests / "schema-21.4.stability.json").write_text(json.dumps(stable))
    policy = {
        "runtime": ".agent-ready/schema/runtime.json",
        "suite": SUITE,
        "shipped": SHARD,
        "shards": {
            SHARD: {
                "dump": f"private_test_data/schemas/{DUMP}",
                "release": "21.4R0",
                "required": "tools/schema-verification/schema-21.4.required.json",
                "stability": "tools/schema-verification/schema-21.4.stability.json",
                "result": f".agent-ready/schema/{SHARD}/result.json",
                "outcomes": f".agent-ready/schema/{SHARD}/outcomes.json",
                "artifacts": f".agent-ready/schema/{SHARD}/artifacts",
                "allowed-skips": {nodeids[2]: "no pinned count for 21.4R0"},
            }
        },
    }
    (manifests / "policy.json").write_text(json.dumps(policy))
    (root / ".gitignore").write_text(
        ".agent-ready/\nprivate_test_data/\n__pycache__/\n.pytest_cache/\n"
    )
    (root / "pyproject.toml").write_text('[tool.pytest.ini_options]\naddopts = ""\n')
    (root / "tests/conftest.py").write_text(
        'def pytest_addoption(parser):\n    parser.addoption("--schema", action="store_true")\n'
    )
    extra = {
        "failed": "assert False, 'actual failed call'",
        "input": f"Path('private_test_data/schemas/{DUMP}').write_text('mutated')",
        "tracked": "Path('pyproject.toml').write_text('mutated')",
    }.get(fault, "assert True")
    source = f"""import gzip, json
from pathlib import Path
import pytest
@pytest.fixture(params=[{DUMP!r}])
def schema_dump(request):
    return request.param
@pytest.fixture(scope="module")
def real_artifacts(tmp_path_factory):
    out = tmp_path_factory.mktemp("actual-generation")
    for name in {PRODUCTS!r}:
        (out / name).write_bytes(gzip.compress(b"generated artifact\\n", mtime=0))
    meta = {{"junos_version": "21.4R0", "generated_at": "actual", "stats": {{"total_nodes": 3}}}}
    metadata = gzip.compress(json.dumps(meta, sort_keys=True).encode(), mtime=0)
    (out / "junos-schema-meta.json.gz").write_bytes(metadata)
    return out
@pytest.fixture
def finalization():
    yield
    {"assert False, 'actual failed teardown'" if fault == "teardown" else "pass"}
def test_generated(schema_dump, real_artifacts, request, tmp_path):
    from tools.schema_verification import check_content
    assert (real_artifacts / "junos-set.lark.gz").is_file()
    schema = tmp_path / "schema.json"
    schema.write_text('{{"type":"string"}}')
    grammar = tmp_path / "grammar.lark"
    grammar.write_text('start: "a"')
    check_content(request.config, schema, "json-schema-draft202012")
    check_content(request.config, grammar, "lark-grammar")
def test_pass(schema_dump, finalization):
    {extra}
class TestIdentifierCounts:
    def test_the_counts_are_the_proposals(self, schema_dump):
        pytest.skip("no pinned count for 21.4R0")
"""
    shutil.copyfile(
        PROJECT_ROOT / "tools/schema_content_worker.py", root / "tools/schema_content_worker.py"
    )
    (root / SUITE).write_text(source)
    write_products(root / "src/junoscfg/validate/data", generated_at="committed")
    commit_fixture(root)
    runtime = root / policy["runtime"]
    runtime.parent.mkdir(parents=True)
    runtime.write_bytes(prepared_runtime_input())
    return root, required, policy


class TestExecutedCompletion:
    def test_passed_reports_complete_exact_ids(self):
        required = {"tests": ["test_a", "test_b"], "shards": [SHARD]}
        actual, outcomes = adapter().completion(
            required,
            reports_for("test_b") + reports_for("test_a"),
            0,
            {},
            collected=["test_b", "test_a"],
        )
        assert set(actual["tests"]) == {"test_a", "test_b"}
        assert actual["shards"] == [SHARD]
        assert all(row["outcome"] == "passed" for row in outcomes["tests"].values())

    def test_allowed_skips_keep_identity_reason(self):
        module = adapter()
        required = {"tests": ["ordinary", "count"], "shards": [SHARD]}
        reason = "no pinned count for 21.4R0"
        observed = reports_for("ordinary") + reports_for("count", "skipped", reason)
        actual, outcomes = module.completion(
            required, observed, 0, {"count": reason}, collected=required["tests"]
        )
        assert set(actual["tests"]) == {"ordinary", "count"}
        assert outcomes["tests"]["count"] == {"outcome": "skipped", "reason": reason}
        for wrong in ("different release", "", reason + " extra"):
            with pytest.raises(ValueError):
                module.completion(
                    required, observed, 0, {"count": wrong}, collected=required["tests"]
                )

    @pytest.mark.parametrize(
        "fault",
        [
            "collection-only",
            "missing-call",
            "duplicate-report",
            "unexpected-id",
            "failed-call",
            "failed-setup",
            "failed-teardown",
            "wrong-collection",
            "duplicate-required",
            "nonzero-exit",
            "all-skipped",
            "unexpected-skip",
        ],
    )
    def test_incomplete_failed_or_wrong_reports_refuse(self, fault):
        module = adapter()
        required = {"tests": ["test_a"], "shards": [SHARD]}
        observed = reports_for("test_a")
        collected, status, allowed = ["test_a"], 0, {}
        if fault == "collection-only":
            observed = []
        elif fault == "missing-call":
            observed.pop(1)
        elif fault == "duplicate-report":
            observed.append(observed[1].copy())
        elif fault == "unexpected-id":
            observed += reports_for("test_extra")
        elif fault.startswith("failed-"):
            observed[{"failed-setup": 0, "failed-call": 1, "failed-teardown": 2}[fault]][
                "outcome"
            ] = "failed"
        elif fault == "wrong-collection":
            collected.append("test_extra")
        elif fault == "duplicate-required":
            required["tests"].append("test_a")
        elif fault == "nonzero-exit":
            status = 1
        else:
            observed = reports_for("test_a", "skipped", "permitted")
            if fault == "all-skipped":
                allowed = {"test_a": "permitted"}
        with pytest.raises(ValueError):
            module.completion(required, observed, status, allowed, collected=collected)


class TestPhysicalInputs:
    @pytest.mark.parametrize("fault", ["missing", "empty", "unknown", "symlink", "parent-symlink"])
    def test_missing_empty_symlink_or_unknown_dump_refuses(self, tmp_path, fault):
        module = adapter()
        directory = tmp_path / "schemas"
        directory.mkdir()
        path = directory / DUMP
        valid = '<schema xmlns:junos="http://xml.juniper.net/junos/21.4R0/junos"/>'
        if fault != "missing":
            path.write_text(
                "" if fault == "empty" else "<schema/>" if fault == "unknown" else valid
            )
        if fault == "symlink":
            real = tmp_path / "physical.xsd"
            path.rename(real)
            path.symlink_to(real)
        elif fault == "parent-symlink":
            real_dir = tmp_path / "physical"
            directory.rename(real_dir)
            directory.symlink_to(real_dir, target_is_directory=True)
        with pytest.raises(ValueError):
            module.validate_input(path, "21.4R0")

    @pytest.mark.parametrize("fault", ["missing", "corrupt", "unknown", "mismatch"])
    def test_unknown_or_changed_runtime_refuses(self, tmp_path, fault):
        module = adapter()
        path = tmp_path / "runtime.json"
        values = json.loads(prepared_runtime_input())
        assert values and all(
            isinstance(v, str) and v not in ("", "unknown") for v in values.values()
        )
        if fault == "corrupt":
            path.write_text("{")
        elif fault != "missing":
            values[next(iter(values))] = "unknown" if fault == "unknown" else "changed version"
            path.write_text(json.dumps(values))
        with pytest.raises(ValueError):
            module.verify_versions(path)


class TestCandidateIntegrity:
    def test_prepared_inputs_are_isolated_without_execution_evidence(self, tmp_path):
        roots = [tmp_path / name for name in ("first", "second")]
        for directory in roots:
            directory.mkdir()
        first, _, policy = small_repository(roots[0])
        runtime = first / policy["runtime"]
        expected = runtime.read_bytes()
        runtime.write_text("corrupted by one test")
        second, _, _ = small_repository(roots[1])
        assert (second / policy["runtime"]).read_bytes() == expected
        adapter().verify_versions(second / policy["runtime"])
        for root in (first, second):
            assert sorted(
                str(path.relative_to(root / ".agent-ready"))
                for path in (root / ".agent-ready").rglob("*")
                if path.is_file()
            ) == ["schema/runtime.json"]
            assert git(root, "status", "--porcelain") == ""

    def test_fixture_commit_starts_no_background_maintenance(self, tmp_path, monkeypatch):
        """A detached maintenance run races the byte snapshots taken of a fixture repository."""
        root = tmp_path / "repo"
        root.mkdir()
        git(root, "init", "-q")
        (root / "tracked").write_text("candidate")
        trace = tmp_path / "trace"
        monkeypatch.setenv("GIT_TRACE", str(trace))
        commit_fixture(root)
        assert "maintenance" not in trace.read_text()

    def test_inherited_hook_context_preserves_parent_repository(self, tmp_path, monkeypatch):
        parent = tmp_path / "parent"
        parent.mkdir()
        git(parent, "init", "-q")
        (parent / "tracked").write_text("parent candidate")
        commit_fixture(parent)
        before = {
            str(path.relative_to(parent)): path.read_bytes()
            for path in parent.rglob("*")
            if path.is_file()
        }
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
        nested = tmp_path / "nested"
        nested.mkdir()
        root, _, _ = small_repository(nested)
        assert adapter().run_shard(root, SHARD) == 0
        after = {
            str(path.relative_to(parent)): path.read_bytes()
            for path in parent.rglob("*")
            if path.is_file()
        }
        assert after == before

    def test_real_runner_exports_artifacts_without_mutation(self, tmp_path):
        root, required, policy = small_repository(tmp_path)
        before = git(root, "status", "--porcelain", "--untracked-files=no")
        assert adapter().run_shard(root, SHARD) == 0
        recipe = policy["shards"][SHARD]
        assert json.loads((root / recipe["result"]).read_text()) == required
        outcomes = json.loads((root / recipe["outcomes"]).read_text())
        assert outcomes["tests"][required["tests"][2]] == {
            "outcome": "skipped",
            "reason": "no pinned count for 21.4R0",
        }
        assert set(outcomes["content_checks"]) == {"json-schema-draft202012", "lark-grammar"}
        assert {row["status"] for row in outcomes["content_checks"].values()} == {"executed"}
        assert adapter().run_shard(root, SHARD) == 0
        repeated = json.loads((root / recipe["outcomes"]).read_text())
        assert {row["status"] for row in repeated["content_checks"].values()} == {"reused"}
        for name in PRODUCTS:
            assert (root / recipe["artifacts"] / name).read_bytes() == (
                root / "src/junoscfg/validate/data" / name
            ).read_bytes()
        assert git(root, "status", "--porcelain", "--untracked-files=no") == before == ""

    @pytest.mark.parametrize("fault", ["failed", "input", "tracked", "teardown", "dirty"])
    def test_mutated_inputs_or_failed_execution_publish_no_success(self, tmp_path, fault):
        root, _, policy = small_repository(tmp_path, fault=fault)
        if fault == "dirty":
            (root / "pyproject.toml").write_text("dirty")
        result = root / policy["shards"][SHARD]["result"]
        result.parent.mkdir(parents=True)
        result.write_text('{"tests":["stale"],"shards":["stale"]}')
        try:
            status = adapter().run_shard(root, SHARD)
        except ValueError:
            status = 1
        assert status != 0
        assert not result.exists()


class TestGenerationIntegrity:
    def test_sentinel_executes_fresh_generation(self, tmp_path, monkeypatch):
        root, _, _ = small_repository(tmp_path)
        outputs = []

        def generate(self, source, output):
            assert Path(source) == root / "private_test_data/schemas" / DUMP
            outputs.append(Path(output))
            write_products(Path(output))
            return {}

        monkeypatch.setattr(ArtifactBuilder, "build", generate)
        assert adapter().run_sentinel(root) == 0
        assert adapter().run_sentinel(root) == 0
        assert len(outputs) == 2 and outputs[0] != outputs[1]
        assert all(".agent-ready/schema" not in str(path) for path in outputs)
        assert git(root, "status", "--porcelain", "--untracked-files=no") == ""

    @pytest.mark.parametrize(
        "fault",
        [
            "protected-bytes",
            "metadata-field",
            "missing-product",
            "generator-failure",
        ],
    )
    def test_wrong_or_unstable_artifacts_refuse(self, tmp_path, monkeypatch, fault):
        root, _, _ = small_repository(tmp_path)

        def generate(self, source, output):
            if fault == "generator-failure":
                raise ValueError("actual generation failure")
            out = Path(output)
            write_products(
                out, payload=b"different" if fault == "protected-bytes" else b"generated artifact\n"
            )
            if fault == "metadata-field":
                (out / "junos-schema-meta.json.gz").write_bytes(
                    gzip.compress(b'{"junos_version":"other","generated_at":"later"}', mtime=0)
                )
            elif fault == "missing-product":
                (out / PRODUCTS[0]).unlink()
            return {}

        monkeypatch.setattr(ArtifactBuilder, "build", generate)
        try:
            status = adapter().run_sentinel(root)
        except (ValueError, OSError):
            status = 1
        assert status != 0


class TestEvidenceConfiguration:
    def test_shipped_assertion_and_generation_tiers_are_declared(self):
        config = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())["tool"]["template"]
        tiers = config["batch"]["expensive-tiers"]
        assert [tier["name"] for tier in tiers] == [
            "schema-dependency-guard",
            "schema-25.2",
            "schema-25.2-generation",
        ]
        guard, assertion, generation = tiers
        assert "uv.lock" in guard["paths"]
        assert "stability-manifest" not in guard
        assert "stability-manifest" not in assertion
        assert not any(tier.get("sentinel-command") for tier in tiers)
        assert assertion["paths"] == generation["paths"]
        assert "tools/schema_verification.py" not in assertion["paths"]
        assert "tools/schema_content_worker.py" in assertion["paths"]
        assert assertion["evidence-files"] == [".agent-ready/schema/schema-25.2/outcomes.json"]
        assert assertion["evidence-files"][0] in generation["inputs"]
        assert "pyproject.toml" not in assertion["paths"]
        assert "uv.lock" not in assertion["paths"]
        assert "tools/schema-verification/dependencies.json" in assertion["paths"]
        assert "tests/conftest.py" in assertion["paths"]
        assert "src/junoscfg/validate/__init__.py" in assertion["paths"]
        assert "src/junoscfg/display/constants.py" in assertion["paths"]
        assert "src/junoscfg/display/__init__.py" in assertion["paths"]
        policy = json.loads((PROJECT_ROOT / "tools/schema-verification/policy.json").read_text())
        assert set(policy["shards"]) == {"schema-21.4", "schema-23.2", "schema-25.2"}
        for shard, recipe in policy["shards"].items():
            required = json.loads((PROJECT_ROOT / recipe["required"]).read_text())
            assert len(required["tests"]) == len(set(required["tests"])) == 12
            assert required["shards"] == [shard]
            generated = json.loads((PROJECT_ROOT / recipe["generation-required"]).read_text())
            assert generated == {
                "tests": ["public-build", "artifact-integrity"],
                "shards": [f"{shard}-generation"],
            }
        stable = json.loads((PROJECT_ROOT / generation["stability-manifest"]).read_text())
        assert len(stable) == 5 and all(name.endswith(PRODUCTS) for name in stable[:4])
        assert stable[4].endswith("junos-schema-meta.normalized.json")
        assert assertion["result-manifest"] in generation["inputs"]
        assert all(tier["version-files"] for tier in (assertion, generation))

    def test_safe_seeds_preserve_policy_and_link_guides(self):
        config = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())["tool"]["template"]
        assessment = PROJECT_ROOT / ".agent-ready/activation.json"
        assert config["verification"]["policy"] == "strategy-a/1"
        assert config["verification"]["enabled"] is assessment.exists()
        if assessment.exists():
            assert json.loads(assessment.read_text())["policy"] == "strategy-a/1"
        assert config["stage"]["surfaces"] == ["consumer", "cli"]
        assert config["always-loaded-budget"] == 4600
        for pattern, count in (
            (".agents/skills/agent-ready-*/SKILL.md", 300),
            (".agents/skills/agent-ready-*/*.md", 100),
            (".agents/skills/agent-ready-*/**/*.md", 100),
        ):
            assert config["caps-report-only"][pattern] == count
        ignore = (PROJECT_ROOT / ".gitignore").read_text().splitlines()
        assert ".agent-ready/verification/" in ignore and ".agent-ready/schema/" in ignore
        nav = (PROJECT_ROOT / "mkdocs.yml").read_text()
        assert "how-to/lifecycle-ledger.md" in nav and "how-to/verification-evidence.md" in nav

    def test_rollback_retains_evidence_and_uncached_declarations(self, tmp_path, monkeypatch):
        from agent_ready_checks import verification

        config = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())["tool"]["template"]
        tiers = config["batch"]["expensive-tiers"]
        assert len(tiers) == 3
        store = tmp_path / ".agent-ready/verification"
        store.mkdir(parents=True)
        retained = store / "historical.json"
        retained.write_text('{"historical":true}')
        executions = []
        monkeypatch.setattr(verification, "tiers", lambda root, base, selection: tiers)

        def execute(root, command, base, declaration, *, reuse=True):
            executions.append((command, reuse))
            return 0

        monkeypatch.setattr(verification, "execute", execute)
        assert verification.run_tiers(tmp_path, None, enabled=False) == 0
        assert len(executions) == 3 and all(reuse is False for _, reuse in executions)
        assert retained.read_text() == '{"historical":true}'
