"""Ordered tree store for building structured Junos configuration output."""

from __future__ import annotations

import re

# Operational attribute prefixes that may appear before keywords
_ATTR_PREFIXES = ("replace:", "protect:", "inactive:", "delete:")


def filter_structured_by_path(text: str, path_tokens: list[str], *, relative: bool = False) -> str:
    """Filter structured (curly-brace) output to the subtree at the given path.

    Args:
        text: Structured config text with curly-brace nesting.
        path_tokens: Path components to match (e.g. ["system", "syslog"]).
        relative: If True, strip the path prefix and re-indent from level 0.
                  If False, wrap the matching block in the full path hierarchy.

    Returns:
        Filtered structured text, or empty string if path not found.
    """
    if not path_tokens:
        return text

    lines = text.splitlines(keepends=True)
    target_depth = len(path_tokens)

    # State: track brace depth and current path at each depth level
    depth = 0
    path_at_depth: list[str] = []  # keyword at each depth level
    matched_start: int | None = None
    matched_depth: int = 0
    captured: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if matched_start is not None:
                captured.append(line)
            continue

        if matched_start is not None:
            # We're capturing lines inside the matched block
            if "{" in stripped and "}" not in stripped:
                depth += 1
            elif stripped == "}":
                depth -= 1
                if depth < matched_depth:
                    # Closed the matched block
                    break
            captured.append(line)
            continue

        # Not yet matched — track path via brace nesting
        if stripped == "}":
            depth -= 1
            if depth < len(path_at_depth):
                path_at_depth = path_at_depth[:depth]
            continue

        # Extract keyword, stripping attribute prefixes
        keyword = stripped
        for prefix in _ATTR_PREFIXES:
            while keyword.startswith(prefix):
                keyword = keyword[len(prefix) :].lstrip()

        # Determine the keyword token (before any value, brace, or semicolon)
        if keyword.endswith("{") or keyword.endswith(";"):
            token = keyword[:-1].strip().split()[0] if keyword[:-1].strip() else ""
        else:
            token = keyword.split()[0] if keyword else ""

        # Check if this line opens a block or is a oneliner at our target path
        current_match_depth = len(path_at_depth)

        if current_match_depth < target_depth and token == path_tokens[current_match_depth]:
            if keyword.rstrip().endswith("{"):
                # Opens a brace block
                path_at_depth.append(token)
                depth += 1
                if len(path_at_depth) == target_depth:
                    matched_start = 0
                    matched_depth = depth
            elif keyword.rstrip().endswith(";"):
                # Oneliner — check if it matches the full remaining path
                # e.g., "system host-name router1;" matches ["system"]
                parts = keyword[:-1].strip().split()
                if current_match_depth == target_depth - 1:
                    # This is a collapsed oneliner at our target depth
                    matched_start = 0
                    matched_depth = depth
                    # For relative: strip the first token; for absolute: keep with path wrapper
                    remaining = " ".join(parts[1:]) + ";" if len(parts) > 1 else parts[0] + ";"
                    if relative:
                        return remaining + "\n"
                    else:
                        # Wrap in path hierarchy
                        result_lines = []
                        for i, pt in enumerate(path_tokens[:-1]):
                            result_lines.append(ConfigStore.OFFSET * i + pt + " {\n")
                        indent = ConfigStore.OFFSET * (target_depth - 1)
                        result_lines.append(indent + stripped + "\n")
                        for i in range(target_depth - 2, -1, -1):
                            result_lines.append(ConfigStore.OFFSET * i + "}\n")
                        return "".join(result_lines)
        else:
            # Different branch — skip over its block if it opens one
            if stripped.endswith("{"):
                depth += 1

    if not captured:
        return ""

    if relative:
        # Re-indent captured lines: subtract the matched depth's indentation
        base_indent = ConfigStore.OFFSET * matched_depth
        result_lines = []
        for cline in captured:
            if cline.startswith(base_indent):
                result_lines.append(cline[len(base_indent) :])
            else:
                result_lines.append(cline.lstrip())
        return "".join(result_lines)
    else:
        # Wrap in path hierarchy
        result_lines = []
        for i, pt in enumerate(path_tokens):
            result_lines.append(ConfigStore.OFFSET * i + pt + " {\n")
        for cline in captured:
            result_lines.append(cline)
        for i in range(target_depth - 1, -1, -1):
            result_lines.append(ConfigStore.OFFSET * i + "}\n")
        return "".join(result_lines)


class ConfigStore:
    """Ordered tree for building structured (curly-brace) configuration.

    Each node is a ConfigStore with an ordered dict of children.
    Supports push (add paths), deactivate (mark inactive), and
    string rendering to curly-brace format.
    """

    OFFSET = "    "

    # Compound keywords: parent merges with each child on the same line.
    # E.g., "family inet {" instead of "family { inet { } }".
    COMPOUND_KEYWORDS: frozenset[str] = frozenset({"family"})

    def __init__(self, depth: int = 0) -> None:
        self._children: dict[str, ConfigStore] = {}
        self._depth = depth
        self.deactivated = False
        self.replaced = False
        self.protected = False
        self.deleted = False

    def push(self, path_str: str) -> None:
        """Add a newline-separated hierarchical path to the tree."""
        path_str = self._join_arg(path_str)
        store = self
        for i, element in enumerate(path_str.split("\n")):
            if element not in store._children:
                store._children[element] = ConfigStore(i + 1)
            store = store._children[element]

    def deactivate(self, deactivated_line: str) -> None:
        """Mark a path as inactive (deactivated)."""
        statement, store = self._match(deactivated_line)

        if statement is not None and store is not None:
            if statement == deactivated_line:
                store.deactivated = True
            else:
                remaining = re.sub(f"^{re.escape(statement)} *", "", deactivated_line)
                store.deactivate(remaining)
        else:
            statement, store = self._inverse_match(deactivated_line)
            if statement is not None and store is not None:
                store.deactivated = True

    def mark_replaced(self, path_str: str) -> None:
        """Mark a path as replaced."""
        statement, store = self._match(path_str)

        if statement is not None and store is not None:
            if statement == path_str:
                store.replaced = True
            else:
                remaining = re.sub(f"^{re.escape(statement)} *", "", path_str)
                store.mark_replaced(remaining)
        else:
            statement, store = self._inverse_match(path_str)
            if statement is not None and store is not None:
                store.replaced = True

    def mark_protected(self, path_str: str) -> None:
        """Mark a path as protected."""
        statement, store = self._match(path_str)

        if statement is not None and store is not None:
            if statement == path_str:
                store.protected = True
            else:
                remaining = re.sub(f"^{re.escape(statement)} *", "", path_str)
                store.mark_protected(remaining)
        else:
            statement, store = self._inverse_match(path_str)
            if statement is not None and store is not None:
                store.protected = True

    def mark_deleted(self, path_str: str) -> None:
        """Mark a path as deleted."""
        statement, store = self._match(path_str)

        if statement is not None and store is not None:
            if statement == path_str:
                store.deleted = True
            else:
                remaining = re.sub(f"^{re.escape(statement)} *", "", path_str)
                store.mark_deleted(remaining)
        else:
            statement, store = self._inverse_match(path_str)
            if statement is not None and store is not None:
                store.deleted = True

    def empty(self) -> bool:
        """Check if this node has no children."""
        return len(self._children) == 0

    def __str__(self) -> str:
        """Render tree as indented curly-brace config (iterative to avoid recursion limits)."""
        parts: list[str] = []
        # Stack: (action, depth, key_or_none, node)
        # action: "open" = emit key + opening brace or leaf, "close" = emit closing brace
        stack: list[tuple[str, int, str | None, ConfigStore]] = []

        # Push children in reverse order so first child is processed first
        for key, child in reversed(list(self._children.items())):
            stack.append(("open", self._depth, key, child))

        while stack:
            action, depth, key, node = stack.pop()
            indent = self.OFFSET * depth

            if action == "close":
                parts.append(f"{indent}}}\n")
            elif action == "leaf":
                # Pre-formatted leaf line (used by compound keywords)
                parts.append(f"{indent}{key};\n")
            elif action == "block_open":
                # Pre-formatted block opening (used by compound keywords)
                parts.append(f"{indent}{key} {{\n")
            elif action == "open":
                assert key is not None
                display_key = self._prefixed(key, node)
                if node.empty():
                    parts.append(f"{indent}{display_key};\n")
                elif self._is_collapsible(key, node):
                    # Single terminal child: render as oneliner
                    # e.g., "then accept;" instead of "then { accept; }"
                    ckey, cchild = next(iter(node._children.items()))
                    ckey = self._prefixed(ckey, cchild)
                    parts.append(f"{indent}{display_key} {ckey};\n")
                elif key in self.COMPOUND_KEYWORDS:
                    # Compound keyword: merge parent with each child.
                    # E.g., "family inet {" instead of "family { inet { }"
                    for ckey, cchild in reversed(list(node._children.items())):
                        dckey = self._prefixed(ckey, cchild)
                        compound_key = f"{display_key} {dckey}"
                        if cchild.empty():
                            stack.append(("leaf", depth, compound_key, cchild))
                        elif self._is_compound_collapsible(cchild):
                            gckey = next(iter(cchild._children))
                            gc = cchild._children[gckey]
                            gckey = self._prefixed(gckey, gc)
                            stack.append(("leaf", depth, f"{compound_key} {gckey}", gc))
                        else:
                            # Open block with compound key, push grandchildren
                            stack.append(("close", depth, None, cchild))
                            for gckey, gcchild in reversed(list(cchild._children.items())):
                                stack.append(("open", depth + 1, gckey, gcchild))
                            stack.append(("block_open", depth, compound_key, cchild))
                else:
                    parts.append(f"{indent}{display_key} {{\n")
                    # Push closing brace first (processed last)
                    stack.append(("close", depth, None, node))
                    # Push children in reverse order
                    for ckey, cchild in reversed(list(node._children.items())):
                        stack.append(("open", depth + 1, ckey, cchild))

        return "".join(parts)

    @staticmethod
    def _is_collapsible(key: str, node: ConfigStore) -> bool:
        """Check if a node should collapse to a oneliner.

        A node collapses when it has exactly one child that is a
        terminal (no grandchildren) and the parent key is a plain
        Junos keyword (lowercase + hyphens only).

        This produces e.g. ``then accept;`` or ``from protocol static;``
        instead of ``then { accept; }`` or ``from { protocol static; }``.

        Named list entries (contain spaces like ``group PEERS``) and
        transparent entries (contain uppercase, digits, or special
        characters like ``ge-0/0/0``) always use block form.
        """
        if len(node._children) != 1:
            return False
        child = next(iter(node._children.values()))
        if not child.empty():
            return False
        # Only collapse plain Junos keywords (lowercase + hyphens)
        return bool(re.fullmatch(r"[a-z][a-z-]*", key))

    @staticmethod
    def _is_compound_collapsible(node: ConfigStore) -> bool:
        """Check if a compound keyword child can collapse to a oneliner.

        Like ``_is_collapsible`` but checks the **child** key (not the
        parent).  Used for compound keywords where the parent is already
        merged, e.g. ``family inet unicast;`` (child ``unicast`` is a
        plain keyword) vs ``family inet { address 10.0.0.1/24; }``
        (child ``address 10.0.0.1/24`` is a leaf with a value).
        """
        if len(node._children) != 1:
            return False
        child_key, child_node = next(iter(node._children.items()))
        if not child_node.empty():
            return False
        return bool(re.fullmatch(r"[a-z][a-z-]*", child_key))

    @staticmethod
    def _prefixed(key: str, node: ConfigStore) -> str:
        """Build display key with operational attribute prefixes.

        Prefix order matches Junos convention: replace: protect: inactive: key
        """
        prefix = ""
        if node.replaced:
            prefix += "replace: "
        if node.protected:
            prefix += "protect: "
        if node.deactivated:
            prefix += "inactive: "
        if node.deleted:
            prefix += "delete: "
        return f"{prefix}{key}" if prefix else key

    def subtree(self, path_tokens: list[str], *, relative: bool = True) -> ConfigStore:
        """Extract a subtree rooted at the given path.

        Args:
            path_tokens: Path components to navigate to (e.g. ["system", "syslog"]).
            relative: If True, return just the subtree contents.
                      If False, wrap the subtree in the full path hierarchy.

        Returns:
            A new ConfigStore containing only the matching subtree.
            Returns an empty ConfigStore if the path is not found.
        """
        if not path_tokens:
            return self

        # Navigate to the target node
        node = self
        for token in path_tokens:
            found = None
            for key, child in node._children.items():
                if key == token:
                    found = child
                    break
            if found is None:
                return ConfigStore()
            node = found

        if relative:
            return node._reroot()

        # Wrap in the path hierarchy
        result = ConfigStore()
        current = result
        for i, token in enumerate(path_tokens[:-1]):
            child = ConfigStore(i + 1)
            current._children[token] = child
            current = child
        # Attach the found node's children at the last path level
        last = ConfigStore(len(path_tokens))
        last._children = node._children
        last.deactivated = node.deactivated
        last.replaced = node.replaced
        last.protected = node.protected
        last.deleted = node.deleted
        current._children[path_tokens[-1]] = last
        return result

    def _reroot(self) -> ConfigStore:
        """Create a new root ConfigStore with this node's children at depth 0."""
        root = ConfigStore()
        for key, child in self._children.items():
            rerooted = child._reroot_at(1)
            root._children[key] = rerooted
        return root

    def _reroot_at(self, depth: int) -> ConfigStore:
        """Recursively clone this node at a new depth."""
        clone = ConfigStore(depth)
        clone.deactivated = self.deactivated
        clone.replaced = self.replaced
        clone.protected = self.protected
        clone.deleted = self.deleted
        for key, child in self._children.items():
            clone._children[key] = child._reroot_at(depth + 1)
        return clone

    def _join_arg(self, s: str) -> str:
        """Process arg(...) wrappers from transformer output."""
        s = re.sub(r"\narg\((.*)\)$", lambda m: f" {m.group(1)}", s)
        s = re.sub(r"arg\((.*)\)", lambda m: m.group(1) or "", s)
        return s

    def _match(self, s: str) -> tuple[str | None, ConfigStore | None]:
        """Find a child whose key is a prefix of s."""
        for statement, store in self._children.items():
            if re.match(f"^{re.escape(statement)}((?= )|$)", s):
                return statement, store
        return None, None

    def _inverse_match(self, s: str) -> tuple[str | None, ConfigStore | None]:
        """Find a child whose key starts with s."""
        for statement, store in self._children.items():
            if re.match(f"^{re.escape(s)}(?= )", statement):
                return statement, store
        return None, None
