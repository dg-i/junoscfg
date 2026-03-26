"""Convert display set commands to the JSON dict IR.

Parses display set/deactivate/protect/delete/activate commands and builds
a Junos JSON dict using the schema tree for type inference.
"""

from __future__ import annotations

from typing import Any

from junoscfg.display.constants import KEY_ALIASES, load_schema_tree
from junoscfg.input import normalize


def set_to_dict(source: str) -> dict[str, Any]:
    """Parse display set commands into the IR dict.

    Handles ``set``, ``deactivate``, ``protect``, ``delete``, and
    ``activate`` commands.
    """
    content = normalize(source)
    lines = [line.strip() for line in content.split("\n") if line.strip()]

    schema = load_schema_tree()
    config: dict[str, Any] = {}

    for line in lines:
        if line.startswith("set "):
            tokens = _tokenize(line[4:])
            if tokens:
                _merge_tokens(config, tokens, schema)
        elif line == "set":
            pass  # bare "set" with no tokens
        elif line.startswith("deactivate "):
            tokens = _tokenize(line[11:])
            if tokens:
                _apply_meta(config, tokens, schema, "inactive", True)
        elif line.startswith("protect "):
            tokens = _tokenize(line[8:])
            if tokens:
                _apply_meta(config, tokens, schema, "protect", "protect")
        elif line.startswith("delete "):
            tokens = _tokenize(line[7:])
            if tokens:
                _apply_meta(config, tokens, schema, "operation", "delete")
        elif line.startswith("activate "):
            tokens = _tokenize(line[9:])
            if tokens:
                _apply_meta(config, tokens, schema, "active", "active")

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


def _find_or_create_entry(lst: list[Any], name: str, key: str = "name") -> dict[str, Any]:
    """Find existing list entry with matching key value, or create new one."""
    for item in lst:
        if isinstance(item, dict) and item.get(key) == name:
            return item
    entry: dict[str, Any] = {key: name}
    lst.append(entry)
    return entry


# ── Core token walking ──────────────────────────────────────────────


def _merge_tokens(config: dict[str, Any], tokens: list[str], schema: dict[str, Any]) -> None:
    """Walk tokens against the schema tree and merge into config dict."""
    current = config
    current_schema = schema
    i = 0

    while i < len(tokens):
        token = tokens[i]
        children = current_schema.get("c", {})

        # Apply-groups (not in the schema, handled specially)
        if token in ("apply-groups", "apply-groups-except"):
            if i + 1 < len(tokens):
                val = _parse_value(tokens[i + 1])
                lst = current.setdefault(token, [])
                if val not in lst:
                    lst.append(val)
            return

        # Apply-macro (not in the schema)
        if token == "apply-macro" and i + 1 < len(tokens):
            name = _parse_value(tokens[i + 1])
            lst = current.setdefault("apply-macro", [])
            entry = _find_or_create_entry(lst, name)
            i += 2
            while i < len(tokens):
                k = _parse_value(tokens[i])
                data = entry.setdefault("data", [])
                if i + 1 < len(tokens):
                    v = _parse_value(tokens[i + 1])
                    data.append({"name": k, "value": v})
                    i += 2
                else:
                    data.append({"name": k})
                    i += 1
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
                entry = _find_or_create_entry(lst, name)
                i += 1
                current = entry
                current_schema = tc_child
                continue

            # Check nokeyword leaf
            nk_found = False
            for cname, cnode in children.items():
                if isinstance(cnode, dict) and cnode.get("nk") and cnode.get("l"):
                    current[cname] = _parse_value(token)
                    i += 1
                    nk_found = True
                    break
            if nk_found:
                if i < len(tokens) and (
                    tokens[i] in children or KEY_ALIASES.get(tokens[i], tokens[i]) in children
                ):
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
                entry = _find_or_create_entry(lst, name)
                i += 1
                if i < len(tokens):
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
                    tc_children = tc_node.get("c", {})
                    if next_key in tc_children:
                        # Match — descend into parent → transparent list → entry
                        name = _parse_value(token)
                        parent = current.setdefault(parent_key, {})
                        lst = parent.setdefault(tc_name, [])
                        entry = _find_or_create_entry(lst, name)
                        i += 1
                        current = entry
                        current_schema = tc_node
                        tc_matched = True
                        break
            if tc_matched:
                continue

            # Unknown token — join remaining as a single key
            remaining = " ".join(_parse_value(t) for t in tokens[i:])
            current[remaining] = True
            return

        child = children[schema_key]

        # Named list (check before leaf/presence — nodes with L+p must use L)
        if child.get("L"):
            has_children = bool(child.get("c"))
            if i + 1 < len(tokens):
                name = _parse_value(tokens[i + 1])
                lst = current.setdefault(token, [])
                fe = child.get("fe")
                entry_key = fe["k"] if fe and fe["k"] else "name"
                if has_children and child.get("o") and name in child.get("c", {}):
                    # Action-first pattern: "community add VALUE"
                    # The next token is a schema child (action keyword), not the entry name.
                    action = name
                    action_node = child["c"][action]
                    if i + 2 < len(tokens):
                        real_name = _parse_value(tokens[i + 2])
                        entry_dict = {"community-name": real_name}
                        entry_dict[action] = [None] if action_node.get("p") else True
                        lst.append(entry_dict)
                        i += 3
                        if i < len(tokens):
                            # More tokens after the value — continue walking
                            current = entry_dict
                            current_schema = child
                            continue
                    else:
                        # Just "community add" with no value
                        entry_dict = {action: [None] if action_node.get("p") else True}
                        lst.append(entry_dict)
                    return
                elif has_children:
                    entry = _find_or_create_entry(lst, name, entry_key)
                    i += 2
                    if i < len(tokens):
                        current = entry
                        current_schema = child
                        continue
                    # No more tokens — entry exists with just the key
                    return
                elif fe:
                    # Flat entry without schema children (e.g. attributes-match).
                    # Store all remaining tokens as ordered values so the
                    # values-only output handler can reconstruct the line.
                    entry_dict: dict[str, Any] = {entry_key: name}
                    for vn, j in enumerate(range(i + 2, len(tokens))):
                        entry_dict[f"_v{vn}"] = _parse_value(tokens[j])
                    lst.append(entry_dict)
                    return
                else:
                    _find_or_create_entry(lst, name, entry_key)
                    return
            else:
                if child.get("p"):
                    current[token] = [None]
                else:
                    current.setdefault(token, [])
                return

        # Leaf node (accumulate repeated values)
        if child.get("l"):
            if i + 1 < len(tokens):
                # Check if token after the value is a schema sibling
                next_idx = i + 2
                if next_idx < len(tokens) and (
                    tokens[next_idx] in children
                    or KEY_ALIASES.get(tokens[next_idx], tokens[next_idx]) in children
                ):
                    # Sibling follows — take only one token as value
                    current[token] = _parse_value(tokens[i + 1])
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
                    current[token] = val
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
            current = current.setdefault(token, {})
            current_schema = child
            i += 1
            continue

        # Unknown node type
        if i + 1 < len(tokens):
            current[token] = _parse_value(tokens[i + 1])
        else:
            current[token] = None
        return


# ── Meta command handling ────────────────────────────────────────────


def _apply_meta(
    config: dict[str, Any],
    tokens: list[str],
    schema: dict[str, Any],
    attr_key: str,
    attr_value: Any,
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
        children = current_schema.get("c", {})

        # Resolve key alias for schema lookup (e.g., ieee-802.3ad → 802.3ad)
        schema_key = KEY_ALIASES.get(token, token)

        if schema_key not in children:
            # Check transparent container
            transparent = current_schema.get("t")
            if transparent and transparent in children:
                tc_child = children[transparent]
                name = _parse_value(token)
                lst = current.setdefault(transparent, [])
                entry = _find_or_create_entry(lst, name)
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
                entry = _find_or_create_entry(lst, name)
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
                    tc_children = tc_node.get("c", {})
                    if next_key in tc_children:
                        name = _parse_value(token)
                        parent = current.setdefault(parent_key, {})
                        lst = parent.setdefault(tc_name, [])
                        entry = _find_or_create_entry(lst, name)
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

        # Named list: descend into entry
        if child.get("L") and i + 1 < len(tokens):
            name = _parse_value(tokens[i + 1])
            lst = current.setdefault(token, [])
            fe = child.get("fe")
            entry_key = fe["k"] if fe and fe["k"] else "name"
            entry = _find_or_create_entry(lst, name, entry_key)
            i += 2
            if i >= len(tokens):
                entry.setdefault("@", {})[attr_key] = attr_value
                return
            current = entry
            current_schema = child
            continue

        # Container: descend
        if child.get("c"):
            current = current.setdefault(token, {})
            current_schema = child
            i += 1
            continue

        # Fallback
        current.setdefault("@", {})[attr_key] = attr_value
        return
