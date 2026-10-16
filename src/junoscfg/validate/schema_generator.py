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
    entry_key_names,
    open_artifact_write,
    statement_name_spellings,
    universal_statements,
)
from junoscfg.validate.schema_node import SchemaNode, xml_name

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
# and the tree is authoritative: `junoscfg.display.universal_statements` names
# the ones it declares. A tree that declares none -- built before that fix, as
# the bundled one was until 0.8.0 -- gets the kernel's floor, so junoscfg does
# not reject its own output for a configuration that carries `apply-groups`,
# which all three real device configurations do. The grammar generator reads
# the flag alone; the two agree on every tree `junoscfg schema generate` builds,
# since it runs the fixes first. The floor here serves only a `SchemaNode` handed
# to this public function without them.


def _universal_properties(root: SchemaNode) -> dict[str, Any]:
    """The `patternProperties` entry for the universal statements, or nothing."""
    names = sorted(universal_statements(root))
    if not names:
        return {}
    return {"^(" + "|".join(re.escape(name) for name in names) + ")$": {}}


class _DefinitionContext:
    """One generation's bounded emitted-shape memo and named definitions.

    Object/depth identity avoids rescanning subtrees; definitions reuse the
    interned semantic shape instead, so separately allocated copies still
    share. A real named cycle is closed by the emission's active registration.
    Shapes containing cycle markers are not memoized under another ancestor.
    """

    def __init__(self, variant: str) -> None:
        self.variant = variant
        self.shapes: dict[tuple[Any, ...], int] = {}
        self.memo: dict[tuple[int, int], int] = {}
        self.definitions: dict[tuple[str, int], str] = {}
        self.active: dict[int, str] = {}
        self.names: set[str] = set()

    def _intern(self, value: tuple[Any, ...]) -> int:
        found = self.shapes.get(value)
        if found is None:
            found = len(self.shapes)
            self.shapes[value] = found
        return found

    def shape(self, node: SchemaNode, depth: int) -> int:
        return self._shape(node, depth, set())[0]

    def _shape(self, node: SchemaNode, depth: int, active: set[int]) -> tuple[int, bool]:
        # Match emission precedence: leaves and presence ignore depth;
        # containers at the cutoff are unconstrained, even when childless.
        if node.is_leaf:
            return self._intern(("any",)), False
        if node.is_presence:
            return self._intern(("presence",)), False
        if depth >= _MAX_DEPTH:
            return self._intern(("cutoff",)), False
        if not node.children:
            return self._intern(("any",)), False
        identity = id(node)
        if node.type_ref and identity in active:
            return self._intern(("recursive", node.type_ref)), True
        key = (identity, depth)
        cached = self.memo.get(key)
        if cached is not None:
            return cached, False
        if node.type_ref:
            active.add(identity)
        properties: dict[str, int] = {}
        cyclic = False
        try:
            for name, child in node.children.items():
                if name == "groups" and depth > 0:
                    child_shape = self._intern(("suppressed-groups",))
                else:
                    child_shape, child_cyclic = self._shape(child, depth + 1, active)
                    cyclic |= child_cyclic
                properties[_property_name(name, child, self.variant)] = child_shape
                for spelling in _switch_spellings(name, child):
                    properties.setdefault(spelling, self._intern(("any",)))
            if node.is_list:
                for name in sorted(entry_key_names(node)):
                    spelled = _key_property(node, name, self.variant)
                    properties.setdefault(spelled, self._intern(("any",)))
            transparent = next(
                (flag.split(":", 1)[1] for flag in node.flags if flag.startswith("transparent:")),
                None,
            )
            group_items = (
                properties[transparent]
                if node.name == "groups" and transparent and transparent in properties
                else None
            )
            shape = self._intern(
                (
                    "list" if node.is_list else "container",
                    tuple(sorted(properties.items())),
                    group_items,
                )
            )
        finally:
            if node.type_ref:
                active.remove(identity)
        if not cyclic:
            self.memo[key] = shape
        return shape, cyclic

    def register(self, type_ref: str, shape: int) -> tuple[str, bool]:
        key = (type_ref, shape)
        previous = self.definitions.get(key)
        if previous is not None:
            return previous, False
        name = type_ref
        suffix = 2
        while name in self.names:
            name = f"{type_ref}__{suffix}"
            suffix += 1
        self.names.add(name)
        self.definitions[key] = name
        return name, True


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
    context = _DefinitionContext(variant)

    schema: dict[str, Any] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": f"Junos Configuration ({variant.upper()} format)",
        "description": "Validates Junos configuration hierarchy (structural only).",
        "type": "object",
        "properties": {
            "configuration": _node_to_schema(root, variant, 0, defs, context, universal),
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
            schema["properties"][_property_name(child_name, child_node, variant)] = _node_to_schema(
                child_node, variant, 1, defs, context, universal
            )

    if defs:
        schema["$defs"] = defs

    return schema


def _node_to_schema(
    node: SchemaNode,
    variant: str,
    depth: int,
    defs: dict[str, Any],
    context: _DefinitionContext,
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
        active = context.active.get(id(node))
        if active is not None:
            return {"$ref": f"#/$defs/{active}"}
        ref_name, fresh = context.register(node.type_ref, context.shape(node, depth))
        if fresh:
            # Register before children, so a real graph cycle closes on this
            # context instead of recursively creating depth variants.
            defs[ref_name] = {}
            context.active[id(node)] = ref_name
            try:
                defs[ref_name] = _container_or_list_schema(
                    node, variant, depth, defs, context, universal
                )
            finally:
                del context.active[id(node)]
        return {"$ref": f"#/$defs/{ref_name}"}

    return _container_or_list_schema(node, variant, depth, defs, context, universal)


def _container_or_list_schema(
    node: SchemaNode,
    variant: str,
    depth: int,
    defs: dict[str, Any],
    context: _DefinitionContext,
    universal: dict[str, Any],
) -> dict[str, Any]:
    """Generate schema for list or container nodes."""
    # List node: array of items
    if node.is_list and node.children:
        item_schema = _container_schema(node, variant, depth, defs, context, universal)
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
        return _container_schema(node, variant, depth, defs, context, universal)

    # Fallback: accept anything
    return {}


def _property_name(name: str, node: SchemaNode, variant: str) -> str:
    """The key *node* takes in a document of *variant*.

    JSON is the device's own spelling, so a node a fix renamed to its CLI
    keyword is named as the device writes it (`end-range`, `ieee-802.3ad`);
    YAML is junoscfg's IR, which holds the keyword (spec
    schema-pipeline/conversion-hints).
    """
    return (xml_name(node) or name) if variant == "json" else name


def _key_property(node: SchemaNode, key: str, variant: str) -> str:
    """The key a list entry's key field *key* takes in a document of *variant*."""
    child = node.children.get(key)
    return key if child is None else _property_name(key, child, variant)


def _switch_spellings(name: str, node: SchemaNode) -> tuple[str, ...]:
    """The statement spellings *node* writes, if it is a folded on/off switch."""
    if not node.is_leaf or "nokeyword" not in node.flags or "freeform-nk" in node.flags:
        return ()
    return statement_name_spellings(name, node.enums or ())


def _container_schema(
    node: SchemaNode,
    variant: str,
    depth: int,
    defs: dict[str, Any],
    context: _DefinitionContext,
    universal: dict[str, Any],
) -> dict[str, Any]:
    """Generate schema for a container node with children."""
    properties: dict[str, Any] = {}

    for child_name, child_node in node.children.items():
        # Skip groups children (recursive reference to configuration)
        if child_name == "groups" and depth > 0:
            properties[child_name] = {"type": ["object", "array", "null"]}
        else:
            properties[_property_name(child_name, child_node, variant)] = _node_to_schema(
                child_node, variant, depth + 1, defs, context, universal
            )
        # A folded on/off switch is written under its spelling, not under the
        # node name: the set reader emits `"disable": [null]`, so a container
        # that names only `enable-disable` rejects junoscfg's own output.
        for spelling in _switch_spellings(child_name, child_node):
            properties.setdefault(spelling, {})

    # A list entry carries its key fields, which the parser keeps as children
    # in declared order: `name` for most, `list-type` and `list-name` for an
    # AS-list reference. A list the XSD declares no identifier for -- one a fix
    # built, such as `groups`' `group` -- is keyed `name` all the same.
    if node.is_list and node.children:
        for key in sorted(entry_key_names(node)):
            properties.setdefault(_key_property(node, key, variant), {})

    # A container is also a statement: `set system services netconf ssh` and
    # `... interface lo0.0 passive` write the keyword alone, which every
    # rendering carries as `[null]`, so the type admits `null` and `array`
    # beside `object`. A type union keeps the schema navigable where a `oneOf`
    # wrapper would bury it -- but `properties` and `additionalProperties` are
    # object-only keywords, so an array form with no `items` bound nothing:
    # every `additionalProperties: false` node -- 52,219 in the 25.2R2
    # artifact -- enforced nothing behind an array wrapper and
    # `{"configuration": "garbage"}` validated. The array
    # form carries `[null]` and leaf-list strings, never objects: across three
    # real device configurations every array of objects sits on a node the
    # tree marks as a list, and a list gets its items from
    # `_container_or_list_schema`. A bare string is not a container rendering.
    #
    # The one exception is `groups`. It is written as its child's list --
    # `group` entries directly -- so its array form carries objects, bounded
    # by that child's own schema rather than by nothing. It is the only
    # container whose JSON rendering drops the wrapper: the other 186 nodes
    # carrying a `transparent:` flag (`interfaces`, `vlans`,
    # `routing-instances`, the UFD `group`, ...) are transparent in a *set*
    # command and keep their wrapper in JSON -- `{"interfaces": {"interface":
    # [...]}}` -- so an array under them is a shape no device and no converter
    # emits. Applying the branch to all 187 let `{"interfaces": [{...}]}`
    # validate; the fresh review of this change caught it.
    transparent = next(
        (flag.split(":", 1)[1] for flag in node.flags if flag.startswith("transparent:")), None
    )
    items: dict[str, Any] = {"type": ["null", "string"]}
    if node.name == "groups" and transparent and transparent in properties:
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
        f.write(json.dumps(schema, separators=(",", ":")))
        f.write("\n")
