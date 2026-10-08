"""Policy tests for the enforced stable-interface type check."""

from __future__ import annotations

import shlex
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]

CHECKED_INTERFACES = {
    "src/junoscfg/__init__.py",
    "src/junoscfg/convert/__init__.py",
    "src/junoscfg/validate/__init__.py",
    "src/junoscfg/anonymize/__init__.py",
    "src/junoscfg/anonymize/config.py",
    "src/junoscfg/audit/__init__.py",
    "src/junoscfg/audit/model.py",
}


def test_ci_enforces_stable_interface_type_check() -> None:
    """Reject a non-blocking or repository-wide mypy CI step."""
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    steps = workflow["jobs"]["full"]["steps"]
    mypy_steps = [step for step in steps if "mypy" in step.get("run", "").split()]

    assert len(mypy_steps) == 1
    step = mypy_steps[0]
    assert step.get("continue-on-error", False) is False

    command = shlex.split(step["run"])
    mypy_index = command.index("mypy")
    assert command[mypy_index + 1] == "--follow-imports=silent"
    assert set(command[mypy_index + 2 :]) == CHECKED_INTERFACES
