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

import hashlib
import itertools
import re

from junoscfg.display import (
    UNQUOTABLE_TYPES,
    entry_keys,
    enum_is_fragment,
    is_keyword_field,
    open_artifact_write,
    statement_children,
    strip_type_prefix,
)
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
# every name in the 24.4R0 set shipped until 0.8.0 (10,958) and the 23.2R2, 23.4R2 and
# 25.2R2 dumps (10,840 / 10,105 / 10,455): zero produce a doubled underscore.
_LIST_RULE_SUFFIX = "__list"

# Oneliner named lists repeat known keyworded children after their entry name.
# Keep their rules separate from ordinary same-named lists: rule definitions
# merge globally, so sharing a name would widen every occurrence of that list.
_ONELINER_SUFFIX = "__ol"

# A container with a flat positional child gains a different production shape
# from an ordinary same-named container. Isolate it before global rule merging,
# just as oneliner lists are isolated above.
_POSITIONAL_FLAT_SUFFIX = "__pkf"
# A list keyed by anything but a lone `name` takes its key values, one per
# field, where a `name`-keyed list takes one token. Same-named lists with
# different keys must not merge -- `then community` is keyed by an action and a
# name, `policy-options community` by a name -- so a keyed list's rule carries
# a digest of its key.
_KEY_SUFFIX = "__k"

# The XSD type whose value is a policy expression rather than a token:
# `from policy (( A && ! B ) || ( ! C && D ))`. In 24.4R0 it is on 7,636 nodes,
# `import`, `export`, `prefix-policy` and `retention-policy` among them, and
# every one of them is a leaf. It is the only slot where a value may hold
# spaces and parentheses without being quoted.
#
# This is a *type reference*, not an element name, which is why an `xsd_fixes`
# entry that searched for it by element name through `find_all` matched
# nothing in four releases and was deleted.
_POLICY_ALGEBRA_TYPE = "policy-algebra"

# The rule holding the statements a configuration may carry at any level. The
# schema declares them once, as root children flagged `universal`
# (`_fix_apply_statements` in `xsd_fixes.py`), and every rule here references
# this one rule rather than repeating them: a copy under each of 123,769
# containers costs +24 MB on the structure tree and +0.6 MB on the grammar.
_UNIVERSAL_RULE = "universal_statement"
_UNIVERSAL_FLAG = "universal"


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


def _value_token(node: SchemaNode) -> str:
    """The value terminal for a slot that writes *node*'s own value.

    `QUOTED_OR_VALUE` everywhere except a policy-algebra slot, which also takes
    an unquoted parenthesised expression. The expression alternative used to
    sit in `QUOTED_OR_VALUE` itself, which put it in all 11,854 value slots of
    the shipped grammar rather than the 7,636 nodes that take one: a hostname
    cannot hold a space or a parenthesis, yet
    `set system host-name (anything at all goes here)` validated.
    """
    if node.type_ref == _POLICY_ALGEBRA_TYPE:
        return "ALGEBRA_OR_VALUE"
    if node.type_ref and strip_type_prefix(node.type_ref) in UNQUOTABLE_TYPES:
        # An integer, an address or a MAC cannot hold whitespace, so a quoted
        # multi-word string is never one of them. Leaving every leaf quotable
        # put 11,695 slots where the pre-change grammar had 82, and
        # `set interfaces ge-0/0/0 mtu "not a number at all"` validated.
        return "VALUE"
    return "QUOTED_OR_VALUE"


def _key_value(node: SchemaNode | None) -> str:
    """The grammar for one key value: its leaf's type, an enum where it is closed.

    `list-type` takes `as-list` or `as-list-group` and nothing else -- the
    device rejects `as-path-neighbors 1 AS-LIST-A` -- while a nokeyword enum
    that is a fragment of a wider union takes any value. A field whose leaf is
    not `nokeyword` is preceded by its keyword, an enum or not:
    `drop-profile-map loss-priority low protocol any`.
    """
    if node is None:
        return "QUOTED_OR_VALUE"
    if node.enums and not enum_is_fragment(node.name, node.enums):
        value = "(" + " | ".join(f'"{value}"' for value in node.enums) + ")"
    else:
        value = _value_token(node)
    if is_keyword_field(node):
        return f'"{node.name}" {value}'
    return value


def _key_sequence(node: SchemaNode) -> str:
    """The tokens an entry's key takes.

    The positional values in declared order, then the fields given by keyword
    in any order among themselves, and a choice of identifiers as one of its
    keywords, with its value where the alternative is a leaf, before or after
    all of them. The device accepts `then community SAMPLE-COMM add`,
    `route-filter exact 198.51.100.0/24` and `virtual-link transit-area
    0.0.0.3 neighbor-id 10.255.255.2` (device probe, vMX 23.2R2-S7.5).
    """
    if not node.key_fields:
        return "QUOTED_OR_VALUE"
    choices: list[str] = []
    positional: list[str] = []
    keyworded: list[str] = []
    for field in entry_keys(node):
        if isinstance(field, tuple):
            alternatives = []
            for name in field:
                child = node.children.get(name)
                keyword = f'"{_NAME_ESCAPES.get(name, name)}"'
                if child is not None and child.is_leaf:
                    keyword = f"{keyword} {_value_token(child)}"
                alternatives.append(keyword)
            choices.append("(" + " | ".join(alternatives) + ")")
        else:
            child = node.children.get(field)
            (keyworded if is_keyword_field(child) else positional).append(_key_value(child))
    values = positional[:]
    if len(keyworded) > 1:
        orders = (" ".join(order) for order in itertools.permutations(keyworded))
        values.append("(" + " | ".join(orders) + ")")
    else:
        values.extend(keyworded)
    if choices and values:
        first, last = " ".join(choices), " ".join(values)
        return f"({first} {last} | {last} {first})"
    return " ".join(choices + values)


def _rule_name_for(name: str, node: SchemaNode) -> str:
    """Return the rule name for a node, keeping named lists in their own rule."""
    base = _safe_rule_name(name)
    if node.is_list and node.children:
        key = _key_sequence(node)
        if key != "QUOTED_OR_VALUE":
            base += f"{_KEY_SUFFIX}{hashlib.sha256(key.encode()).hexdigest()[:10]}"
        if "oneliner" in node.flags:
            return f"{base}{_LIST_RULE_SUFFIX}{_ONELINER_SUFFIX}"
        return f"{base}{_LIST_RULE_SUFFIX}"
    if node.children and any(
        "positional-key-flat" in child.flags for child in node.children.values()
    ):
        return f"{base}{_POSITIONAL_FLAT_SUFFIX}"
    return base


def _has_direct_sibling_variant(node: SchemaNode) -> bool:
    """Whether *node* itself gains metadata-specific sibling repetition."""
    return bool(
        (node.is_list and statement_children(node) and "oneliner" in node.flags)
        or any("positional-key-flat" in child.flags for child in node.children.values())
    )


def _variant_rule_names(root: SchemaNode) -> dict[int, str]:
    """Name metadata-sensitive subtrees without leaking through merged parents.

    Rules normally merge globally by element name. A compact-sibling rule has
    context-specific syntax, so every ancestor carrying it needs a stable
    variant name until the unique configuration root. Otherwise a same-named
    parent merges the marked and unmarked child references back together.
    """
    names: dict[int, str] = {}
    visited: dict[int, tuple[str, str | None]] = {}

    def visit(node: SchemaNode, *, is_root: bool = False) -> tuple[str, str | None]:
        node_id = id(node)
        if node_id in visited:
            return visited[node_id]

        children = [
            (name, *visit(child)) for name, child in sorted(statement_children(node).items())
        ]
        own_shape = (
            node.name,
            node.combinator.value,
            node.is_key,
            node.is_list,
            node.is_mandatory,
            node.is_leaf,
            node.is_presence,
            tuple(node.enums or ()),
            node.pattern,
            node.pattern_negated,
            node.type_ref,
            tuple(sorted(node.flags)),
            *((_key_sequence(node),) if node.key_fields else ()),
        )
        full_payload = repr((own_shape, [(name, full) for name, full, _ in children]))
        full_digest = hashlib.sha256(full_payload.encode()).hexdigest()

        direct = _has_direct_sibling_variant(node)
        affected_children = [(name, variant) for name, _, variant in children if variant]
        variant_digest: str | None = None
        if direct or affected_children:
            variant_payload = repr(
                (
                    "direct" if direct else "ancestor",
                    full_digest if direct else own_shape,
                    affected_children,
                )
            )
            variant_digest = hashlib.sha256(variant_payload.encode()).hexdigest()
            if node.children and not is_root:
                names[node_id] = f"{_rule_name_for(node.name, node)}__v{variant_digest[:10]}"

        result = (full_digest, variant_digest)
        visited[node_id] = result
        return result

    visit(root, is_root=True)
    return names


class _RuleInfo:
    """Accumulated info for a single Lark rule (may be merged from multiple nodes)."""

    __slots__ = (
        "alts",
        "is_named_list",
        "key",
        "positional_alts",
        "repeatable_alts",
        "repeats_siblings",
    )

    def __init__(self) -> None:
        self.alts: set[str] = set()
        self.repeatable_alts: set[str] = set()
        self.positional_alts: set[str] = set()
        self.is_named_list: bool = False
        self.repeats_siblings: bool = False
        # The tokens an entry's key takes; `QUOTED_OR_VALUE` for a lone name.
        self.key: str = "QUOTED_OR_VALUE"


def generate_lark_grammar(root: SchemaNode) -> str:
    """Generate a Lark grammar from a SchemaNode tree.

    Args:
        root: The schema tree rooted at 'configuration'.

    Returns:
        Lark grammar string.
    """
    # The statements valid at every level, declared once on the root.
    universal = {
        name: node for name, node in root.children.items() if _UNIVERSAL_FLAG in node.flags
    }
    variant_names = _variant_rule_names(root)

    # Pass 1: collect all rule definitions (merged by rule name)
    rule_map: dict[str, _RuleInfo] = {}
    common_alts: dict[str, set[str]] = {}
    merge_families: dict[str, str] = {}
    visited: set[int] = set()  # id(node) to prevent infinite recursion
    _collect_rules(
        root,
        rule_map,
        visited,
        variant_names,
        common_alts,
        merge_families,
        skip=set(universal),
    )

    # Ancestor variants keep metadata-sensitive child references local, while
    # retaining the grammar's established union of ordinary alternatives for
    # same-named rules. This prevents compact syntax leaking across paths
    # without turning unrelated historical merges into new rejections.
    for rule_name, family in merge_families.items():
        rule_map[rule_name].alts.update(common_alts.get(family, ()))

    if universal:
        # One rule, referenced from every other. `configuration` included, so
        # `set apply-groups global-vxlan` at the top level parses as itself
        # rather than being stripped to a bare `set` before it reaches here.
        for info in rule_map.values():
            # Not after an entry that is nothing but its key: the device
            # rejects a further token there.
            if info.alts or not info.is_named_list:
                info.alts.add(_UNIVERSAL_RULE)

    # Pass 2: emit grammar
    lines: list[str] = []

    # Header
    lines.append("// Junos set command grammar (auto-generated, structural only)")
    lines.append("// Validates: set <path> [value]")
    lines.append("")
    lines.append("start: SET configuration")
    lines.append("")

    if universal:
        alts = sorted(
            _child_reference(name, node, variant_names=variant_names)
            for name, node in universal.items()
        )
        lines.append(f"{_UNIVERSAL_RULE}: {' | '.join(alts)}")
        lines.append("")

    # Emit rules in stable order
    for rule_name in sorted(rule_map):
        info = rule_map[rule_name]
        alts = sorted(info.alts)
        body = " | ".join(alts)

        if info.is_named_list and not info.alts:
            # Nothing but a key: nothing may follow it.
            lines.append(f"{rule_name}: {info.key}")
        elif info.is_named_list and info.repeats_siblings:
            # An oneliner entry may carry several known keyworded settings:
            # `server 198.51.100.1 version 4 prefer`. Repeat only alternatives
            # that render their own keyword. Repeating a bare VALUE is both
            # ambiguous and would accept an arbitrary run of unknown tokens.
            repeatable = " | ".join(sorted(info.repeatable_alts))
            non_repeatable = " | ".join(sorted(info.alts - info.repeatable_alts))
            continuations = f"({repeatable})+"
            if non_repeatable:
                continuations = f"{non_repeatable} | {continuations}"
            lines.append(f"{rule_name}: {info.key} ({continuations})?")
        elif info.is_named_list:
            # Named list: VALUE captures the entry name. Only list nodes reach
            # this rule name, so the slot can no longer be merged away.
            #
            # The entry name is QUOTED_OR_VALUE, not VALUE: `ssh-ed25519` is
            # itself a list, so the key is the entry name, and a key is quoted
            # and contains spaces. VALUE is /\S+/ and cannot match one.
            #
            # One continuation, not a global repetition. `(...)*` here would
            # also repeat bare VALUE alternatives, making the grammar highly
            # ambiguous and allowing arbitrary runs of unknown tokens. Marked
            # oneliner rules take the narrow keyword-only path above instead.
            # Lark's `~0..n` range is not a middle way: it expands
            # combinatorially and does not finish compiling.
            lines.append(f"{rule_name}: {info.key} ({body})?")
        elif info.positional_alts and info.repeatable_alts:
            # A flat positional child is a standalone alternative in expanded
            # display-set form, but may also lead a compact run of keyworded
            # siblings: `maximum-prefixes 300000 threshold 50 log-interval 5`.
            # The positional token is consumed once and only known keyworded
            # alternatives repeat after it.
            positional = " | ".join(sorted(info.positional_alts))
            repeatable = " | ".join(sorted(info.repeatable_alts))
            lines.append(f"{rule_name}: {body} | ({positional}) ({repeatable})+")
        else:
            lines.append(f"{rule_name}: {body}")

        lines.append("")

    # Footer holding the terminals
    lines.append("// Terminals")
    lines.append('SET: "set"')
    lines.append('DEACTIVATE: "deactivate"')
    lines.append("VALUE: /\\S+/")
    lines.append('QUOTED: /"[^"]*"/')
    # A policy expression is one value spanning several tokens:
    # `from policy (( A && ! B ) || ( ! C && D ))`. A device carries it as a
    # single opaque string -- `"policy": ["(( A && ! B ) || ( ! C && D ))"]` --
    # and junoscfg converts it to exactly that, so conversion was already
    # right and only the grammar was wrong: VALUE is /\S+/ and stops at the
    # first space. Confirmed against a device's own `| display json`.
    #
    # It reaches only ALGEBRA_OR_VALUE, which `_value_token` hands to the
    # nodes typed `policy-algebra` and to nothing else. Put in QUOTED_OR_VALUE
    # it widened every value slot in the grammar instead.
    lines.append("EXPRESSION: /\\([^\\n]*\\)/")
    lines.append("QUOTED_OR_VALUE: QUOTED | VALUE")
    lines.append("ALGEBRA_OR_VALUE: QUOTED | EXPRESSION | VALUE")
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
    variant_names: dict[int, str],
    common_alts: dict[str, set[str]],
    merge_families: dict[str, str],
    skip: set[str] | None = None,
) -> None:
    """Recursively collect rule definitions from the schema tree.

    Uses id(node) for dedup to handle shared schema nodes correctly.
    Same-named rules from different tree locations merge their alternatives.

    ``skip`` names root children that belong to ``universal_statement`` rather
    than to ``configuration``'s own alternatives; their own sub-rules are still
    collected, so ``apply-macro``'s entry shape gets a rule.
    """
    node_id = id(node)
    if node_id in visited:
        return
    visited.add(node_id)

    if not node.children:
        # Leaf or presence — no rule needed (handled inline by parent)
        return
    statements = statement_children(node)
    if node.is_list and not statements and not node.key_fields:
        # A list of names alone, rendered inline by the parent.
        return

    family = _rule_name_for(node.name, node)
    rule_name = variant_names.get(node_id, family)

    # Build child alternatives
    child_alts: list[str] = []
    ordinary_alts: list[str] = []
    repeatable_alts: list[str] = []
    positional_alts: list[str] = []
    for child_name, child_node in statements.items():
        if skip and child_name in skip:
            continue
        spliced = f"transparent:{child_name}" in node.flags
        child_ref = _child_reference(
            child_name,
            child_node,
            spliced=spliced,
            variant_names=variant_names,
        )
        child_alts.append(child_ref)
        if id(child_node) not in variant_names:
            ordinary_alts.append(child_ref)
        # Every written keyword reference begins with its quoted literal;
        # bare VALUE and spliced sub-rules do not. Only the former are safe to
        # repeat without widening the grammar to arbitrary unknown tokens.
        if child_ref.startswith('"'):
            repeatable_alts.append(child_ref)
        if "positional-key-flat" in child_node.flags:
            positional_alts.append(child_ref)

    if child_alts or node.is_list:
        # Merge into rule map
        if rule_name not in rule_map:
            rule_map[rule_name] = _RuleInfo()
        info = rule_map[rule_name]
        info.alts.update(child_alts)
        if not _has_direct_sibling_variant(node):
            common_alts.setdefault(family, set()).update(ordinary_alts)
            merge_families[rule_name] = family
        info.repeatable_alts.update(repeatable_alts)
        info.positional_alts.update(positional_alts)
        if node.is_list:
            info.is_named_list = True
            info.key = _key_sequence(node)
            if "oneliner" in node.flags:
                info.repeats_siblings = True

    # Recurse into children
    for child_node in node.children.values():
        _collect_rules(
            child_node,
            rule_map,
            visited,
            variant_names,
            common_alts,
            merge_families,
        )


def _flat_entry(node: SchemaNode) -> str:
    """The run of tokens one entry of a list written flat takes.

    Its key, then optionally one entry of each child list in the same form,
    then optionally each leaf's value: `apply-macro` takes its name, a
    keyword and that keyword's value, at most, and the device rejects a
    fourth (device probe, vMX 23.2R2-S7.5). `keyword value+` accepted any run.
    """
    parts = [_key_sequence(node)]
    for child in statement_children(node).values():
        if child.is_list and child.children:
            parts.append(f"({_flat_entry(child)})?")
        elif child.is_leaf:
            parts.append(f"{_value_token(child)}?")
    return " ".join(parts)


def _child_reference(
    name: str,
    node: SchemaNode,
    *,
    spliced: bool = False,
    variant_names: dict[int, str] | None = None,
) -> str:
    """Generate the Lark expression for referencing a child node.

    ``spliced`` says the parent carries ``transparent:<name>``, so this child's
    own name is not written in a set command.
    """
    safe_name = (variant_names or {}).get(id(node), _rule_name_for(name, node))

    # Determine the keyword token
    if name in _NAME_ESCAPES:
        keyword = f'"{_NAME_ESCAPES[name]}"'
    elif name.startswith("$"):
        # Variable placeholder - accept any value
        return "VALUE"
    else:
        keyword = f'"{name}"'

    # Flattened renderings. `flat-dict` marks a place where the schema's own
    # shape is not what a set command writes: `trigger {"after": [null],
    # "count": 1}` is written `trigger after 1`, a run of tokens where the tree
    # has structure, so the run itself is the value. A keyed entry such as
    # `attributes-match` is no longer one: its key fields are its values.
    value = _value_token(node)

    if "flat-dict" in node.flags:
        if node.is_list:
            return f"{keyword} {_flat_entry(node)}"
        return f"{keyword} {value}+"

    # Leaf nodes
    if node.is_leaf:
        if "nokeyword" in node.flags and "freeform-nk" not in node.flags:
            return value  # No keyword, just a value
        # `freeform-nk` marks a node carrying `nokeyword` only so its value is
        # validated as freeform; `_fix_freeform_nk_keys` says it is still
        # "treated as a normal keyword in conversion". Reading the bare
        # `nokeyword` here rejected `set interfaces ge-0/0/1 unit 0 vlan-id
        # 100`, which is every VLAN-bearing configuration. In 24.4R0 the flag
        # is on `vlan-id` and `vlan-name` only.
        return f"{keyword} {value}"

    # A list of names alone was a childless presence list until the parser kept
    # its `name`, and is written as one: the name is the whole content.
    if node.is_list and node.children and not node.key_fields and not statement_children(node):
        node = SchemaNode(name=node.name, is_list=True, is_presence=True, flags=node.flags)

    # Presence containers (no value)
    if node.is_presence:
        if node.is_list and "nokeyword" not in node.flags:
            # A presence *list* with no children still names its entries: the
            # entry name is the whole content. `snmp filter-interfaces
            # interfaces "^sxe-.*"` is one, and emitting a bare keyword left
            # the pattern with nowhere to go -- 43 rejected lines across three
            # devices, the only class that appeared on all of them. 24.4R0 has
            # 5,808 of these across 193 names. The name is optional because the
            # bare keyword brings the list into being.
            return f"{keyword} QUOTED_OR_VALUE?"
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
    with open_artifact_write(output_path) as f:
        f.write(grammar)
        f.write("\n")
