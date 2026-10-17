"""Convert display set commands to the JSON dict IR.

Parses display set/deactivate/protect/delete/activate commands and builds
a Junos JSON dict using the schema tree for type inference.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from junoscfg.display import (
    UNPLACED_STATEMENTS,
    entry_keys,
    is_algebra_token,
    is_policy_algebra,
    is_transparent_list_key,
    load_schema_tree,
    meta_target,
    passes_tag_to_child,
    read_entry_key,
    schema_child,
    statement_children,
    statement_key,
    statement_name_spellings,
    unplaced_record_problem,
)
from junoscfg.input import (
    InputError,
    find_unsupported_set_brackets,
    find_unsupported_set_commands,
    normalize,
    set_token_value,
    set_tokens,
)


def _is_statement_name(cname: str, cnode: dict[str, Any], token: str) -> bool:
    """True when a nokeyword leaf's value is itself the statement name.

    The schema folds an on/off switch into a single node whose name joins both
    spellings — ``enable-disable``, carrying the enum ``['disable']`` — so the
    token in the configuration *is* the statement rather than a value beneath
    it. A device renders it ``"disable": [null]``; keying the dict on the
    schema node invents an ``enable-disable`` statement no Junos would accept.

    In 24.4R0 this is 4,238 nodes and every one of them is ``enable-disable``.
    The other 26,386 nokeyword leaves carry a positional value and keep the
    node name, as do the 352 marked ``freeform-nk``.
    """
    if cnode.get("frnk") or "e" not in cnode:
        return False
    tree = load_schema_tree() or {}
    enums = tree.get("_enums", [])
    index = cnode["e"]
    if not isinstance(index, int) or index >= len(enums):
        return False
    allowed = enums[index]
    # `token in parts`, not `token in allowed`: 4,152 of the 4,238 nodes carry
    # the enum `['disable']` alone, so keying on the enum fixed `disable` and
    # left `enable` -- the other half of the same switch -- still writing an
    # `enable-disable` key no device accepts.
    return token in statement_name_spellings(cname, allowed)


def set_to_dict(source: str) -> dict[str, Any]:
    """Parse display set commands into the IR dict.

    Handles ``set``, ``deactivate``, ``protect``, ``delete``, and
    ``activate`` commands.
    """
    bracket_findings = find_unsupported_set_brackets(source)
    if bracket_findings:
        lineno, message = bracket_findings[0]
        raise InputError(message, lineno)

    command_findings = find_unsupported_set_commands(source)
    if command_findings:
        lineno, message = command_findings[0]
        raise InputError(message, lineno)

    content = normalize(source)
    lines = [line.strip() for line in content.split("\n") if line.strip()]

    schema = load_schema_tree()
    config: dict[str, Any] = {}
    index: _EntryIndex = {}

    for line in lines:
        if line.startswith("set "):
            tokens = set_tokens(line[4:])
            if tokens:
                _merge_tokens(config, tokens, schema, index)
        elif line.startswith("deactivate "):
            tokens = set_tokens(line[11:])
            if tokens:
                _apply_meta(config, tokens, schema, "inactive", True, index)
        elif line.startswith("protect "):
            tokens = set_tokens(line[8:])
            if tokens:
                _apply_meta(config, tokens, schema, "protect", "protect", index)
        elif line.startswith("delete "):
            tokens = set_tokens(line[7:])
            if tokens:
                _apply_meta(config, tokens, schema, "operation", "delete", index)
        elif line.startswith("activate "):
            tokens = set_tokens(line[9:])
            if tokens:
                _apply_meta(config, tokens, schema, "active", "active", index)

    return config


def statements_to_dict(
    statements: list[list[tuple[str, frozenset[str]]]],
    set_lines: list[tuple[str, bool]] | None = None,
    lines: tuple[int, ...] = (),
) -> dict[str, Any]:
    """Build the IR dict from curly statements, as `SetConverter.statements()` lexes them.

    Each statement is its levels -- the block openers above it, then itself
    -- with the tags that lead each one. The set reader's walk reads the
    tokens and puts a level's tags on the node that level starts: a list
    entry, which ends after its key; a leaf, never its value; a container.
    `inactive: route 0.0.0.0/0 next-hop 10.0.0.1;` marks the route, as the
    device's XML does (`<route inactive="inactive">`). The bridge used to
    flatten curly text to `deactivate <whole statement>`, which marked
    `next-hop`.

    *set_lines*, when given, receives each set statement the walk read, in the
    input's own tokens and without tags, with whether it is complete: a
    one-line statement the walk reads as siblings (`hold-time up 2000 down
    0`) gives one line per sibling, and a leaf read without its value gives
    an incomplete line.

    *lines*, when given, is the line each statement starts on
    (`SetConverter.statement_lines()`), named in a refusal.
    """
    schema = load_schema_tree()
    config: dict[str, Any] = {}
    index: _EntryIndex = {}
    for number, levels in enumerate(statements):
        tokens: list[str] = []
        tags: dict[int, frozenset[str]] = {}
        for text, level_tags in levels:
            level = set_tokens(text)
            if level:
                # Every level start is recorded, tagged or not: where a level
                # starts says which node a tag belongs to.
                tags[len(tokens)] = level_tags
            tokens += level
        if tokens:
            reading = _Reading() if set_lines is not None else None
            _merge_tokens(config, tokens, schema, index, tags, reading)
            if set_lines is not None and reading is not None:
                read = _split_at_cuts(tokens, reading.cuts)
                set_lines.extend((" ".join(line), True) for line in read[:-1])
                set_lines.append((" ".join(read[-1]), not reading.incomplete))
        if any(tags.values()):
            # A level boundary inside a key or a value: no node starts
            # there, so the tag has nowhere to go. No device writes this.
            line = lines[number] if number < len(lines) else None
            where = f" on line {line}" if line is not None else ""
            raise InputError(
                f"Invalid structured input{where}: a tag inside a key or value in "
                + " ".join(text for text, _ in levels),
                line,
            )
    return config


# The IR spelling of each curly tag, as the set commands write it.
_TAG_ATTRS: dict[str, tuple[str, Any]] = {
    "inactive": ("inactive", True),
    "protect": ("protect", "protect"),
    "replace": ("operation", "replace"),
    "delete": ("operation", "delete"),
}


def _mark(holder: dict[str, Any], tags: frozenset[str], key: str | None = None) -> None:
    """Put *tags* on *holder* itself, or with *key* on its child *key* (``@key``)."""
    if not tags:
        return
    attrs = holder.setdefault("@" if key is None else f"@{key}", {})
    for tag in sorted(tags):
        name, value = _TAG_ATTRS[tag]
        attrs[name] = value


def _tag_attrs(tags: frozenset[str]) -> dict[str, Any]:
    """*tags* as the ``@`` dict they make."""
    return dict(_TAG_ATTRS[tag] for tag in sorted(tags))


def _tags_from(tags: dict[int, frozenset[str]], i: int) -> frozenset[str]:
    """Every tag left at or after token *i*, taken: a statement kept whole holds them all."""
    found: frozenset[str] = frozenset()
    for at in [at for at in tags if at >= i]:
        found |= tags.pop(at)
    return found


def _leaf_value(text: str, leaf: dict[str, Any]) -> str:
    """The value of *leaf* that *text*, one token or the line's rest, spells.

    A quoted `policy-algebra` name whose text starts with `(` is kept as
    written, quotes included, as the device's XML and JSON hold it
    (`<import>"( P-A )"</import>`, vMX 23.2R2-S7.5 `synthetic-probes`):
    unquoted it would read as an expression, another configuration (DEV-5;
    spec conversion/value-quoting). Every other value is read as any is.
    """
    if text.startswith('"') and is_policy_algebra(leaf) and is_algebra_token(text):
        return text
    return set_token_value(text)


# ── Dict entry helpers ───────────────────────────────────────────────


#: Each IR list's entries by key, so finding one is a lookup, not a scan:
#: `id(list)` to the list -- held so the id is not reused -- and its entries
#: by key tuple. One per `set_to_dict` call.
_EntryIndex = dict[int, tuple[list[Any], dict[tuple[Any, ...], dict[str, Any]]]]


def _find_or_create_entry(
    lst: list[Any], key: dict[str, Any], index: _EntryIndex
) -> dict[str, Any]:
    """The entry of *lst* whose key fields hold *key*, created if there is none.

    An entry's identity is its whole key: `as-list X` and `as-list-group X`
    are two entries, as `route-filter A exact` and `route-filter A orlonger`
    are. Comparing every entry's key on every line made a 233,512-line
    configuration take 72.8 s where 0.14.0 took 12.8 s (phase-6 review).
    """
    entries = index.setdefault(id(lst), (lst, {}))[1]
    identity = tuple((k, tuple(v) if isinstance(v, list) else v) for k, v in key.items())
    entry = entries.get(identity)
    if entry is None:
        entry = dict(key)
        lst.append(entry)
        entries[identity] = entry
    return entry


def _kept_record(current: dict[str, Any], tokens: list[str]) -> tuple[dict[str, Any], str]:
    """The record *current* keeps unplaced statements in, and *tokens* as one of them.

    The tokens are the input's own, quotes included: the joined text is what
    every writer prints. A statement no writer could print as one line --
    a word holding an unquoted `;` or brace -- is refused, as bracket syntax is.
    """
    text = " ".join(tokens)
    problem = unplaced_record_problem({text: True})
    if problem is not None:
        raise ValueError(f"Invalid set input: {problem}")
    return current.setdefault(UNPLACED_STATEMENTS, {}), text


def _keep_whole(
    current: dict[str, Any],
    tokens: list[str],
    i: int,
    tags: dict[int, frozenset[str]] | None = None,
) -> None:
    """Keep ``tokens[i:]`` as one statement the reader could not place.

    It goes to the level's record (`UNPLACED_STATEMENTS`), never to a key of
    its own: a bare `apply-groups` beside `apply-groups G1`, or a bare
    `host-name` beside its value, would have the placed node's key. Field
    validation reports it `UNPLACED` and every writer reproduces it, so
    nothing of a line the reader cannot complete is applied or dropped. A
    curly tag on any of those tokens goes with it, as ``@<statement>``.
    """
    record, text = _kept_record(current, tokens[i:])
    record.setdefault(text, True)
    if tags:
        _mark(record, _tags_from(tags, i), text)


def _keep_meta_whole(
    current: dict[str, Any],
    tokens: list[str],
    i: int,
    attr_key: str,
    attr_value: Any,
) -> None:
    """Keep a meta command's unresolved suffix without annotating its prefix.

    A node or positional value the reader placed under that one word -- a
    folded switch's `disable`, a nokeyword leaf's value -- carries it as
    ``@<word>``; any other
    suffix is kept in the level's record as ``@<statement>``, beside a kept
    statement it names or one below it, which stays the single report.
    """
    value_text = " ".join(set_token_value(token) for token in tokens[i:])
    if " " not in value_text and any(
        existing == value_text
        or (isinstance(value, str | int | float) and str(value) == value_text)
        for existing, value in current.items()
        if not existing.startswith("@") and existing != UNPLACED_STATEMENTS
    ):
        current.setdefault(f"@{value_text}", {})[attr_key] = attr_value
        return
    record, text = _kept_record(current, tokens[i:])
    record.setdefault(f"@{text}", {})[attr_key] = attr_value


# ── Core token walking ──────────────────────────────────────────────


@dataclasses.dataclass
class _Reading:
    """Where one statement's walk started a sibling, and whether it ended whole.

    A cut ``(base, at)`` says the sibling starting at token ``at`` belongs to
    the node whose children start at token ``base``.
    """

    cuts: list[tuple[int, int]] = dataclasses.field(default_factory=list)
    incomplete: bool = False


def _cut(reading: _Reading | None, base: int, at: int) -> int:
    """Record a sibling starting at *at*; its node's children now start there."""
    if reading is not None:
        reading.cuts.append((base, at))
    return at


def _split_at_cuts(tokens: list[str], cuts: list[tuple[int, int]]) -> list[list[str]]:
    """One token list per statement: the path to the node, then the sibling.

    The walk only descends, so the path to each cut's node is the path to the
    previous one plus the tokens between that sibling's start and this node's
    children.
    """
    lines: list[list[str]] = []
    path: list[str] = []
    start = 0
    for base, at in cuts:
        lines.append(path + tokens[start:at])
        path = path + tokens[start:base]
        start = at
    lines.append(path + tokens[start:])
    return lines


def _merge_tokens(
    config: dict[str, Any],
    tokens: list[str],
    schema: dict[str, Any],
    index: _EntryIndex,
    tags: dict[int, frozenset[str]] | None = None,
    reading: _Reading | None = None,
) -> None:
    """Walk tokens against the schema tree and merge into config dict.

    *tags* maps the token where each curly level starts to the tags leading
    it; each lands on the node that token starts (`statements_to_dict`).
    Set input passes none. *reading*, when given, records where the walk
    starts a sibling statement and whether a leaf went without its value.
    """
    curly = tags is not None
    current = config
    current_schema = schema
    root = schema
    i = 0
    # Where the children of `current` start among the tokens.
    base = 0
    # Where the statement holding `current` starts, and the node above it.
    owner, owner_i = config, 0
    tags = tags if tags is not None else {}

    while i < len(tokens):
        token = tokens[i]
        children = statement_children(current_schema)
        here = tags.pop(i, frozenset())
        # A statement valid at every level is declared on the root only; the
        # reader meets it below the root too, never inside one (`schema_child`).
        found = schema_child(current_schema, token, root)
        universal = found if found is not None and found.get("u") else None
        if universal is not None and token not in children:
            children = {**children, token: universal}

        # A universal leaf-list (`apply-groups`, `apply-groups-except`) takes
        # one value a statement; `set apply-groups G1 G2` and a bare `set
        # apply-groups` are statements the device rejects, kept in the record
        # beside the values.
        if universal is not None and universal.get("ll"):
            lst = current.get(token, [])
            if i + 2 != len(tokens):
                tags[i] = here
                _keep_whole(current, tokens, i, tags)
                return
            val = set_token_value(tokens[i + 1])
            if curly and lst and current.get(f"@{token}", {}) != _tag_attrs(here):
                # `apply-groups G1; inactive: apply-groups G2;`: as for a
                # leaf, a tag on one value is not widened to the others.
                raise ValueError(
                    f"Invalid structured input: '{token}' tags some of its values and not "
                    "others; Junos tags a leaf as a whole"
                )
            current[token] = lst
            if val not in lst:
                lst.append(val)
            _mark(current, here, token)
            return

        # A universal flat-dict list (`apply-macro`) takes a name, then
        # optionally a keyword and that keyword's value; the device rejects a
        # fourth value (device probe, vMX 23.2R2-S7.5), which used to become a
        # second data entry without a word.
        if (
            universal is not None
            and universal.get("L")
            and universal.get("fd")
            and i + 1 < len(tokens)
        ):
            lst = current.get(token, [])
            # A tag on one data line has no place in the IR's `data` pairs:
            # the line is kept whole and reported, never widened to the macro.
            data_tagged = any(tags.get(k) for k in range(i + 2, len(tokens)))
            if len(tokens) - i > 4 or data_tagged:
                tags[i] = here
                _keep_whole(current, tokens, i, tags)
                return
            current[token] = lst
            entry = _find_or_create_entry(lst, {"name": set_token_value(tokens[i + 1])}, index)
            _mark(entry, here | tags.pop(i + 1, frozenset()))
            if i + 2 < len(tokens):
                pair = dict(
                    zip(("name", "value"), map(set_token_value, tokens[i + 2 :]), strict=False)
                )
                entry.setdefault("data", []).append(pair)
            return

        # The tree's key for the token: an XML and JSON element name is read as
        # the keyword it was renamed to (e.g., ieee-802.3ad → 802.3ad).
        schema_key = statement_key(children, token)

        if schema_key not in children:
            # Check transparent container
            transparent = current_schema.get("t")
            if transparent and transparent in children:
                tc_child = children[transparent]
                name = set_token_value(token)
                lst = current.setdefault(transparent, [])
                entry = _find_or_create_entry(lst, {"name": name}, index)
                _mark(entry, here)
                owner, owner_i = current, i
                i += 1
                base = i
                current = entry
                current_schema = tc_child
                continue

            # Check nokeyword leaf. It takes one token; when more follow and
            # the next is no sibling, the statement is one the schema does not
            # model. It used to be cut here -- the token kept as this leaf's
            # value, the rest of the line dropped without a word, and the
            # result validated -- so it falls through to be kept whole instead.
            nk_found = False
            for cname, cnode in children.items():
                if isinstance(cnode, dict) and cnode.get("nk") and cnode.get("l"):
                    if i + 1 < len(tokens):
                        after = tokens[i + 1]
                        if statement_key(children, after) not in children:
                            break
                    if _is_statement_name(cname, cnode, token):
                        current[token] = [None]
                        _mark(current, here, token)
                    elif current.get(cname, set_token_value(token)) != set_token_value(token):
                        # A second, different value: this node is no list, so
                        # writing it would replace the first without a word --
                        # three forwarding classes read as one, while the
                        # parser counted only `unbounded` as a list. Kept
                        # whole from the node's own keyword.
                        tags[i] = here
                        _keep_whole(owner, tokens, owner_i, tags)
                        return
                    else:
                        current[cname] = set_token_value(token)
                        _mark(current, here, cname)
                    i += 1
                    nk_found = True
                    break
            if nk_found:
                if i < len(tokens):
                    base = _cut(reading, base, i)
                    continue  # Process sibling tokens
                return

            # A hidden list consumes its complete declared key, just as a
            # keyworded list does. Partial keys remain whole at this level.
            tk_matched = False
            for cname, cnode in children.items():
                if not isinstance(cnode, dict) or not is_transparent_list_key(cnode):
                    continue
                read = read_entry_key(cnode, tokens, i)
                if read is None:
                    continue
                key, after = read
                if after < len(tokens) and not statement_children(cnode):
                    continue
                entry = _find_or_create_entry(current.setdefault(cname, []), key, index)
                on_key = here
                for k in range(i, after):
                    on_key |= tags.pop(k, frozenset())
                _mark(entry, on_key)
                if after == len(tokens):
                    return
                owner, owner_i = current, i
                i = base = after
                current = entry
                current_schema = cnode
                tk_matched = True
                break
            if tk_matched:
                continue

            # Check if token is a name in a child's transparent named list.
            # E.g., "ge-0/0/0" is an interface name under interfaces → interface.
            # Use look-ahead: verify the NEXT token matches a child of the
            # transparent list's schema to avoid false positives.
            tc_matched = False
            if i + 1 < len(tokens):
                next_token = tokens[i + 1]
                for parent_key, parent_node in children.items():
                    if not isinstance(parent_node, dict):
                        continue
                    tc_name = parent_node.get("t")
                    if not tc_name:
                        continue
                    tc_node = parent_node.get("c", {}).get(tc_name)
                    if not tc_node or not tc_node.get("L"):
                        continue
                    tc_children = statement_children(tc_node)
                    if statement_key(tc_children, next_token) in tc_children:
                        # Match — descend into parent → transparent list → entry
                        name = set_token_value(token)
                        parent = current.setdefault(parent_key, {})
                        lst = parent.setdefault(tc_name, [])
                        entry = _find_or_create_entry(lst, {"name": name}, index)
                        _mark(entry, here)
                        owner, owner_i = current, i
                        i += 1
                        base = i
                        current = entry
                        current_schema = tc_node
                        tc_matched = True
                        break
            if tc_matched:
                continue

            # Unknown token — join remaining as a single key
            tags[i] = here
            _keep_whole(current, tokens, i, tags)
            return

        child = children[schema_key]

        # Named list (check before leaf/presence — nodes with L+p must use L).
        # The key fields come from the tree, one token each. A key the tokens
        # cannot complete, or a token after an entry that has nothing but its
        # key, is a statement the device rejects: kept whole, from here.
        if child.get("L"):
            if i + 1 == len(tokens):
                # A bare list keyword. A list of names alone stands bare, as
                # the device brings it into being (`snmp filter-interfaces
                # interfaces`); a list keyed otherwise has no key value, a
                # statement the reader cannot complete, kept whole.
                if entry_keys(child) != ("name",):
                    tags[i] = here
                    _keep_whole(current, tokens, i, tags)
                    return
                if statement_children(child):
                    current.setdefault(token, [])
                else:
                    current[token] = [None]
                _mark(current, here, token)
                return
            read = read_entry_key(child, tokens, i + 1)
            if read is None:
                tags[i] = here
                _keep_whole(current, tokens, i, tags)
                return
            key, after = read
            entries = current.get(token, [])
            if after < len(tokens) and not statement_children(child):
                # A surplus after an entry that has nothing but its key.
                tags[i] = here
                _keep_whole(current, tokens, i, tags)
                return
            current[token] = entries
            entry = _find_or_create_entry(entries, key, index)
            # The entry ends after its key: a tag on `route 0.0.0.0/0
            # next-hop 10.0.0.1` is the route's. Where the keyword stands
            # alone on its line -- `source-prefix-list { inactive: PL1; }`,
            # as the device writes a list of bare names -- a tag on the
            # keyword is the whole list's (`deactivate … source-prefix-list`)
            # and one on the key's line is the entry's.
            alone = i + 1 in tags
            on_key: frozenset[str] = frozenset()
            for k in range(i + 1, after):
                on_key |= tags.pop(k, frozenset())
            if alone:
                _mark(current, here, token)
                _mark(entry, on_key)
            else:
                _mark(entry, here | on_key)
            if after == len(tokens):
                return
            owner, owner_i = current, i
            current = entry
            current_schema = child
            i = base = after
            continue

        # Leaf node (accumulate repeated values). A tag is the leaf's, never
        # its value's: `inactive: vlan-id 751;` is `<vlan-id inactive=…>751`.
        if child.get("l"):
            if i + 1 == len(tokens):
                # A leaf without its value is a statement the device rejects
                # (`set system host-name`). It used to replace a value read
                # before it with `null`, without a word (NEW-C1).
                tags[i] = here
                _keep_whole(current, tokens, i, tags)
                if reading is not None:
                    reading.incomplete = True
                return
            if curly and token in current and current.get(f"@{token}", {}) != _tag_attrs(here):
                # `members 64496:1; inactive: members 64496:2;`: the device
                # rejects a tag on one value (`deactivate … members 64496:2`
                # is a syntax error), and widening it deactivates the other.
                raise ValueError(
                    f"Invalid structured input: '{token}' tags some of its values and not "
                    "others; Junos tags a leaf as a whole"
                )
            _mark(current, here, token)
            is_leaf_list = child.get("ll")
            # Check if token after the value is a schema sibling
            next_idx = i + 2
            if next_idx < len(tokens) and statement_key(children, tokens[next_idx]) in children:
                # Sibling follows — take only one token as value
                val = _leaf_value(tokens[i + 1], child)
                current[token] = [val] if is_leaf_list else val
                i = next_idx
                base = _cut(reading, base, i)
                continue
            # No sibling — join all remaining tokens as the value
            val = _leaf_value(" ".join(tokens[i + 1 :]), child)
            existing = current.get(token)
            if existing is not None:
                if isinstance(existing, list):
                    existing.append(val)
                else:
                    current[token] = [existing, val]
            else:
                current[token] = [val] if is_leaf_list else val
            return

        # Presence flag
        if child.get("p"):
            current[token] = [None]
            _mark(current, here, token)
            i += 1
            if i < len(tokens):
                base = _cut(reading, base, i)
                continue  # Let main loop handle next token (sibling or nokeyword)
            return

        # Regular container
        if child.get("c"):
            owner, owner_i = current, i
            current = current.setdefault(token, {})
            if here and passes_tag_to_child(child) and i + 1 < len(tokens) and i + 1 not in tags:
                # `inactive: family inet {` marks `inet`: the device never
                # tags `family` (`deactivate … family` is rejected). On a line
                # of its own, `inactive: family {` tags `family` itself, which
                # field validation reports.
                tags[i + 1] = here
            else:
                _mark(current, here)
            current_schema = child
            i += 1
            base = i
            continue

        # A schema node of no type the reader knows: keep the line whole from
        # here, as the unknown-token path does, rather than one token of it.
        tags[i] = here
        _keep_whole(current, tokens, i, tags)
        return


# ── Meta command handling ────────────────────────────────────────────


def _apply_meta(
    config: dict[str, Any],
    tokens: list[str],
    schema: dict[str, Any],
    attr_key: str,
    attr_value: Any,
    index: _EntryIndex,
) -> None:
    """Apply a meta attribute where the verb line's path ends.

    `meta_target` walks the path read only, as set validation does; this
    creates the containers and entries its steps name and sets the ``@`` or
    ``@key`` attribute. A path the device cannot tag is refused with an error
    naming it: the keyword of a list the XSD does not mark `homogeneous`
    without its entry's name (QFX5120 25.2R2-S1.5: "syntax error, expecting
    <identifier>", probe D5) and a leaf's value (probe A2). One the tree does
    not place, or that stops inside an entry's key, is kept whole.
    """
    target = meta_target(tokens, schema)
    current = config
    for step in target.steps:
        holder = current.setdefault(step.under, {}) if step.under else current
        if step.entry is None:
            current = holder.setdefault(step.key, {})
        else:
            current = _find_or_create_entry(holder.setdefault(step.key, []), step.entry, index)

    if target.kind == "entry":
        current.setdefault("@", {})[attr_key] = attr_value
    elif target.kind in ("leaf", "whole-list"):
        current.setdefault(f"@{target.key}", {})[attr_key] = attr_value
    elif target.kind in ("container", "merged"):
        # A merged container's tag is read as written; the writers drop it with
        # a note, as the device never tags one (`passes_tag_to_child`).
        current.setdefault(target.key, {}).setdefault("@", {})[attr_key] = attr_value
    elif target.kind == "list":
        raise ValueError("Metadata commands cannot target a list without its entry's name")
    elif target.kind == "value":
        raise ValueError("Metadata commands cannot target scalar-leaf values")
    elif not (
        target.kind == "unplaced"
        and target.at == len(tokens) - 1
        and _tag_an_entry_held(current, target.node, tokens[-1], attr_key, attr_value)
    ):
        _keep_meta_whole(current, tokens, target.at, attr_key, attr_value)


def _tag_an_entry_held(
    current: dict[str, Any],
    node: dict[str, Any] | None,
    token: str,
    attr_key: str,
    attr_value: Any,
) -> bool:
    """Tag the entry named *token* of a child's hidden list *current* already
    holds; the last token of a path has no next one to tell the list by."""
    name = set_token_value(token)
    for parent_key, parent_node in statement_children(node or {}).items():
        if not isinstance(parent_node, dict):
            continue
        tc_name = parent_node.get("t")
        tc_node = parent_node.get("c", {}).get(tc_name) if tc_name else None
        if not tc_node or not tc_node.get("L"):
            continue
        parent_dict = current.get(parent_key)
        existing = parent_dict.get(tc_name) if isinstance(parent_dict, dict) else None
        if not isinstance(existing, list):
            continue
        for item in existing:
            if isinstance(item, dict) and item.get("name") == name:
                item.setdefault("@", {})[attr_key] = attr_value
                return True
    return False
