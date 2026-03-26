"""Generate JSON Schema from SchemaNode tree.

Produces Draft 7 JSON Schema for JSON and YAML configuration validation.
Currently STRUCTURAL only - validates hierarchy/nesting, not enum values or patterns.

Uses $defs/$ref for named types (type_ref) to avoid massive duplication.
Limits depth to keep output manageable for large schemas.
"""

from __future__ import annotations

import json
from typing import Any

from junoscfg.validate.schema_node import SchemaNode  # noqa: TC001

# Maximum recursion depth for schema generation.
# Beyond this, containers accept any object structure.
_MAX_DEPTH = 12


def generate_json_schema(
    root: SchemaNode,
    variant: str = "json",
) -> dict[str, Any]:
    """Generate a JSON Schema (Draft 7) from a SchemaNode tree.

    Args:
        root: The schema tree rooted at 'configuration'.
        variant: "json" for strict JSON, "yaml" for YAML (allows _ansible_*/_meta_*).

    Returns:
        A JSON Schema dict.
    """
    defs: dict[str, Any] = {}
    seen_refs: set[str] = set()

    schema: dict[str, Any] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": f"Junos Configuration ({variant.upper()} format)",
        "description": "Validates Junos configuration hierarchy (structural only).",
        "type": "object",
        "properties": {
            "configuration": _node_to_schema(root, variant, 0, defs, seen_refs),
        },
        "additionalProperties": False,
    }

    # Also accept configs without the "configuration" wrapper
    for child_name, child_node in root.children.items():
        # Skip groups (recursive, would cause huge expansion)
        if child_name == "groups":
            schema["properties"][child_name] = {
                "type": ["object", "array", "null"],
            }
        else:
            schema["properties"][child_name] = _node_to_schema(
                child_node, variant, 1, defs, seen_refs
            )

    if defs:
        schema["$defs"] = defs

    return schema


def _node_to_schema(
    node: SchemaNode,
    variant: str,
    depth: int,
    defs: dict[str, Any],
    seen_refs: set[str],
) -> dict[str, Any]:
    """Convert a SchemaNode to its JSON Schema representation."""
    # Leaf node: accept any value type (structural only)
    if node.is_leaf:
        return {}  # Accept anything

    # Presence container: can be null (flag) or object
    if node.is_presence:
        return {
            "oneOf": [
                {"type": "null"},
                {"type": "string"},
                {"type": "object", "additionalProperties": True},
            ]
        }

    # Depth limit: accept any object beyond max depth
    if depth >= _MAX_DEPTH:
        return {"type": ["object", "string", "number", "boolean", "null", "array"]}

    # If this node has a type_ref, use $defs/$ref for deduplication
    if node.type_ref and node.children:
        ref_name = node.type_ref
        if ref_name not in seen_refs:
            seen_refs.add(ref_name)
            # Generate the def inline (not yet recursive-safe, but type_ref stops recursion)
            defs[ref_name] = _container_or_list_schema(node, variant, depth, defs, seen_refs)
        return {"$ref": f"#/$defs/{ref_name}"}

    return _container_or_list_schema(node, variant, depth, defs, seen_refs)


def _container_or_list_schema(
    node: SchemaNode,
    variant: str,
    depth: int,
    defs: dict[str, Any],
    seen_refs: set[str],
) -> dict[str, Any]:
    """Generate schema for list or container nodes."""
    # List node: array of items
    if node.is_list and node.children:
        item_schema = _container_schema(node, variant, depth, defs, seen_refs)
        return {
            "oneOf": [
                {"type": "array", "items": item_schema},
                item_schema,  # Also accept single object
            ]
        }

    # Container with children
    if node.children:
        return _container_schema(node, variant, depth, defs, seen_refs)

    # Fallback: accept anything
    return {}


def _container_schema(
    node: SchemaNode,
    variant: str,
    depth: int,
    defs: dict[str, Any],
    seen_refs: set[str],
) -> dict[str, Any]:
    """Generate schema for a container node with children."""
    properties: dict[str, Any] = {}
    required: list[str] = []

    for child_name, child_node in node.children.items():
        # Skip groups children (recursive reference to configuration)
        if child_name == "groups" and depth > 0:
            properties[child_name] = {"type": ["object", "array", "null"]}
        else:
            properties[child_name] = _node_to_schema(
                child_node, variant, depth + 1, defs, seen_refs
            )
        if child_node.is_mandatory:
            required.append(child_name)

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }

    if required:
        schema["required"] = sorted(required)

    # YAML variant allows Ansible/meta keys
    if variant == "yaml":
        schema["patternProperties"] = {
            "^_ansible_": {},
            "^_meta_": {},
        }

    return schema


def write_json_schema(
    root: SchemaNode,
    output_path: str,
    variant: str = "json",
) -> None:
    """Generate and write a JSON Schema file.

    Args:
        root: SchemaNode tree root.
        output_path: Path to write the JSON Schema.
        variant: "json" or "yaml".
    """
    schema = generate_json_schema(root, variant)
    with open(output_path, "w") as f:
        json.dump(schema, f, separators=(",", ":"))
        f.write("\n")
