"""Junoscfg: Convert and validate Junos configurations between formats.

Provides convenience functions for converting between display set, structured,
XML, JSON, and YAML configuration formats, as well as validation against the
Junos XSD schema.
"""

from __future__ import annotations

from enum import Enum
from typing import TextIO

from junoscfg.convert import FieldValidationError  # noqa: TC001
from junoscfg.validate import ValidationResult  # noqa: TC001

__version__ = "0.13.0"

__all__ = [
    "Format",
    "convert_config",
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
    """Convert a Junos configuration between formats.

    Args:
        source: Configuration text as a string or file-like object.
        from_format: The input format.
        to_format: The desired output format.
        validate: If True (default), run field-level validation on
            conversion paths that use the dict IR.  Warnings are printed
            to stderr.
        strict: If True, raise on field validation errors instead of
            warning.
        path: Dot-separated path to filter output (e.g. ``"system.syslog"``).
        relative: If True, strip the *path* prefix from the output.
            Requires *path* to be set.
        anon_config: An :class:`~junoscfg.anonymize.config.AnonymizeConfig`
            instance, or None to skip anonymization.

    Returns:
        The converted configuration as a string.

    Raises:
        NotImplementedError: If the target format is XML (not yet supported).
        ValueError: If the format combination is not supported, or if
            *relative* is True without *path*.
        junoscfg.convert.field_validator.FieldValidationError: When
            *strict* is True and validation errors are found.

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

    result = _pipeline_convert(
        source,
        from_format.value,
        to_format.value,
        validate=validate,
        strict=strict,
        anon_config=anon_config,
    )

    if path and result:
        result = _filter_by_path(result, to_format, path, relative)

    return result


def _filter_by_path(result: str, to_format: Format, path: str, relative: bool) -> str:
    """Dispatch path filtering to the appropriate format-specific filter."""
    path_tokens = path.split(".")

    if to_format is Format.SET:
        from junoscfg.display import filter_set_by_path

        return filter_set_by_path(result, path_tokens, relative=relative)
    elif to_format is Format.STRUCTURED:
        from junoscfg.display import filter_structured_by_path

        return filter_structured_by_path(result, path_tokens, relative=relative)
    elif to_format is Format.YAML:
        from junoscfg.display import filter_yaml_by_path

        return filter_yaml_by_path(result, path_tokens, relative=relative)
    elif to_format is Format.JSON:
        from junoscfg.display import filter_json_by_path

        return filter_json_by_path(result, path_tokens, relative=relative)
    return result


def _read_source(source: str | TextIO) -> str:
    """Read a string or file-like object into a string."""
    return source if isinstance(source, str) else source.read()


def _pipeline_convert(
    source: str | TextIO,
    from_fmt: str,
    to_fmt: str,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    from junoscfg.convert import pipeline

    return pipeline(
        _read_source(source),
        from_format=from_fmt,
        to_format=to_fmt,
        validate=validate,
        strict=strict,
        anon_config=anon_config,
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

    Converts to set commands internally, then validates.

    Args:
        source: Structured configuration as a string.
        artifacts_dir: Path to custom validation artifacts directory.
            Falls back to ``JUNOSCFG_ARTIFACTS`` env var, then bundled defaults.

    Returns:
        Validation result with any errors found.
    """
    from junoscfg.validate import JunosValidator

    return JunosValidator(artifacts_dir=artifacts_dir).validate_structured(source)


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
        # Auto-detect set vs structured
        from junoscfg.display import is_display_set

        if is_display_set(source):
            return validate_set(source, artifacts_dir=artifacts_dir)
        return validate_structured(source, artifacts_dir=artifacts_dir)
