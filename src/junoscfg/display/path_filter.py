"""Shared dict-navigation helper for JSON and YAML path filtering."""

from __future__ import annotations

from typing import Any


def filter_dict_by_path(
    data: dict[str, Any], path_tokens: list[str], *, relative: bool = False
) -> dict[str, Any] | None:
    """Navigate a dict to the subtree at *path_tokens*, optionally stripping the path prefix.

    Args:
        data: Parsed dict (e.g. from ``json.loads`` or ``yaml.safe_load``).
        path_tokens: Path components to navigate (e.g. ``["system", "syslog"]``).
        relative: If True, return the subtree directly.
            If False, rebuild the full hierarchy around it.

    Returns:
        Filtered dict, or ``None`` if the path is not found.
    """
    # Navigate through "configuration" wrapper if present
    if "configuration" in data:
        node: Any = data["configuration"]
        has_config_wrapper = True
    else:
        node = data
        has_config_wrapper = False

    # Walk to the target path
    for token in path_tokens:
        if not isinstance(node, dict) or token not in node:
            return None
        node = node[token]

    if relative:
        return node  # type: ignore[no-any-return]

    # Rebuild the path hierarchy around the subtree
    result: Any = node
    for token in reversed(path_tokens):
        result = {token: result}
    if has_config_wrapper:
        result = {"configuration": result}
    return result  # type: ignore[no-any-return]
