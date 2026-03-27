"""Junoscfg: Convert and validate Junos configurations between formats.

Provides convenience functions for converting between display set, structured,
XML, JSON, and YAML configuration formats, as well as validation against the
Junos XSD schema.
"""

from __future__ import annotations

from enum import Enum
from typing import TextIO

from junoscfg.convert.field_validator import FieldValidationError  # noqa: TC001
from junoscfg.validate import ValidationResult  # noqa: TC001

__version__ = "0.5.8"

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


# Supported (from_format, to_format) conversion pairs.
_CONVERTERS: dict[tuple[Format, Format], str] = {
    (Format.JSON, Format.SET): "_convert_json_to_set",
    (Format.JSON, Format.STRUCTURED): "_convert_json_to_structured",
    (Format.JSON, Format.YAML): "_convert_json_to_yaml",
    (Format.XML, Format.SET): "_convert_xml_to_set",
    (Format.XML, Format.STRUCTURED): "_convert_xml_to_structured",
    (Format.XML, Format.YAML): "_convert_xml_to_yaml",
    (Format.YAML, Format.SET): "_convert_yaml_to_set",
    (Format.YAML, Format.STRUCTURED): "_convert_yaml_to_structured",
    (Format.YAML, Format.JSON): "_convert_yaml_to_json",
    (Format.XML, Format.JSON): "_convert_xml_to_json",
    (Format.SET, Format.STRUCTURED): "_convert_set_to_structured",
    (Format.SET, Format.JSON): "_convert_set_to_json",
    (Format.SET, Format.YAML): "_convert_set_to_yaml",
    (Format.STRUCTURED, Format.SET): "_convert_structured_to_set",
    (Format.STRUCTURED, Format.JSON): "_convert_structured_to_json",
    (Format.STRUCTURED, Format.YAML): "_convert_structured_to_yaml",
    # Identity conversions (parse and re-render for normalization)
    (Format.JSON, Format.JSON): "_convert_json_to_json",
    (Format.SET, Format.SET): "_convert_set_to_set",
    (Format.YAML, Format.YAML): "_convert_yaml_to_yaml",
    (Format.STRUCTURED, Format.STRUCTURED): "_convert_structured_to_structured",
}

# All converters go through the pipeline and support validate/strict kwargs.
_PIPELINE_CONVERTERS: frozenset[str] = frozenset(_CONVERTERS.values())


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

    func_name = _CONVERTERS.get((from_format, to_format))
    if func_name is None:
        raise ValueError(f"Unsupported conversion: {from_format.value} -> {to_format.value}")

    converter = globals()[func_name]

    # Pipeline-based converters accept validate/strict/anon_config kwargs
    if func_name in _PIPELINE_CONVERTERS:
        result = converter(source, validate=validate, strict=strict, anon_config=anon_config)
    else:
        result = converter(source)

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
        from junoscfg.display.config_store import filter_structured_by_path

        return filter_structured_by_path(result, path_tokens, relative=relative)
    elif to_format is Format.YAML:
        from junoscfg.display.to_yaml import filter_yaml_by_path

        return filter_yaml_by_path(result, path_tokens, relative=relative)
    elif to_format is Format.JSON:
        from junoscfg.display.to_json import filter_json_by_path

        return filter_json_by_path(result, path_tokens, relative=relative)
    return result


def _read_source(source: str | TextIO) -> str:
    """Read a string or file-like object into a string."""
    return source.read() if hasattr(source, "read") else str(source)  # type: ignore[union-attr]


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


def _convert_json_to_set(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "json", "set", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_json_to_structured(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "json", "structured", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_json_to_yaml(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "json", "yaml", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_xml_to_set(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "xml", "set", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_xml_to_structured(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "xml", "structured", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_xml_to_yaml(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "xml", "yaml", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_yaml_to_set(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "yaml", "set", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_yaml_to_structured(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "yaml", "structured", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_yaml_to_json(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "yaml", "json", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_xml_to_json(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "xml", "json", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_set_to_structured(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "set", "structured", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_set_to_json(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "set", "json", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_set_to_yaml(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "set", "yaml", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_structured_to_json(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "structured", "json", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_structured_to_yaml(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "structured", "yaml", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_structured_to_set(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "structured", "set", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_json_to_json(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "json", "json", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_set_to_set(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "set", "set", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_yaml_to_yaml(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source, "yaml", "yaml", validate=validate, strict=strict, anon_config=anon_config
    )


def _convert_structured_to_structured(
    source: str | TextIO,
    *,
    validate: bool = True,
    strict: bool = False,
    anon_config: object | None = None,
) -> str:
    return _pipeline_convert(
        source,
        "structured",
        "structured",
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
    from junoscfg.validate.validator import JunosValidator

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
    from junoscfg.validate.validator import JunosValidator

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
    from junoscfg.validate.validator import JunosValidator

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
    from junoscfg.validate.validator import JunosValidator

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
    from junoscfg.validate.validator import JunosValidator

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
