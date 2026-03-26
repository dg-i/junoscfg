"""Schema-guided tree walker for anonymization.

Adapted from :class:`~junoscfg.convert.field_validator.FieldValidator._walk`.
Walks the dict IR and schema tree in parallel, applying anonymization rules
to leaf values.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from junoscfg.anonymize.path_filter import PathFilter

if TYPE_CHECKING:
    from junoscfg.anonymize.config import AnonymizeConfig
    from junoscfg.anonymize.rules import Rule


def walk(
    ir: dict[str, Any],
    rules: list[Rule],
    config: AnonymizeConfig,
) -> None:
    """Walk the IR in-place, applying anonymization rules to matching leaves.

    Args:
        ir: The full IR dict (mutated in-place).
        rules: Ordered list of active rules.
        config: Anonymization config (for include/exclude filters, log level).
    """
    from junoscfg.display.constants import load_schema_tree

    schema = load_schema_tree()
    if not schema:
        return

    path_filter = PathFilter(config.include, config.exclude)
    log_debug = config.log_level == "debug"

    # Navigate to configuration node in schema
    schema_root = schema.get("c", {}).get("configuration", schema)

    # The IR is {"configuration": {...}} — walk inside it
    cfg = ir.get("configuration")
    if cfg is None:
        # Try walking IR directly if it's not wrapped
        _walk_node(ir, schema_root, [], rules, path_filter, log_debug)
    else:
        _walk_node(cfg, schema_root, [], rules, path_filter, log_debug)


def _walk_node(
    obj: Any,
    schema_node: dict[str, Any] | None,
    path: list[str],
    rules: list[Rule],
    path_filter: PathFilter,
    log_debug: bool,
) -> None:
    """Recursively walk the IR dict, applying rules to leaves."""
    if obj is None or schema_node is None:
        return

    if isinstance(obj, dict):
        children = schema_node.get("c", {})
        is_named_list = bool(schema_node.get("L"))

        for key, value in list(obj.items()):
            # Skip attribute keys (@ prefix)
            if key.startswith("@"):
                continue

            child_schema = children.get(key)

            # Handle transparent containers
            if child_schema and child_schema.get("t"):
                transparent_child = child_schema["t"]
                tc_children = child_schema.get("c", {})
                inner_schema = tc_children.get(transparent_child)
                if isinstance(value, dict) and transparent_child in value:
                    value = value[transparent_child]
                if isinstance(value, list) and inner_schema:
                    for item in value:
                        path.append(key)
                        _walk_node(item, inner_schema, path, rules, path_filter, log_debug)
                        path.pop()
                    continue
                elif isinstance(value, dict) and inner_schema:
                    path.append(key)
                    _walk_node(value, inner_schema, path, rules, path_filter, log_debug)
                    path.pop()
                    continue

            # Named list key field: "name" inside a named list item.
            # The schema doesn't list "name" as an explicit child — it's
            # the implicit key. Synthesize a leaf schema node so rules
            # can inspect the value. Use the list node's tr if available.
            if is_named_list and key == "name" and (child_schema is None or child_schema == {}):
                path.append(key)
                if path_filter.matches(path):
                    synthetic_schema = {"l": True}
                    parent_tr = schema_node.get("tr")
                    if parent_tr:
                        synthetic_schema["tr"] = parent_tr
                    _anonymize_leaf(obj, key, value, synthetic_schema, path, rules, log_debug)
                path.pop()
                continue

            if child_schema is None:
                continue

            # Named list (L flag)
            if child_schema.get("L"):
                if isinstance(value, list):
                    for item in value:
                        path.append(key)
                        _walk_node(item, child_schema, path, rules, path_filter, log_debug)
                        path.pop()
                    continue
                elif isinstance(value, dict):
                    path.append(key)
                    _walk_node(value, child_schema, path, rules, path_filter, log_debug)
                    path.pop()
                    continue

            # Leaf node — apply anonymization rules
            if child_schema.get("l"):
                path.append(key)
                if path_filter.matches(path):
                    _anonymize_leaf(obj, key, value, child_schema, path, rules, log_debug)
                path.pop()
            # Container — recurse
            elif isinstance(value, dict):
                path.append(key)
                _walk_node(value, child_schema, path, rules, path_filter, log_debug)
                path.pop()

    elif isinstance(obj, list):
        for item in obj:
            _walk_node(item, schema_node, path, rules, path_filter, log_debug)


def _anonymize_leaf(
    parent: dict[str, Any],
    key: str,
    value: Any,
    schema_node: dict[str, Any],
    path: list[str],
    rules: list[Rule],
    log_debug: bool,
) -> None:
    """Try each rule against a leaf value; first match wins."""
    if value is None or value is True or value == "":
        return

    if isinstance(value, list):
        new_list = []
        for item in value:
            replaced = _try_rules(item, schema_node, path, rules, log_debug)
            new_list.append(replaced)
        parent[key] = new_list
        return

    replaced = _try_rules(value, schema_node, path, rules, log_debug)
    if replaced is not value:
        parent[key] = replaced


def _try_rules(
    value: Any,
    schema_node: dict[str, Any],
    path: list[str],
    rules: list[Rule],
    log_debug: bool,
) -> Any:
    """Apply the first matching rule to *value* and return the result."""
    str_value = str(value)
    for rule in rules:
        if rule.matches(str_value, schema_node, path):
            result = rule.transform(str_value)
            if log_debug:
                dot_path = ".".join(path)
                print(
                    f"anonymize: [{rule.name}] {dot_path}: {str_value!r} -> {result!r}",
                    file=sys.stderr,
                )
            return result
    return value
