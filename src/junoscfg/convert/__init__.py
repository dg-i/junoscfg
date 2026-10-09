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

    # Standalone field validation
    result = validate_ir(ir)
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from junoscfg.anonymize import AnonymizeConfig

from junoscfg.convert.field_validator import FieldValidationError
from junoscfg.convert.input import to_dict
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
    """Convert a configuration between any two supported formats.

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
        validate: If True (default), run field-level validation. Warnings
                  are printed to stderr.
        strict: If True, raise :class:`FieldValidationError` on validation
                errors instead of just warning.
        anon_config: An :class:`~junoscfg.anonymize.config.AnonymizeConfig`
                     instance, or None to skip anonymization.
        path: Dot-separated path to select before rendering.
        relative: If True, render only the selected subtree rather than
                  rebuilding its parent hierarchy. Requires *path*.

    Returns:
        The converted configuration as a string.

    Raises:
        FieldValidationError: When *strict* is True and validation errors
            are found.
        ValueError: When *relative* is True without *path*.
    """
    if relative and not path:
        raise ValueError("relative=True requires path to be set.")

    ir = to_dict(source, from_format)

    if anon_config is not None:
        cfg: AnonymizeConfig = anon_config  # type: ignore[assignment]

        if cfg.any_enabled:
            _refuse_unplaced(ir)

        # Revert mode: apply a saved mapping to restore originals
        if cfg.revert_map:
            from junoscfg.anonymize import apply_revert, load_mapping

            mapping = load_mapping(cfg.revert_map)
            apply_revert(ir, mapping)

        # Normal anonymization mode
        if cfg.any_enabled:
            from junoscfg.anonymize import anonymize

            anon_result = anonymize(ir, cfg)
            ir = anon_result.ir

            # Dump the revert mapping if requested
            if cfg.dump_map:
                from junoscfg.anonymize import export_mapping

                export_mapping(anon_result.mapping, cfg.dump_map)

    if validate:
        from junoscfg.convert.field_validator import FieldValidationError, FieldValidator

        result = FieldValidator().validate(ir)
        if not result.valid:
            if strict:
                raise FieldValidationError(result)
            else:
                _report_warnings(result)

    if path:
        from junoscfg.display import filter_dict_by_path

        filtered = filter_dict_by_path(ir, path.split("."), relative=relative)
        if filtered is None:
            return ""
        ir = filtered

    if relative and to_format in {"json", "yaml"}:
        return from_dict(ir, to_format, wrap=False)
    return from_dict(ir, to_format)


def validate_ir(config: dict[str, Any]) -> Any:
    """Validate an IR dict against field-level schema constraints.

    Args:
        config: The IR dict (content inside ``{"configuration": ...}``).

    Returns:
        A :class:`~junoscfg.convert.field_validator.FieldValidationResult`.
    """
    from junoscfg.convert.field_validator import FieldValidator

    return FieldValidator().validate(config)


def _refuse_unplaced(ir: dict[str, Any]) -> None:
    """Fail anonymization on a statement the schema could not place.

    The anonymizer is schema-guided and never rewrites a key the schema does
    not name, so a statement kept as written would leave verbatim -- with the
    address in `set protocols bgp neighbor 10.11.12.13 ...` in it -- where the
    reader used to drop it. Refusing is the one answer that neither loses nor
    leaks; it holds whatever ``validate`` and ``strict`` say.
    """
    from junoscfg.convert.field_validator import (
        UNPLACED,
        FieldError,
        FieldValidationError,
        FieldValidationResult,
        FieldValidator,
    )

    unplaced = [
        FieldError(path=e.path, message=f"cannot anonymize: {e.message}", value=e.value)
        for e in FieldValidator().validate(ir).errors
        if e.expected == UNPLACED
    ]
    if unplaced:
        raise FieldValidationError(FieldValidationResult(errors=unplaced))


def _report_warnings(result: Any) -> None:
    """Print field validation errors/warnings to stderr."""
    for err in result.errors:
        print(f"field-validate: {err.path}: {err.message}", file=sys.stderr)
    for warn in result.warnings:
        print(f"field-validate: {warn.path}: {warn.message}", file=sys.stderr)


__all__ = [
    "FieldValidationError",
    "find_configuration",
    "from_dict",
    "pipeline",
    "to_dict",
    "validate_ir",
]
