"""Unified conversion pipeline: Any Format → JSON Dict IR → Any Format.

Public API::

    from junoscfg.convert import pipeline, to_dict, from_dict, validate_ir

    # Full pipeline
    result = pipeline("set system host-name r1", from_format="set", to_format="json")

    # Full pipeline with strict validation
    result = pipeline("set system host-name r1", from_format="set", to_format="json",
                       strict=True)

    # Input only (any format → dict)
    ir = to_dict('{"configuration": {"system": {"host-name": "r1"}}}', "json")

    # Output only (dict → any format)
    output = from_dict(ir, "set")

    # Standalone field validation: a FieldValidationResult of FieldErrors;
    # an error whose ``expected`` is UNPLACED is a statement the schema
    # could not place
    result = validate_ir(ir)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from junoscfg.anonymize import AnonymizeConfig

from junoscfg.convert.diagnostics import ConversionResult, Diagnostic
from junoscfg.convert.field_validator import (
    UNPLACED,
    FieldError,
    FieldValidationError,
    FieldValidationResult,
)
from junoscfg.convert.input import to_dict
from junoscfg.convert.input.structured_input import StructuredSetLines, structured_set_lines
from junoscfg.convert.ir import find_configuration
from junoscfg.convert.output import from_dict


def pipeline(
    source: str,
    *,
    from_format: str,
    to_format: str,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
    path: str | None = None,
    relative: bool = False,
) -> str:
    """Convert a configuration and return only its rendered output."""
    return pipeline_result(
        source,
        from_format=from_format,
        to_format=to_format,
        validate=validate,
        strict=strict,
        anon_config=anon_config,
        path=path,
        relative=relative,
    ).output


def pipeline_result(
    source: str,
    *,
    from_format: str,
    to_format: str,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
    path: str | None = None,
    relative: bool = False,
) -> ConversionResult:
    """Convert a configuration and return output plus diagnostics.

    This is the core conversion function. It:
    1. Parses *source* into the JSON dict IR via the appropriate input converter
    2. Optionally anonymizes the IR according to *anon_config*
    3. Optionally validates leaf values against schema constraints
    4. Optionally selects a path from the IR
    5. Renders the IR into the target format via the appropriate output converter

    Args:
        source: Configuration text.
        from_format: Input format name (``"json"``, ``"yaml"``, ``"xml"``,
                     ``"set"``, ``"structured"``).
        to_format: Output format name (same choices).
        validate: If True (default), run field-level validation. Non-fatal
                  findings are returned as diagnostics.
        strict: If True, raise :class:`FieldValidationError` on validation
                errors instead of just warning.
        anon_config: An :class:`~junoscfg.anonymize.config.AnonymizeConfig`
                     instance, or None to skip anonymization.
        path: Dot-separated path to select before rendering.
        relative: If True, render only the selected subtree rather than
                  rebuilding its parent hierarchy. Requires *path*.

    Returns:
        The converted output and immutable diagnostics.

    Raises:
        FieldValidationError: When *strict* is True and validation errors
            are found.
        ValueError: When *relative* is True without *path*, or the input
            cannot be read.
        RuntimeError: In a conversion that anonymizes, for any failure but
            those above: "the conversion failed (<class>); details withheld:
            the run anonymizes", the wording the CLI prints.

    A conversion that anonymizes quotes no word of the configuration in what
    it raises: a refusal to read the input is a fresh `ValueError`
    (`yaml.YAMLError` for YAML) naming its line, any other failure a fresh
    `RuntimeError` naming its class, both with no cause, context or notes
    (spec anonymization/placed-values).
    """
    if relative and not path:
        raise ValueError("relative=True requires path to be set.")

    anonymizing = bool(getattr(anon_config, "any_enabled", False))
    if not anonymizing:
        return _convert(
            source, from_format, to_format, validate, strict, anon_config, path, relative, False
        )
    failure: Exception
    try:
        return _convert(
            source, from_format, to_format, validate, strict, anon_config, path, relative, True
        )
    except FieldValidationError:
        raise  # its reports are withheld already
    except _UnreadableError as unreadable:
        failure = _withheld_refusal(unreadable.error)
    except Exception as error:  # noqa: BLE001 -- every failure is withheld, by class
        failure = _withheld_failure(error)
    # Raised outside the handler, so the original is neither its cause nor its context.
    raise failure


class _UnreadableError(Exception):
    """A reader's refusal, carried to `pipeline_result` to be withheld."""

    def __init__(self, error: Exception) -> None:
        super().__init__(type(error).__name__)
        self.error = error


def _convert(
    source: str,
    from_format: str,
    to_format: str,
    validate: bool,
    strict: bool,
    anon_config: object | None,
    path: str | None,
    relative: bool,
    anonymizing: bool,
) -> ConversionResult:
    """`pipeline_result`'s steps; *anonymizing* decides what the messages may quote."""
    diagnostics: list[Diagnostic] = []
    # The reader's warnings name a path of the input, values included; they
    # join the result once it is known whether the conversion anonymizes.
    read_notes: list[tuple[str, str]] = []
    try:
        ir = to_dict(
            source,
            from_format,
            diagnostic_sink=lambda where, what: read_notes.append((where, what)),
        )
    except Exception as error:
        if anonymizing:
            raise _UnreadableError(error) from None
        raise
    for where, what in read_notes:
        if anonymizing:
            # A block that yields no statement never reaches the IR, so no
            # rule sees its keys: the path is withheld rather than shown.
            withheld = f"{what} (the block's path is withheld: the conversion anonymizes)"
            diagnostics.append(Diagnostic(source="structured-input", message=withheld))
        else:
            diagnostics.append(Diagnostic(source="structured-input", path=where, message=what))

    if anon_config is not None:
        cfg: AnonymizeConfig = anon_config  # type: ignore[assignment]

        # Revert mode: apply a saved mapping to restore originals
        if cfg.revert_map:
            from junoscfg.anonymize import apply_revert, load_mapping

            mapping = load_mapping(cfg.revert_map)
            apply_revert(ir, mapping)

        # Normal anonymization mode
        if cfg.any_enabled:
            from junoscfg.anonymize import anonymize

            anon_result = anonymize(
                ir,
                cfg,
                diagnostic_sink=lambda message: diagnostics.append(
                    Diagnostic(source="anonymize", message=message, severity="debug")
                ),
            )
            ir = anon_result.ir
            diagnostics.extend(_unplaced_warnings(anon_result.unplaced, cfg))
            diagnostics.extend(_pattern_warnings(anon_result.patterns))

            # Dump the revert mapping if requested
            if cfg.dump_map:
                from junoscfg.anonymize import export_mapping

                export_mapping(anon_result.mapping, cfg.dump_map)

    if validate:
        from junoscfg.convert.field_validator import FieldValidationError, FieldValidator

        result = FieldValidator(withhold_values=anonymizing).validate(ir)
        if not result.valid:
            if strict:
                raise FieldValidationError(result)
            else:
                diagnostics.extend(
                    Diagnostic(
                        source="field-validate",
                        path=item.path,
                        message=item.message,
                    )
                    for item in (*result.errors, *result.warnings)
                )

    if path:
        from junoscfg.display import filter_dict_by_path

        filtered = filter_dict_by_path(ir, path.split("."), relative=relative)
        if filtered is None:
            return ConversionResult(output="", diagnostics=tuple(diagnostics))
        ir = filtered

    if relative and to_format in {"json", "yaml"}:
        output = from_dict(
            ir,
            to_format,
            wrap=False,
            withhold_values=anonymizing,
            diagnostic_sink=lambda message: diagnostics.append(
                Diagnostic(source="structured-output", message=message, severity="note")
            ),
        )
    else:
        output = from_dict(
            ir,
            to_format,
            withhold_values=anonymizing,
            diagnostic_sink=lambda message: diagnostics.append(
                Diagnostic(source="structured-output", message=message, severity="note")
            ),
        )
    return ConversionResult(output=output, diagnostics=tuple(diagnostics))


def validate_ir(config: dict[str, Any]) -> Any:
    """Validate an IR dict against field-level schema constraints.

    Args:
        config: The IR dict (content inside ``{"configuration": ...}``).

    Returns:
        A :class:`~junoscfg.convert.field_validator.FieldValidationResult`.
    """
    from junoscfg.convert.field_validator import FieldValidator

    return FieldValidator().validate(config)


def _unplaced_warnings(unplaced: tuple[str, ...], cfg: AnonymizeConfig) -> list[Diagnostic]:
    """One warning per schema path the anonymizer could not place content at.

    The path holds schema names only; the content, its key and every entry
    name are withheld (owner answer 5, spec anonymization/placed-values). The
    message names only the shapes the active rules replace.
    """
    counts: dict[str, int] = {}
    for path in unplaced:
        counts[path] = counts.get(path, 0) + 1
    shapes = [
        shape
        for shape, active in (
            ("address", cfg.ips),
            ("password hash", cfg.passwords),
            ("sensitive word", bool(cfg.sensitive_words or cfg.sensitive_patterns)),
        )
        if active
    ]
    replaced = (
        f"each {' or '.join(shapes)} in it is replaced, every other word is left as written"
        if shapes
        else "no active rule replaces a word of it by its shape; every word is left as written"
    )
    return [
        Diagnostic(
            source="anonymize",
            path=path or None,
            message=(
                f"{count} statement(s) {'here' if path else 'at the top level'} the schema "
                f"does not place: {replaced}"
            ),
        )
        for path, count in counts.items()
    ]


def _pattern_warnings(patterns: tuple[str, ...]) -> list[Diagnostic]:
    """One warning per schema path holding wildcard names anonymization changed the meaning of.

    The path holds schema names only; the wildcard and the names it selects
    are withheld (spec anonymization/placed-values).
    """
    counts: dict[str, int] = {}
    for path in patterns:
        counts[path] = counts.get(path, 0) + 1
    return [
        Diagnostic(
            source="anonymize",
            path=path,
            message=(
                f"{count} wildcard name(s) here select other names once anonymized, or hold "
                "text no rule could rewrite as a pattern, which is left as written"
            ),
        )
        for path, count in counts.items()
    ]


def _withheld_refusal(error: Exception) -> Exception:
    """A reader's refusal, as an anonymized conversion raises it.

    Every reader's refusal may quote the input: the set reader's bracket line,
    the structured reader's statement, PyYAML's snippet, the XML reader's
    element names, and `json.JSONDecodeError.doc` holds the whole source. The
    run raises a fresh error of the same family (`ValueError`,
    `yaml.YAMLError`) saying where -- each reader sets `lineno` on its
    refusal, PyYAML marks it -- never what. Anything else a reader raises is
    a failure (`_withheld_failure`).
    """
    import yaml

    line = getattr(error, "lineno", None)
    mark = getattr(error, "problem_mark", None) or getattr(error, "context_mark", None)
    if line is None and mark is not None:
        line = mark.line + 1
    where = f" (line {line})" if isinstance(line, int) else ""
    message = (
        f"the input could not be read{where}; the reason quotes the input, so it is "
        "withheld: the conversion anonymizes (convert it without anonymizing to see it)"
    )
    if isinstance(error, yaml.YAMLError):
        return yaml.YAMLError(message)
    if isinstance(error, ValueError):
        return ValueError(message)
    return _withheld_failure(error)


def _withheld_failure(error: Exception) -> RuntimeError:
    """Any other failure of an anonymized conversion: its class, never its text or notes."""
    return RuntimeError(
        f"the conversion failed ({type(error).__name__}); details withheld: the run anonymizes"
    )


__all__ = [
    "UNPLACED",
    "ConversionResult",
    "Diagnostic",
    "FieldError",
    "FieldValidationError",
    "FieldValidationResult",
    "StructuredSetLines",
    "find_configuration",
    "from_dict",
    "pipeline",
    "pipeline_result",
    "structured_set_lines",
    "to_dict",
    "validate_ir",
]
