"""Ordinary execution uses the shared exact-command evidence authority."""

import sys
from types import SimpleNamespace

import pytest

from tools import affected_tests


@pytest.fixture
def execution(monkeypatch):
    from agent_ready_checks import readiness, verification

    calls = []
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
    assert declaration == {"name": "affected-tests", "runtime-command": [sys.executable]}


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
