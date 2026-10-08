"""Generate JSON Schema from SchemaNode tree.

Produces Draft 7 JSON Schema for JSON and YAML configuration validation.
Currently STRUCTURAL only - validates hierarchy/nesting, not enum values or patterns.

Uses $defs/$ref for named types (type_ref) to avoid massive duplication.
Limits depth to keep output manageable for large schemas.
"""

from __future__ import annotations

import json
import re
from typing import Any

from junoscfg.display import (
    ENTRY_KEY_OVERRIDES,
    UNIVERSAL_STATEMENTS,
    open_artifact_write,
    statement_name_spellings,
)
from junoscfg.validate.schema_node import SchemaNode  # noqa: TC001

# Maximum recursion depth for schema generation.
# Beyond this, containers accept any object structure.
_MAX_DEPTH = 12

# The statements a configuration may carry at any hierarchy level. The
# generated schema names them as a `patternProperties` entry on every
# container: a property per container would be four names copied across
# 123,769 of them, and `additionalProperties: false` rejects them anywhere it
# does not say.
#
# `_fix_apply_statements` declares them on the root with the `universal` flag,
# but a tree built before that fix carries no such node, as the bundled one did
# not until 0.8.0. The kernel list is the floor, so junoscfg does not reject
# its own output for a configuration that carries `apply-groups` -- which all
# three real device configurations do -- whatever tree it runs on.
_UNIVERSAL_FLAG = "universal"


def _universal_properties(root: SchemaNode) -> dict[str, Any]:
    """The `patternProperties` entry for the universal statements, or nothing."""
    names = sorted(
        {name for name, node in root.children.items() if _UNIVERSAL_FLAG in node.flags}
        | set(UNIVERSAL_STATEMENTS)
    )
    return {"^(" + "|".join(re.escape(name) for name in names) + ")$": {}}


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
    universal = _universal_properties(root)
    defs: dict[str, Any] = {}
    seen_refs: set[str] = set()

    schema: dict[str, Any] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": f"Junos Configuration ({variant.upper()} format)",
        "description": "Validates Junos configuration hierarchy (structural only).",
        "type": "object",
        "properties": {
            "configuration": _node_to_schema(root, variant, 0, defs, seen_refs, universal),
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
                child_node, variant, 1, defs, seen_refs, universal
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
    universal: dict[str, Any],
) -> dict[str, Any]:
    """Convert a SchemaNode to its JSON Schema representation."""
    # Leaf node: accept any value type (structural only)
    if node.is_leaf:
        return {}  # Accept anything

    # Presence container: can be null (flag) or object
    if node.is_presence:
        # `[null]` is how a device renders a presence flag and what every
        # junoscfg rendering emits -- `"disable": [null]`, `"accept": [null]`.
        # Leaving the array out rejected eight statements in `examples
        # /router1.set` alone, all of them junoscfg's own output.
        return {
            "oneOf": [
                {"type": "null"},
                {"type": "string"},
                {"type": "array"},
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
            defs[ref_name] = _container_or_list_schema(
                node, variant, depth, defs, seen_refs, universal
            )
        return {"$ref": f"#/$defs/{ref_name}"}

    return _container_or_list_schema(node, variant, depth, defs, seen_refs, universal)


def _container_or_list_schema(
    node: SchemaNode,
    variant: str,
    depth: int,
    defs: dict[str, Any],
    seen_refs: set[str],
    universal: dict[str, Any],
) -> dict[str, Any]:
    """Generate schema for list or container nodes."""
    # List node: array of items
    if node.is_list and node.children:
        item_schema = _container_schema(node, variant, depth, defs, seen_refs, universal)
        # `anyOf`, not `oneOf`: a container accepts the bare-statement shapes
        # too, so an array matches both branches and `oneOf` -- which demands
        # exactly one -- rejected every list. These are alternatives, not
        # exclusive choices.
        return {
            "anyOf": [
                {"type": "array", "items": item_schema},
                item_schema,  # Also accept single object
            ]
        }

    # Container with children
    if node.children:
        return _container_schema(node, variant, depth, defs, seen_refs, universal)

    # Fallback: accept anything
    return {}


def _switch_spellings(name: str, node: SchemaNode) -> tuple[str, ...]:
    """The statement spellings *node* writes, if it is a folded on/off switch."""
    if not node.is_leaf or "nokeyword" not in node.flags or "freeform-nk" in node.flags:
        return ()
    return statement_name_spellings(name, node.enums or ())


_FLAT_ENTRY_PREFIX = "flat-entry:"


def _entry_keys(node: SchemaNode) -> tuple[str, ...]:
    """The properties a list entry may carry its key under.

    `name` for most, but a flat-entry list names its own key -- `route-filter`
    writes `address` -- and the set reader spells a few of them out, so a
    schema expecting `name` alone rejected every prefix list junoscfg
    produced. They are alternatives rather than a single answer: the same node
    reaches the schema from readers that disagree.
    """
    keys = ["name"]
    for flag in node.flags:
        if flag.startswith(_FLAT_ENTRY_PREFIX):
            keys.append(flag.split(":")[1])
    override = ENTRY_KEY_OVERRIDES.get(node.name)
    if override:
        keys.append(override)
    return tuple(dict.fromkeys(keys))


def _container_schema(
    node: SchemaNode,
    variant: str,
    depth: int,
    defs: dict[str, Any],
    seen_refs: set[str],
    universal: dict[str, Any],
) -> dict[str, Any]:
    """Generate schema for a container node with children."""
    properties: dict[str, Any] = {}

    for child_name, child_node in node.children.items():
        # Skip groups children (recursive reference to configuration)
        if child_name == "groups" and depth > 0:
            properties[child_name] = {"type": ["object", "array", "null"]}
        else:
            properties[child_name] = _node_to_schema(
                child_node, variant, depth + 1, defs, seen_refs, universal
            )
        # A folded on/off switch is written under its spelling, not under the
        # node name: the set reader emits `"disable": [null]`, so a container
        # that names only `enable-disable` rejects junoscfg's own output.
        for spelling in _switch_spellings(child_name, child_node):
            properties.setdefault(spelling, {})

    # A named list entry carries its key as `name`, which is how every
    # rendering writes it and how `set_input` reads it back. The XSD models the
    # key positionally, so only 4 of 24.4R0's 20,367 named lists have a `name`
    # child and the rest rejected junoscfg's own output -- every configuration
    # holding an interface, a policy or a BGP group.
    if node.is_list and node.children:
        for key in _entry_keys(node):
            properties.setdefault(key, {})

    # A container is also a statement: `set system services netconf ssh` and
    # `... interface lo0.0 passive` write the keyword alone, which every
    # rendering carries as `[null]`, so the type admits `null` and `array`
    # beside `object`. A type union keeps the schema navigable where a `oneOf`
    # wrapper would bury it -- but `properties` and `additionalProperties` are
    # object-only keywords, so an array form with no `items` bound nothing:
    # 43,331 `additionalProperties: false` nodes enforced nothing behind an
    # array wrapper and `{"configuration": "garbage"}` validated. The array
    # form carries `[null]` and leaf-list strings, never objects: across three
    # real device configurations every array of objects sits on a node the
    # tree marks as a list, and a list gets its items from
    # `_container_or_list_schema`. A bare string is not a container rendering.
    #
    # The exception is a transparent container. `groups` is written as its
    # child's list -- `group` entries directly -- so its array form carries
    # objects, bounded by that child's own schema rather than by nothing.
    transparent = next(
        (flag.split(":", 1)[1] for flag in node.flags if flag.startswith("transparent:")), None
    )
    items: dict[str, Any] = {"type": ["null", "string"]}
    if transparent and transparent in properties:
        items = {"anyOf": [{"type": ["null", "string"]}, properties[transparent]]}

    # No `required`. The XSD marks fields mandatory for a whole configuration,
    # and these 8,782 arrays were inert behind the array escape; live, they
    # reject every fragment -- `set system login user admin uid 2000` for want
    # of `class` -- which is what broke the first attempt at closing it.
    # Mandatory stays a field-validator warning.
    schema: dict[str, Any] = {
        "type": ["object", "null", "array"],
        "properties": properties,
        "additionalProperties": False,
        "items": items,
    }

    pattern_properties: dict[str, Any] = dict(universal)

    # `@` carries the attributes a device puts on an element -- the
    # `junos:commit-seconds` and friends that `| display json` emits and that
    # junoscfg's own converters round-trip. `field_validator` already skips
    # them by prefix; the schema has to name them or it rejects its own
    # output. Invisible until the array escape was closed.
    pattern_properties["^@"] = {}

    # YAML variant allows Ansible/meta keys
    if variant == "yaml":
        pattern_properties["^_ansible_"] = {}
        pattern_properties["^_meta_"] = {}

    if pattern_properties:
        schema["patternProperties"] = pattern_properties

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
    with open_artifact_write(output_path) as f:
        json.dump(schema, f, separators=(",", ":"))
        f.write("\n")
