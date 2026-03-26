"""Structured configuration validation.

Thin wrapper: converts structured config to set commands, then validates.
"""

from __future__ import annotations

from junoscfg.validate import ValidationError, ValidationResult


class StructuredValidator:
    """Validates Junos structured (curly-brace) configurations."""

    def __init__(self, set_validator: object) -> None:
        """Initialize with a SetValidator instance.

        Args:
            set_validator: A SetValidator instance for validating converted set commands.
        """
        self._set_validator = set_validator

    def validate(self, source: str) -> ValidationResult:
        """Validate structured configuration.

        Converts to set commands first, then validates with SetValidator.

        Args:
            source: Structured configuration as a string.

        Returns:
            ValidationResult with errors if invalid.
        """
        from junoscfg.display.set_converter import SetConverter

        try:
            set_commands = SetConverter(source).to_set()
        except Exception as e:
            return ValidationResult(
                valid=False,
                errors=(ValidationError(message=f"Failed to convert structured config: {e}"),),
            )

        if not set_commands.strip():
            return ValidationResult(valid=True)

        # Delegate to set validator
        return self._set_validator.validate(set_commands)  # type: ignore[union-attr]
