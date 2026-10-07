"""Shared Junos configuration constants and schema flag helpers.

Schema flag helpers read conversion-hint flags from schema tree nodes
(set by Group H xsd_fixes and serialized by artifact_builder). When
schema_node is None (schema walk lost track), they fall back to
name-based constants.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

# ── XML-compat constants ─────────────────────────────────────────────
# These mirror schema flags for converters that walk XML trees instead
# of the schema (xml_to_set.py, to_yaml.py). Keep in sync with
# xsd_fixes.py Group H.

# Parent key => child key that should be skipped in the path.
# Junos JSON/XML wraps keyed lists: {"interfaces": {"interface": [...]}}.
# The inner element name is an XML artifact, not part of set commands.
TRANSPARENT_CONTAINERS: dict[str, str] = {
    "groups": "group",
    "interfaces": "interface",
    "routing-instances": "instance",
    "vlans": "vlan",
}

# Array/list wrapper keys whose name should be stripped from the path.
TRANSPARENT_LIST_KEYS: frozenset[str] = frozenset(["prefix-list-item", "contents"])

# Keys whose value is a positional argument that creates nesting scopes.
# Their value is emitted without the element name in the set command.
POSITIONAL_KEY_ELEMENTS: frozenset[str] = frozenset(["filter-name", "aspath", "list_name"])

# Positional key elements that do NOT create nesting scopes.
# Their value is emitted as a standalone set line; remaining siblings
# are emitted at the parent path level.
NON_NESTING_POSITIONAL_KEYS: frozenset[str] = frozenset(
    [
        "filename",
        "as-number",
        "confederation-as",
        "path",
        "limit",
        "timeout",
    ]
)

# All positional keys (union of nesting and non-nesting).
ALL_POSITIONAL_KEYS: frozenset[str] = POSITIONAL_KEY_ELEMENTS | NON_NESTING_POSITIONAL_KEYS

# Elements whose children should be flattened into a single set line.
# These named lists render as oneliners in Junos structured config:
# e.g., "route-filter 0.0.0.0/0 exact;" NOT "route-filter 0.0.0.0/0 { exact; }"
FLAT_ENTRY_ELEMENTS: frozenset[str] = frozenset(
    [
        "attributes-match",
        "route-filter",
        "source-address-filter",
        "prefix-list-filter",
    ]
)

# ── Private fallback constants ───────────────────────────────────────
# Used internally by schema flag helpers as fallbacks when the schema
# walk loses track. Not exported.

_FLAT_DICT_ELEMENTS: frozenset[str] = frozenset(["trigger"])

_FLAT_ENTRY_KEYS: dict[str, tuple[str, str]] = {
    "attributes-match": ("", "values-only"),
    "route-filter": ("address", "first"),
    "prefix-list-filter": ("list_name", "first"),
}

# ── Key aliases ──────────────────────────────────────────────────────

# JSON/XML element names that differ from set command keywords.
# These correspond to renames applied in xsd_fixes.py.
KEY_ALIASES: dict[str, str] = {
    "ieee-802.3ad": "802.3ad",
    "end-range": "to",
    "dest-nat-rule-match": "match",
    "src-nat-rule-match": "match",
    "static-nat-rule-match": "match",
    "equal-literal": "=",
    "plus-literal": "+",
    "minus-literal": "-",
}


def resolve_key_alias(key: str) -> str:
    """Resolve a conf/JSON element name to its schema key for lookup."""
    return KEY_ALIASES.get(key, key)


# ── Schema flag helpers ──────────────────────────────────────────────
# These read conversion-hint flags from schema tree nodes (set by Group H
# xsd_fixes and serialized by artifact_builder). When schema_node is None
# (schema walk lost track), they fall back to name-based constants.


def get_transparent_child(schema_node: dict[str, Any] | None, key: str | None = None) -> str | None:
    """Return the transparent child name from a schema node, or None.

    Falls back to TRANSPARENT_CONTAINERS when schema_node is unavailable.
    """
    if schema_node is not None:
        t = schema_node.get("t")
        if t is not None:
            return t
    if key is not None:
        return TRANSPARENT_CONTAINERS.get(key)
    return None


def is_transparent_list_key(schema_node: dict[str, Any] | None, key: str | None = None) -> bool:
    """Check if a schema node is a transparent list key.

    Falls back to TRANSPARENT_LIST_KEYS when schema_node is unavailable.
    """
    if schema_node is not None:
        return bool(schema_node.get("tk"))
    return key is not None and key in TRANSPARENT_LIST_KEYS


def is_positional_key(schema_node: dict[str, Any] | None, key: str | None = None) -> bool:
    """Check if a schema node is a positional key (nesting or flat).

    Falls back to ALL_POSITIONAL_KEYS when schema_node is unavailable.
    """
    if schema_node is not None:
        return bool(schema_node.get("pk") or schema_node.get("pkf"))
    return key is not None and key in ALL_POSITIONAL_KEYS


def is_flat_dict(schema_node: dict[str, Any] | None, key: str | None = None) -> bool:
    """Check if a schema node is a flat dict element.

    Falls back to _FLAT_DICT_ELEMENTS when schema_node is unavailable.
    """
    if schema_node is not None:
        return bool(schema_node.get("fd"))
    return key is not None and key in _FLAT_DICT_ELEMENTS


def get_flat_entry_config(
    schema_node: dict[str, Any] | None, key: str | None = None
) -> tuple[str, str] | None:
    """Return (positional_key, position) for a flat entry node, or None.

    Falls back to _FLAT_ENTRY_KEYS when schema_node is unavailable.
    """
    if schema_node is not None:
        fe = schema_node.get("fe")
        if fe is not None:
            return (fe["k"], fe["p"])
    if key is not None:
        return _FLAT_ENTRY_KEYS.get(key)
    return None


def is_freeform_nk(schema_node: dict[str, Any] | None) -> bool:
    """Check if a schema node is a freeform nk key (not keyword-suppressed).

    No name-based fallback needed: the freeform check is only reached when
    child_schema is not None (guarded by the nk flag check).
    """
    if schema_node is None:
        return False
    return bool(schema_node.get("frnk"))


# ── Shared artifact resolution ───────────────────────────────────────
#
# One resolver for the whole package. Conversion and validation used to answer
# "where do the artifacts live?" separately: `JunosValidator` took an argument,
# then `JUNOSCFG_ARTIFACTS`, then the bundle, and documented it; this module
# hardcoded the bundled path and cached it in a process-wide singleton. So
# `JUNOSCFG_ARTIFACTS` switched validation and was silently ignored by
# conversion, which is the larger feature and the one the Ansible collection
# uses. A documented option that works for half a tool is worse than one that
# does not exist.

_BUNDLED_DIR = Path(__file__).resolve().parent.parent / "validate" / "data"
_ARTIFACTS_ENV = "JUNOSCFG_ARTIFACTS"
STRUCTURE_TREE_NAME = "junos-structure-tree.json"

# Set for the length of one CLI invocation by `--artifacts`, which is a
# single-schema context by definition. The library takes the directory as an
# argument instead; nothing in the package mutates this.
_override_dir: Path | None = None

# Keyed on the resolved directory, so two schemas can coexist in one process.
# The old singleton could not: an Ansible play touching two device roles would
# have got whichever tree was loaded first.
_schema_trees: dict[Path, dict[str, Any]] = {}


def resolve_artifacts_dir(artifacts_dir: str | Path | None = None) -> Path:
    """Where the artifacts live, by one rule for every caller.

    Explicit argument, then the process override an invocation may set, then
    ``JUNOSCFG_ARTIFACTS``, then the bundled directory.
    """
    if artifacts_dir is not None:
        return Path(artifacts_dir)
    if _override_dir is not None:
        return _override_dir
    env = os.environ.get(_ARTIFACTS_ENV)
    if env:
        return Path(env)
    return _BUNDLED_DIR


@contextmanager
def artifacts_dir(path: str | Path | None) -> Iterator[None]:
    """Resolve to *path* for the duration of the block, then restore.

    A context manager rather than a setter, because the override is process
    state and junoscfg is not only a command. `CliRunner` runs the CLI in the
    test process, and the Ansible collection imports the library into a
    long-lived `ansible-playbook`; a setter with no matching reset leaks one
    invocation's schema into everything after it. That is what this very
    change did on first writing, and 109 conversion tests caught it.

    A library caller should pass the directory to the call instead; this is
    for a command that processes one configuration against one schema.
    """
    global _override_dir  # noqa: PLW0603
    previous = _override_dir
    _override_dir = Path(path) if path is not None else None
    try:
        yield
    finally:
        _override_dir = previous


def load_schema_tree(artifacts_dir: str | Path | None = None) -> dict[str, Any] | None:
    """Load a structure tree, cached per directory. None if it cannot be read."""
    directory = resolve_artifacts_dir(artifacts_dir)
    cached = _schema_trees.get(directory)
    if cached is not None:
        return cached
    try:
        with open(directory / STRUCTURE_TREE_NAME) as f:
            tree = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    _schema_trees[directory] = tree
    return tree
