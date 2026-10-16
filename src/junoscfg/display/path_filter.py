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
        the selection keeps the annotation its last key has beside it
        (``@<key>``: a leaf's or leaf-list's tags); a container or list entry
        holds its own inside the selected value.
    """
    # Navigate through "configuration" wrapper if present
    if "configuration" in data:
        node: Any = data["configuration"]
        has_config_wrapper = True
    else:
        node = data
        has_config_wrapper = False

    # Walk to the target path
    parent: Any = None
    for token in path_tokens:
        if not isinstance(node, dict) or token not in node:
            return None
        parent, node = node, node[token]

    if relative:
        return node  # type: ignore[no-any-return]

    # Rebuild the path hierarchy around the subtree, the last key's tags beside it
    result: Any = node
    if path_tokens:
        last, tags = path_tokens[-1], f"@{path_tokens[-1]}"
        result = {last: node, tags: parent[tags]} if tags in parent else {last: node}
    for token in reversed(path_tokens[:-1]):
        result = {token: result}
    if has_config_wrapper:
        result = {"configuration": result}
    return result  # type: ignore[no-any-return]
