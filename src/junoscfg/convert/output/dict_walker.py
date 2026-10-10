"""Shared recursive dict walker for output converters.

Walks a Junos JSON dict IR against the schema tree and calls abstract
output methods on a :class:`WalkOutput` strategy object. This is the
core algorithm extracted from ``json_to_set.py``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from junoscfg.display import (
    entry_key_names,
    entry_keys,
    format_value,
    get_transparent_child,
    is_flat_dict,
    is_freeform_nk,
    is_positional_key,
    is_transparent_list_key,
    key_is_positional,
    load_schema_tree,
    resolve_key_alias,
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

    def finalize(self) -> None:  # noqa: B027
        """Called after all emit calls are complete."""


class DictWalker:
    """Walk a Junos JSON dict IR and emit output via a strategy object."""

    def __init__(self, output: WalkOutput) -> None:
        """Walk into *output*, the strategy that renders each emitted path."""
        self._output = output

    def walk(self, config: dict[str, Any]) -> None:
        """Walk the configuration dict from the root."""
        schema = load_schema_tree()
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
    ) -> None:
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
                    parts.append(format_value(v))
                else:
                    parts.append(k)
                    parts.append(format_value(v))
            elif v is None:
                parts.append(k)
        self._output.emit(path + [" ".join(parts)])

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
        temp_walker = DictWalker(temp)
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
            if key.startswith("@"):
                continue

            set_key = resolve_key_alias(key)
            child_schema = children.get(set_key)

            if isinstance(value, dict):
                if is_flat_dict(child_schema, set_key):
                    self._emit_flat_dict(value, path, set_key, child_schema)
                    continue

                child_key = get_transparent_child(child_schema, set_key)
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
                            path + [set_key],
                            schema_node=child_schema,
                        )

                    if isinstance(child_value, list):
                        for entry in child_value:
                            if isinstance(entry, dict):
                                self._process_hash(
                                    set_key,
                                    entry,
                                    path,
                                    split_key_name=True,
                                    schema_node=tc_schema,
                                )
                    elif isinstance(child_value, dict):
                        self._process_hash(
                            set_key,
                            child_value,
                            path,
                            split_key_name=True,
                            schema_node=tc_schema,
                        )
                else:
                    self._process_hash(
                        set_key,
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
                    items = " ".join(format_value(v) for v in value)
                    output.emit(path + [f"{set_key} [ {items} ]"])
                    continue

                if key == "data" and path and path[-1].startswith("apply-macro"):
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
                        if schema_node and schema_node.get("L"):
                            output.emit(path + [set_key])
                        else:
                            output.emit_positional(path, set_key)
                        continue

                list_schema = child_schema
                tc_child_name = get_transparent_child(child_schema, set_key)
                if tc_child_name and list_schema is not None:
                    tc_child = self._schema_children(list_schema).get(tc_child_name)
                    if tc_child is not None:
                        list_schema = tc_child

                is_tc = tc_child_name is not None
                for entry in value:
                    if isinstance(entry, dict):
                        if is_transparent_list_key(child_schema, key):
                            self._process_hash(
                                set_key,
                                entry,
                                path,
                                skip_key=True,
                                schema_node=list_schema,
                            )
                        else:
                            self._process_hash(
                                set_key,
                                entry,
                                path,
                                split_key_name=is_tc,
                                schema_node=list_schema,
                            )
                    elif is_transparent_list_key(child_schema, key):
                        if entry is not None:
                            output.emit(path + [format_value(entry)])
                        else:
                            output.emit(path)
                    elif entry is None:
                        output.emit(path + [set_key])
                    else:
                        output.emit(path + [f"{set_key} {format_value(entry)}"])

                attr = obj.get(f"@{key}")
                if isinstance(attr, dict):
                    attrs = self._read_leaf_attrs(attr)
                    if attrs:
                        self._emit_attrs(path + [set_key], attrs)

            elif isinstance(value, bool):
                output.emit(path + [set_key])

            elif isinstance(value, (str, int, float)):
                is_nk = (
                    isinstance(child_schema, dict)
                    and child_schema.get("nk", False)
                    and not is_freeform_nk(child_schema)
                )
                positional = (
                    is_nk or is_positional_key(child_schema, key) or self._self_named_key(key, path)
                )
                formatted = format_value(value)
                if positional:
                    if is_nk and schema_node and schema_node.get("L"):
                        output.emit(path + [formatted])
                    else:
                        output.emit_positional(path, formatted)
                else:
                    output.emit(path + [f"{set_key} {formatted}"])

                attr_key = f"@{key}"
                attr = obj.get(attr_key)
                if isinstance(attr, dict):
                    leaf_attrs = self._read_leaf_attrs(attr)
                    if leaf_attrs:
                        self._emit_attrs(path + [set_key], leaf_attrs)

            elif value is None:
                output.emit(path + [set_key])

        # A meta command can target an unknown statement that is already kept
        # whole only through longer descendant statements.  Its sibling
        # attribute therefore has no exact data key to trigger the branches
        # above; emit that command without inventing a corresponding `set`.
        for attr_key, attr in obj.items():
            if not attr_key.startswith("@") or attr_key == "@":
                continue
            key = attr_key[1:]
            if (
                key in obj and not isinstance(obj[key], bool) and obj[key] is not None
            ) or not isinstance(attr, dict):
                continue
            attrs = self._read_leaf_attrs(attr)
            if attrs:
                self._emit_attrs(path + [resolve_key_alias(key)], attrs)

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

            is_oneliner = (
                self._is_structured_mode()
                and not skip_key
                and schema_node is not None
                and schema_node.get("o")
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
        outside a known list is keyed `name`, as it always was.
        """
        fields = entry_keys(schema_node) if schema_node and schema_node.get("L") else ("name",)
        parts: list[str] = []
        written: set[str] = set()
        for field in fields:
            if isinstance(field, tuple):
                chosen = next((k for k in hash_ if resolve_key_alias(k) in field), None)
                if chosen is None:
                    return None
                written.add(chosen)
                parts.append(resolve_key_alias(chosen))
                value = hash_[chosen]
                if not (value is None or value is True or value == [None]):
                    parts.append(format_value(value[0] if isinstance(value, list) else value))
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
            parts.append(format_value(value))
        return " ".join(parts), written

    def _is_structured_mode(self) -> bool:
        """Check if the output strategy is structured mode (for oneliner logic)."""
        from junoscfg.convert.output.structured_output import StructuredWalkOutput

        return isinstance(self._output, StructuredWalkOutput)

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
