"""JSON and YAML configuration validation via JSON Schema.

Validates Junos JSON and YAML configurations against generated JSON Schema.
"""

from __future__ import annotations

import json
from pathlib import Path  # noqa: TC003

import jsonschema
import yaml

from junoscfg.display import build_from_artifact
from junoscfg.input import META_KEY_PREFIXES, NonJsonValue, find_non_json_value
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

        A value nested deeper than 64 levels, which the ``json`` reader refuses,
        is an error naming its path (`find_non_json_value`).

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

        found = find_non_json_value(data)
        if found is not None:
            return _refused(found, "JSON")
        return _validate_data(data, self._json_validator)

    def validate_yaml(self, source: str) -> ValidationResult:
        """Validate a YAML configuration (the format ``yaml``).

        What the ``yaml`` reader refuses outside the ``_ansible*`` and
        ``_meta_*`` keys, which the schema admits unread, is an error naming its
        kind and path (`find_non_json_value`): a mapping key that is not a
        string, a cycle, or a value nested deeper than 64 levels.

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
            return _yaml_parse_error(e)

        if data is None:
            return ValidationResult(valid=True)

        found = find_non_json_value(data, scalars=False, unwalked=META_KEY_PREFIXES)
        if found is not None:
            return _refused(found, "YAML")
        return _validate_data(data, self._yaml_validator)

    def validate_yaml_as_json(self, source: str) -> ValidationResult:
        """Validate YAML that spells the Junos JSON object (the format ``yaml-new``).

        The loaded object is judged by the JSON schema, exactly as
        :meth:`validate_json` judges the same object; an empty document is
        the object ``null``. A mapping or list shared through an alias is
        judged written out; a value no JSON document can hold (a timestamp, a
        key that is not a string), a cycle, or a value nested deeper than 64
        levels (`find_non_json_value`) is an error naming its kind and path,
        as conversion refuses it.

        Args:
            source: YAML configuration as a string.

        Returns:
            ValidationResult with errors if invalid.
        """
        if self._json_validator is None:
            raise SchemaLoadError("JSON schema not loaded")

        try:
            data = yaml.safe_load(source)
        except yaml.YAMLError as e:
            return _yaml_parse_error(e)

        found = find_non_json_value(data)
        if found is not None:
            return _refused(found, "YAML")
        return _validate_data(data, self._json_validator)


def _refused(found: NonJsonValue, label: str) -> ValidationResult:
    """The invalid result for what the *label* reader refuses, by its kind and path."""
    return ValidationResult(
        valid=False,
        errors=(
            ValidationError(
                message=f"{label} {found.kind} {found.reason}", path=found.path or None
            ),
        ),
    )


def _yaml_parse_error(error: yaml.YAMLError) -> ValidationResult:
    """The invalid result for a document PyYAML could not parse, with its line."""
    line = None
    if hasattr(error, "problem_mark") and error.problem_mark is not None:
        line = error.problem_mark.line + 1
    return ValidationResult(
        valid=False,
        errors=(ValidationError(message=f"YAML parse error: {error}", line=line),),
    )


def _load_validator(schema_path: str | Path, label: str) -> jsonschema.Draft7Validator:
    """Load and compile a JSON Schema validator."""
    try:
        return build_from_artifact(schema_path, _compile)
    except Exception as e:
        raise SchemaLoadError(f"Failed to load {label} schema: {e}") from e


def _compile(schema_text: str) -> jsonschema.Draft7Validator:
    """The validator for a schema; one per schema file and process, through the cache."""
    return jsonschema.Draft7Validator(json.loads(schema_text))


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
