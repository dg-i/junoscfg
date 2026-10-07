"""Generate Lark grammar from SchemaNode tree.

Produces a Lark grammar for validating/parsing set commands.
Currently STRUCTURAL only - all leaf values accept any token.

Uses a two-pass approach:
1. Walk the schema tree, collecting rule alternatives into a merged map
   (same-named nodes at different tree depths merge into one rule)
2. Emit the final Lark grammar from the merged map

Named list nodes (is_list=True with children) get a VALUE token prepended
to capture the entry name (e.g., policy-statement NAME, term NAME), and are
kept in a rule of their own so that a same-named container elsewhere in the
tree cannot merge the entry name away.
"""

from __future__ import annotations

import re

from junoscfg.validate.schema_node import SchemaNode  # noqa: TC001

# Every leaf value may be quoted, so there is no list of which ones. Junos
# quotes any value holding a space, and a real device configuration puts a
# nested `set` command inside `event-options policy <n> then
# change-configuration commands "..."`. The former hard-coded list of 13 names
# left every other such value unparseable.

# Lark-safe name mapping for special characters
_NAME_ESCAPES = {
    "=": "eq_literal",
    "+": "plus_literal",
    "-": "minus_literal",
    "*": "star_literal",
    "__wildcard__": "wildcard_arg",
}


# Names the grammar itself uses. A schema element called `start` would
# otherwise emit a second `start:` rule and the whole grammar stops compiling,
# which is what happened: Junos has an element `start` -- it is `start-options`
# that is its child, not the collision -- so every bundled grammar from the
# 24.4 migration until the artefact was rebuilt was invalid. Set validation did
# not pass silently; `SetValidator` raised and the CLI exited 3.
_RESERVED_RULE_NAMES = {"start"}

# Rules are merged by name across the whole tree, which keeps the grammar a
# few thousand rules instead of one per path. A named list and a plain
# container that happen to share a name must not merge, though: the merged
# rule loses the entry-name slot, and every `set` line addressing a list entry
# stops parsing. `user` is both a list under `system login` and a container
# under `snmp`, and that one collision rejected most of a valid config. List
# nodes therefore get their own rule. The suffix is collision-free by
# measurement, not by construction: `_safe_rule_name` maps each non-alphanumeric
# to one underscore and does not collapse runs, so `a--b` would give `a__b` --
# but no element name carries two consecutive non-alphanumerics. Checked over
# every name in the bundled 24.4R0 (10,958) and in the 23.2R2, 23.4R2 and
# 25.2R2 dumps (10,840 / 10,105 / 10,455): zero produce a doubled underscore.
_LIST_RULE_SUFFIX = "__list"


def _safe_rule_name(name: str) -> str:
    """Convert an element name to a valid Lark rule name.

    Lark reads a name containing an uppercase letter as a *terminal*, not a
    rule, so the result is lowercased: Junos has elements such as
    `jnx-tel-RE-local-interfaces-stats`, which produced
    `jnx_tel_RE_local_...` and an unparseable grammar.
    """
    if name in _NAME_ESCAPES:
        return _NAME_ESCAPES[name]
    # Replace non-alphanumeric with underscore, and lowercase: an uppercase
    # letter anywhere makes Lark treat the name as a terminal.
    safe = re.sub(r"[^a-zA-Z0-9]", "_", name).lower()
    # Ensure it starts with a letter
    if safe and safe[0].isdigit():
        safe = "n" + safe
    # Avoid empty names
    if not safe:
        safe = "unnamed"
    if safe in _RESERVED_RULE_NAMES:
        safe = f"{safe}_element"
    return safe


def _rule_name_for(name: str, node: SchemaNode) -> str:
    """Return the rule name for a node, keeping named lists in their own rule."""
    base = _safe_rule_name(name)
    if node.is_list and node.children:
        return f"{base}{_LIST_RULE_SUFFIX}"
    return base


class _RuleInfo:
    """Accumulated info for a single Lark rule (may be merged from multiple nodes)."""

    __slots__ = ("alts", "is_named_list", "either_order")

    def __init__(self) -> None:
        self.alts: set[str] = set()
        self.is_named_list: bool = False
        # A oneliner list whose children are all bare keywords may write them
        # before the entry name or after it; see `generate_lark_grammar`.
        self.either_order: bool = False


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

        if info.is_named_list and info.either_order:
            # A oneliner list whose children are all bare keywords takes them
            # on either side of the entry name, and nothing in the schema says
            # which: `community add COMM-A` puts the keyword first, while
            # `flag all detail` and `from source-address 10/8 except` put it
            # last. Across three real device configurations the first form
            # alone accounted for 343 of 507 rejected lines, and assuming it
            # universally was worse than assuming it never happened -- that
            # took 7.1% rejected to 30.4%. Accepting both costs 1.4s of
            # grammar load and takes 7.1% to 2.3%.
            lines.append(f"{rule_name}: QUOTED_OR_VALUE ({body})? | ({body}) QUOTED_OR_VALUE")
        elif info.is_named_list:
            # Named list: VALUE captures the entry name. Only list nodes reach
            # this rule name, so the slot can no longer be merged away.
            #
            # The entry name is QUOTED_OR_VALUE, not VALUE: `ssh-ed25519` is
            # itself a list, so the key is the entry name, and a key is quoted
            # and contains spaces. VALUE is /\S+/ and cannot match one.
            #
            # One continuation, not a repetition. `(...)*` here would let a
            # line carry several settings after the entry name --
            # `set system ntp server 198.51.100.1 version 4 prefer` -- but it
            # makes the grammar ambiguous enough to cost 228 ms a line against
            # 4 ms, so a 5,000-line configuration takes 19 minutes instead of
            # 18 seconds. It also let a bare VALUE alternative absorb any run
            # of unknown tokens. Lark's `~0..n` range is not a middle way: it
            # expands combinatorially and does not finish compiling.
            lines.append(f"{rule_name}: QUOTED_OR_VALUE ({body})?")
        else:
            lines.append(f"{rule_name}: {body}")

        lines.append("")

    # Footer holding the terminals
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

    rule_name = _rule_name_for(node.name, node)

    # Build child alternatives
    child_alts: list[str] = []
    for child_name, child_node in node.children.items():
        spliced = f"transparent:{child_name}" in node.flags
        child_ref = _child_reference(child_name, child_node, spliced=spliced)
        child_alts.append(child_ref)

    if child_alts:
        # Merge into rule map
        if rule_name not in rule_map:
            rule_map[rule_name] = _RuleInfo()
        info = rule_map[rule_name]
        info.alts.update(child_alts)
        if node.is_list:
            info.is_named_list = True
            if (
                "oneliner" in node.flags
                and node.children
                and all(c.is_presence and not c.children for c in node.children.values())
            ):
                info.either_order = True

    # Recurse into children
    for child_node in node.children.values():
        _collect_rules(child_node, rule_map, visited)


def _child_reference(name: str, node: SchemaNode, *, spliced: bool = False) -> str:
    """Generate the Lark expression for referencing a child node.

    ``spliced`` says the parent carries ``transparent:<name>``, so this child's
    own name is not written in a set command.
    """
    safe_name = _rule_name_for(name, node)

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
        if "nokeyword" in node.flags and "freeform-nk" not in node.flags:
            return "QUOTED_OR_VALUE"  # No keyword, just a value
        # `freeform-nk` marks a node carrying `nokeyword` only so its value is
        # validated as freeform; `_fix_freeform_nk_keys` says it is still
        # "treated as a normal keyword in conversion". Reading the bare
        # `nokeyword` here rejected `set interfaces ge-0/0/1 unit 0 vlan-id
        # 100`, which is every VLAN-bearing configuration. In 24.4R0 the flag
        # is on `vlan-id` and `vlan-name` only.
        return f"{keyword} QUOTED_OR_VALUE"

    # Presence containers (no value)
    if node.is_presence:
        if "nokeyword" in node.flags:
            # A nokeyword presence node is a hidden list: the token is the
            # entry name and the element name is never written.
            # `set policy-options prefix-list PL-A 10.0.0.0/8` writes no
            # `prefix-list-item`, and junoscfg's own converter emits exactly
            # that line -- which this validator used to reject. 24.4R0 has 204
            # such nodes, `prefix-list-item` and syslog `contents` among them.
            return "VALUE"
        return keyword

    # Containers with children
    if node.children:
        if spliced or "nokeyword" in node.flags:
            # The keyword is not written in a set command, so the child's own
            # content follows the parent directly. `interfaces` holds a
            # nokeyword `interface` list: `set interfaces ge-0/0/0 mtu 9192`
            # names no `interface`. Emitting the keyword here left the parent
            # offering a bare VALUE, with nothing allowed after the name.
            #
            # `nokeyword` carries all but one of these. The exception is
            # `groups`, whose `group` child is a list with no such flag, and it
            # is the single case of 135 where the parent's `transparent:` flag
            # is the only signal -- which is why `spliced` exists. Without it
            # every `set groups <name> ...` is rejected, including the output
            # the downstream Ansible collection renders by default.
            return safe_name
        if node.is_list:
            # A list entry is named, so the entry name is not optional.
            return f"{keyword} {safe_name}"
        # A container may be set bare to bring it into being:
        # `set system services netconf ssh` names a container that also holds
        # `port` and `connection-limit`. Requiring content rejected it.
        return f"{keyword} {safe_name}?"

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
