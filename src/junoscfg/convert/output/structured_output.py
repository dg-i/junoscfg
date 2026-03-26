"""Convert JSON dict IR to structured (curly-brace) configuration."""

from __future__ import annotations

from typing import Any

from junoscfg.convert.output.dict_walker import DictWalker, WalkOutput
from junoscfg.display.config_store import ConfigStore
from junoscfg.display.constants import load_schema_tree
from junoscfg.display.value_format import format_value


class StructuredWalkOutput(WalkOutput):
    """Pushes hierarchy paths into a ConfigStore for curly-brace rendering."""

    def __init__(self) -> None:
        self.config = ConfigStore()
        self._deferred: list[tuple[str, list[str]]] = []

    def emit(self, hierarchy: list[str]) -> None:
        self.config.push("\n".join(hierarchy))

    def emit_positional(self, path: list[str], value: str) -> None:
        merged = list(path)
        merged[-1] = f"{merged[-1]} {value}"
        self.config.push("\n".join(merged))

    def emit_deactivate(self, hierarchy: list[str]) -> None:
        self._deferred.append(("deactivate", hierarchy))

    def emit_replace(self, hierarchy: list[str]) -> None:
        self._deferred.append(("replace", hierarchy))

    def emit_protect(self, hierarchy: list[str]) -> None:
        self._deferred.append(("protect", hierarchy))

    def emit_activate(self, hierarchy: list[str]) -> None:
        pass  # Active is the default state

    def emit_delete(self, hierarchy: list[str]) -> None:
        self._deferred.append(("delete", hierarchy))

    def finalize(self) -> None:
        for op, hierarchy in self._deferred:
            path_str = " ".join(hierarchy)
            if op == "deactivate":
                self.config.deactivate(path_str)
            elif op == "replace":
                self.config.mark_replaced(path_str)
            elif op == "protect":
                self.config.mark_protected(path_str)
            elif op == "delete":
                self.config.mark_deleted(path_str)


def dict_to_structured(config: dict[str, Any]) -> str:
    """Render the IR dict as structured (curly-brace) configuration."""
    output = StructuredWalkOutput()
    walker = DictWalker(output)

    # Emit top-level apply-groups first (matches Structure.py ordering)
    ag_keys = ("apply-groups", "apply-groups-except")
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
    schema = load_schema_tree()
    walker._walk(filtered, [], schema_node=schema)  # noqa: SLF001
    output.finalize()

    result = str(output.config)
    return result if result else ""
