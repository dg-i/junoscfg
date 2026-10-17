"""Convert JSON dict IR to structured (curly-brace) configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from junoscfg.convert.output.dict_walker import (
    Below,
    DictWalker,
    WalkOutput,
    merged_tags_note,
    path_words,
    selection_tags_note,
    value_tags_note,
)
from junoscfg.display import ConfigStore, format_value, load_schema_tree, universal_statements


class StructuredWalkOutput(WalkOutput):
    """Pushes hierarchy paths into a ConfigStore for curly-brace rendering."""

    def __init__(
        self,
        diagnostic_sink: Callable[[str], None] | None = None,
        *,
        withhold_values: bool = False,
    ) -> None:
        """Start with an empty store and no deferred operations.

        With *withhold_values* a note names no path (an anonymized conversion).
        """
        self.config = ConfigStore()
        self._deferred: list[tuple[str, list[str]]] = []
        self._dropped_deletes: list[str] = []
        self._dropped_kept_tags = 0
        self._dropped_selected = 0
        self._dropped_values = 0
        self._merged: list[str] = []
        self._blocks: list[str] = []
        self._diagnostic_sink = diagnostic_sink
        self._withhold = withhold_values

    def emit(self, hierarchy: list[str]) -> None:
        """Push *hierarchy* into the store as one path; a relative selection whose
        statement is its path alone leaves none, and writes nothing."""
        if hierarchy:
            self.config.push("\n".join(hierarchy))

    def emit_positional(self, path: list[str], value: str) -> None:
        """Push a positional-key leaf, merging *value* into the last segment."""
        merged = list(path)
        merged[-1] = f"{merged[-1]} {value}"
        self.config.push("\n".join(merged))

    def emit_deactivate(self, hierarchy: list[str]) -> None:
        """Defer an ``inactive:`` marker until :meth:`finalize`."""
        self._deferred.append(("deactivate", hierarchy))

    def emit_replace(self, hierarchy: list[str]) -> None:
        """Defer a ``replace:`` marker until :meth:`finalize`."""
        self._deferred.append(("replace", hierarchy))

    def emit_protect(self, hierarchy: list[str]) -> None:
        """Defer a ``protect:`` marker until :meth:`finalize`."""
        self._deferred.append(("protect", hierarchy))

    def emit_activate(self, hierarchy: list[str]) -> None:
        """Do nothing: active is the default state in structured output."""
        pass  # Active is the default state

    def emit_delete(self, hierarchy: list[str]) -> None:
        """Record a dropped delete; structured output cannot express one."""
        # The structured format cannot represent delete operations; dropped
        # with an aggregated note in finalize()
        self._dropped_deletes.append(" ".join(hierarchy))

    def drop_kept_tag(self) -> None:
        """Count a tag on a statement kept whole that this output does not write.

        Curly text tags a statement it writes; a meta command on a kept
        statement it does not hold whole, or on part of one, has none.
        """
        self._dropped_kept_tags += 1

    def drop_selected_tag(self) -> None:
        """Count a tag at or above a relative selection's path."""
        self._dropped_selected += 1

    def drop_value_tags(self, count: int) -> None:
        """Count tags on single values of a leaf-list."""
        self._dropped_values += count

    def keep_block(self, hierarchy: list[str]) -> None:
        """Defer writing *hierarchy* as a block until :meth:`finalize`."""
        self._blocks.append(" ".join(hierarchy))

    def mark_merged(self, hierarchy: list[str]) -> None:
        """Defer writing *hierarchy* merged with each child until :meth:`finalize`."""
        self._merged.append(" ".join(hierarchy))

    def finalize(self) -> None:
        """Apply the deferred markers and note what structured output cannot write."""
        merged = set(self._merged)
        for path_str in self._merged:
            self.config.mark_merged(path_str)
        for path_str in self._blocks:
            self.config.keep_block(path_str)
        dropped_tags: list[str] = []
        for op, hierarchy in self._deferred:
            path_str = " ".join(hierarchy)
            if path_str in merged:
                # `family` takes no tag on the device, and `inactive: family
                # inet {` would mark `inet`; field validation reports it.
                dropped_tags.append(f"{op} {path_str}")
                continue
            if op == "deactivate":
                self.config.deactivate(path_str)
            elif op == "replace":
                self.config.mark_replaced(path_str)
            elif op == "protect":
                self.config.mark_protected(path_str)
        if dropped_tags and self._diagnostic_sink is not None:
            self._diagnostic_sink(merged_tags_note(dropped_tags, withhold=self._withhold))
        if self._dropped_selected and self._diagnostic_sink is not None:
            self._diagnostic_sink(selection_tags_note(self._dropped_selected))
        if self._dropped_values and self._diagnostic_sink is not None:
            self._diagnostic_sink(value_tags_note(self._dropped_values))
        if self._dropped_kept_tags and self._diagnostic_sink is not None:
            self._diagnostic_sink(
                f"note: {self._dropped_kept_tags} meta command(s) on a statement kept whole "
                "dropped: structured output tags only a statement it writes"
            )
        if self._dropped_deletes and self._diagnostic_sink is not None:
            self._diagnostic_sink(
                f"note: {len(self._dropped_deletes)} delete annotation(s) dropped: "
                "structured output cannot represent delete operations"
            )


def dict_to_structured(
    config: Any,
    *,
    diagnostic_sink: Callable[[str], None] | None = None,
    withhold_values: bool = False,
    below: list[str] | None = None,
) -> str:
    """Render the IR dict as structured (curly-brace) configuration; with
    *below*, *config* is the IR along that path and the statements are
    written without its words (a relative selection)."""
    if not isinstance(config, dict):
        # The legacy rendered-text filter produced no structured statement
        # when a relative path selected a leaf rather than a hierarchy.
        return ""

    store = StructuredWalkOutput(diagnostic_sink, withhold_values=withhold_values)
    output: WalkOutput = Below(store, path_words(below)) if below else store
    schema = load_schema_tree()
    walker = DictWalker(output, schema)

    # The top level's universal leaf-lists -- `apply-groups`,
    # `apply-groups-except` -- come first, one value a line (matches
    # Structure.py ordering).
    ag_keys = tuple(name for name, node in universal_statements(schema).items() if node.get("ll"))
    for agk in ag_keys:
        if agk in config:
            val = config[agk]
            if isinstance(val, str):
                output.emit([f"{agk} {format_value(val)}"])
            elif isinstance(val, list):
                for v in val:
                    if v is not None:
                        output.emit([f"{agk} {format_value(v)}"])

    # Walk remaining config (skip already-emitted apply-groups)
    filtered = {k: v for k, v in config.items() if k not in ag_keys}
    walker._walk(filtered, [], schema_node=schema)  # noqa: SLF001
    output.finalize()

    result = str(store.config)
    return result if result else ""
