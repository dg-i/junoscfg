"""Generate Lark grammar from SchemaNode tree.

Produces a Lark grammar for validating/parsing set commands.
Currently STRUCTURAL only - all leaf values accept any token.

Uses a two-pass approach:
1. Walk the schema tree, collecting rule alternatives into a merged map
   (same-named nodes at different tree depths merge into one rule)
2. Emit the final Lark grammar from the merged map

Named list nodes (is_list=True with children) get a VALUE token prepended
to capture the entry name (e.g., policy-statement NAME, term NAME).
"""

from __future__ import annotations

import re

from junoscfg.validate.schema_node import SchemaNode  # noqa: TC001

# Elements whose values can be quoted strings in set commands
_QUOTED_FIELDS = frozenset(
    {
        "description",
        "message",
        "as-path-prepend",
        "tcp-flags",
        "full-name",
        "location",
        "contact",
        "apply-path",
        "name",  # in snmp context and license key context
        "ssh-dss",
        "ssh-ecdsa",
        "ssh-ed25519",
        "ssh-rsa",
    }
)

# Lark-safe name mapping for special characters
_NAME_ESCAPES = {
    "=": "eq_literal",
    "+": "plus_literal",
    "-": "minus_literal",
    "*": "star_literal",
    "__wildcard__": "wildcard_arg",
}


def _safe_rule_name(name: str) -> str:
    """Convert an element name to a valid Lark rule name."""
    if name in _NAME_ESCAPES:
        return _NAME_ESCAPES[name]
    # Replace non-alphanumeric with underscore
    safe = re.sub(r"[^a-zA-Z0-9]", "_", name)
    # Ensure it starts with a letter
    if safe and safe[0].isdigit():
        safe = "n" + safe
    # Avoid empty names
    if not safe:
        safe = "unnamed"
    return safe


class _RuleInfo:
    """Accumulated info for a single Lark rule (may be merged from multiple nodes)."""

    __slots__ = ("alts", "is_named_list", "has_non_list")

    def __init__(self) -> None:
        self.alts: set[str] = set()
        self.is_named_list: bool = False
        self.has_non_list: bool = False


def generate_lark_grammar(root: SchemaNode) -> str:
    """Generate a Lark grammar from a SchemaNode tree.

    Args:
        root: The schema tree rooted at 'configuration'.

    Returns:
        Lark grammar string.
    """
    # Pass 1: collect all rule definitions (merged by rule name)
    rule_map: dict[str, _RuleInfo] = {}
    visited: set[int] = set()  # id(node) to prevent infinite recursion
    _collect_rules(root, rule_map, visited)

    # Pass 2: emit grammar
    lines: list[str] = []

    # Header
    lines.append("// Junos set command grammar (auto-generated, structural only)")
    lines.append("// Validates: set <path> [value]")
    lines.append("")
    lines.append("start: SET configuration")
    lines.append("")

    # Emit rules in stable order
    for rule_name in sorted(rule_map):
        info = rule_map[rule_name]
        alts = sorted(info.alts)
        body = " | ".join(alts)

        if info.is_named_list and not info.has_non_list:
            # Non-conflicting named list: VALUE captures entry name
            lines.append(f"{rule_name}: VALUE ({body})*")
        else:
            # Regular container or conflicting named list
            lines.append(f"{rule_name}: {body}")

        lines.append("")

    # Footer: terminals
    lines.append("// Terminals")
    lines.append('SET: "set"')
    lines.append('DEACTIVATE: "deactivate"')
    lines.append("VALUE: /\\S+/")
    lines.append('QUOTED: /"[^"]*"/')
    lines.append("QUOTED_OR_VALUE: QUOTED | VALUE")
    lines.append("")
    lines.append("// Whitespace handling")
    lines.append("%import common.WS")
    lines.append("%ignore WS")
    lines.append("")

    return "\n".join(lines)


def _collect_rules(
    node: SchemaNode,
    rule_map: dict[str, _RuleInfo],
    visited: set[int],
) -> None:
    """Recursively collect rule definitions from the schema tree.

    Uses id(node) for dedup to handle shared schema nodes correctly.
    Same-named rules from different tree locations merge their alternatives.
    """
    node_id = id(node)
    if node_id in visited:
        return
    visited.add(node_id)

    if not node.children:
        # Leaf or presence — no rule needed (handled inline by parent)
        return

    rule_name = _safe_rule_name(node.name)

    # Build child alternatives
    child_alts: list[str] = []
    for child_name, child_node in node.children.items():
        child_ref = _child_reference(child_name, child_node)
        child_alts.append(child_ref)

    if child_alts:
        # Merge into rule map
        if rule_name not in rule_map:
            rule_map[rule_name] = _RuleInfo()
        info = rule_map[rule_name]
        info.alts.update(child_alts)
        if node.is_list:
            info.is_named_list = True
        else:
            info.has_non_list = True

    # Recurse into children
    for child_node in node.children.values():
        _collect_rules(child_node, rule_map, visited)


def _child_reference(name: str, node: SchemaNode) -> str:
    """Generate the Lark expression for referencing a child node."""
    safe_name = _safe_rule_name(name)

    # Determine the keyword token
    if name in _NAME_ESCAPES:
        keyword = f'"{_NAME_ESCAPES[name]}"'
    elif name.startswith("$"):
        # Variable placeholder - accept any value
        return "VALUE"
    else:
        keyword = f'"{name}"'

    # Leaf nodes
    if node.is_leaf:
        if name in _QUOTED_FIELDS:
            return f"{keyword} QUOTED_OR_VALUE"
        if "nokeyword" in node.flags:
            return "VALUE"  # No keyword, just a value
        return f"{keyword} VALUE"

    # Presence containers (no value)
    if node.is_presence:
        return keyword

    # Containers with children
    if node.children:
        return f"{keyword} {safe_name}"

    return keyword


def write_lark_grammar(root: SchemaNode, output_path: str) -> None:
    """Generate and write a Lark grammar file.

    Args:
        root: SchemaNode tree root.
        output_path: Path to write the grammar.
    """
    grammar = generate_lark_grammar(root)
    with open(output_path, "w") as f:
        f.write(grammar)
        f.write("\n")
