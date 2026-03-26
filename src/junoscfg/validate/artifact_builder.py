"""ArtifactBuilder: full pipeline from NETCONF dump to validation artifacts.

Orchestrates XSD extraction, parsing, fixes, and artifact generation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from junoscfg.validate.grammar_generator import write_lark_grammar
from junoscfg.validate.schema_generator import write_json_schema
from junoscfg.validate.schema_node import SchemaNode  # noqa: TC001
from junoscfg.validate.xsd_extractor import extract_xsd
from junoscfg.validate.xsd_fixes import apply_all_fixes, get_fix_count
from junoscfg.validate.xsd_parser import parse_xsd


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
        json_schema_path = str(output_dir / "junos-json-schema.json")
        write_json_schema(schema_tree, json_schema_path, variant="json")
        artifacts["json-schema"] = json_schema_path

        # JSON Schema (YAML variant)
        yaml_schema_path = str(output_dir / "junos-yaml-schema.json")
        write_json_schema(schema_tree, yaml_schema_path, variant="yaml")
        artifacts["yaml-schema"] = yaml_schema_path

        # Lark grammar
        grammar_path = str(output_dir / "junos-set.lark")
        write_lark_grammar(schema_tree, grammar_path)
        artifacts["lark-grammar"] = grammar_path

        # Structure tree (compact schema for set-to-structured conversion)
        structure_tree_path = str(output_dir / "junos-structure-tree.json")
        write_structure_tree(schema_tree, structure_tree_path)
        artifacts["structure-tree"] = structure_tree_path

        # Metadata
        meta_path = str(output_dir / "junos-schema-meta.json")
        _write_metadata(meta_path, stats, fixes_applied)
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

        json_schema_path = str(output_dir / "junos-json-schema.json")
        write_json_schema(schema_tree, json_schema_path, variant="json")
        artifacts["json-schema"] = json_schema_path

        yaml_schema_path = str(output_dir / "junos-yaml-schema.json")
        write_json_schema(schema_tree, yaml_schema_path, variant="yaml")
        artifacts["yaml-schema"] = yaml_schema_path

        grammar_path = str(output_dir / "junos-set.lark")
        write_lark_grammar(schema_tree, grammar_path)
        artifacts["lark-grammar"] = grammar_path

        structure_tree_path = str(output_dir / "junos-structure-tree.json")
        write_structure_tree(schema_tree, structure_tree_path)
        artifacts["structure-tree"] = structure_tree_path

        meta_path = str(output_dir / "junos-schema-meta.json")
        _write_metadata(meta_path, stats, fixes_applied)
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


def _write_metadata(
    path: str,
    stats: dict[str, int],
    fixes_applied: int,
) -> None:
    """Write schema metadata file."""
    meta = {
        "junos_version": "21.4R0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator_version": "0.2.0",
        "fixes_applied": fixes_applied,
        "fixes_registered": get_fix_count(),
        "stats": stats,
    }
    with open(path, "w") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")


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
        nk: true if nokeyword flag
        o: true if flat/oneliner entry (name + children on single line)
        t: transparent container child name (e.g. "interface")
        tk: true if transparent list key
        pk: true if positional key (nesting)
        pkf: true if positional key (flat/non-nesting)
        fd: true if flat dict element
        fe: {"k": key, "p": position} for flat entry config
        frnk: true if freeform nk key
        e: index into root _enums dedup table
        r: index into root _patterns dedup table
        m: true if mandatory field
        tr: XSD type reference
    """
    d: dict[str, Any] = {}

    if node.is_leaf:
        d["l"] = True
    elif node.is_presence and not node.children:
        # Only mark as presence if truly empty (no children)
        d["p"] = True

    if node.is_list and not node.is_leaf:
        d["L"] = True

    if "nokeyword" in node.flags:
        d["nk"] = True

    # Oneliner named lists: all tokens on single line
    if node.is_list and node.children and "oneliner" in node.flags:
        d["o"] = True

    # Conversion-hint flags (Group H)
    for flag in node.flags:
        if flag.startswith("transparent:"):
            d["t"] = flag.split(":", 1)[1]
        elif flag == "transparent-list-key":
            d["tk"] = True
        elif flag == "positional-key":
            d["pk"] = True
        elif flag == "positional-key-flat":
            d["pkf"] = True
        elif flag == "flat-dict":
            d["fd"] = True
        elif flag.startswith("flat-entry:"):
            _, key, position = flag.split(":", 2)
            d["fe"] = {"k": key, "p": position}
        elif flag == "freeform-nk":
            d["frnk"] = True

    # Field-level validation metadata
    if node.enums:
        d["e"] = state.intern_enums(node.enums)

    if node.pattern:
        d["r"] = state.intern_pattern(node.pattern, node.pattern_negated)

    if node.is_mandatory:
        d["m"] = True

    if node.type_ref:
        d["tr"] = node.type_ref

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

    with open(output_path, "w") as f:
        json.dump(data, f, separators=(",", ":"))
        f.write("\n")
