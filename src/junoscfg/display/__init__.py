"""Junoscfg display format converters."""

from __future__ import annotations

import re

_SET_PREFIXES = ("set", "deactivate", "protect", "activate", "delete")


def is_display_set(text: str) -> bool:
    """Check if text is in 'display set' format (set/deactivate commands)."""
    for line in text.strip().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not re.match(r"^(set|deactivate|delete)\s", stripped):
            return False
    return True


def filter_set_by_path(text: str, path_tokens: list[str], *, relative: bool = False) -> str:
    """Filter set command output to lines matching the given path prefix.

    Args:
        text: Set command output (one command per line).
        path_tokens: Path components to match (e.g. ["system", "syslog"]).
        relative: If True, strip the path prefix from matching lines.

    Returns:
        Filtered text with only matching lines.
    """
    if not path_tokens:
        return text

    path_prefix = " ".join(path_tokens)
    result_lines: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # Split off the command prefix (set, deactivate, protect, activate)
        parts = stripped.split(None, 1)
        if len(parts) < 2 or parts[0] not in _SET_PREFIXES:
            continue

        cmd, rest = parts[0], parts[1]

        # Check if rest starts with the path prefix (exact token boundary)
        if rest == path_prefix or rest.startswith(path_prefix + " "):
            if relative:
                remaining = rest[len(path_prefix) :].lstrip()
                if remaining:
                    result_lines.append(f"{cmd} {remaining}")
                else:
                    result_lines.append(cmd)
            else:
                result_lines.append(stripped)

    if not result_lines:
        return ""
    return "\n".join(result_lines) + "\n"
