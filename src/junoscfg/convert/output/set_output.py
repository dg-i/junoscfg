"""Convert JSON dict IR to display set commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from junoscfg.convert.output.dict_walker import (
    Below,
    DictWalker,
    WalkOutput,
    merged_tags_note,
    path_words,
    selection_tags_note,
    value_tags_note,
)
from junoscfg.display import format_value

if TYPE_CHECKING:
    from collections.abc import Callable


class SetWalkOutput(WalkOutput):
    """Accumulates set/deactivate/protect/activate/delete command strings."""

    def __init__(self) -> None:
        """Start with no accumulated lines."""
        self.lines: list[str] = []
        # Unused today, but public on a public class: removing it is an API
        # break that belongs in a change, not in onboarding. Whitelisted for
        # vulture; see .agent-ready/vulture-whitelist.py.
        self.meta_lines: list[str] = []
        self.dropped_selected = 0
        self.dropped_values = 0
        self.dropped_merged: list[str] = []
        self._merged: set[str] = set()

    def emit(self, hierarchy: list[str]) -> None:
        """Emit a ``set`` command for *hierarchy*."""
        self.lines.append(" ".join(["set", *hierarchy]))

    def emit_positional(self, path: list[str], value: str) -> None:
        """Emit a ``set`` command for a positional-key leaf."""
        self.lines.append(" ".join(["set", *path, value]))

    def _tag(self, verb: str, hierarchy: list[str]) -> None:
        """Emit *verb* for *hierarchy*, but not on a container Junos writes
        merged with each child: the device refuses `deactivate ... family`."""
        path = " ".join(hierarchy)
        if path in self._merged:
            if f"{verb} {path}" not in self.dropped_merged:
                self.dropped_merged.append(f"{verb} {path}")
        else:
            self.lines.append(f"{verb} {path}")

    def mark_merged(self, hierarchy: list[str]) -> None:
        """Remember a container Junos never tags."""
        self._merged.add(" ".join(hierarchy))

    def emit_deactivate(self, hierarchy: list[str]) -> None:
        """Emit a ``deactivate`` command for *hierarchy*."""
        self._tag("deactivate", hierarchy)

    def emit_replace(self, hierarchy: list[str]) -> None:
        """Do nothing: set mode has no equivalent of ``replace:``."""
        pass  # No set-mode equivalent for replace

    def emit_protect(self, hierarchy: list[str]) -> None:
        """Emit a ``protect`` command for *hierarchy*."""
        self._tag("protect", hierarchy)

    def emit_activate(self, hierarchy: list[str]) -> None:
        """Emit an ``activate`` command for *hierarchy*."""
        self._tag("activate", hierarchy)

    def emit_delete(self, hierarchy: list[str]) -> None:
        """Emit a ``delete`` command for *hierarchy*."""
        self._tag("delete", hierarchy)

    def drop_selected_tag(self) -> None:
        """Count a tag at or above a relative selection's path."""
        self.dropped_selected += 1

    def drop_value_tags(self, count: int) -> None:
        """Count tags on single values of a leaf-list."""
        self.dropped_values += count


def dict_to_set(
    config: Any,
    *,
    below: list[str] | None = None,
    diagnostic_sink: Callable[[str], None] | None = None,
    withhold_values: bool = False,
) -> str:
    """Render the IR dict as display set commands; with *below*, *config* is
    the IR along that path and the statements are written without its words
    (a relative selection). A tag the output cannot write is noted to
    *diagnostic_sink*: one at or above a relative path, one on a single value
    of a leaf-list, one on a container Junos never tags; with
    *withhold_values* a note names no path."""
    if not isinstance(config, dict):
        if config is None or config is True:
            return "set\n"
        return f"set {format_value(config)}\n"

    output = SetWalkOutput()
    walker = DictWalker(Below(output, path_words(below)) if below else output)
    walker.walk(config)
    if diagnostic_sink is not None:
        if output.dropped_selected:
            diagnostic_sink(selection_tags_note(output.dropped_selected))
        if output.dropped_values:
            diagnostic_sink(value_tags_note(output.dropped_values))
        if output.dropped_merged:
            diagnostic_sink(merged_tags_note(output.dropped_merged, withhold=withhold_values))

    if not output.lines:
        return ""
    return "\n".join(output.lines) + "\n"
