"""Shared fixtures for the audit test suite."""

from __future__ import annotations

from typing import Any

import pytest

from junoscfg.audit.registry import Registry, TypeEntry
from junoscfg.convert import to_dict


@pytest.fixture
def make_ir() -> Any:
    """Parse display-set text into the unwrapped IR."""

    def _make(set_text: str, fmt: str = "set") -> dict[str, Any]:
        return to_dict(set_text.strip(), fmt)

    return _make


def make_registry(*entries: TypeEntry) -> Registry:
    """Build a small inline registry for engine-level tests."""
    return Registry(types={entry.name: entry for entry in entries})


POLICY_STATEMENT = TypeEntry(
    name="policy-statement",
    source="curated",
    definition=(("policy-options", "policy-statement"),),
    reference_schema_types=frozenset({"policy-algebra"}),
)

PREFIX_LIST = TypeEntry(
    name="prefix-list",
    source="curated",
    definition=(("policy-options", "prefix-list"),),
    reference_paths=(("from", "prefix-list"),),
)

CONFIG_GROUP = TypeEntry(
    name="config-group",
    source="curated",
    definition=(("groups", "group"),),
    reference_paths=(("apply-groups",), ("apply-groups-except",)),
    implicit=("re0", "re1", "global", "node*", "member*", "fabric*"),
)
