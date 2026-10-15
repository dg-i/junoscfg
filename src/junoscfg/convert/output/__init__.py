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
        diagnostic_sink: Optional receiver for renderer diagnostics. The
            caller owns any terminal or log rendering.
        withhold_values: The diagnostics quote no word of the configuration
            (an anonymized conversion): a note gives counts, not paths.

    Returns:
        The rendered configuration as a string.
    """
    from junoscfg.convert.formats import implementation

    implemented = implementation(fmt, "output")
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

        return dict_to_set(config, below=below)
    if implemented == "structured":
        from junoscfg.convert.output.structured_output import dict_to_structured

        return dict_to_structured(
            config, diagnostic_sink=diagnostic_sink, withhold_values=withhold_values, below=below
        )
    raise ValueError(f"Unknown implementation {implemented!r} for output format {fmt}")
