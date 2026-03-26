"""JSON and YAML configuration validation via JSON Schema.

Validates Junos JSON and YAML configurations against generated JSON Schema.
"""

from __future__ import annotations

import json
from pathlib import Path  # noqa: TC003

import jsonschema
import yaml

from junoscfg.validate import SchemaLoadError, ValidationError, ValidationResult


class JsonYamlValidator:
    """Validates Junos JSON and YAML configurations."""

    def __init__(
        self,
        json_schema_path: str | Path | None = None,
        yaml_schema_path: str | Path | None = None,
    ) -> None:
        """Load JSON Schema files.

        Args:
            json_schema_path: Path to JSON format schema.
            yaml_schema_path: Path to YAML format schema.

        Raises:
            SchemaLoadError: If schemas cannot be loaded.
        """
        self._json_validator = None
        self._yaml_validator = None

        if json_schema_path:
            self._json_validator = _load_validator(json_schema_path, "JSON")
        if yaml_schema_path:
            self._yaml_validator = _load_validator(yaml_schema_path, "YAML")

    def validate_json(self, source: str) -> ValidationResult:
        """Validate a JSON configuration.

        Args:
            source: JSON configuration as a string.

        Returns:
            ValidationResult with errors if invalid.
        """
        if self._json_validator is None:
            raise SchemaLoadError("JSON schema not loaded")

        try:
            data = json.loads(source)
        except json.JSONDecodeError as e:
            return ValidationResult(
                valid=False,
                errors=(ValidationError(message=f"JSON parse error: {e}", line=e.lineno),),
            )

        return _validate_data(data, self._json_validator)

    def validate_yaml(self, source: str) -> ValidationResult:
        """Validate a YAML configuration.

        Args:
            source: YAML configuration as a string.

        Returns:
            ValidationResult with errors if invalid.
        """
        if self._yaml_validator is None:
            raise SchemaLoadError("YAML schema not loaded")

        try:
            data = yaml.safe_load(source)
        except yaml.YAMLError as e:
            line = None
            if hasattr(e, "problem_mark") and e.problem_mark is not None:
                line = e.problem_mark.line + 1
            return ValidationResult(
                valid=False,
                errors=(ValidationError(message=f"YAML parse error: {e}", line=line),),
            )

        if data is None:
            return ValidationResult(valid=True)

        return _validate_data(data, self._yaml_validator)


def _load_validator(schema_path: str | Path, label: str) -> jsonschema.Draft7Validator:
    """Load and compile a JSON Schema validator."""
    try:
        with open(schema_path) as f:
            schema = json.load(f)
        return jsonschema.Draft7Validator(schema)
    except Exception as e:
        raise SchemaLoadError(f"Failed to load {label} schema: {e}") from e


def _validate_data(
    data: dict,
    validator: jsonschema.Draft7Validator,
) -> ValidationResult:
    """Validate parsed data against a JSON Schema validator."""
    # Unwrap configuration wrapper if present
    if isinstance(data, dict):
        # Handle rpc-reply wrapper
        if "rpc-reply" in data:
            data = data["rpc-reply"]
        # If it's already under "configuration" key, validate as-is
        # If not, wrap it
        if "configuration" not in data:
            data = {"configuration": data}

    errors_list = list(validator.iter_errors(data))

    if not errors_list:
        return ValidationResult(valid=True)

    errors = tuple(
        ValidationError(
            message=err.message,
            path=".".join(str(p) for p in err.absolute_path) or None,
        )
        for err in errors_list
    )
    return ValidationResult(valid=False, errors=errors)
