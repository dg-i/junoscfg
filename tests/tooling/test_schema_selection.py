"""Qualification is omitted only when relevance and prior proof are established."""

from __future__ import annotations

import importlib
import json

import pytest
import tomllib

from tests.support.paths import PROJECT_ROOT
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
        "src/junoscfg/convert/json.py",
        "src/junoscfg/anonymize/rules.py",
        "src/junoscfg/validate/json_yaml_validator.py",
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
    assert (
        selector().classify("src/junoscfg/convert/json.py", producer_patterns(), old, new) is True
    )


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
    path = tmp_path / "src/junoscfg/convert/json.py"
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
