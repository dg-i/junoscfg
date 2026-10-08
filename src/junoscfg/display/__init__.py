"""Junoscfg display format converters: the shared kernel.

Six of the eight packages import from here, so this module is the one door.
Everything other packages may use is re-exported below and listed in
``__all__``; reaching past it into a submodule is what ``tach check`` and
``agent-ready interfaces`` both refuse.
"""

from __future__ import annotations

import re

from junoscfg.display.config_store import ConfigStore, filter_structured_by_path
from junoscfg.display.constants import (
    ENTRY_KEY_OVERRIDES,
    INTEGER_TYPES,
    KEY_ALIASES,
    UNIVERSAL_STATEMENTS,
    UNQUOTABLE_TYPES,
    artifacts_dir,
    enum_is_fragment,
    find_artifact,
    get_flat_entry_config,
    get_transparent_child,
    is_flat_dict,
    is_freeform_nk,
    is_positional_key,
    is_transparent_list_key,
    load_schema_tree,
    open_artifact_write,
    read_artifact_text,
    resolve_artifacts_dir,
    resolve_key_alias,
    statement_name_spellings,
    strip_type_prefix,
)
from junoscfg.display.set_converter import SetConverter
from junoscfg.display.to_json import filter_json_by_path
from junoscfg.display.to_yaml import filter_yaml_by_path, xml_to_yaml
from junoscfg.display.value_format import format_value

__all__ = [
    "ENTRY_KEY_OVERRIDES",
    "INTEGER_TYPES",
    "KEY_ALIASES",
    "UNIVERSAL_STATEMENTS",
    "UNQUOTABLE_TYPES",
    "ConfigStore",
    "SetConverter",
    "filter_json_by_path",
    "filter_set_by_path",
    "filter_structured_by_path",
    "filter_yaml_by_path",
    "format_value",
    "get_flat_entry_config",
    "get_transparent_child",
    "is_display_set",
    "is_flat_dict",
    "is_freeform_nk",
    "is_positional_key",
    "is_transparent_list_key",
    "load_schema_tree",
    "open_artifact_write",
    "read_artifact_text",
    "artifacts_dir",
    "enum_is_fragment",
    "find_artifact",
    "resolve_artifacts_dir",
    "resolve_key_alias",
    "statement_name_spellings",
    "strip_type_prefix",
    "xml_to_yaml",
]

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
