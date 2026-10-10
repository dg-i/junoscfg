"""Fixtures for the audit tests; inline registries are in ``registries.py``."""

from __future__ import annotations

from typing import Any

import pytest

from junoscfg.convert import to_dict


@pytest.fixture
def make_ir() -> Any:
    """Parse display-set text into the unwrapped IR."""

    def _make(set_text: str, fmt: str = "set") -> dict[str, Any]:
        return to_dict(set_text.strip(), fmt)

    return _make


@pytest.fixture
def schema_root(bundled_tree: dict[str, Any]) -> dict[str, Any]:
    """The configuration node of the shipped structure tree, as the engine walks it."""
    return bundled_tree.get("c", {}).get("configuration", bundled_tree)
