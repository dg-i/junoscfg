"""Convert JSON dict IR to display set commands."""

from __future__ import annotations

from typing import Any

from junoscfg.convert.output.dict_walker import DictWalker, WalkOutput


class SetWalkOutput(WalkOutput):
    """Accumulates set/deactivate/protect/activate/delete command strings."""

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.meta_lines: list[str] = []

    def emit(self, hierarchy: list[str]) -> None:
        self.lines.append(f"set {' '.join(hierarchy)}")

    def emit_positional(self, path: list[str], value: str) -> None:
        self.lines.append(f"set {' '.join(path + [value])}")

    def emit_deactivate(self, hierarchy: list[str]) -> None:
        self.lines.append(f"deactivate {' '.join(hierarchy)}")

    def emit_replace(self, hierarchy: list[str]) -> None:
        pass  # No set-mode equivalent for replace

    def emit_protect(self, hierarchy: list[str]) -> None:
        self.lines.append(f"protect {' '.join(hierarchy)}")

    def emit_activate(self, hierarchy: list[str]) -> None:
        self.lines.append(f"activate {' '.join(hierarchy)}")

    def emit_delete(self, hierarchy: list[str]) -> None:
        self.lines.append(f"delete {' '.join(hierarchy)}")


def dict_to_set(config: dict[str, Any]) -> str:
    """Render the IR dict as display set commands."""
    output = SetWalkOutput()
    walker = DictWalker(output)
    walker.walk(config)

    if not output.lines:
        return ""
    return "\n".join(output.lines) + "\n"
