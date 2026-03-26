"""JSON path filtering for Junos configurations."""

from __future__ import annotations

import json

from junoscfg.display.path_filter import filter_dict_by_path


def filter_json_by_path(text: str, path_tokens: list[str], *, relative: bool = False) -> str:
    """Filter JSON output to the subtree at the given path.

    Args:
        text: JSON text with ``configuration`` as the top-level key.
        path_tokens: Path components to navigate (e.g. ["system", "syslog"]).
        relative: If True, return just the subtree value.
                  If False, wrap the subtree in the full path hierarchy.

    Returns:
        Filtered JSON text, or empty string if path not found.
    """
    if not path_tokens:
        return text

    data = json.loads(text)
    if not isinstance(data, dict):
        return ""

    result = filter_dict_by_path(data, path_tokens, relative=relative)
    if result is None:
        return ""

    return json.dumps(result, indent=2) + "\n"
