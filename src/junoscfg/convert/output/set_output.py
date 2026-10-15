"""Convert JSON dict IR to display set commands."""

from __future__ import annotations

from typing import Any

from junoscfg.convert.output.dict_walker import Below, DictWalker, WalkOutput, path_words
from junoscfg.display import format_value


class SetWalkOutput(WalkOutput):
    """Accumulates set/deactivate/protect/activate/delete command strings."""

    def __init__(self) -> None:
        """Start with no accumulated lines."""
        self.lines: list[str] = []
        # Unused today, but public on a public class: removing it is an API
        # break that belongs in a change, not in onboarding. Whitelisted for
        # vulture; see .agent-ready/vulture-whitelist.py.
        self.meta_lines: list[str] = []

    def emit(self, hierarchy: list[str]) -> None:
        """Emit a ``set`` command for *hierarchy*."""
        self.lines.append(" ".join(["set", *hierarchy]))

    def emit_positional(self, path: list[str], value: str) -> None:
        """Emit a ``set`` command for a positional-key leaf."""
        self.lines.append(" ".join(["set", *path, value]))

    def emit_deactivate(self, hierarchy: list[str]) -> None:
        """Emit a ``deactivate`` command for *hierarchy*."""
        self.lines.append(" ".join(["deactivate", *hierarchy]))

    def emit_replace(self, hierarchy: list[str]) -> None:
        """Do nothing: set mode has no equivalent of ``replace:``."""
        pass  # No set-mode equivalent for replace

    def emit_protect(self, hierarchy: list[str]) -> None:
        """Emit a ``protect`` command for *hierarchy*."""
        self.lines.append(" ".join(["protect", *hierarchy]))

    def emit_activate(self, hierarchy: list[str]) -> None:
        """Emit an ``activate`` command for *hierarchy*."""
        self.lines.append(" ".join(["activate", *hierarchy]))

    def emit_delete(self, hierarchy: list[str]) -> None:
        """Emit a ``delete`` command for *hierarchy*."""
        self.lines.append(" ".join(["delete", *hierarchy]))


def dict_to_set(config: Any, *, below: list[str] | None = None) -> str:
    """Render the IR dict as display set commands; with *below*, *config* is
    the IR along that path and the statements are written without its words
    (a relative selection)."""
    if not isinstance(config, dict):
        if config is None or config is True:
            return "set\n"
        return f"set {format_value(config)}\n"

    output = SetWalkOutput()
    walker = DictWalker(Below(output, path_words(below)) if below else output)
    walker.walk(config)

    if not output.lines:
        return ""
    return "\n".join(output.lines) + "\n"
