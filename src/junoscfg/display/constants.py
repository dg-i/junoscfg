"""Shared Junos configuration constants and schema flag helpers.

Schema flag helpers read conversion-hint flags from schema tree nodes
(set by Group H xsd_fixes and serialized by artifact_builder). When
schema_node is None (schema walk lost track), they fall back to
name-based constants.
"""

from __future__ import annotations

import gzip
import io
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

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


# ── Reading an artifact ──────────────────────────────────────────────
#
# Artifacts ship gzipped: the set is 34.5 MB raw and 2.1 MB compressed, and the
# two JSON schemas alone give back 20 MB at a 5% ratio. Readers accept either
# form, newest-first, because a directory a user generated before this, or by
# hand, has the plain files and should keep working. One pair of helpers rather
# than seven call sites each deciding — the divergence that produced
# `resolve_artifacts_dir` started exactly that way.


def find_artifact(directory: str | Path, name: str) -> Path | None:
    """The gzipped artifact if present, else the plain one, else None."""
    directory = Path(directory)
    compressed = directory / f"{name}.gz"
    if compressed.is_file():
        return compressed
    plain = directory / name
    return plain if plain.is_file() else None


def read_artifact_text(path: str | Path) -> str:
    """Read an artifact, decompressing when the name says to."""
    path = Path(path)
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return handle.read()
    return path.read_text(encoding="utf-8")


@contextmanager
def open_artifact_write(path: str | Path) -> Iterator[Any]:
    """Open an artifact for writing, compressing when the name says to.

    The pair of `read_artifact_text`: a writer names `.gz` and this does the
    rest, so no generator has to know about compression.
    """
    path = Path(path)
    if path.suffix == ".gz":
        # `mtime=0`, so regenerating identical content produces identical
        # bytes. gzip stamps the current time by default, which made every
        # regeneration a diff in git and would have made any byte-for-byte
        # comparison of a rebuilt artifact flaky for reasons nothing in the
        # schema explains.
        with (
            gzip.GzipFile(path, "wb", mtime=0) as gz,
            io.TextIOWrapper(gz, encoding="utf-8") as handle,
        ):
            yield handle
    else:
        with open(path, "w", encoding="utf-8") as handle:
            yield handle


def load_schema_tree(artifacts_dir: str | Path | None = None) -> dict[str, Any] | None:
    """Load a structure tree, cached per directory. None if it cannot be read.

    A directory the caller *chose* -- through the argument, the override or
    `JUNOSCFG_ARTIFACTS` -- raises instead of returning None. Conversion reads
    this and dereferences the result immediately, so a typo in `--artifacts`
    produced a Python traceback rather than an error; the bundled directory is
    the only one whose absence is reported as None, because a package missing
    its own artifacts is not something the user can fix by fixing the path.
    """
    directory = resolve_artifacts_dir(artifacts_dir)
    cached = _schema_trees.get(directory)
    if cached is not None:
        return cached
    path = find_artifact(directory, STRUCTURE_TREE_NAME)
    chosen = directory != _BUNDLED_DIR
    if path is None:
        if chosen:
            raise ValueError(f"No {STRUCTURE_TREE_NAME} in artifacts directory: {directory}")
        return None
    try:
        tree = json.loads(read_artifact_text(path))
    except (OSError, json.JSONDecodeError) as exc:
        if chosen:
            raise ValueError(f"Unreadable {STRUCTURE_TREE_NAME} in {directory}: {exc}") from exc
        return None
    _schema_trees[directory] = tree
    return tree


# --- XSD type names -------------------------------------------------------
#
# The structure tree stores a leaf's type as the XSD writes it, so an XSD
# built-in arrives prefixed: `xsd:unsignedShort`, not `unsignedShort`. Two
# packages need to ask what a type *is* -- `convert.field_validator` to check a
# value, `validate.grammar_generator` to pick a terminal -- and a second copy
# of the answer is how the two drift apart.

_XSD_PREFIX = "xsd:"


def strip_type_prefix(type_ref: str) -> str:
    """The bare XSD type name: ``xsd:unsignedShort`` is ``unsignedShort``."""
    return type_ref[len(_XSD_PREFIX) :] if type_ref.startswith(_XSD_PREFIX) else type_ref


#: XSD integer types, by their bare names.
INTEGER_TYPES = frozenset(
    {
        "int8",
        "int16",
        "int32",
        "int64",
        "uint8",
        "uint16",
        "uint32",
        "uint64",
        "integer",
        "unsignedInt",
        "unsignedShort",
        "unsignedByte",
        "unsignedLong",
        "short",
        "long",
        "byte",
        "positiveInteger",
        "nonNegativeInteger",
        "negativeInteger",
        "nonPositiveInteger",
    }
)

#: Types whose values cannot contain whitespace, so a quoted multi-word string
#: is never one. A grammar slot typed like this takes `VALUE`, not
#: `QUOTED_OR_VALUE`: `set interfaces ge-0/0/0 mtu "not a number at all"` and
#: `set system host-name "r1 r2 r3"` both validated while every leaf was
#: quotable, which put 11,695 slots where the pre-change grammar had 82.
#:
#: Interface names are deliberately absent: `interface-range` carries shell
#: patterns that a configuration may legitimately quote.
UNQUOTABLE_TYPES = frozenset(
    INTEGER_TYPES
    | {
        "ipaddr",
        "ipprefix",
        "ipprefix-optional",
        "ipv4addr",
        "ipv6addr",
        "ipv4prefix",
        "ipv6prefix",
        "mac-addr",
        "mac-unicast",
        "mac-multicast",
        "boolean",
    }
)


def statement_name_spellings(name: str, enums: Sequence[str]) -> tuple[str, ...]:
    """The statement spellings a folded on/off switch writes, or ``()``.

    The schema folds an on/off switch into one node whose name joins both
    spellings -- ``enable-disable``, carrying the enum ``['disable']`` -- so the
    token in a configuration *is* the statement, not a value beneath it. A
    device renders it ``"disable": [null]``.

    Two packages need this answer and must not each hold their own: the set
    reader keys the dict on it, and the JSON/YAML schema generator has to name
    the same spellings as properties. They did not agree, so junoscfg emitted
    ``disable`` and then rejected its own output.

    Returns every spelling, so ``enable`` is handled with ``disable``. The
    guard is that each enum value is a word of the node's own name; in 24.4R0
    that holds for 4,238 nodes and all of them are ``enable-disable``.
    """
    parts = tuple(name.split("-"))
    if len(parts) < 2 or not enums:
        return ()
    return parts if all(value in parts for value in enums) else ()


#: The statements a configuration may carry at any hierarchy level. They are
#: valid everywhere and appear in no NETCONF XSD of 21.4R0, 23.2R2, 23.4R2 or
#: 25.2R2, so every layer that reads a configuration has had to know them
#: separately -- eight modules do. One source, so a ninth copy is not the way a
#: new one is added.
UNIVERSAL_STATEMENTS = ("apply-groups", "apply-groups-except", "apply-flags", "apply-macro")


#: List nodes whose entry key is not ``name``. The set reader invents the key
#: when the XSD models it positionally, so the readers and the schema generator
#: have to agree on the spelling; `audit/walker.py` already carried a comment
#: that ``community-name`` was "hardcoded in the set parser", which is the
#: shape of a defect, not a note.
ENTRY_KEY_OVERRIDES: dict[str, str] = {"community": "community-name"}


def enum_is_fragment(name: str, enums: Sequence[str]) -> bool:
    """Whether *enums* is a fragment of a wider union rather than the whole type.

    A nokeyword leaf is positional: the value stands where the element name
    would, and the XSD models it as a union of an enum with a freeform type, of
    which extraction keeps only the enum. Enforcing those fragments produced
    53,326 field warnings over Juniper's validated designs.

    But not every nokeyword enum is a fragment. 26 of 24.4R0's 4,368 are closed
    Junos enums -- ``autorp-mode``, ``dense-group-flags``, ``transport`` -- and
    escaping those meant ``set protocols pim rp auto-rp frobnicate`` passed
    ``--strict`` while a device rejected it. The signature is mechanical: a
    fragment's values are words of the node's own name, or the single value
    ``default`` on a ``*-name`` node.
    """
    parts = set(name.split("-"))
    if all(value in parts or value == name for value in enums):
        return True
    return set(enums) == {"default"} and name.endswith("-name")
