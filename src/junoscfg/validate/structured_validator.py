"""Structured configuration validation, schema-free. Deprecated.

Converts structured config to set commands with `SetConverter.to_set()`, then
validates them. This package may not import `junoscfg.convert`, so it cannot
read a one-line statement as the conversion walk does;
`junoscfg.validate_structured()` composes that walk with set validation.
"""

from __future__ import annotations

import warnings

from junoscfg.validate import ValidationError, ValidationResult

DEPRECATION = (
    "{door} is deprecated and will be removed in the next minor release: it validates "
    "curly text without the schema walk, so it rejects a one-line statement such as "
    "`hold-time up 2000 down 0;`. Use junoscfg.validate_structured()."
)


class StructuredValidator:
    """Validates Junos structured (curly-brace) configurations. Deprecated."""

    def __init__(self, set_validator: object) -> None:
        """Initialize with a SetValidator instance.

        Args:
            set_validator: A SetValidator instance for validating converted set commands.
        """
        self._set_validator = set_validator

    def validate(self, source: str) -> ValidationResult:
        """Validate structured configuration. Deprecated.

        Converts to set commands first, then validates with SetValidator.
        What the text holds that yields no statement is a warning.

        Args:
            source: Structured configuration as a string.

        Returns:
            ValidationResult with errors if invalid.
        """
        warnings.warn(
            DEPRECATION.format(door="StructuredValidator"), DeprecationWarning, stacklevel=2
        )
        return self._validate(source)

    def _validate(self, source: str) -> ValidationResult:
        """`validate` without its warning; the facade door warns in its own name."""
        from junoscfg.display import SetConverter

        converter = SetConverter(source)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                set_commands = converter.to_set()
        except Exception as e:
            return ValidationResult(
                valid=False,
                errors=(ValidationError(message=f"Failed to convert structured config: {e}"),),
            )

        notes = tuple(
            ValidationError(message=str(note), path=note.path) for note in converter.notes()
        )
        if not set_commands.strip():
            return ValidationResult(valid=True, warnings=notes)

        # Delegate to set validator
        result: ValidationResult = self._set_validator.validate(set_commands)  # type: ignore[attr-defined]
        return ValidationResult(
            valid=result.valid, errors=result.errors, warnings=(*result.warnings, *notes)
        )
