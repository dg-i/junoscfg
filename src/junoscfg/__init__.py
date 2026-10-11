"""Junoscfg: Convert and validate Junos configurations between formats.

Provides convenience functions for converting between display set, structured,
XML, JSON, and YAML configuration formats, as well as validation against the
Junos XSD schema.
"""

from __future__ import annotations

from enum import Enum
from typing import TextIO

from junoscfg.convert import ConversionResult, FieldValidationError  # noqa: TC001
from junoscfg.validate import ValidationResult  # noqa: TC001

__version__ = "0.20.3"

__all__ = [
    "Format",
    "convert_config",
    "convert_config_result",
    "ConversionResult",
    "validate_config",
    "validate_xml",
    "validate_json",
    "validate_yaml",
    "validate_set",
    "validate_structured",
    "FieldValidationError",
]


class Format(Enum):
    """Configuration format identifiers for use with :func:`convert`."""

    SET = "set"
    STRUCTURED = "structured"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"


# Supported (from_format, to_format) conversion pairs. XML output is rejected
# separately so callers retain its documented NotImplementedError.
_SUPPORTED_CONVERSIONS: frozenset[tuple[Format, Format]] = frozenset(
    {
        (Format.JSON, Format.SET),
        (Format.JSON, Format.STRUCTURED),
        (Format.JSON, Format.YAML),
        (Format.XML, Format.SET),
        (Format.XML, Format.STRUCTURED),
        (Format.XML, Format.YAML),
        (Format.YAML, Format.SET),
        (Format.YAML, Format.STRUCTURED),
        (Format.YAML, Format.JSON),
        (Format.XML, Format.JSON),
        (Format.SET, Format.STRUCTURED),
        (Format.SET, Format.JSON),
        (Format.SET, Format.YAML),
        (Format.STRUCTURED, Format.SET),
        (Format.STRUCTURED, Format.JSON),
        (Format.STRUCTURED, Format.YAML),
        # Identity conversions (parse and re-render for normalization)
        (Format.JSON, Format.JSON),
        (Format.SET, Format.SET),
        (Format.YAML, Format.YAML),
        (Format.STRUCTURED, Format.STRUCTURED),
    }
)


def convert_config(
    source: str | TextIO,
    *,
    from_format: Format,
    to_format: Format,
    validate: bool = True,
    strict: bool = False,
    path: str | None = None,
    relative: bool = False,
    anon_config: object | None = None,
) -> str:
    """Convert a Junos configuration and return only rendered output.

    It raises as :func:`convert_config_result` does, an anonymized
    conversion's errors included.
    """
    return convert_config_result(
        source,
        from_format=from_format,
        to_format=to_format,
        validate=validate,
        strict=strict,
        path=path,
        relative=relative,
        anon_config=anon_config,
    ).output


def convert_config_result(
    source: str | TextIO,
    *,
    from_format: Format,
    to_format: Format,
    validate: bool = True,
    strict: bool = False,
    path: str | None = None,
    relative: bool = False,
    anon_config: object | None = None,
) -> ConversionResult:
    """Convert a Junos configuration and return output plus diagnostics.

    Args:
        source: Configuration text as a string or file-like object.
        from_format: The input format.
        to_format: The desired output format.
        validate: If True (default), run field-level validation on
            conversion paths that use the dict IR. Non-fatal findings are
            returned as diagnostics.
        strict: If True, raise on field validation errors instead of
            warning.
        path: Dot-separated path to filter output (e.g. ``"system.syslog"``).
        relative: If True, strip the *path* prefix from the output.
            Requires *path* to be set.
        anon_config: An :class:`~junoscfg.anonymize.config.AnonymizeConfig`
            instance, or None to skip anonymization.

    Returns:
        The converted output and immutable diagnostics.

    Raises:
        NotImplementedError: If the target format is XML (not yet supported).
        ValueError: If the format combination is not supported, or if
            *relative* is True without *path*.
        junoscfg.convert.field_validator.FieldValidationError: When
            *strict* is True and validation errors are found.
        RuntimeError: In a conversion that anonymizes, for any other
            failure; it names only the failure's class.

    In a conversion that anonymizes no message quotes the configuration: a
    refusal to read the input is a plain ``ValueError`` (``yaml.YAMLError``
    for YAML; never a subclass such as ``json.JSONDecodeError``) naming only
    its line, with no cause or context; field-validation messages keep path,
    reason and expected value and withhold the value.

    Example:
        >>> convert_config('{"configuration":{"system":{"host-name":"r1"}}}',
        ...         from_format=Format.JSON, to_format=Format.SET)
        'set system host-name r1\\n'
    """
    if relative and not path:
        raise ValueError("relative=True requires path to be set.")

    if to_format is Format.XML:
        raise NotImplementedError("XML output is not yet supported.")

    if (from_format, to_format) not in _SUPPORTED_CONVERSIONS:
        raise ValueError(f"Unsupported conversion: {from_format.value} -> {to_format.value}")

    result = _pipeline_convert_result(
        source,
        from_format.value,
        to_format.value,
        validate=validate,
        strict=strict,
        anon_config=anon_config,
        path=path,
        relative=relative,
    )

    return result


def _read_source(source: str | TextIO) -> str:
    """Read a string or file-like object into a string."""
    return source if isinstance(source, str) else source.read()


def _pipeline_convert_result(
    source: str | TextIO,
    from_fmt: str,
    to_fmt: str,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
    path: str | None = None,
    relative: bool = False,
) -> ConversionResult:
    from junoscfg.convert import pipeline_result

    return pipeline_result(
        _read_source(source),
        from_format=from_fmt,
        to_format=to_fmt,
        validate=validate,
        strict=strict,
        anon_config=anon_config,
        path=path,
        relative=relative,
    )


# ── Validation API ────────────────────────────────────────────────────


def validate_xml(source: str, artifacts_dir: str | None = None) -> ValidationResult:
    """Validate XML configuration against the Junos XSD schema.

    Args:
        source: XML configuration as a string.
        artifacts_dir: Path to custom validation artifacts directory.
            Falls back to ``JUNOSCFG_ARTIFACTS`` env var, then bundled defaults.

    Returns:
        Validation result with any errors found.
    """
    from junoscfg.validate import JunosValidator

    return JunosValidator(artifacts_dir=artifacts_dir).validate_xml(source)


def validate_json(source: str, artifacts_dir: str | None = None) -> ValidationResult:
    """Validate JSON configuration against the Junos schema.

    Args:
        source: JSON configuration as a string.
        artifacts_dir: Path to custom validation artifacts directory.
            Falls back to ``JUNOSCFG_ARTIFACTS`` env var, then bundled defaults.

    Returns:
        Validation result with any errors found.
    """
    from junoscfg.validate import JunosValidator

    return JunosValidator(artifacts_dir=artifacts_dir).validate_json(source)


def validate_yaml(source: str, artifacts_dir: str | None = None) -> ValidationResult:
    """Validate YAML configuration against the Junos schema.

    Args:
        source: YAML configuration as a string.
        artifacts_dir: Path to custom validation artifacts directory.
            Falls back to ``JUNOSCFG_ARTIFACTS`` env var, then bundled defaults.

    Returns:
        Validation result with any errors found.
    """
    from junoscfg.validate import JunosValidator

    return JunosValidator(artifacts_dir=artifacts_dir).validate_yaml(source)


def validate_set(source: str, artifacts_dir: str | None = None) -> ValidationResult:
    """Validate set commands against the Junos schema.

    Args:
        source: Set commands as a string (one per line).
        artifacts_dir: Path to custom validation artifacts directory.
            Falls back to ``JUNOSCFG_ARTIFACTS`` env var, then bundled defaults.

    Returns:
        Validation result with any errors found.
    """
    from junoscfg.validate import JunosValidator

    return JunosValidator(artifacts_dir=artifacts_dir).validate_set(source)


def validate_structured(source: str, artifacts_dir: str | None = None) -> ValidationResult:
    """Validate structured (curly-brace) configuration against the Junos schema.

    Each statement is checked as the conversion walk reads it: one set line
    in the input's own tokens per statement, a one-line statement the walk
    reads as siblings split where each sibling starts
    (:func:`junoscfg.convert.structured_set_lines`). A leaf read without its
    value is an error; what the text holds that yields no statement (the
    device's ``/* OMITTED */`` placeholder, an empty block) is a warning.

    Args:
        source: Structured configuration as a string.
        artifacts_dir: Path to custom validation artifacts directory.
            Falls back to ``JUNOSCFG_ARTIFACTS`` env var, then bundled defaults.
            The schema walk and the set grammar both come from it.

    Returns:
        Validation result with any errors found.

    Raises:
        junoscfg.validate.SchemaLoadError: When the artifacts lack the set
            grammar or the structure tree the walk reads.
    """
    from contextlib import nullcontext

    from junoscfg.convert import structured_set_lines
    from junoscfg.display import artifacts_dir as artifacts_scope
    from junoscfg.display import load_schema_tree
    from junoscfg.validate import JunosValidator, SchemaLoadError, ValidationError

    validator = JunosValidator(artifacts_dir=artifacts_dir)
    scope = artifacts_scope(artifacts_dir) if artifacts_dir is not None else nullcontext()
    with scope:
        try:
            # The walk needs the structure tree: its absence is the artifacts'
            # failure, never a verdict on the configuration (ARCHITECTURE.md §8).
            load_schema_tree()
        except ValueError as e:
            raise SchemaLoadError(str(e)) from e
        try:
            read = structured_set_lines(source)
        except ValueError as e:
            return ValidationResult(
                valid=False,
                errors=(ValidationError(message=f"Failed to convert structured config: {e}"),),
            )

    notes = tuple(
        ValidationError(message=f"{where}: {what}", path=where) for where, what in read.notes
    )
    incomplete = tuple(
        ValidationError(message=f"Invalid syntax: {line}: the statement has no value")
        for line in read.incomplete
    )
    if not read.lines:
        return ValidationResult(valid=True, warnings=notes)
    result = validator.validate_set("\n".join(read.lines))
    return ValidationResult(
        valid=result.valid and not incomplete,
        errors=(*result.errors, *incomplete),
        warnings=(*result.warnings, *notes),
    )


def validate_config(
    source: str,
    *,
    format: str | Format | None = None,  # noqa: A002
    artifacts_dir: str | None = None,
) -> ValidationResult:
    """Validate a Junos configuration, dispatching by format.

    Args:
        source: Configuration text.
        format: Input format (``"xml"``, ``"json"``, ``"yaml"``, ``"set"``,
            ``"structured"``, or a :class:`Format` enum member).
            If ``None``, auto-detects set vs structured.
        artifacts_dir: Path to custom validation artifacts directory.
            Falls back to ``JUNOSCFG_ARTIFACTS`` env var, then bundled defaults.

    Returns:
        :class:`~junoscfg.validate.ValidationResult` with any errors found.

    Raises:
        junoscfg.validate.SchemaLoadError: When validation artifacts
            cannot be loaded.
    """
    # Normalise Format enum to string
    fmt = format.value if isinstance(format, Format) else format

    if fmt == "xml":
        return validate_xml(source, artifacts_dir=artifacts_dir)
    elif fmt == "json":
        return validate_json(source, artifacts_dir=artifacts_dir)
    elif fmt == "yaml":
        return validate_yaml(source, artifacts_dir=artifacts_dir)
    elif fmt == "set":
        return validate_set(source, artifacts_dir=artifacts_dir)
    elif fmt == "structured":
        return validate_structured(source, artifacts_dir=artifacts_dir)
    else:
        from junoscfg.display import VALIDATION_FORMATS, detect_format

        if not source.strip():
            return validate_structured(source, artifacts_dir=artifacts_dir)
        detected = detect_format(source, accepted_formats=VALIDATION_FORMATS)
        if detected == "set":
            return validate_set(source, artifacts_dir=artifacts_dir)
        return validate_structured(source, artifacts_dir=artifacts_dir)
