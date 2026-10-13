"""Qualification is omitted only when relevance and prior proof are established."""

from __future__ import annotations

import importlib
import json

import pytest
import tomllib

from tests.support.paths import PROJECT_ROOT
from tests.tooling.test_schema_dependency_trigger_challenge import (
    isolated_git_environment as isolated_git_environment,
)
from tests.tooling.test_schema_verification import commit_fixture, git

OLD = "def consume(value):\n    return value\n"
NEW = "def consume(value):\n    return str(value)\n"


def selector():
    return importlib.import_module("tools.schema_selection")


def producer_patterns():
    config = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    tiers = config["tool"]["template"]["batch"]["expensive-tiers"]
    return next(tier["paths"] for tier in tiers if tier["name"] == "schema-25.2")


@pytest.mark.parametrize(
    "path",
    [
        "src/junoscfg/validate/artifact_builder.py",
        "src/junoscfg/validate/schema_generator.py",
        "src/junoscfg/validate/grammar_generator.py",
        "src/junoscfg/validate/xsd_parser.py",
        "src/junoscfg/validate/__init__.py",
        "src/junoscfg/display/constants.py",
        "src/junoscfg/validate/data/junos-set.lark.gz",
        "tests/conftest.py",
        "tests/support/schema_data.py",
        "tests/support/regen.py",
        "tests/corpus/test_schema_data.py",
        "tools/schema_content_worker.py",
        "tools/schema_verification.py",
        "tools/schema_dependencies.py",
        "private_test_data/schemas/25.2R2-S1.5_qfx5120.xsd",
        "new/unclassified.cfg",
        "../outside.py",
        "/absolute.py",
        "",
    ],
)
def test_all_producers_and_unknown_paths_qualify(path):
    assert selector().classify(path, producer_patterns(), OLD, NEW) is True


@pytest.mark.parametrize(
    "path",
    [
        "src/junoscfg/audit/json.py",
        "src/junoscfg/anonymize/rules.py",
        "docs/guide/usage.md",
        "openspec/changes/fixture/tasks.md",
        "README.md",
        ".github/workflows/test.yml",
        "tests/tooling/test_some_check.py",
    ],
)
def test_consumer_body_and_workflow_exemptions(path):
    assert selector().classify(path, producer_patterns(), OLD, NEW) is False


@pytest.mark.parametrize(
    "old,new",
    [
        (None, NEW),
        (OLD, None),
        (OLD, "def broken(:\n"),
        ("FLAG = 1\n" + OLD, "FLAG = 2\n" + NEW),
        ("import one\n" + OLD, "import two\n" + NEW),
        ("@decorate\n" + OLD, "@decorate\n" + NEW),
        ("@decorate()\n" + OLD, "@decorate()\n" + NEW),
        (OLD + "answer = consume(1)\n", NEW + "answer = consume(1)\n"),
        (
            "def consume(value=make()):\n    return value\n",
            "def consume(value=make()):\n    return str(value)\n",
        ),
        (
            "class Consumer(Base):\n    def run(self):\n        return 1\n",
            "class Consumer(Base):\n    def run(self):\n        return 2\n",
        ),
    ],
)
def test_import_time_uncertainty_qualifies(old, new):
    assert selector().classify("src/junoscfg/audit/json.py", producer_patterns(), old, new) is True


@pytest.mark.parametrize(
    "path",
    [
        ".agent-ready/schema/runtime.json",
        "tools/schema-verification/dependencies.json",
        "uv.lock",
        "pyproject.toml",
        "private_test_data/schemas/new.xsd",
    ],
)
def test_runtime_or_input_change_cannot_skip(path):
    assert selector().classify(path, producer_patterns(), "old", "new") is True


@pytest.mark.parametrize("proved", [False, True])
def test_consumer_selection_requires_successful_context_after_preparation(
    tmp_path, monkeypatch, proved
):
    module = selector()
    (tmp_path / "pyproject.toml").write_bytes((PROJECT_ROOT / "pyproject.toml").read_bytes())
    path = tmp_path / "src/junoscfg/audit/json.py"
    path.parent.mkdir(parents=True)
    path.write_text(OLD)
    git(tmp_path, "init", "-q")
    commit_fixture(tmp_path)
    base = git(tmp_path, "rev-parse", "HEAD").strip()
    path.write_text(NEW)
    commit_fixture(tmp_path)
    monkeypatch.setattr(module, "check_dependencies", lambda root: None)
    observed = []

    def context(root, compared_base, patterns):
        observed.append((root, compared_base, patterns))
        return proved

    monkeypatch.setattr(module, "established_context", context)
    assert module.select(tmp_path, base) is (not proved)
    assert len(observed) == 1
    assert observed[0][0:2] == (tmp_path, base)
    assert observed[0][2]


def test_selection_command_emits_exact_boolean_json(tmp_path, monkeypatch, capsys):
    module = selector()
    monkeypatch.setattr(module, "select", lambda root, base: True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["schema_selection", "--base", "deadbeef"])
    assert module.main() in (None, 0)
    value = json.loads(capsys.readouterr().out)
    assert value == {"selected": True}
    assert type(value["selected"]) is bool


@pytest.mark.parametrize("receipt", [None, "not json", "{}", '{"success": true}'])
def test_prepared_metadata_without_valid_qualification_still_selects(
    tmp_path, monkeypatch, receipt
):
    module = selector()
    (tmp_path / "pyproject.toml").write_bytes((PROJECT_ROOT / "pyproject.toml").read_bytes())
    path = tmp_path / "README.md"
    path.write_text("before\n")
    git(tmp_path, "init", "-q")
    commit_fixture(tmp_path)
    base = git(tmp_path, "rev-parse", "HEAD").strip()
    path.write_text("after\n")
    commit_fixture(tmp_path)
    prepared = tmp_path / ".agent-ready/schema/runtime.json"
    prepared.parent.mkdir(parents=True)
    prepared.write_text('{"prepared": true}\n')
    if receipt is not None:
        record = tmp_path / ".agent-ready/verification/fake.json"
        record.parent.mkdir(parents=True)
        record.write_text(receipt)
    monkeypatch.setattr(module, "check_dependencies", lambda root: None)
    assert module.select(tmp_path, base) is True


@pytest.mark.parametrize(
    "path,old,new",
    [
        (
            "pyproject.toml",
            '[project]\nname = "junoscfg"\nversion = "0.28.3"\n',
            '[project]\nname = "junoscfg"\nversion = "0.28.4"\n',
        ),
        ("src/junoscfg/__init__.py", '__version__ = "0.28.3"\n', '__version__ = "0.28.4"\n'),
    ],
)
def test_release_version_only_keeps_cheap_guard_exception(path, old, new):
    assert selector().classify(path, producer_patterns(), old, new) is False


@pytest.mark.parametrize("root_only", [True, False])
def test_only_editable_root_lock_version_is_exempt(root_only):
    from tests.tooling.test_schema_dependency_trigger_challenge import LOCK

    changed = LOCK.replace('version = "0.28.3"', 'version = "0.28.4"')
    if not root_only:
        changed = changed.replace('version = "1.0"', 'version = "2.0"')
    assert selector().classify("uv.lock", producer_patterns(), LOCK, changed) is (not root_only)


@pytest.fixture
def native_generation_context(tmp_path, monkeypatch):
    """Execute a tiny native generation command; retain real receipt/hash validation."""
    import copy
    import sys

    from agent_ready_checks import verification, verification_runtime

    from tests.tooling.test_schema_dependency_trigger_challenge import LOCK
    from tools import schema_verification

    root = tmp_path / "native-context"
    root.mkdir()
    files = {
        "src/junoscfg/audit/consumer.py": OLD,
        "src/junoscfg/validate/schema_generator.py": "def build():\n    return 1\n",
        "src/junoscfg/__init__.py": '__version__ = "0.28.3"\n',
        "README.md": "fixture\n",
        "tools/schema_verification.py": "def prepare():\n    return 1\n",
        "pyproject.toml": '[project]\nname = "junoscfg"\nversion = "0.28.3"\n',
        "uv.lock": LOCK,
        ".gitignore": ".agent-ready/\nprivate_test_data/\n",
        "required.json": '{"tests": ["generation"], "shards": []}',
        "stability.json": '[".agent-ready/product.txt"]',
    }
    for name, contents in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
    git(root, "init", "-q")
    commit_fixture(root)
    base = git(root, "rev-parse", "HEAD").strip()
    metadata = {"python": "fixture-runtime", "version:junoscfg": "0.28.3"}
    engine = {"stdlib": "original", "dependencies": "original"}
    runtime = root / ".agent-ready/schema/runtime.json"
    runtime.parent.mkdir(parents=True)
    runtime.write_text(json.dumps(metadata))
    dump = root / "private_test_data/schemas/fixture.xsd"
    dump.parent.mkdir(parents=True)
    dump.write_text("synthetic schema input")
    command = [
        sys.executable,
        "-c",
        "from pathlib import Path; "
        "Path('.agent-ready/result.json').write_bytes(Path('required.json').read_bytes()); "
        "Path('.agent-ready/product.txt').write_text('stable product')",
    ]
    declared = {
        "name": "schema-25.2-generation",
        "paths": ["src/junoscfg/validate/schema_generator.py"],
        "command": command,
        "runtime-command": [sys.executable],
        "runtime-packages": ["pytest"],
        "inputs": ["private_test_data/schemas/fixture.xsd", ".agent-ready/schema/runtime.json"],
        "version-files": [".agent-ready/schema/runtime.json"],
        "required-manifest": "required.json",
        "result-manifest": ".agent-ready/result.json",
        "stability-manifest": "stability.json",
    }
    module = selector()
    monkeypatch.setattr(module, "declarations", lambda path: [declared])
    write_source_boundary(root)
    commit_fixture(root)
    base = git(root, "rev-parse", "HEAD").strip()
    monkeypatch.setattr(schema_verification, "observe_versions", lambda: dict(metadata))
    monkeypatch.setattr(verification_runtime, "runtime", lambda path, tier: copy.deepcopy(engine))

    def observed_identity(path, argv, reference, tier):
        return {
            "root": str(path.resolve()),
            "base": reference,
            "command": argv,
            "declaration": tier,
            "tier_runtime": copy.deepcopy(engine),
            "files": verification.manifest(path, verification.tracked(path) + tier["inputs"]),
        }

    monkeypatch.setattr(verification, "identity", observed_identity)
    monkeypatch.setattr(verification, "record_event", lambda *args, **kwargs: None)
    assert verification.execute(root, command, base, declared, reuse=False) == 0
    identity = observed_identity(root, command, base, declared)
    receipt = root / verification.STORE / (verification.digest(identity) + ".json")
    assert verification.valid(root, identity, verification.read_json(receipt))
    return root, base, declared["paths"], metadata, engine, receipt


@pytest.mark.parametrize(
    "change,expected",
    [
        ("unchanged", True),
        ("consumer-body", True),
        ("release-reprepared", True),
        ("input", False),
        ("missing-input", False),
        ("runtime-stale-metadata", False),
        ("runtime-reprepared", False),
        ("dependency-reprepared", False),
        ("producer", False),
        ("consumer-old-hash-mismatch", False),
        ("output", False),
        ("failed-record", False),
        ("corrupt-record", False),
    ],
)
def test_native_generation_context_rejects_stale_proof(native_generation_context, change, expected):
    root, base, patterns, metadata, engine, receipt = native_generation_context
    runtime = root / ".agent-ready/schema/runtime.json"
    consumer = root / "src/junoscfg/audit/consumer.py"
    if change == "consumer-body":
        consumer.write_text(NEW)
    elif change == "release-reprepared":
        (root / "src/junoscfg/__init__.py").write_text('__version__ = "0.28.4"\n')
        metadata["version:junoscfg"] = "0.28.4"
        runtime.write_text(json.dumps(metadata))
    elif change == "input":
        (root / "private_test_data/schemas/fixture.xsd").write_text("changed input")
    elif change == "missing-input":
        (root / "private_test_data/schemas/fixture.xsd").unlink()
    elif change == "runtime-stale-metadata":
        metadata["python"] = "changed runtime"
    elif change in {"runtime-reprepared", "dependency-reprepared"}:
        key = "stdlib" if change == "runtime-reprepared" else "dependencies"
        engine[key] = "changed bytes at the same package version"
        metadata["content:" + key] = "changed"
        runtime.write_text(json.dumps(metadata))
    elif change == "producer":
        (root / "src/junoscfg/validate/schema_generator.py").write_text(
            "def build():\n    return 2\n"
        )
    elif change == "consumer-old-hash-mismatch":
        consumer.write_text(NEW)
        commit_fixture(root)
        base = git(root, "rev-parse", "HEAD").strip()
        consumer.write_text("def consume(value):\n    return repr(value)\n")
    elif change == "output":
        (root / ".agent-ready/product.txt").write_text("changed product")
    elif change == "failed-record":
        value = json.loads(receipt.read_text())
        value["exit_status"] = 1
        receipt.write_text(json.dumps(value))
    elif change == "corrupt-record":
        receipt.write_text("not JSON")
    assert selector().established_context(root, base, patterns) is expected


@pytest.mark.parametrize("version_path", ["src/junoscfg/__init__.py", "pyproject.toml", "uv.lock"])
def test_successive_release_only_changes_keep_cheap_guard_exception(
    native_generation_context, version_path
):
    root, base, patterns, metadata, engine, receipt = native_generation_context
    version = root / version_path
    original = version.read_text()
    runtime = root / ".agent-ready/schema/runtime.json"
    version.write_text(original.replace("0.28.3", "0.28.4"))
    metadata["version:junoscfg"] = "0.28.4"
    runtime.write_text(json.dumps(metadata))
    assert selector().established_context(root, base, patterns) is True
    commit_fixture(root)
    second_base = git(root, "rev-parse", "HEAD").strip()
    version.write_text(original.replace("0.28.3", "0.28.5"))
    metadata["version:junoscfg"] = "0.28.5"
    runtime.write_text(json.dumps(metadata))
    assert selector().established_context(root, second_base, patterns) is True


BOUNDARY = "tools/schema-verification/consumer-boundary.json"


def write_source_boundary(root):
    """Represent an explicit fixture audit, never successful qualification."""
    path = root / BOUNDARY
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"format": 1, "sources": selector().source_boundary(root)}))


@pytest.mark.parametrize(
    "change,unchanged",
    [
        ("eligible-body", True),
        ("root-version", True),
        ("producer-body", False),
        ("unsafe-import", False),
        ("new-source", False),
        ("deleted-source", False),
        ("lock-root-version", True),
        ("lock-dependency", False),
    ],
)
def test_audited_boundary_normalizes_only_isolated_consumer_bodies(
    native_generation_context, change, unchanged
):
    root, base, patterns, metadata, engine, receipt = native_generation_context
    before = selector().source_boundary(root)
    assert set(before) == {
        "uv.lock",
        "pyproject.toml",
        "tools/schema_verification.py",
        "src/junoscfg/__init__.py",
        "src/junoscfg/audit/consumer.py",
        "src/junoscfg/validate/schema_generator.py",
    }
    assert selector().verified_source_boundary(root) is True
    consumer = root / "src/junoscfg/audit/consumer.py"
    if change == "eligible-body":
        consumer.write_text(NEW)
    elif change == "root-version":
        (root / "src/junoscfg/__init__.py").write_text('__version__ = "0.28.4"\n')
    elif change == "producer-body":
        (root / "src/junoscfg/validate/schema_generator.py").write_text(
            "def build():\n    return 2\n"
        )
    elif change == "unsafe-import":
        consumer.write_text(NEW + "result = consume(1)\n")
    elif change == "new-source":
        (root / "src/junoscfg/audit/added.py").write_text("def added():\n    return 1\n")
        git(root, "add", "src/junoscfg/audit/added.py")
    elif change == "deleted-source":
        git(root, "rm", "src/junoscfg/audit/consumer.py")
    elif change in {"lock-root-version", "lock-dependency"}:
        lock = root / "uv.lock"
        before_version, after_version = (
            ('version = "0.28.3"', 'version = "0.28.4"')
            if change == "lock-root-version"
            else ('version = "1.0"', 'version = "2.0"')
        )
        lock.write_text(lock.read_text().replace(before_version, after_version))
    assert (selector().source_boundary(root) == before) is unchanged
    assert selector().verified_source_boundary(root) is unchanged


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "corrupt",
        "empty",
        "missing-format",
        "wrong-format",
        "boolean-format",
        "extra-field",
        "missing-source",
        "unknown-source",
        "changed-hash",
        "symlink",
    ],
)
def test_invalid_audited_boundary_cannot_authorize_receipt(native_generation_context, fault):
    root, base, patterns, metadata, engine, receipt = native_generation_context
    path = root / BOUNDARY
    original = path.read_text()
    record = json.loads(original)
    if fault == "missing":
        path.unlink()
    elif fault == "corrupt":
        path.write_text("not JSON")
    elif fault == "empty":
        record["sources"] = {}
    elif fault == "missing-format":
        del record["format"]
    elif fault == "wrong-format":
        record["format"] = 2
    elif fault == "boolean-format":
        record["format"] = True
    elif fault == "extra-field":
        record["unknown"] = "value"
    elif fault == "missing-source":
        del record["sources"]["src/junoscfg/audit/consumer.py"]
    elif fault == "unknown-source":
        record["sources"]["src/junoscfg/audit/unknown.py"] = "0" * 64
    elif fault == "changed-hash":
        record["sources"]["src/junoscfg/audit/consumer.py"] = "0" * 64
    elif fault == "symlink":
        target = root / "boundary-copy.json"
        target.write_text(original)
        path.unlink()
        path.symlink_to(target)
    if fault not in {"missing", "corrupt", "symlink"}:
        path.write_text(json.dumps(record))
    assert selector().verified_source_boundary(root) is False
    assert selector().established_context(root, base, patterns) is False


@pytest.mark.parametrize("dynamic_attribute", [False, True])
def test_newly_qualified_producer_dependency_does_not_expand_consumer_exemption(
    native_generation_context, dynamic_attribute
):
    import subprocess
    import sys

    from agent_ready_checks import verification

    root, base, patterns, metadata, engine, receipt = native_generation_context
    consumer = root / "src/junoscfg/validate/json_yaml_validator.py"
    original = (
        'def __getattr__(name):\n    if name == "schema_flag":\n'
        "        return lambda: True\n    raise AttributeError(name)\n"
        if dynamic_attribute
        else "def schema_flag():\n    return True\n"
    )
    consumer.write_text(original)
    (consumer.parent / "__init__.py").write_text("")
    git(root, "add", consumer.relative_to(root).as_posix(), "src/junoscfg/validate/__init__.py")
    # The audit precedes the new producer dependency. Executing new production
    # successfully must not silently refresh this reviewed source boundary.
    write_source_boundary(root)
    commit_fixture(root)
    audited = (root / BOUNDARY).read_bytes()
    producer = root / "src/junoscfg/validate/schema_generator.py"
    producer.write_text(
        "from .json_yaml_validator import schema_flag\n\n"
        "def build():\n"
        "    return {'type': 'object', 'additionalProperties': schema_flag()}\n"
    )
    commit_fixture(root)
    qualified_base = git(root, "rev-parse", "HEAD").strip()
    declaration = selector().declarations(root)[0]
    generate = (
        "import json,sys; from pathlib import Path; sys.path.insert(0, 'src'); "
        "from junoscfg.validate.schema_generator import build as generate; "
    )
    declaration["command"] = [
        sys.executable,
        "-B",
        "-c",
        generate + "Path('.agent-ready/product.txt').write_text(json.dumps(generate())); "
        "Path('.agent-ready/result.json').write_bytes(Path('required.json').read_bytes())",
    ]
    assert (
        verification.execute(root, declaration["command"], qualified_base, declaration, reuse=False)
        == 0
    )
    identity = verification.identity(root, declaration["command"], qualified_base, declaration)
    fresh_record = root / verification.STORE / (verification.digest(identity) + ".json")
    assert verification.valid(root, identity, verification.read_json(fresh_record))
    qualified = json.loads((root / ".agent-ready/product.txt").read_text())
    consumer.write_text(original.replace("True", "False"))
    commit_fixture(root)
    changed = json.loads(
        subprocess.check_output(
            [sys.executable, "-B", "-c", generate + "print(json.dumps(generate()))"],
            cwd=root,
            text=True,
        )
    )
    assert qualified["additionalProperties"] is True
    assert changed["additionalProperties"] is False
    assert (
        selector().classify(
            consumer.relative_to(root).as_posix(), patterns, original, consumer.read_text()
        )
        is True
    )
    assert (root / BOUNDARY).read_bytes() == audited
    assert selector().verified_source_boundary(root) is False
    assert selector().established_context(root, qualified_base, patterns) is False


@pytest.mark.parametrize("change", ["dependency", "wrapper", "config"])
def test_qualified_input_change_does_not_refresh_audited_boundary(
    native_generation_context, change
):
    from agent_ready_checks import verification

    from tools import schema_dependencies

    root, base, patterns, metadata, engine, receipt = native_generation_context
    audited = (root / BOUNDARY).read_bytes()
    if change == "dependency":
        lock = root / "uv.lock"
        lock.write_text(lock.read_text().replace('version = "1.0"', 'version = "2.0"'))
        schema_dependencies.write_dependencies(root)
        engine["dependencies"] = "updated dependency implementation"
        metadata["content:library"] = "updated dependency implementation"
        (root / ".agent-ready/schema/runtime.json").write_text(json.dumps(metadata))
    elif change == "wrapper":
        (root / "tools/schema_verification.py").write_text("def prepare():\n    return 2\n")
    else:
        project = root / "pyproject.toml"
        project.write_text(project.read_text() + "\n[tool.pytest.ini_options]\naddopts = '-x'\n")
    commit_fixture(root)
    current = git(root, "rev-parse", "HEAD").strip()
    declaration = selector().declarations(root)[0]
    assert (
        verification.execute(root, declaration["command"], current, declaration, reuse=False) == 0
    )
    identity = verification.identity(root, declaration["command"], current, declaration)
    record = root / verification.STORE / (verification.digest(identity) + ".json")
    assert verification.valid(root, identity, verification.read_json(record))
    assert (root / BOUNDARY).read_bytes() == audited
    assert selector().verified_source_boundary(root) is False
    assert selector().established_context(root, current, patterns) is False
