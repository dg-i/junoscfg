"""JSON and YAML configuration validation via JSON Schema.

Validates Junos JSON and YAML configurations against generated JSON Schema.
"""

from __future__ import annotations

import json
import re
from pathlib import Path  # noqa: TC003
from typing import Any

import jsonschema
import yaml

from junoscfg.display import build_from_artifact
from junoscfg.input import find_non_json_value
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
            return _yaml_parse_error(e)

        if data is None:
            return ValidationResult(valid=True)

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
            return ValidationResult(
                valid=False,
                errors=(
                    ValidationError(
                        message=f"YAML {found.kind} {found.reason}",
                        path=found.path or None,
                    ),
                ),
            )
        return _validate_data(data, self._json_validator)


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

    errors: list[ValidationError] = []
    for err in errors_list:
        leaf = _cause(err)
        error = ValidationError(
            message=_message(leaf),
            path=".".join(str(p) for p in leaf.absolute_path) or None,
        )
        if error not in errors:
            errors.append(error)
    return ValidationResult(valid=False, errors=tuple(errors))


def _cause(error: jsonschema.ValidationError) -> jsonschema.ValidationError:
    """The error that says why *error* failed.

    A list's `anyOf` fails as a whole; inside it, each alternative's errors.
    The alternative whose type the instance has is the one that matters (an
    array of entries is judged by the array form, not by the single entry
    form's type), and of its errors the deepest: the entry and the key that
    failed.
    """
    while error.context:
        relevant = [e for e in error.context if e.validator != "type"] or error.context
        error = max(relevant, key=lambda e: len(e.absolute_path))
    return error


#: JSON's name for each Python type a loaded document holds.
_JSON_TYPES = {dict: "object", list: "array", str: "string", bool: "boolean", type(None): "null"}


def _message(error: jsonschema.ValidationError) -> str:
    """What failed, by the keys or the kind of the failure, never by a value.

    jsonschema's own message reprints the instance: a whole list of
    interfaces, `secret` values included (owner's log, 2026-10-16).
    """
    if error.validator == "additionalProperties" and isinstance(error.instance, dict):
        keys = _unexpected_keys(error.instance, error.schema)
        if keys:
            named = ", ".join(repr(key) for key in keys)
            if len(keys) == 1:
                return f"{named} is not a statement the schema places here"
            return f"{named} are not statements the schema places here"
    if error.validator == "type":
        expected = error.validator_value
        wanted = " or ".join(expected) if isinstance(expected, list) else str(expected)
        found = _JSON_TYPES.get(type(error.instance), "number")
        return f"expected {wanted} here, not {found}"
    return f"fails the schema's '{error.validator}' constraint here"


def _unexpected_keys(instance: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """The keys of *instance* its schema neither names nor matches by pattern."""
    named = schema.get("properties", {})
    patterns = list(schema.get("patternProperties", {}))
    return [
        key
        for key in instance
        if key not in named and not any(re.search(pattern, key) for pattern in patterns)
    ]
