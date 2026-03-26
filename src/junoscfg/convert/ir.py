"""IR utilities for the JSON dict internal representation.

The IR is a plain Python dict matching the Junos JSON format:
``{"configuration": {"system": {"host-name": "r1"}, "@system": {"inactive": true}}}``.
"""

from __future__ import annotations

from typing import Any


def find_configuration(data: Any) -> dict[str, Any] | None:
    """Locate the ``configuration`` dict, handling rpc-reply wrappers.

    Accepts bare ``{"configuration": {...}}``, nested rpc-reply wrappers,
    or bare content dicts containing well-known top-level keys.
    """
    if isinstance(data, dict):
        if "configuration" in data:
            return data["configuration"]  # type: ignore[no-any-return]
        for v in data.values():
            if isinstance(v, dict) and "configuration" in v:
                return v["configuration"]  # type: ignore[no-any-return]
        # Looks like bare configuration content
        if any(k in data for k in ("system", "interfaces", "protocols")):
            return data  # type: ignore[return-value]
    return None


def wrap_configuration(config: dict[str, Any]) -> dict[str, Any]:
    """Wrap a configuration dict in the standard Junos JSON envelope."""
    return {"configuration": config}
