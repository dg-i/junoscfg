"""Schema-guided occurrence collector for the unused-config audit.

Walks the dict IR and schema tree in parallel (adapted from
:mod:`junoscfg.anonymize.walker`) and collects every name-like string
value as an :class:`~junoscfg.audit.model.Occurrence`. Two paths are
maintained per occurrence: ``schema_path`` (schema keys, including
transparent wrapper keys) for registry pattern matching, and ``path``
(CLI tokens, including instance names) for emitted commands.

Safety property: string values the schema walk cannot classify are still
collected (kind ``unknown``) so an incomplete registry can never turn a
referenced object into a confident delete suggestion.
"""

from __future__ import annotations

from typing import Any

from junoscfg.audit.algebra import extract_names
from junoscfg.audit.model import Occurrence, OccurrenceKind
from junoscfg.display import entry_keys, key_is_positional

# Group references: the audit reads them as references to a group, a meaning
# the tree's universal `apply-groups` leaf does not carry.
_APPLY_GROUPS_KEYS: dict[str, OccurrenceKind] = {
    "apply-groups": "apply-groups",
    "apply-groups-except": "apply-groups-except",
}

# Consumed by external automation; contents are collected conservatively
# as unknown occurrences, the macro objects themselves are never audited.
_APPLY_MACRO_KEY = "apply-macro"


def collect_occurrences(config: dict[str, Any], schema_root: dict[str, Any]) -> list[Occurrence]:
    """Collect all name-like string occurrences from the IR.

    Args:
        config: Unwrapped configuration content dict.
        schema_root: The schema tree's configuration node.

    Returns:
        All occurrences in tree order.
    """
    collector: list[Occurrence] = []
    _walk_dict(config, schema_root, (), (), frozenset(), collector, schema_root)
    return collector


def _emit(
    collector: list[Occurrence],
    value: Any,
    path: tuple[str, ...],
    schema_path: tuple[str, ...],
    kind: OccurrenceKind,
    schema_types: tuple[str, ...] = (),
) -> None:
    """Append an occurrence for a name value.

    Numeric values are coerced to strings so numeric-named objects (e.g. a
    firewall filter named ``100``) are matched symmetrically on both the
    definition and reference sides. Booleans and ``None`` are presence
    markers, not names, and are ignored.
    """
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, int | float):
        value = str(value)
    if isinstance(value, str) and value:
        collector.append(
            Occurrence(
                value=value,
                path=path,
                schema_path=schema_path,
                kind=kind,
                schema_types=schema_types,
            )
        )


def _schema_types(*type_refs: str | None) -> tuple[str, ...]:
    """Filter type references down to meaningful names (drop None/xsd builtins)."""
    return tuple(tr for tr in type_refs if tr is not None and not tr.startswith("xsd:"))


def _walk_dict(
    obj: dict[str, Any],
    schema_node: dict[str, Any],
    match_path: tuple[str, ...],
    cli_path: tuple[str, ...],
    skip_keys: frozenset[str],
    collector: list[Occurrence],
    root: dict[str, Any],
) -> None:
    """Walk one IR dict level against its schema node, past *skip_keys*.

    A key resolves through `junoscfg.display.schema_child`, so a universal
    statement below the root is walked against the root's node (*root*).
    """
    from junoscfg.display import resolve_key_alias, schema_child

    for key, value in obj.items():
        if key.startswith("@") or key in skip_keys:
            continue

        if key in _APPLY_GROUPS_KEYS:
            items = value if isinstance(value, list) else [value]
            for item in items:
                _emit(
                    collector,
                    item,
                    cli_path + (key, str(item)),
                    match_path + (key,),
                    _APPLY_GROUPS_KEYS[key],
                )
            continue

        if key == _APPLY_MACRO_KEY:
            _walk_unknown(value, match_path + (key,), cli_path + (key,), collector)
            continue

        child_schema = schema_child(schema_node, resolve_key_alias(key), root)
        if child_schema is None:
            _walk_unknown(value, match_path + (key,), cli_path + (key,), collector)
            continue

        transparent_child = child_schema.get("t")
        if transparent_child:
            inner_schema = child_schema.get("c", {}).get(transparent_child)
            if isinstance(value, dict):
                # The transparent child holds the keyed entries (its name is
                # stripped from the CLI path). Every OTHER sibling key is a
                # normal child of the container and must still be walked —
                # e.g. apply-groups under routing-instances, or an
                # interface-range alongside interface.
                if transparent_child in value:
                    _walk_container_child(
                        value[transparent_child],
                        inner_schema,
                        match_path + (key, transparent_child),
                        cli_path + (key,),
                        collector,
                        root,
                    )
                siblings = {k: v for k, v in value.items() if k != transparent_child}
                if siblings:
                    _walk_dict(
                        siblings,
                        child_schema,
                        match_path + (key,),
                        cli_path + (key,),
                        frozenset(),
                        collector,
                        root,
                    )
            elif isinstance(value, list):
                # Native JSON keeps the entries as a bare list (no wrapper).
                _walk_container_child(
                    value,
                    inner_schema,
                    match_path + (key, transparent_child),
                    cli_path + (key,),
                    collector,
                    root,
                )
            else:
                _walk_unknown(value, match_path + (key,), cli_path + (key,), collector)
            continue

        if child_schema.get("L"):
            _walk_entries(
                value,
                child_schema,
                match_path + (key,),
                cli_path + (key,),
                collector,
                root,
            )
            continue

        if child_schema.get("l"):
            _walk_leaf(
                value,
                child_schema,
                schema_node,
                match_path + (key,),
                cli_path + (key,),
                collector,
            )
            continue

        # Plain container
        if isinstance(value, dict):
            _walk_dict(
                value,
                child_schema,
                match_path + (key,),
                cli_path + (key,),
                frozenset(),
                collector,
                root,
            )
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _walk_dict(
                        item,
                        child_schema,
                        match_path + (key,),
                        cli_path + (key,),
                        frozenset(),
                        collector,
                        root,
                    )
                else:
                    _emit(collector, item, cli_path + (key,), match_path + (key,), "unknown")
        else:
            # Schema expects a container but the IR holds a scalar —
            # collect conservatively rather than dropping it.
            _emit(collector, value, cli_path + (key,), match_path + (key,), "unknown")


def _walk_container_child(
    value: Any,
    inner_schema: dict[str, Any] | None,
    match_path: tuple[str, ...],
    cli_path: tuple[str, ...],
    collector: list[Occurrence],
    root: dict[str, Any],
) -> None:
    """Walk the transparent child of a transparent container."""
    if inner_schema is None:
        _walk_unknown(value, match_path, cli_path, collector)
    else:
        _walk_entries(value, inner_schema, match_path, cli_path, collector, root)


def _walk_entries(
    value: Any,
    list_schema: dict[str, Any],
    match_path: tuple[str, ...],
    cli_path: tuple[str, ...],
    collector: list[Occurrence],
    root: dict[str, Any],
) -> None:
    """Walk the entries of a named list (or transparent container content).

    The key fields come from the tree through `entry_keys`; no spelling
    decides them.
    """
    from junoscfg.display import entry_key_names, entry_keys

    entries = value if isinstance(value, list) else [value]
    list_types = _schema_types(list_schema.get("tr"))
    keys = entry_keys(list_schema)
    value_fields = [field for field in keys if isinstance(field, str)]
    children = list_schema.get("c", {})

    for entry in entries:
        if entry is None:
            continue
        if not isinstance(entry, dict):
            # A bare value where the schema expects a keyed entry — the
            # value is the entry name (e.g. presence-only list members).
            _emit(
                collector,
                entry,
                cli_path + (str(entry),),
                match_path,
                "entry-key",
                list_types,
            )
            continue

        entry_cli_path = cli_path + _key_tokens(list_schema, entry)
        if len(value_fields) == 1:
            # One value field, beside any key choice: it names the entry.
            name = entry.get(value_fields[0])
            if isinstance(name, str | int | float):
                _emit(collector, str(name), entry_cli_path, match_path, "entry-key", list_types)
        else:
            # Several value fields: each is a leaf under its own tree node. An
            # enum field is a keyword, never a name -- `_walk_leaf` records
            # nothing for it -- and its value selects the namespace of the
            # others: `as-list` and `as-list-group` name two kinds of object.
            namespace = tuple(
                str(entry[f])
                for f in value_fields
                if f in entry and "e" in children.get(f, {}) and isinstance(entry[f], str)
            )
            for f in value_fields:
                if f in entry and f in children:
                    _walk_leaf(
                        entry[f],
                        children[f],
                        list_schema,
                        match_path + namespace + (f,),
                        entry_cli_path + (f,),
                        collector,
                    )
        _walk_dict(
            entry,
            list_schema,
            match_path,
            entry_cli_path,
            entry_key_names(list_schema),
            collector,
            root,
        )


def _key_tokens(list_schema: dict[str, Any], entry: dict[str, Any]) -> tuple[str, ...]:
    """An entry's key as the set writer writes it: `upto /24`, `neighbor-id 10.0.0.1`."""
    tokens: list[str] = []
    for field in entry_keys(list_schema):
        for name in field if isinstance(field, tuple) else (field,):
            value = entry.get(name)
            written = isinstance(value, str | int | float) and not isinstance(value, bool)
            keyword = not key_is_positional(list_schema.get("c", {}).get(name))
            if (isinstance(field, tuple) and name in entry) or (written and keyword):
                tokens.append(name)
            tokens.extend([str(value)] if written else [])
    return tuple(tokens)


def _walk_leaf(
    value: Any,
    leaf_schema: dict[str, Any],
    parent_schema: dict[str, Any],
    match_path: tuple[str, ...],
    cli_path: tuple[str, ...],
    collector: list[Occurrence],
) -> None:
    """Collect occurrences from a leaf or leaf-list value."""
    if "e" in leaf_schema:
        # Enum leaf: values are schema keywords, never object names.
        return

    type_ref = leaf_schema.get("tr")
    items = value if isinstance(value, list) else [value]

    if type_ref == "policy-algebra":
        for item in items:
            if isinstance(item, str):
                for name in extract_names(item):
                    _emit(
                        collector,
                        name,
                        cli_path + (name,),
                        match_path,
                        "algebra",
                        ("policy-algebra",),
                    )
        return

    schema_types = _schema_types(type_ref, parent_schema.get("tr"))
    for item in items:
        for name in _leaf_names(item):
            _emit(collector, name, cli_path + (name,), match_path, "leaf", schema_types)


def _leaf_names(item: Any) -> list[str]:
    """Yield the reference name(s) carried by one leaf-list item.

    Pre-built IR or native JSON may carry a bracket list as one opaque string
    ``"[ a b ]"``; split it so multi-value references are recognized. Raw set
    input rejects that interactive shorthand, while structured input expands
    it to real list values before the audit walker sees it.
    """
    if isinstance(item, str):
        stripped = item.strip()
        if len(stripped) >= 2 and stripped[0] == "[" and stripped[-1] == "]":
            return stripped[1:-1].split()
        return [item] if item else []
    if isinstance(item, bool) or item is None:
        return []
    if isinstance(item, int | float):
        return [str(item)]
    return []


def _walk_unknown(
    obj: Any,
    match_path: tuple[str, ...],
    cli_path: tuple[str, ...],
    collector: list[Occurrence],
) -> None:
    """Blind walk for subtrees the schema does not describe.

    Every string value is collected as an ``unknown`` occurrence so that
    rule (d) — unknown position, potential reference — applies. Dict keys
    are structural keywords in the IR and are not collected.
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.startswith("@"):
                continue
            _walk_unknown(value, match_path + (key,), cli_path + (key,), collector)
    elif isinstance(obj, list):
        for item in obj:
            _walk_unknown(item, match_path, cli_path, collector)
    else:
        _emit(collector, obj, cli_path, match_path, "unknown")
