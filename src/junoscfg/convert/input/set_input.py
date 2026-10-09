"""Convert display set commands to the JSON dict IR.

Parses display set/deactivate/protect/delete/activate commands and builds
a Junos JSON dict using the schema tree for type inference.
"""

from __future__ import annotations

from typing import Any

from junoscfg.display import (
    KEY_ALIASES,
    entry_keys,
    load_schema_tree,
    statement_children,
    statement_name_spellings,
)
from junoscfg.input import find_unsupported_set_brackets, normalize


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
        raise ValueError(bracket_findings[0][1])

    content = normalize(source)
    lines = [line.strip() for line in content.split("\n") if line.strip()]

    schema = load_schema_tree()
    config: dict[str, Any] = {}
    index: _EntryIndex = {}

    for line in lines:
        if line.startswith("set "):
            tokens = _tokenize(line[4:])
            if tokens:
                _merge_tokens(config, tokens, schema, index)
        elif line == "set":
            pass  # bare "set" with no tokens
        elif line.startswith("deactivate "):
            tokens = _tokenize(line[11:])
            if tokens:
                _apply_meta(config, tokens, schema, "inactive", True, index)
        elif line.startswith("protect "):
            tokens = _tokenize(line[8:])
            if tokens:
                _apply_meta(config, tokens, schema, "protect", "protect", index)
        elif line.startswith("delete "):
            tokens = _tokenize(line[7:])
            if tokens:
                _apply_meta(config, tokens, schema, "operation", "delete", index)
        elif line.startswith("activate "):
            tokens = _tokenize(line[9:])
            if tokens:
                _apply_meta(config, tokens, schema, "active", "active", index)
        elif line.startswith("replace "):
            # Pseudo command emitted by the structured-input bridge
            # (SetConverter with emit_replace=True); not display-set syntax.
            tokens = _tokenize(line[8:])
            if tokens:
                _apply_meta(config, tokens, schema, "operation", "replace", index)

    return config


# ── Tokenizer ────────────────────────────────────────────────────────


def _tokenize(line: str) -> list[str]:
    """Tokenize a set command line, preserving quoted strings with quotes.

    Splits on whitespace but keeps quoted strings (including their quotes)
    as single tokens.
    """
    tokens: list[str] = []
    i = 0
    n = len(line)

    while i < n:
        while i < n and line[i] == " ":
            i += 1
        if i >= n:
            break

        if line[i] == '"':
            j = i + 1
            while j < n and line[j] != '"':
                if line[j] == "\\" and j + 1 < n:
                    j += 2
                else:
                    j += 1
            if j < n:
                j += 1
            tokens.append(line[i:j])
            i = j
        else:
            j = i
            while j < n and line[j] != " ":
                j += 1
            tokens.append(line[i:j])
            i = j

    return tokens


# ── Value parsing ────────────────────────────────────────────────────


def _parse_value(token: str) -> str:
    """Convert a tokenized value back to its dict representation.

    Strips surrounding quotes and unescapes if needed.
    """
    if len(token) >= 2 and token[0] == '"' and token[-1] == '"':
        inner = token[1:-1]
        return inner.replace('\\"', '"').replace("\\\\", "\\")
    return token


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


def _is_keyword_field(leaf: Any) -> bool:
    """Whether a key field is written `keyword value`: a leaf not `nokeyword`."""
    return isinstance(leaf, dict) and bool(leaf.get("l")) and not leaf.get("nk")


def _read_key(
    list_node: dict[str, Any], tokens: list[str], j: int
) -> tuple[dict[str, Any], int] | None:
    """The key of an entry of *list_node* read from ``tokens[j:]``, and where it ends.

    One token per positional field, in declared order; a field whose leaf is
    not `nokeyword` as `keyword value`, those fields in any order among
    themselves after the positional ones; a choice of identifiers as one of
    its keywords, with its value where the alternative is a leaf, before or
    after all of them. The device accepts `then community SAMPLE-COMM add`,
    `route-filter exact 198.51.100.0/24` and `virtual-link transit-area
    0.0.0.3 neighbor-id 10.255.255.2`, and rejects a keyword field given
    without its keyword or left out (device probe, vMX 23.2R2-S7.5). The key
    comes back in declared order, the device's. None when the tokens run out
    first, or a token is not the keyword a field needs: a statement the
    device rejects.
    """
    children = list_node.get("c", {})
    fields = list(entry_keys(list_node))
    choices = [field for field in fields if isinstance(field, tuple)]
    keyworded = [
        field
        for field in fields
        if not isinstance(field, tuple) and _is_keyword_field(children.get(field))
    ]
    positional = [f for f in fields if not isinstance(f, tuple) and f not in keyworded]
    found: dict[str | tuple[str, ...], tuple[str, Any]] = {}

    def read_choices(j: int) -> int | None:
        for field in choices:
            if j >= len(tokens) or KEY_ALIASES.get(tokens[j], tokens[j]) not in field:
                return None
            token = tokens[j]
            if children.get(KEY_ALIASES.get(token, token), {}).get("l"):
                if j + 1 >= len(tokens):
                    return None
                found[field] = (token, _parse_value(tokens[j + 1]))
                j += 2
            else:
                found[field] = (token, [None])
                j += 1
        return j

    leads = j < len(tokens) and any(KEY_ALIASES.get(tokens[j], tokens[j]) in c for c in choices)
    if leads and (j := read_choices(j)) is None:
        return None
    for field in positional:
        if j >= len(tokens):
            return None
        found[field] = (field, _parse_value(tokens[j]))
        j += 1
    pending = list(keyworded)
    while pending:
        if j + 1 >= len(tokens) or tokens[j] not in pending:
            return None
        pending.remove(tokens[j])
        found[tokens[j]] = (tokens[j], _parse_value(tokens[j + 1]))
        j += 2
    if not leads and (j := read_choices(j)) is None:
        return None
    return dict(found[field] for field in fields), j


def _keep_whole(current: dict[str, Any], tokens: list[str], i: int) -> None:
    """Keep ``tokens[i:]`` as one statement the reader could not place.

    Field validation reports it `UNPLACED` and every writer reproduces it, so
    nothing of a line the reader cannot complete is applied or dropped.
    """
    current.setdefault(" ".join(_parse_value(t) for t in tokens[i:]), True)


# ── Core token walking ──────────────────────────────────────────────


def _merge_tokens(
    config: dict[str, Any], tokens: list[str], schema: dict[str, Any], index: _EntryIndex
) -> None:
    """Walk tokens against the schema tree and merge into config dict."""
    current = config
    current_schema = schema
    i = 0
    # Where the statement holding `current` starts, and the node above it.
    owner, owner_i = config, 0

    while i < len(tokens):
        token = tokens[i]
        children = statement_children(current_schema)

        # Apply-groups (not in the schema, handled specially). It takes one
        # group; `set apply-groups G1 G2` and a bare `set apply-groups` are
        # statements the device rejects. A group after a bare one, which is
        # kept whole under the same key, is kept whole as well.
        if token in ("apply-groups", "apply-groups-except"):
            lst = current.get(token, [])
            if i + 2 != len(tokens) or not isinstance(lst, list):
                _keep_whole(current, tokens, i)
                return
            val = _parse_value(tokens[i + 1])
            current[token] = lst
            if val not in lst:
                lst.append(val)
            return

        # Apply-macro (not in the schema). It takes a name, then optionally a
        # keyword and that keyword's value; the device rejects a fourth value
        # (device probe, vMX 23.2R2-S7.5), which used to become a second data
        # entry without a word.
        if token == "apply-macro" and i + 1 < len(tokens):
            lst = current.get("apply-macro", [])
            if len(tokens) - i > 4 or not isinstance(lst, list):
                _keep_whole(current, tokens, i)
                return
            current["apply-macro"] = lst
            entry = _find_or_create_entry(lst, {"name": _parse_value(tokens[i + 1])}, index)
            if i + 2 < len(tokens):
                pair = dict(
                    zip(("name", "value"), map(_parse_value, tokens[i + 2 :]), strict=False)
                )
                entry.setdefault("data", []).append(pair)
            return

        # Resolve key alias for schema lookup (e.g., ieee-802.3ad → 802.3ad)
        schema_key = KEY_ALIASES.get(token, token)

        if schema_key not in children:
            # Check transparent container
            transparent = current_schema.get("t")
            if transparent and transparent in children:
                tc_child = children[transparent]
                name = _parse_value(token)
                lst = current.setdefault(transparent, [])
                entry = _find_or_create_entry(lst, {"name": name}, index)
                owner, owner_i = current, i
                i += 1
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
                        if after not in children and KEY_ALIASES.get(after, after) not in children:
                            break
                    if _is_statement_name(cname, cnode, token):
                        current[token] = [None]
                    elif current.get(cname, _parse_value(token)) != _parse_value(token):
                        # A second, different value: this node is no list, so
                        # writing it would replace the first without a word --
                        # three forwarding classes read as one, while the
                        # parser counted only `unbounded` as a list. Kept
                        # whole from the node's own keyword.
                        _keep_whole(owner, tokens, owner_i)
                        return
                    else:
                        current[cname] = _parse_value(token)
                    i += 1
                    nk_found = True
                    break
            if nk_found:
                if i < len(tokens):
                    continue  # Process sibling tokens
                return

            # Check transparent-list-key children (tk flag).
            # E.g., prefix-list-item inside prefix-list, contents inside
            # syslog file.  The token is the entry name for the hidden list.
            tk_matched = False
            for cname, cnode in children.items():
                if not isinstance(cnode, dict) or not cnode.get("tk"):
                    continue
                name = _parse_value(token)
                lst = current.setdefault(cname, [])
                entry = _find_or_create_entry(lst, {"name": name}, index)
                i += 1
                if i < len(tokens):
                    owner, owner_i = current, i - 1
                    current = entry
                    current_schema = cnode
                    tk_matched = True
                else:
                    return  # Entry created, no more tokens
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
                next_key = KEY_ALIASES.get(next_token, next_token)
                for parent_key, parent_node in children.items():
                    if not isinstance(parent_node, dict):
                        continue
                    tc_name = parent_node.get("t")
                    if not tc_name:
                        continue
                    tc_node = parent_node.get("c", {}).get(tc_name)
                    if not tc_node or not tc_node.get("L"):
                        continue
                    if next_key in statement_children(tc_node):
                        # Match — descend into parent → transparent list → entry
                        name = _parse_value(token)
                        parent = current.setdefault(parent_key, {})
                        lst = parent.setdefault(tc_name, [])
                        entry = _find_or_create_entry(lst, {"name": name}, index)
                        owner, owner_i = current, i
                        i += 1
                        current = entry
                        current_schema = tc_node
                        tc_matched = True
                        break
            if tc_matched:
                continue

            # Unknown token — join remaining as a single key
            _keep_whole(current, tokens, i)
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
                    _keep_whole(current, tokens, i)
                elif statement_children(child):
                    current.setdefault(token, [])
                else:
                    current[token] = [None]
                return
            read = _read_key(child, tokens, i + 1)
            if read is None:
                _keep_whole(current, tokens, i)
                return
            key, after = read
            entries = current.get(token, [])
            if (after < len(tokens) and not statement_children(child)) or not isinstance(
                entries, list
            ):
                # A surplus after an entry that has nothing but its key, or a
                # full entry after a bare keyword kept whole under this key.
                _keep_whole(current, tokens, i)
                return
            current[token] = entries
            entry = _find_or_create_entry(entries, key, index)
            if after == len(tokens):
                return
            owner, owner_i = current, i
            current = entry
            current_schema = child
            i = after
            continue

        # Leaf node (accumulate repeated values)
        if child.get("l"):
            is_leaf_list = child.get("ll")
            if i + 1 < len(tokens):
                # Check if token after the value is a schema sibling
                next_idx = i + 2
                if next_idx < len(tokens) and (
                    tokens[next_idx] in children
                    or KEY_ALIASES.get(tokens[next_idx], tokens[next_idx]) in children
                ):
                    # Sibling follows — take only one token as value
                    val = _parse_value(tokens[i + 1])
                    current[token] = [val] if is_leaf_list else val
                    i = next_idx
                    continue
                # No sibling — join all remaining tokens as the value
                val = _parse_value(" ".join(tokens[i + 1 :]))
                existing = current.get(token)
                if existing is not None:
                    if isinstance(existing, list):
                        existing.append(val)
                    else:
                        current[token] = [existing, val]
                else:
                    current[token] = [val] if is_leaf_list else val
            else:
                current[token] = None
            return

        # Presence flag
        if child.get("p"):
            current[token] = [None]
            i += 1
            if i < len(tokens):
                continue  # Let main loop handle next token (sibling or nokeyword)
            return

        # Regular container
        if child.get("c"):
            owner, owner_i = current, i
            current = current.setdefault(token, {})
            current_schema = child
            i += 1
            continue

        # A schema node of no type the reader knows: keep the line whole from
        # here, as the unknown-token path does, rather than one token of it.
        _keep_whole(current, tokens, i)
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
    """Apply a meta attribute to the target node in the config dict.

    Walks the token path to find the target, then sets the ``@`` or
    ``@key`` attribute as appropriate.
    """
    current = config
    current_schema = schema
    i = 0

    while i < len(tokens):
        token = tokens[i]
        children = statement_children(current_schema)

        # Resolve key alias for schema lookup (e.g., ieee-802.3ad → 802.3ad)
        schema_key = KEY_ALIASES.get(token, token)

        if schema_key not in children:
            # Check transparent container
            transparent = current_schema.get("t")
            if transparent and transparent in children:
                tc_child = children[transparent]
                name = _parse_value(token)
                lst = current.setdefault(transparent, [])
                entry = _find_or_create_entry(lst, {"name": name}, index)
                i += 1
                if i >= len(tokens):
                    entry.setdefault("@", {})[attr_key] = attr_value
                    return
                current = entry
                current_schema = tc_child
                continue

            # Check transparent-list-key children (tk flag).
            tk_matched = False
            for cname, cnode in children.items():
                if not isinstance(cnode, dict) or not cnode.get("tk"):
                    continue
                name = _parse_value(token)
                lst = current.setdefault(cname, [])
                entry = _find_or_create_entry(lst, {"name": name}, index)
                i += 1
                if i >= len(tokens):
                    entry.setdefault("@", {})[attr_key] = attr_value
                    return
                current = entry
                current_schema = cnode
                tk_matched = True
                break
            if tk_matched:
                continue

            # Check if token is a name in a child's transparent named list.
            tc_matched = False
            if i + 1 < len(tokens):
                next_token = tokens[i + 1]
                next_key = KEY_ALIASES.get(next_token, next_token)
                for parent_key, parent_node in children.items():
                    if not isinstance(parent_node, dict):
                        continue
                    tc_name = parent_node.get("t")
                    if not tc_name:
                        continue
                    tc_node = parent_node.get("c", {}).get(tc_name)
                    if not tc_node or not tc_node.get("L"):
                        continue
                    if next_key in statement_children(tc_node):
                        name = _parse_value(token)
                        parent = current.setdefault(parent_key, {})
                        lst = parent.setdefault(tc_name, [])
                        entry = _find_or_create_entry(lst, {"name": name}, index)
                        i += 1
                        if i >= len(tokens):
                            entry.setdefault("@", {})[attr_key] = attr_value
                            return
                        current = entry
                        current_schema = tc_node
                        tc_matched = True
                        break
            if tc_matched:
                continue

            # No look-ahead possible (last token) — check if the name
            # already exists in a child's transparent named list.
            if i == len(tokens) - 1:
                name = _parse_value(token)
                for parent_key, parent_node in children.items():
                    if not isinstance(parent_node, dict):
                        continue
                    tc_name = parent_node.get("t")
                    if not tc_name:
                        continue
                    tc_node = parent_node.get("c", {}).get(tc_name)
                    if not tc_node or not tc_node.get("L"):
                        continue
                    # Only match if the entry already exists in config
                    parent_dict = current.get(parent_key)
                    if not isinstance(parent_dict, dict):
                        continue
                    existing_list = parent_dict.get(tc_name)
                    if not isinstance(existing_list, list):
                        continue
                    for item in existing_list:
                        if isinstance(item, dict) and item.get("name") == name:
                            item.setdefault("@", {})[attr_key] = attr_value
                            return

            # Unknown path — apply to current
            current.setdefault("@", {})[attr_key] = attr_value
            return

        child = children[schema_key]

        # Last token — determine target type
        if i == len(tokens) - 1:
            if child.get("L") or child.get("l") or child.get("p"):
                # List/leaf/presence: use sibling @key format
                current.setdefault(f"@{token}", {})[attr_key] = attr_value
            else:
                # Container: use inline @ format
                sub = current.setdefault(token, {})
                sub.setdefault("@", {})[attr_key] = attr_value
            return

        # Named list: descend into the entry its whole key names
        read = _read_key(child, tokens, i + 1) if child.get("L") else None
        if read is not None:
            key, i = read
            entry = _find_or_create_entry(current.setdefault(token, []), key, index)
            if i >= len(tokens):
                entry.setdefault("@", {})[attr_key] = attr_value
                return
            current = entry
            current_schema = child
            continue

        # Container, so descend
        if child.get("c"):
            current = current.setdefault(token, {})
            current_schema = child
            i += 1
            continue

        # Scalar leaf followed by its value token(s): annotate the leaf and
        # ignore the trailing value (e.g. "deactivate system host-name r1")
        if child.get("l"):
            current.setdefault(f"@{token}", {})[attr_key] = attr_value
            return

        # Fallback
        current.setdefault("@", {})[attr_key] = attr_value
        return
