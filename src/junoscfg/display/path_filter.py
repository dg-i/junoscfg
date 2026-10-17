"""Shared dict-navigation helper for JSON and YAML path filtering."""

from __future__ import annotations

from typing import Any


def filter_dict_by_path(
    data: dict[str, Any], path_tokens: list[str], *, relative: bool = False
) -> Any | None:
    """Navigate a dict to the subtree at *path_tokens*, optionally stripping the path prefix.

    Args:
        data: Parsed dict (e.g. from ``json.loads`` or ``yaml.safe_load``).
        path_tokens: Path components to navigate (e.g. ``["system", "syslog"]``).
        relative: If True, return the subtree directly.
            If False, rebuild the full hierarchy around it.

    Returns:
        Filtered subtree value, or ``None`` if the path is not found. A
        relative path may select a scalar or list as well as a dict. Rebuilt,
        the selection keeps the annotations along its path: each step's
        ``@<key>`` beside it (a leaf's or leaf-list's tags) and each ancestor
        container's own ``@``, so a statement inside a deactivated container
        stays inside it, as the device prints it (probe C3); a container or
        list entry holds its own inside the selected value.
    """
    # Navigate through "configuration" wrapper if present
    if "configuration" in data:
        node: Any = data["configuration"]
        has_config_wrapper = True
    else:
        node = data
        has_config_wrapper = False

    # Walk to the target path, keeping each level that holds a step
    holders: list[dict[str, Any]] = []
    for token in path_tokens:
        if not isinstance(node, dict) or token not in node:
            return None
        holders.append(node)
        node = node[token]

    if relative:
        return node  # type: ignore[no-any-return]

    # Rebuild the path hierarchy around the subtree with the annotations along
    # it: each step's `@<key>` beside it and each ancestor container's own `@`
    # (not the configuration's), as the whole configuration holds them.
    result: Any = node
    for depth in reversed(range(len(path_tokens))):
        holder, token = holders[depth], path_tokens[depth]
        level: dict[str, Any] = {}
        if depth and token != "@" and "@" in holder:
            level["@"] = holder["@"]
        level[token] = result
        if f"@{token}" in holder:
            level[f"@{token}"] = holder[f"@{token}"]
        result = level
    if has_config_wrapper:
        result = {"configuration": result}
    return result  # type: ignore[no-any-return]
