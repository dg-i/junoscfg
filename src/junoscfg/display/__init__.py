"""Junoscfg display format converters: the shared kernel.

Six of the eight packages import from here, so this module is the one door.
Everything other packages may use is re-exported below and listed in
``__all__``; reaching past it into a submodule is what ``tach check`` and
``agent-ready interfaces`` both refuse.
"""

from __future__ import annotations

from junoscfg.display.config_store import ConfigStore, filter_structured_by_path
from junoscfg.display.constants import (
    INTEGER_TYPES,
    KEY_ALIASES,
    UNIVERSAL_STATEMENTS,
    UNQUOTABLE_TYPES,
    artifacts_dir,
    build_from_artifact,
    entry_key_names,
    entry_keys,
    enum_is_fragment,
    find_artifact,
    forget_loaded_artifacts,
    get_transparent_child,
    holds_tag,
    is_flat_dict,
    is_freeform_nk,
    is_positional_key,
    is_transparent_list_key,
    key_is_positional,
    load_schema_tree,
    open_artifact_write,
    passes_tag_to_child,
    read_artifact_text,
    resolve_artifacts_dir,
    resolve_key_alias,
    statement_children,
    statement_name_spellings,
    strip_type_prefix,
)
from junoscfg.display.format_detection import (
    AUDIT_FORMATS,
    CONVERSION_FORMATS,
    VALIDATION_FORMATS,
    detect_format,
    is_display_set,
)
from junoscfg.display.path_filter import filter_dict_by_path
from junoscfg.display.set_converter import SetConverter
from junoscfg.display.to_json import filter_json_by_path
from junoscfg.display.to_yaml import filter_yaml_by_path, xml_to_dict, xml_to_yaml
from junoscfg.display.value_format import format_value

__all__ = [
    "INTEGER_TYPES",
    "KEY_ALIASES",
    "UNIVERSAL_STATEMENTS",
    "UNQUOTABLE_TYPES",
    "AUDIT_FORMATS",
    "CONVERSION_FORMATS",
    "VALIDATION_FORMATS",
    "ConfigStore",
    "SetConverter",
    "filter_json_by_path",
    "filter_dict_by_path",
    "filter_set_by_path",
    "filter_structured_by_path",
    "filter_yaml_by_path",
    "detect_format",
    "format_value",
    "get_transparent_child",
    "holds_tag",
    "is_display_set",
    "is_flat_dict",
    "is_freeform_nk",
    "key_is_positional",
    "is_positional_key",
    "is_transparent_list_key",
    "load_schema_tree",
    "open_artifact_write",
    "passes_tag_to_child",
    "read_artifact_text",
    "artifacts_dir",
    "build_from_artifact",
    "entry_key_names",
    "entry_keys",
    "enum_is_fragment",
    "find_artifact",
    "forget_loaded_artifacts",
    "resolve_artifacts_dir",
    "resolve_key_alias",
    "statement_children",
    "statement_name_spellings",
    "strip_type_prefix",
    "xml_to_dict",
    "xml_to_yaml",
]

_SET_PREFIXES = ("set", "deactivate", "protect", "activate", "delete")


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
