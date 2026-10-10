"""Convert JSON dict IR to structured (curly-brace) configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from junoscfg.convert.output.dict_walker import DictWalker, WalkOutput
from junoscfg.display import ConfigStore, format_value, load_schema_tree


class StructuredWalkOutput(WalkOutput):
    """Pushes hierarchy paths into a ConfigStore for curly-brace rendering."""

    def __init__(self, diagnostic_sink: Callable[[str], None] | None = None) -> None:
        """Start with an empty store and no deferred operations."""
        self.config = ConfigStore()
        self._deferred: list[tuple[str, list[str]]] = []
        self._dropped_deletes: list[str] = []
        self._merged: list[str] = []
        self._diagnostic_sink = diagnostic_sink

    def emit(self, hierarchy: list[str]) -> None:
        """Push *hierarchy* into the store as one path."""
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

    def mark_merged(self, hierarchy: list[str]) -> None:
        """Defer writing *hierarchy* merged with each child until :meth:`finalize`."""
        self._merged.append(" ".join(hierarchy))

    def finalize(self) -> None:
        """Apply the deferred markers and note what structured output cannot write."""
        merged = set(self._merged)
        for path_str in self._merged:
            self.config.mark_merged(path_str)
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
            self._diagnostic_sink(
                f"note: {len(dropped_tags)} tag(s) dropped from a container Junos never "
                f"tags ({'; '.join(dropped_tags)}): it is written merged with each child"
            )
        if self._dropped_deletes and self._diagnostic_sink is not None:
            self._diagnostic_sink(
                f"note: {len(self._dropped_deletes)} delete annotation(s) dropped: "
                "structured output cannot represent delete operations"
            )


def dict_to_structured(config: Any, *, diagnostic_sink: Callable[[str], None] | None = None) -> str:
    """Render the IR dict as structured (curly-brace) configuration."""
    if not isinstance(config, dict):
        # The legacy rendered-text filter produced no structured statement
        # when a relative path selected a leaf rather than a hierarchy.
        return ""

    output = StructuredWalkOutput(diagnostic_sink)
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
