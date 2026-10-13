"""ArtifactBuilder: full pipeline from NETCONF dump to validation artifacts.

Orchestrates XSD extraction, parsing, fixes, and artifact generation.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple

from junoscfg.display import open_artifact_write, read_artifact_text
from junoscfg.validate.grammar_generator import write_lark_grammar
from junoscfg.validate.schema_generator import write_json_schema
from junoscfg.validate.schema_node import SchemaNode  # noqa: TC001
from junoscfg.validate.xsd_extractor import extract_xsd
from junoscfg.validate.xsd_fixes import apply_all_fixes, get_fix_count
from junoscfg.validate.xsd_parser import parse_xsd

if TYPE_CHECKING:
    from collections.abc import Callable


class ArtifactBuilder:
    """Generates all validation artifacts from a NETCONF XSD dump."""

    def build(
        self,
        netconf_source: str | Path,
        output_dir: str | Path,
    ) -> dict[str, str]:
        """Run the full artifact generation pipeline.

        Args:
            netconf_source: Path to NETCONF dump file, or XSD text.
            output_dir: Directory to write artifacts to.

        Returns:
            Dict of artifact name → file path.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Extract XSD
        xsd_text = extract_xsd(netconf_source)

        # Step 2: Parse XSD into SchemaNode tree
        schema_tree = parse_xsd(xsd_text)

        # Step 3: Apply structural fixes
        fixes_applied = apply_all_fixes(schema_tree)

        # Step 4: Count schema elements
        stats = _count_stats(schema_tree)

        # Step 5: Generate artifacts
        artifacts: dict[str, str] = {}

        # JSON Schema (JSON variant)
        json_schema_path = str(output_dir / "junos-json-schema.json.gz")
        write_json_schema(schema_tree, json_schema_path, variant="json")
        artifacts["json-schema"] = json_schema_path

        # JSON Schema (YAML variant)
        yaml_schema_path = str(output_dir / "junos-yaml-schema.json.gz")
        write_json_schema(schema_tree, yaml_schema_path, variant="yaml")
        artifacts["yaml-schema"] = yaml_schema_path

        # Structure tree (compact schema for set-to-structured conversion)
        structure_tree_path = str(output_dir / "junos-structure-tree.json.gz")
        write_structure_tree(schema_tree, structure_tree_path)
        artifacts["structure-tree"] = structure_tree_path

        # Lark grammar
        # The grammar is built from the structure tree just written, not from
        # `schema_tree` directly, so that it is a function of the artefact that
        # ships beside it. Built from the XSD tree the two disagree -- the
        # writer cannot store `is_presence` on a node that has children, so
        # `groups` renders differently -- and `--regen-schema` would then turn
        # TestTheShippedGrammarIsTheGeneratorsOutput red on a correctly regenerated set.
        grammar_path = str(output_dir / "junos-set.lark.gz")
        write_lark_grammar(read_structure_tree(structure_tree_path), grammar_path)
        artifacts["lark-grammar"] = grammar_path

        # Metadata
        meta_path = str(output_dir / "junos-schema-meta.json.gz")
        _write_metadata(meta_path, stats, fixes_applied, _extract_junos_version(xsd_text))
        artifacts["metadata"] = meta_path

        return artifacts

    def build_from_xsd(
        self,
        xsd_text: str,
        output_dir: str | Path,
    ) -> dict[str, str]:
        """Build artifacts from already-extracted XSD text.

        Args:
            xsd_text: The XSD schema XML string.
            output_dir: Directory to write artifacts to.

        Returns:
            Dict of artifact name → file path.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        schema_tree = parse_xsd(xsd_text)
        fixes_applied = apply_all_fixes(schema_tree)
        stats = _count_stats(schema_tree)
        artifacts: dict[str, str] = {}

        json_schema_path = str(output_dir / "junos-json-schema.json.gz")
        write_json_schema(schema_tree, json_schema_path, variant="json")
        artifacts["json-schema"] = json_schema_path

        yaml_schema_path = str(output_dir / "junos-yaml-schema.json.gz")
        write_json_schema(schema_tree, yaml_schema_path, variant="yaml")
        artifacts["yaml-schema"] = yaml_schema_path

        structure_tree_path = str(output_dir / "junos-structure-tree.json.gz")
        write_structure_tree(schema_tree, structure_tree_path)
        artifacts["structure-tree"] = structure_tree_path

        # The grammar is built from the structure tree just written, not from
        # `schema_tree` directly, so that it is a function of the artefact that
        # ships beside it. Built from the XSD tree the two disagree -- the
        # writer cannot store `is_presence` on a node that has children, so
        # `groups` renders differently -- and `--regen-schema` would then turn
        # TestTheShippedGrammarIsTheGeneratorsOutput red on a correctly regenerated set.
        grammar_path = str(output_dir / "junos-set.lark.gz")
        write_lark_grammar(read_structure_tree(structure_tree_path), grammar_path)
        artifacts["lark-grammar"] = grammar_path

        meta_path = str(output_dir / "junos-schema-meta.json.gz")
        _write_metadata(meta_path, stats, fixes_applied, _extract_junos_version(xsd_text))
        artifacts["metadata"] = meta_path

        return artifacts


def _count_stats(root: SchemaNode) -> dict[str, int]:
    """Count schema tree statistics."""
    total = 0
    leaves = 0
    containers = 0
    lists = 0
    enum_count = 0

    stack = [root]
    while stack:
        node = stack.pop()
        total += 1
        if node.is_leaf:
            leaves += 1
        elif node.children:
            containers += 1
        if node.is_list:
            lists += 1
        if node.enums:
            enum_count += len(node.enums)
        stack.extend(node.children.values())

    return {
        "total_nodes": total,
        "leaf_nodes": leaves,
        "container_nodes": containers,
        "list_nodes": lists,
        "enum_values": enum_count,
    }


def _extract_junos_version(xsd_text: str) -> str:
    """Extract Junos version from XSD namespace declaration."""
    m = re.search(r'xmlns:junos="http://xml\.juniper\.net/junos/([^/"]+)/junos"', xsd_text)
    return m.group(1) if m else "unknown"


def _write_metadata(
    path: str,
    stats: dict[str, int],
    fixes_applied: int,
    junos_version: str = "unknown",
) -> None:
    """Write schema metadata file."""
    meta = {
        "junos_version": junos_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator_version": "0.2.0",
        "fixes_applied": fixes_applied,
        "fixes_registered": get_fix_count(),
        "stats": stats,
    }
    with open_artifact_write(path) as f:
        json.dump(meta, f, indent=2)
        f.write("\n")


# The flag tables. Both directions read them: `_serialize_node` writes every
# key here and `_deserialize_node` reads every key back. That was once only
# half true -- the reader was table-driven and the writer was an if/elif chain,
# so adding a flag took two edits that looked nothing alike and the comment
# claiming "in both directions" was false.

# Flags the structure tree stores as a plain boolean key.
_BOOL_FLAG_KEYS = {
    "nk": "nokeyword",
    "o": "oneliner",
    "tk": "transparent-list-key",
    "pk": "positional-key",
    "pkf": "positional-key-flat",
    "fd": "flat-dict",
    "frnk": "freeform-nk",
    # `homogeneous` on a container without a key -- `family` -- means the
    # device never tags the container and writes it merged with each child:
    # `inactive: family inet {`. See `junoscfg.display.passes_tag_to_child`.
    "h": "homogeneous",
    # `universal` marks a statement Junos accepts at every hierarchy level --
    # the four `apply-*` meta-statements, which no NETCONF XSD models. They are
    # declared once, on the root, and the generators splice them in. Adding
    # this key took one line here, which is the point of the tables.
    "u": "universal",
}

# The one key the writer guards. `oneliner` means "entry name and children on
# one line", which only a named list with children can be, and `xsd_fixes` sets
# the flag on nodes that are neither. The guard is declared here rather than
# buried in the writer, so the asymmetry it creates is readable: a node whose
# `oneliner` the guard drops comes back without it.
_GUARDED_BOOL_KEYS = {
    "o": lambda node: node.is_list and bool(node.children),
}


class _ValueFlag(NamedTuple):
    """A flag whose compact key carries a payload rather than a bare ``true``.

    ``encode`` turns the text after ``prefix`` into the JSON value, ``decode``
    turns it back. Adding one is a single entry here, read by both directions.
    """

    prefix: str
    encode: Callable[[str], Any]
    decode: Callable[[Any], str]


_VALUE_FLAG_KEYS: dict[str, _ValueFlag] = {
    # `transparent:interface` -> "t": "interface"
    "t": _ValueFlag("transparent:", str, str),
}


class _SerializeState:
    """Deduplication state for structure tree serialization."""

    def __init__(self) -> None:
        self.enum_index: dict[tuple[str, ...], int] = {}
        self.enum_table: list[list[str]] = []
        self.pattern_index: dict[str, int] = {}
        self.pattern_table: list[str] = []

    def intern_enums(self, enums: list[str]) -> int:
        """Return the dedup table index for an enum value set."""
        key = tuple(enums)
        idx = self.enum_index.get(key)
        if idx is None:
            idx = len(self.enum_table)
            self.enum_table.append(enums)
            self.enum_index[key] = idx
        return idx

    def intern_pattern(self, pattern: str, negated: bool) -> int:
        """Return the dedup table index for a pattern string.

        Negated patterns are stored with a ``!`` prefix.
        """
        stored = f"!{pattern}" if negated else pattern
        idx = self.pattern_index.get(stored)
        if idx is None:
            idx = len(self.pattern_table)
            self.pattern_table.append(stored)
            self.pattern_index[stored] = idx
        return idx


def _serialize_node(node: SchemaNode, state: _SerializeState) -> dict[str, Any]:
    """Serialize a SchemaNode to a compact dict for structure conversion.

    Compact format keys:
        c: children dict (name → child node)
        l: true if leaf
        p: true if presence
        L: true if named list (is_list and has children)
        ll: true if leaf-list (repeated leaf, always array in JSON)
        nk: true if nokeyword flag
        o: true if flat/oneliner entry (name + children on single line)
        t: transparent container child name (e.g. "interface")
        tk: true if transparent list key
        pk: true if positional key (nesting)
        pkf: true if positional key (flat/non-nesting)
        fd: true if flat dict element
        k: the entry's key fields in declared order, a choice of identifiers
           as a nested list; omitted where the one key is ``name``
        frnk: true if freeform nk key
        h: true if the XSD marks the node ``homogeneous``
        u: true if the statement is valid at every hierarchy level
        e: index into root _enums dedup table
        r: index into root _patterns dedup table
        m: true if mandatory field
        tr: XSD type reference
        atr: anonymization-only XSD type reference
    """
    d: dict[str, Any] = {}

    if node.is_leaf:
        d["l"] = True
    elif node.is_presence and not node.children:
        # Only mark as presence if truly empty (no children)
        d["p"] = True

    if node.is_list and not node.is_leaf:
        d["L"] = True
    if node.is_list and node.is_leaf:
        d["ll"] = True

    # Flags, off the same tables `_deserialize_node` reads.
    for key, flag in _BOOL_FLAG_KEYS.items():
        if flag not in node.flags:
            continue
        guard = _GUARDED_BOOL_KEYS.get(key)
        if guard is None or guard(node):
            d[key] = True

    for key, codec in _VALUE_FLAG_KEYS.items():
        for flag in sorted(node.flags):
            if flag.startswith(codec.prefix):
                d[key] = codec.encode(flag[len(codec.prefix) :])
                break

    # Field-level validation metadata
    if node.enums:
        d["e"] = state.intern_enums(node.enums)

    if node.pattern:
        d["r"] = state.intern_pattern(node.pattern, node.pattern_negated)

    if node.is_mandatory:
        d["m"] = True

    if node.type_ref:
        d["tr"] = node.type_ref

    if node.anonymization_type_ref:
        d["atr"] = node.anonymization_type_ref

    if node.key_fields:
        d["k"] = [list(f) if isinstance(f, tuple) else f for f in node.key_fields]

    if node.children:
        d["c"] = {name: _serialize_node(child, state) for name, child in node.children.items()}

    return d


def write_structure_tree(root: SchemaNode, output_path: str) -> None:
    """Serialize the SchemaNode tree to a compact JSON file.

    Used by the Structure class for set-to-structured conversion and
    field-level validation.  Contains hierarchy inference flags plus
    field-level metadata (enums, patterns, types, mandatory).

    Deduplication tables ``_enums`` and ``_patterns`` are stored at the
    root level to keep the artifact compact.
    """
    state = _SerializeState()
    data = _serialize_node(root, state)

    # Attach dedup tables at root level
    if state.enum_table:
        data["_enums"] = state.enum_table
    if state.pattern_table:
        data["_patterns"] = state.pattern_table

    with open_artifact_write(output_path) as f:
        f.write(json.dumps(data, separators=(",", ":")))
        f.write("\n")


def _deserialize_node(
    name: str,
    d: dict[str, Any],
    enums: list[list[str]],
    patterns: list[str],
) -> SchemaNode:
    """Rebuild one SchemaNode from its compact dict. Inverse of _serialize_node."""
    node = SchemaNode(name=name)

    node.is_leaf = bool(d.get("l"))
    node.is_presence = bool(d.get("p"))
    node.is_list = bool(d.get("L")) or bool(d.get("ll"))
    node.is_mandatory = bool(d.get("m"))
    node.type_ref = d.get("tr")
    node.anonymization_type_ref = d.get("atr")
    node.key_fields = tuple(tuple(f) if isinstance(f, list) else f for f in d.get("k", ()))

    if "e" in d:
        node.enums = list(enums[d["e"]])
    if "r" in d:
        stored = patterns[d["r"]]
        node.pattern_negated = stored.startswith("!")
        node.pattern = stored[1:] if node.pattern_negated else stored

    for key, flag in _BOOL_FLAG_KEYS.items():
        if d.get(key):
            node.flags.add(flag)
    for key, codec in _VALUE_FLAG_KEYS.items():
        if key in d:
            node.flags.add(codec.prefix + codec.decode(d[key]))

    for child_name, child in (d.get("c") or {}).items():
        node.children[child_name] = _deserialize_node(child_name, child, enums, patterns)

    return node


def read_structure_tree(path: str | Path) -> SchemaNode:
    """Rebuild a SchemaNode tree from a structure tree artifact.

    The inverse of :func:`write_structure_tree`, so a grammar can be rebuilt
    from the bundled artifacts when the XSD dump they came from is no longer
    to hand. :func:`junoscfg.validate.grammar_generator.generate_lark_grammar`
    reads only ``name``, ``children``, ``is_leaf``, ``is_list``,
    ``is_presence``, ``flags`` and ``type_ref``, all of which the format carries.

    What it does not carry, because ``_serialize_node`` never writes it. This
    is a lossy format, not a faithful copy; do not use this tree where any of
    these matter:

    - ``combinator``, which every node gets back as ``Combinator.CHOICE``.
    - ``is_key``, which comes back ``False``.
    - ``is_presence`` on a node that has children. The writer stores ``p``
      only for a childless node, so such a node returns as a plain container.
      In the 24.4R0 set shipped until 0.8.0 that was ``groups``, the one place
      a grammar rebuilt from this tree differed from one built straight off the
      XSD; 25.2R2 has no such node. ``ArtifactBuilder`` builds the grammar
      through this function regardless, so the two cannot drift.
    - any flag the XSD carried verbatim that is not in the writer's tables
      (``oneliner-plus``, …). The tables are
      ``_BOOL_FLAG_KEYS`` and ``_VALUE_FLAG_KEYS``, and both directions read
      them, so what is dropped is exactly what is not in them.
    - ``oneliner`` on a node that is not a list with children, which the
      writer guards away.
    - ``is_presence`` on a leaf, and ``pattern_negated`` with no ``pattern``.

    None of these reaches ``generate_lark_grammar``, which reads only ``name``,
    ``children``, ``is_leaf``, ``is_list``, ``is_presence``, ``type_ref``, the
    ``nokeyword``, ``freeform-nk`` and ``flat-dict`` flags, and
    ``key_fields`` -- all of which survive. ``type_ref`` is how a policy-algebra slot is told
    apart from every other value slot.

    Args:
        path: Path to a ``junos-structure-tree.json`` artifact.

    Returns:
        The tree rooted at ``configuration``.
    """
    data = json.loads(read_artifact_text(path))
    return _deserialize_node(
        "configuration", data, data.get("_enums", []), data.get("_patterns", [])
    )
