"""Ordinary schema checks retain their test-only dependency boundary."""

from __future__ import annotations

import builtins
import subprocess
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(autouse=True)
def unavailable_development_framework(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make accidental framework imports fail before the public fixture runs."""
    original = builtins.__import__

    def blocked(name, *args, **kwargs):
        if (
            name == "agent_ready_checks"
            or name.startswith("agent_ready_checks.")
            or name == "tools.schema_verification"
        ):
            raise ModuleNotFoundError(f"development framework intentionally unavailable: {name}")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)


@pytest.mark.parametrize(
    "operation, text",
    [
        ("json-schema-draft202012", '{"type":"string"}'),
        ("lark-grammar", 'start: "a"'),
    ],
)
def test_valid_content_executes_without_development_framework(
    schema_content_check, tmp_path: Path, operation: str, text: str
) -> None:
    """Both original checker operations remain available to the test group."""
    artifact = tmp_path / "artifact"
    artifact.write_text(text)
    schema_content_check(artifact, operation)


@pytest.mark.parametrize(
    "operation, text",
    [
        ("json-schema-draft202012", '{"type":"invalid-kind"}'),
        ("lark-grammar", "start: ("),
    ],
)
def test_invalid_content_fails_without_development_framework(
    schema_content_check, tmp_path: Path, operation: str, text: str
) -> None:
    """Unavailable tooling cannot turn invalid checker inputs into success."""
    artifact = tmp_path / "artifact"
    artifact.write_text(text)
    with pytest.raises(subprocess.CalledProcessError):
        schema_content_check(artifact, operation)
