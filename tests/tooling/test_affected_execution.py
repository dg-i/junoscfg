"""Ordinary execution uses the shared exact-command evidence authority."""

import sys
from types import SimpleNamespace

import pytest

from tools import affected_tests


@pytest.fixture
def execution(monkeypatch):
    from agent_ready_checks import readiness, verification

    calls = []
    monkeypatch.setattr(affected_tests, "reuse_blocker", lambda: None)
    monkeypatch.setattr(
        affected_tests, "select", lambda files: ["tests/tooling/test_cli_reference.py"]
    )
    monkeypatch.setattr(readiness, "config", lambda root: {"enabled": True})

    def run(root, command, base, declaration):
        calls.append((root, command, base, declaration))
        return 0

    monkeypatch.setattr(verification, "execute", run)
    return calls


def test_selected_command_is_the_shared_evidence_obligation(execution):
    assert affected_tests.main(["--run", "tools/generate_cli_reference.py"]) == 0
    root, command, base, declaration = execution[0]
    assert root == affected_tests.ROOT
    assert command == [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--no-header",
        "tests/tooling/test_cli_reference.py",
    ]
    assert base is None  # Shared stage resolver binds the actual change base.
    assert declaration == {"name": "affected-tests"}


def test_shared_execution_failure_is_not_relabelled_or_retried(execution, monkeypatch):
    from agent_ready_checks import verification

    monkeypatch.setattr(verification, "execute", lambda *args: 1)
    monkeypatch.setattr(
        affected_tests.subprocess, "run", lambda *args, **kwargs: pytest.fail("retry")
    )
    assert affected_tests.main(["--run", "tools/generate_cli_reference.py"]) == 1


@pytest.mark.parametrize("enabled", [True, False])
def test_unavailable_evidence_or_disabled_policy_executes_tests(execution, monkeypatch, enabled):
    from agent_ready_checks import readiness, verification

    monkeypatch.setattr(readiness, "config", lambda root: {"enabled": enabled})

    def unavailable(*args):
        if not enabled:
            pytest.fail("disabled policy must not consult evidence")
        raise ValueError("deleted tracked input")

    monkeypatch.setattr(verification, "execute", unavailable)
    calls = []
    monkeypatch.setattr(
        affected_tests.subprocess,
        "run",
        lambda command, **kwargs: calls.append(command) or SimpleNamespace(returncode=3),
    )
    assert affected_tests.main(["--run", "tools/generate_cli_reference.py"]) == 3
    assert calls[0][-1] == "tests/tooling/test_cli_reference.py"


@pytest.mark.parametrize("input_kind", ["captures", "schemas", "override", "options", "alternate"])
def test_undeclared_inputs_cannot_consult_a_success_receipt(tmp_path, monkeypatch, input_kind):
    from agent_ready_checks import verification

    monkeypatch.setattr(affected_tests, "ROOT", tmp_path)
    monkeypatch.setattr(affected_tests, "select", lambda files: ["tests/"])
    for key in list(affected_tests.os.environ):
        if key.startswith(("PYTEST_", "JUNOSCFG_")):
            monkeypatch.delenv(key)
    project = tmp_path / "pyproject.toml"
    project.write_text(
        '[tool.pytest.ini_options]\naddopts = ["--strict-markers", "--strict-config", "-ra"]\n'
    )
    assert affected_tests.reuse_blocker() is None
    if input_kind in {"captures", "schemas"}:
        directory = tmp_path / "private_test_data" / input_kind
        directory.mkdir(parents=True)
        (directory / "input.conf").write_text("changed private bytes")
    elif input_kind == "override":
        monkeypatch.setenv("PYTEST_ADDOPTS", "--regen-schema")
    elif input_kind == "options":
        project.write_text('[tool.pytest.ini_options]\naddopts = ["--device-grammar"]\n')
    else:
        (tmp_path / "pytest.ini").write_text("[pytest]\naddopts = --schema\n")
    assert affected_tests.reuse_blocker() is not None
    monkeypatch.setattr(
        verification, "execute", lambda *args: pytest.fail("must not consult old success")
    )
    monkeypatch.setattr(
        affected_tests.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=2)
    )
    assert affected_tests.main(["--run", "tests/corpus/test_device_truth.py"]) == 2


@pytest.mark.parametrize(
    "variable",
    ["JUNOSCFG_ARTIFACTS", "JUNOSCFG_AUDIT_REGISTRY", "JUNOSCFG_XSD_SOURCE", "PYTEST_PLUGINS"],
)
def test_external_path_contents_are_not_proven_by_environment_strings(monkeypatch, variable):
    monkeypatch.setenv(variable, "same-path-with-changed-content")
    assert affected_tests.reuse_blocker() is not None
