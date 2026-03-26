"""Resolve dot-separated paths with wildcards against nested dicts/lists."""

from __future__ import annotations

import re
from fnmatch import fnmatch

_BRACKET_RE = re.compile(r"^(.+)\[(.+)\]$")


def _has_glob(s: str) -> bool:
    """Return True if *s* contains glob metacharacters (but is not just ``*``)."""
    return s != "*" and ("*" in s or "?" in s or "[" in s)


def _parse_path(path: str) -> list[tuple[str, str]]:
    """Parse a dot-separated path into (key, kind) segments.

    *kind* is one of:

    - ``"key"`` — fixed dict key
    - ``"list"`` — ``[*]`` iterate all list items
    - ``"match:VALUE"`` — ``[VALUE]`` select list item where ``name == VALUE``
    - ``"glob:PATTERN"`` — ``[PATTERN]`` select list items where ``name`` matches glob
    - ``"dict"`` — ``*`` iterate all dict-valued children
    - ``"dictglob"`` — ``pattern*`` iterate dict children whose key matches glob

    Examples::

        a.b[*].c          -> [("a", "key"), ("b", "list"), ("c", "key")]
        family.*           -> [("family", "key"), ("", "dict")]
        groups[foo-bar]    -> [("groups", "match:foo-bar")]
        groups[ansible-*]  -> [("groups", "glob:ansible-*")]
        family.inet*       -> [("family", "key"), ("inet*", "dictglob")]
    """
    segments: list[tuple[str, str]] = []
    for part in path.split("."):
        if part == "*":
            segments.append(("", "dict"))
            continue
        m = _BRACKET_RE.match(part)
        if m:
            key, bracket = m.group(1), m.group(2)
            if bracket == "*":
                segments.append((key, "list"))
            elif _has_glob(bracket):
                segments.append((key, f"glob:{bracket}"))
            else:
                segments.append((key, f"match:{bracket}"))
        elif _has_glob(part):
            segments.append((part, "dictglob"))
        else:
            segments.append((part, "key"))
    return segments


def resolve_path(data: dict, path: str) -> list[dict]:
    """Walk *data* along *path* and return all matching dict nodes.

    ``[*]`` segments iterate list items (non-dict items are skipped).
    ``[value]`` segments select the list item where ``name == value``.
    Missing keys or type mismatches silently return an empty list.
    """
    segments = _parse_path(path)
    current: list[dict] = [data]

    for key, kind in segments:
        next_nodes: list[dict] = []
        for node in current:
            if kind == "dict":
                for v in node.values():
                    if isinstance(v, dict):
                        next_nodes.append(v)
            elif kind == "dictglob":
                for k, v in node.items():
                    if isinstance(v, dict) and fnmatch(k, key):
                        next_nodes.append(v)
            elif kind.startswith("glob:"):
                pattern = kind[5:]
                value = node.get(key)
                if not isinstance(value, list):
                    continue
                for item in value:
                    if isinstance(item, dict) and fnmatch(str(item.get("name", "")), pattern):
                        next_nodes.append(item)
            elif kind.startswith("match:"):
                match_name = kind[6:]
                value = node.get(key)
                if not isinstance(value, list):
                    continue
                for item in value:
                    if isinstance(item, dict) and item.get("name") == match_name:
                        next_nodes.append(item)
            else:
                value = node.get(key)
                if value is None:
                    continue
                if kind == "list":
                    if isinstance(value, list):
                        next_nodes.extend(item for item in value if isinstance(item, dict))
                else:
                    if isinstance(value, dict):
                        next_nodes.append(value)
        current = next_nodes

    return current


def resolve_path_with_context(data: dict, path: str, leaf_key: str) -> list[tuple[dict, list[str]]]:
    """Like :func:`resolve_path` but track discriminator components.

    Returns ``(matched_node, discriminators)`` tuples where *discriminators*
    is a list of strings identifying each wildcard step.

    For ``[*]`` list segments the discriminator is ``item["name"]``, unless
    *leaf_key* is ``"name"`` **and** this is the last ``[*]`` in *path* — then
    the list index is used (because the name IS the extracted value).

    For ``*`` dict segments the discriminator is the dict key.

    ``[value]`` named-match segments do not add a discriminator — they are
    fixed filters, not wildcards.
    """
    segments = _parse_path(path)
    # Find last list-wildcard index for the terminal-list rule
    last_list_idx = -1
    for i, (_key, kind) in enumerate(segments):
        if kind == "list":
            last_list_idx = i

    current: list[tuple[dict, list[str]]] = [(data, [])]

    for seg_idx, (key, kind) in enumerate(segments):
        next_entries: list[tuple[dict, list[str]]] = []
        for node, discs in current:
            if kind == "dict":
                for k, v in node.items():
                    if isinstance(v, dict):
                        next_entries.append((v, discs + [k]))
            elif kind == "dictglob":
                for k, v in node.items():
                    if isinstance(v, dict) and fnmatch(k, key):
                        next_entries.append((v, discs + [k]))
            elif kind.startswith("glob:"):
                pattern = kind[5:]
                value = node.get(key)
                if not isinstance(value, list):
                    continue
                for item in value:
                    if isinstance(item, dict) and fnmatch(str(item.get("name", "")), pattern):
                        # Glob is a wildcard — add name as discriminator
                        next_entries.append((item, discs + [str(item.get("name", ""))]))
            elif kind.startswith("match:"):
                match_name = kind[6:]
                value = node.get(key)
                if not isinstance(value, list):
                    continue
                for item in value:
                    if isinstance(item, dict) and item.get("name") == match_name:
                        # Named match is a fixed filter — no discriminator added
                        next_entries.append((item, discs))
            else:
                value = node.get(key)
                if value is None:
                    continue
                if kind == "list":
                    if not isinstance(value, list):
                        continue
                    use_index = leaf_key == "name" and seg_idx == last_list_idx
                    for i, item in enumerate(value):
                        if not isinstance(item, dict):
                            continue
                        disc = str(i) if use_index else str(item.get("name", i))
                        next_entries.append((item, discs + [disc]))
                else:
                    if isinstance(value, dict):
                        next_entries.append((value, discs))
        current = next_entries

    return current
