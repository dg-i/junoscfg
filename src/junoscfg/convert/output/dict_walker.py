"""Shared recursive dict walker for output converters.

Walks a Junos JSON dict IR against the schema tree and calls abstract
output methods on a :class:`WalkOutput` strategy object. This is the
core algorithm extracted from ``json_to_set.py``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from junoscfg.display import (
    UNPLACED_STATEMENTS,
    entry_key_names,
    entry_keys,
    format_value,
    get_transparent_child,
    holds_tag,
    is_flat_dict,
    is_freeform_nk,
    is_positional_key,
    is_transparent_list_key,
    key_is_positional,
    load_schema_tree,
    passes_tag_to_child,
    schema_child,
    unplaced_record_problem,
)


class WalkOutput(ABC):
    """Abstract output strategy for the dict walker."""

    @abstractmethod
    def emit(self, hierarchy: list[str]) -> None:
        """Emit a set command or push a hierarchy path."""

    @abstractmethod
    def emit_positional(self, path: list[str], value: str) -> None:
        """Emit a positional (nk/pk) value."""

    @abstractmethod
    def emit_deactivate(self, hierarchy: list[str]) -> None:
        """Emit a deactivate operation."""

    @abstractmethod
    def emit_replace(self, hierarchy: list[str]) -> None:
        """Emit a replace annotation."""

    @abstractmethod
    def emit_protect(self, hierarchy: list[str]) -> None:
        """Emit a protect operation."""

    @abstractmethod
    def emit_activate(self, hierarchy: list[str]) -> None:
        """Emit an activate operation."""

    @abstractmethod
    def emit_delete(self, hierarchy: list[str]) -> None:
        """Emit a delete operation."""

    def keep_block(self, hierarchy: list[str]) -> None:  # noqa: B027
        """A node structured output must write as a block, never one line.

        A list whose tag is on the list itself is written as its keyword's
        block; joined to one entry's line, the tag would read as that entry's.
        """

    def drop_kept_tag(self) -> None:  # noqa: B027
        """A meta command on a statement kept whole that the output cannot write.

        Only structured output has one: curly text tags a statement it writes.
        """

    def mark_merged(self, hierarchy: list[str]) -> None:  # noqa: B027
        """A container the schema says is written merged with each child.

        Only structured output has layout to decide; `family inet {`. The
        device never tags such a container (`passes_tag_to_child`).
        """

    def finalize(self) -> None:  # noqa: B027
        """Called after all emit calls are complete."""


def path_words(path: list[str]) -> list[str]:
    """The words a configuration path's keys are written as in set and
    structured output: each key as the walker spells it, without the list
    names the schema hides (`interface` under `interfaces`, `group` under
    `groups`, a list hiding its own key). A key no statement names (an
    annotation key, the kept-statements key) is passed over by `Below`."""
    root = load_schema_tree()
    node: dict[str, Any] | None = root
    words: list[str] = []
    for key in path:
        child = schema_child(node, key, root)
        hidden = get_transparent_child(node) == key or is_transparent_list_key(child)
        if not hidden:
            words.append(key)
        node = child
    return words


class Below(WalkOutput):
    """*inner* given every path without the leading *words*: a relative
    selection written as absolute output writes it, without its path.

    A word the path holds but a statement does not (a key the schema hides
    in a way `path_words` does not model) is passed over, never matched
    against what follows it.
    """

    def __init__(self, inner: WalkOutput, words: list[str]) -> None:
        """Strip *words* from each path before *inner* receives it."""
        self.inner = inner
        self._words = words

    def _below(self, hierarchy: list[str]) -> list[str]:
        rest = list(hierarchy)
        for word in self._words:
            if not rest:
                break
            if rest[0] == word:
                rest.pop(0)
            elif rest[0].startswith(word + " "):
                rest[0] = rest[0][len(word) + 1 :]
        return rest

    def emit(self, hierarchy: list[str]) -> None:
        """Emit *hierarchy* below the words."""
        self.inner.emit(self._below(hierarchy))

    def emit_positional(self, path: list[str], value: str) -> None:
        """Emit a positional leaf below the words."""
        below = self._below(path)
        if below:
            self.inner.emit_positional(below, value)
        else:
            self.inner.emit([value])

    def emit_deactivate(self, hierarchy: list[str]) -> None:
        """Deactivate *hierarchy* below the words."""
        self.inner.emit_deactivate(self._below(hierarchy))

    def emit_replace(self, hierarchy: list[str]) -> None:
        """Replace *hierarchy* below the words."""
        self.inner.emit_replace(self._below(hierarchy))

    def emit_protect(self, hierarchy: list[str]) -> None:
        """Protect *hierarchy* below the words."""
        self.inner.emit_protect(self._below(hierarchy))

    def emit_activate(self, hierarchy: list[str]) -> None:
        """Activate *hierarchy* below the words."""
        self.inner.emit_activate(self._below(hierarchy))

    def emit_delete(self, hierarchy: list[str]) -> None:
        """Delete *hierarchy* below the words."""
        self.inner.emit_delete(self._below(hierarchy))

    def keep_block(self, hierarchy: list[str]) -> None:
        """Keep *hierarchy* a block, below the words."""
        self.inner.keep_block(self._below(hierarchy))

    def drop_kept_tag(self) -> None:
        """Pass a dropped tag on."""
        self.inner.drop_kept_tag()

    def mark_merged(self, hierarchy: list[str]) -> None:
        """Mark *hierarchy* merged, below the words."""
        self.inner.mark_merged(self._below(hierarchy))

    def finalize(self) -> None:
        """Finalize *inner*."""
        self.inner.finalize()


class DictWalker:
    """Walk a Junos JSON dict IR and emit output via a strategy object."""

    def __init__(self, output: WalkOutput, root: dict[str, Any] | None = None) -> None:
        """Walk into *output*, the strategy that renders each emitted path.

        *root* is the structure tree the walk resolves a universal statement
        against (`schema_child`); `walk` loads it when not given.
        """
        self._output = output
        self._root = root

    def walk(self, config: dict[str, Any]) -> None:
        """Walk the configuration dict from the root."""
        schema = load_schema_tree()
        self._root = schema
        self._walk(config, [], schema_node=schema)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _schema_children(schema_node: dict[str, Any] | None) -> dict[str, Any]:
        if schema_node is None:
            return {}
        return schema_node.get("c", {})

    @staticmethod
    def _self_named_key(key: str, path: list[str]) -> bool:
        return bool(path) and path[-1] == key

    # ------------------------------------------------------------------
    # Flat dict emission
    # ------------------------------------------------------------------

    def _emit_flat_dict(
        self,
        value: dict[str, Any],
        path: list[str],
        set_key: str,
        schema_node: dict[str, Any] | None,
    ) -> bool:
        """Emit only a representable flat run; richer content uses the normal walk."""
        for key, child in value.items():
            if key.startswith("@") or isinstance(child, bool):
                return False
            if child is not None and not isinstance(child, (str, int, float)) and child != [None]:
                return False
        parts = [set_key]
        child_children = self._schema_children(schema_node)
        for k, v in value.items():
            if k.startswith("@"):
                continue
            if isinstance(v, list) and v == [None]:
                parts.append(k)
            elif isinstance(v, (str, int, float)):
                k_schema = child_children.get(k)
                is_nk = isinstance(k_schema, dict) and k_schema.get("nk")
                if is_nk:
                    parts.append(format_value(v, k_schema))
                else:
                    parts.append(k)
                    parts.append(format_value(v, k_schema))
            elif v is None:
                parts.append(k)
        self._output.emit(path + [" ".join(parts)])
        return True

    # ------------------------------------------------------------------
    # Oneliner emission
    # ------------------------------------------------------------------

    def _emit_oneliner(
        self,
        key: str,
        formatted_name: str,
        remaining: dict[str, Any],
        path: list[str],
        schema_node: dict[str, Any] | None,
    ) -> None:
        from junoscfg.convert.output.set_output import SetWalkOutput

        temp = SetWalkOutput()
        temp_walker = DictWalker(temp, self._root)
        temp_walker._walk(remaining, [], schema_node=schema_node)
        base = f"{key} {formatted_name}"

        if self._is_structured_mode():
            # Structured mode: combine all set children into a single oneliner
            parts: list[str] = [base]
            for line in temp.lines:
                if line.startswith("set "):
                    child_tokens = line[4:]
                    if child_tokens:
                        parts.append(child_tokens)
                elif line.startswith("deactivate "):
                    child_tokens = line[11:]
                    self._output.emit_deactivate(path + [f"{base} {child_tokens}"])
                elif line.startswith("protect "):
                    child_tokens = line[8:]
                    self._output.emit_protect(path + [f"{base} {child_tokens}"])
                elif line.startswith("activate "):
                    child_tokens = line[9:]
                    self._output.emit_activate(path + [f"{base} {child_tokens}"])
                elif line.startswith("delete "):
                    child_tokens = line[7:]
                    self._output.emit_delete(path + [f"{base} {child_tokens}"])
            self._output.emit(path + [" ".join(parts)])
        else:
            for line in temp.lines:
                if line.startswith("set "):
                    child_tokens = line[4:]
                    if child_tokens:
                        self._output.emit(path + [f"{base} {child_tokens}"])
                    else:
                        self._output.emit(path + [base])
                elif line.startswith("deactivate "):
                    child_tokens = line[11:]
                    self._output.emit_deactivate(path + [f"{base} {child_tokens}"])
                elif line.startswith("protect "):
                    child_tokens = line[8:]
                    self._output.emit_protect(path + [f"{base} {child_tokens}"])
                elif line.startswith("activate "):
                    child_tokens = line[9:]
                    self._output.emit_activate(path + [f"{base} {child_tokens}"])
                elif line.startswith("delete "):
                    child_tokens = line[7:]
                    self._output.emit_delete(path + [f"{base} {child_tokens}"])

    # ------------------------------------------------------------------
    # Recursive walk
    # ------------------------------------------------------------------

    def _walk(
        self,
        obj: dict[str, Any],
        path: list[str],
        *,
        schema_node: dict[str, Any] | None = None,
    ) -> None:
        children = self._schema_children(schema_node)
        output = self._output

        for key, value in obj.items():
            if key.startswith("@") or key == UNPLACED_STATEMENTS:
                continue

            child_schema = schema_child(schema_node, key, self._root)

            if isinstance(value, dict):
                if (
                    is_flat_dict(child_schema)
                    and UNPLACED_STATEMENTS not in value
                    and self._emit_flat_dict(value, path, key, child_schema)
                ):
                    continue

                child_key = get_transparent_child(child_schema)
                if child_key and child_key in value:
                    child_value = value[child_key]

                    tc_schema = child_schema
                    if tc_schema is not None:
                        tc_child = self._schema_children(tc_schema).get(child_key)
                        if tc_child is not None:
                            tc_schema = tc_child

                    siblings = {
                        k: v for k, v in value.items() if k != child_key and not k.startswith("@")
                    }
                    if siblings:
                        self._walk(
                            siblings,
                            path + [key],
                            schema_node=child_schema,
                        )

                    if isinstance(child_value, list):
                        for entry in child_value:
                            if isinstance(entry, dict):
                                self._process_hash(
                                    key,
                                    entry,
                                    path,
                                    split_key_name=True,
                                    schema_node=tc_schema,
                                )
                    elif isinstance(child_value, dict):
                        self._process_hash(
                            key,
                            child_value,
                            path,
                            split_key_name=True,
                            schema_node=tc_schema,
                        )
                else:
                    self._process_hash(
                        key,
                        value,
                        path,
                        schema_node=child_schema,
                    )

            elif isinstance(value, list):
                # Leaf with multiple string values: bracket expansion in structured mode
                if (
                    self._is_structured_mode()
                    and child_schema is not None
                    and child_schema.get("l")
                    and len(value) > 1
                    and all(isinstance(v, (str, int, float)) for v in value)
                ):
                    items = " ".join(format_value(v, child_schema) for v in value)
                    output.emit(path + [f"{key} [ {items} ]"])
                    # `inactive: members [ … ];`, as the device writes it.
                    attr = obj.get(f"@{key}")
                    if isinstance(attr, dict):
                        self._emit_attrs(path + [key], self._read_leaf_attrs(attr))
                    continue

                # A flat-dict list's own list of pairs -- `apply-macro M1 { k1
                # v1; }` holds `data` -- is written as runs of tokens, each
                # pair a line of its own below the entry.
                if (
                    schema_node is not None
                    and schema_node.get("L")
                    and schema_node.get("fd")
                    and child_schema is not None
                    and child_schema.get("L")
                ):
                    for entry in value:
                        if isinstance(entry, dict) and "name" in entry:
                            name_val = format_value(entry["name"])
                            val = entry.get("value")
                            if val is not None:
                                output.emit(path + [f"{name_val} {format_value(val)}"])
                            else:
                                output.emit(path + [name_val])
                    continue

                if child_schema is None and value == [None]:
                    keys = (
                        entry_key_names(schema_node) if schema_node and schema_node.get("L") else ()
                    )
                    has_nk_leaf = any(
                        isinstance(cs, dict) and cs.get("nk") and cs.get("l")
                        for name, cs in children.items()
                        if name not in keys
                    )
                    if has_nk_leaf:
                        # `deactivate interfaces xe-0/0/0 disable`: the tag was
                        # dropped here, and the interface loaded disabled. A
                        # tagged flag is a line of its own, never merged into
                        # its parent's (`lldp disable;`), where the tag would
                        # be lost or read as the parent's.
                        attrs = self._read_leaf_attrs(obj.get(f"@{key}") or {})
                        if (schema_node and schema_node.get("L")) or attrs:
                            output.emit(path + [key])
                        else:
                            output.emit_positional(path, key)
                        self._emit_attrs(path + [key], attrs)
                        continue

                list_schema = child_schema
                tc_child_name = get_transparent_child(child_schema)
                if tc_child_name and list_schema is not None:
                    tc_child = self._schema_children(list_schema).get(tc_child_name)
                    if tc_child is not None:
                        list_schema = tc_child

                is_tc = tc_child_name is not None
                # A tag on the whole list: structured output writes it as the
                # device writes `inactive: routing-instance { R1 {…} }`, the
                # keyword on its own tagged line and the entries in its block,
                # which reads back as a tag on the list, not on its first entry.
                wrapped = bool(
                    self._is_structured_mode()
                    and not is_tc
                    and holds_tag(obj.get(f"@{key}"))
                    and any(isinstance(entry, dict) for entry in value)
                )
                if wrapped:
                    output.keep_block(path + [key])
                for entry in value:
                    if isinstance(entry, dict):
                        if is_transparent_list_key(child_schema):
                            self._process_hash(
                                key,
                                entry,
                                path,
                                skip_key=True,
                                schema_node=list_schema,
                            )
                        else:
                            self._process_hash(
                                key,
                                entry,
                                path,
                                split_key_name=is_tc or wrapped,
                                schema_node=list_schema,
                            )
                    elif is_transparent_list_key(child_schema):
                        if entry is not None:
                            output.emit(path + [format_value(entry, child_schema)])
                        else:
                            output.emit(path)
                    elif entry is None:
                        output.emit(path + [key])
                    else:
                        output.emit(path + [f"{key} {format_value(entry, child_schema)}"])

                attr = obj.get(f"@{key}")
                if isinstance(attr, dict):
                    attrs = self._read_leaf_attrs(attr)
                    if attrs:
                        self._emit_attrs(path + [key], attrs)

            elif isinstance(value, bool):
                output.emit(path + [key])

            elif isinstance(value, (str, int, float)):
                is_nk = (
                    isinstance(child_schema, dict)
                    and child_schema.get("nk", False)
                    and not is_freeform_nk(child_schema)
                )
                positional = (
                    is_nk or is_positional_key(child_schema) or self._self_named_key(key, path)
                )
                formatted = format_value(value, child_schema)
                if positional:
                    if is_nk and schema_node and schema_node.get("L"):
                        output.emit(path + [formatted])
                    else:
                        output.emit_positional(path, formatted)
                else:
                    output.emit(path + [f"{key} {formatted}"])

                attr_key = f"@{key}"
                attr = obj.get(attr_key)
                if isinstance(attr, dict):
                    leaf_attrs = self._read_leaf_attrs(attr)
                    if leaf_attrs:
                        self._emit_attrs(path + [key], leaf_attrs)

            elif value is None:
                output.emit(path + [key])

        # A meta command on a value or a whole list the level holds has no
        # data key of its own to trigger the branches above; emit that
        # command without inventing a corresponding `set`.
        for attr_key, attr in obj.items():
            if not attr_key.startswith("@") or attr_key == "@":
                continue
            key = attr_key[1:]
            # A container's tag is its inline `@`; JSON may also write it
            # beside the container, as `@family`, and that is repeated too.
            held = obj.get(key)
            if (
                (key in obj and not isinstance(held, bool | dict) and held is not None)
                or (isinstance(held, dict) and holds_tag(held.get("@")))
                or not isinstance(attr, dict)
            ):
                continue
            attrs = self._read_leaf_attrs(attr)
            if attrs:
                self._emit_attrs(path + [key], attrs)

        if UNPLACED_STATEMENTS in obj:
            self._emit_unplaced(obj[UNPLACED_STATEMENTS], path)

    def _emit_unplaced(self, record: Any, path: list[str]) -> None:
        """Write the statements a level keeps whole, as written, after its placed nodes.

        A statement is its own text; a tag or meta command on it follows it,
        and one on a statement the record does not hold whole is written
        alone. Structured text tags only a statement it writes, so it leaves
        such a command out and notes it. A record no writer could print as it
        stands is refused rather than written (`unplaced_record_problem`).
        """
        problem = unplaced_record_problem(record)
        if problem is not None:
            raise ValueError(f"Cannot write the IR: {problem}")
        for text in record:
            if not text.startswith("@"):
                self._output.emit(path + [text])
                self._emit_attrs(path + [text], self._read_leaf_attrs(record.get(f"@{text}", {})))
        for key, attr in record.items():
            text = key[1:]
            if not key.startswith("@") or text in record:
                continue
            attrs = self._read_leaf_attrs(attr)
            if not attrs:
                continue
            if self._is_structured_mode():
                self._output.drop_kept_tag()
            else:
                self._emit_attrs(path + [text], attrs)

    def _process_hash(
        self,
        key: str,
        hash_: dict[str, Any],
        path: list[str],
        *,
        skip_key: bool = False,
        split_key_name: bool = False,
        schema_node: dict[str, Any] | None = None,
    ) -> None:
        output = self._output
        attrs = self._read_attrs(hash_)
        key_fields = self._entry_key(hash_, schema_node)

        if key_fields is not None:
            formatted_name, written = key_fields
            remaining = {k: v for k, v in hash_.items() if k not in written}
            has_content = any(not k.startswith("@") for k in remaining)

            if skip_key:
                new_path = path + [formatted_name]
            elif split_key_name and schema_node and schema_node.get("c"):
                new_path = path + [key, formatted_name]
            else:
                new_path = path + [f"{key} {formatted_name}"]

            # One line only while no node after the first carries a tag: a
            # tag leads the line of the node it marks.
            is_oneliner = (
                self._is_structured_mode()
                and not skip_key
                and schema_node is not None
                and schema_node.get("o")
                and not split_key_name
                and not _holds_a_tag(remaining)
            )

            if not has_content:
                # Delete-only nodes emit just the delete command
                if "delete" not in attrs:
                    output.emit(new_path)
            elif is_oneliner:
                self._emit_oneliner(key, formatted_name, remaining, path, schema_node)
            else:
                self._walk(
                    remaining,
                    new_path,
                    schema_node=schema_node,
                )

            self._emit_attrs(new_path, attrs)
        else:
            new_path = path if skip_key else path + [key]
            if passes_tag_to_child(schema_node):
                output.mark_merged(new_path)

            has_content = any(not k.startswith("@") for k in hash_)

            if not has_content:
                # An attribute-only unknown node is a kept-whole meta command,
                # not an invented `set` command. Known containers still emit
                # their set form before the attribute, as before.
                if "delete" not in attrs and (schema_node is not None or not attrs):
                    output.emit(new_path)
            else:
                self._walk(
                    hash_,
                    new_path,
                    schema_node=schema_node,
                )

            self._emit_attrs(new_path, attrs)

    @staticmethod
    def _entry_key(
        hash_: dict[str, Any], schema_node: dict[str, Any] | None
    ) -> tuple[str, set[str]] | None:
        """An entry's key as written, and the IR keys it consumed; None if absent.

        The key values in declared order, a field whose leaf is not
        `nokeyword` as its keyword and value, a choice of identifiers as its
        keyword and, where the alternative carries one, its value. A hash
        with no schema node is keyed `name`, as it always was. A known
        ordinary name child (list, container, leaf-list, presence or keyworded
        leaf) cannot be an entry key. Scalar positional-name ambiguity keeps
        the historical fallback until the owning schema resolves it.
        """
        if schema_node is not None and not schema_node.get("L"):
            name_schema = schema_node.get("c", {}).get("name")
            if name_schema is not None and (
                name_schema.get("L")
                or "c" in name_schema
                or name_schema.get("ll")
                or name_schema.get("p")
                or (name_schema.get("l") and not name_schema.get("nk"))
            ):
                return None
            fields = ("name",)
        else:
            fields = entry_keys(schema_node) if schema_node is not None else ("name",)
        parts: list[str] = []
        written: set[str] = set()
        for field in fields:
            if isinstance(field, tuple):
                chosen = next((k for k in hash_ if k in field), None)
                if chosen is None:
                    return None
                written.add(chosen)
                parts.append(chosen)
                value = hash_[chosen]
                if not (value is None or value is True or value == [None]):
                    leaf = (schema_node or {}).get("c", {}).get(chosen)
                    parts.append(format_value(value[0] if isinstance(value, list) else value, leaf))
                continue
            if field not in hash_:
                return None
            value = hash_[field]
            if isinstance(value, list):
                value = value[0]
            written.add(field)
            leaf = (schema_node or {}).get("c", {}).get(field)
            if not key_is_positional(leaf):
                # A key field whose leaf is not `nokeyword` is written with its
                # keyword: `virtual-link neighbor-id 10.255.255.1 transit-area
                # 0.0.0.2` (device probe, vMX 23.2R2-S7.5).
                parts.append(field)
            parts.append(format_value(value, leaf))
        return " ".join(parts), written

    def _is_structured_mode(self) -> bool:
        """Check if the output strategy is structured mode (for oneliner logic)."""
        from junoscfg.convert.output.structured_output import StructuredWalkOutput

        output = self._output.inner if isinstance(self._output, Below) else self._output
        return isinstance(output, StructuredWalkOutput)

    @staticmethod
    def _read_attrs(hash_: dict[str, Any]) -> set[str]:
        result: set[str] = set()
        at = hash_.get("@")
        if isinstance(at, dict):
            if at.get("inactive") is True:
                result.add("deactivate")
            if at.get("operation") == "replace":
                result.add("replace")
            if at.get("operation") == "delete":
                result.add("delete")
            if at.get("protect") == "protect":
                result.add("protect")
            if at.get("active") == "active":
                result.add("activate")
        if hash_.get("@inactive") is True:
            result.add("deactivate")
        return result

    @staticmethod
    def _read_leaf_attrs(attr: dict[str, Any]) -> set[str]:
        result: set[str] = set()
        if attr.get("inactive") is True:
            result.add("deactivate")
        if attr.get("operation") == "replace":
            result.add("replace")
        if attr.get("operation") == "delete":
            result.add("delete")
        if attr.get("protect") == "protect":
            result.add("protect")
        if attr.get("active") == "active":
            result.add("activate")
        return result

    def _emit_attrs(self, path: list[str], attrs: set[str]) -> None:
        output = self._output
        if "deactivate" in attrs:
            output.emit_deactivate(path)
        if "replace" in attrs:
            output.emit_replace(path)
        if "protect" in attrs:
            output.emit_protect(path)
        if "activate" in attrs:
            output.emit_activate(path)
        if "delete" in attrs:
            output.emit_delete(path)


def _holds_a_tag(value: Any) -> bool:
    """Whether a tag sits anywhere in *value*, on an ``@`` or an ``@key``."""
    if isinstance(value, dict):
        return any(
            (key.startswith("@") and holds_tag(item)) or _holds_a_tag(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_holds_a_tag(item) for item in value)
    return False
