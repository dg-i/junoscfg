"""Output converters: render the JSON dict IR into various formats."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


def from_dict(
    config: Any,
    fmt: str,
    *,
    wrap: bool = True,
    below: list[str] | None = None,
    diagnostic_sink: Callable[[str], None] | None = None,
    withhold_values: bool = False,
) -> str:
    """Dispatch to the appropriate output converter.

    Args:
        config: The configuration content (without the ``"configuration"``
                wrapper), or with *wrap* false a relative selection: the value
                under its path's last key, which may be a list, ``{}``, a flag
                or a scalar.
        fmt: Format name, a key of
             :data:`~junoscfg.convert.formats.FORMAT_IMPLEMENTATIONS`
             (``"json"``, ``"yaml"``, ``"yaml-new"``, ``"xml"``, ``"set"``,
             ``"structured"``).
        wrap: Wrap JSON and both YAML outputs in a top-level
              ``"configuration"`` mapping. Ignored by the other renderers.
        below: A relative selection's path: *config* is the IR along it, and
              every renderer writes what its absolute output writes at the
              path, without the path (spec conversion/path-filtering).
        diagnostic_sink: Optional receiver for renderer diagnostics, each a
            note on a tag the output cannot write: one at or above a relative
            selection's path (every writer), one on a single value of a
            leaf-list (set and structured), and the structured writer's own.
            The caller owns any terminal or log rendering.
        withhold_values: The diagnostics quote no word of the configuration
            (an anonymized conversion): a note gives counts, not paths.

    Returns:
        The rendered configuration as a string.
    """
    from junoscfg.convert.formats import implementation

    implemented = implementation(fmt, "output")
    if below is not None and implemented in ("junos-json", "junos-yaml", "ir-yaml"):
        # The value at the path leaves out every tag at or above it; set and
        # structured output count theirs as they walk (`Below`).
        from junoscfg.convert.output.dict_walker import selection_tags_note, tags_above

        dropped = tags_above(config, below)
        if dropped and diagnostic_sink is not None:
            diagnostic_sink(selection_tags_note(dropped))
    if implemented == "junos-json":
        from junoscfg.convert.output.json_output import dict_to_json

        return dict_to_json(config, wrap=wrap, below=below)
    if implemented == "junos-yaml":
        from junoscfg.convert.output.json_output import dict_to_junos_yaml

        return dict_to_junos_yaml(config, wrap=wrap, below=below)
    if implemented == "ir-yaml":
        from junoscfg.convert.output.yaml_output import dict_to_yaml

        return dict_to_yaml(config, wrap=wrap, below=below)
    if implemented == "xml":
        raise NotImplementedError("XML output conversion is not yet implemented.")
    if implemented == "set":
        from junoscfg.convert.output.set_output import dict_to_set

        return dict_to_set(config, below=below, diagnostic_sink=diagnostic_sink)
    if implemented == "structured":
        from junoscfg.convert.output.structured_output import dict_to_structured

        return dict_to_structured(
            config, diagnostic_sink=diagnostic_sink, withhold_values=withhold_values, below=below
        )
    raise ValueError(f"Unknown implementation {implemented!r} for output format {fmt}")
